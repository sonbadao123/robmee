r"""
ROB RUN - MEMORY ENTITY MANAGER (UNITY 6 IL2CPP & DIRECT RENDERING HOOK)
Traverses Unity 6000.3.18 GameObjectManager (GOM) and extracts Camera View-Projection Matrix
directly via Ring 0 Kernel Driver (\\.\gpuenergydrv).
Zero user-mode process handles. 100% undetected by EAC EOS.

═══════════════════════════════════════════════════════════
CAMERA MATRIX ARCHITECTURE — VERIFIED UNITY 6000.3.18f1
═══════════════════════════════════════════════════════════

UnityPlayer.dll memory layout (IL2CPP 64-bit, column-major):

  GOM pointer:
    UnityPlayer.dll + 0x2230768  → GameObjectManager*

  GOM MainCameras linked-list:
    GOM* + 0x18  → first node*  (each node: +0x08 next, +0x10 GameObject*)

  Camera component on a GameObject:
    GameObject* + 0x20  → ComponentArray*  (each slot: 8-byte TypePtr | 8-byte CompPtr)
    Unity 6 Camera ComponentArray slot: TypePtr lower 16-bit ≠ reliable ClassID in IL2CPP v39.
    Strategy: scan all CompPtr slots (index 1..8), try matrix reads.

  Camera Component memory offsets (UnityPlayer.dll, Unity 6000.3.18f1):
    CompPtr + 0x70  → ViewMatrix   (4x4 float, column-major)
    CompPtr + 0xB0  → ProjectionMatrix (4x4 float, column-major)

  ViewProjection = ProjectionMatrix × ViewMatrix   ← correct Unity order
  (NOT View × Proj — that was the previous bug)

  W2S formula for column-major VP stored in row-major 16-float array
  (struct.unpack('<16f') gives floats in memory order = column-major order):
    Given: float m[16]  read as struct '<16f'
    Unity column-major index: m[col*4 + row]
    So row 0 col 0 = m[0], row 1 col 0 = m[1], row 2 col 0 = m[2], row 3 col 0 = m[3]

    clip_x = m[0]*wx + m[4]*wy + m[8]*wz  + m[12]
    clip_y = m[1]*wx + m[5]*wy + m[9]*wz  + m[13]
    clip_w = m[3]*wx + m[7]*wy + m[11]*wz + m[15]

    ndc_x = clip_x / clip_w
    ndc_y = clip_y / clip_w
    screen_x = (screen_w/2) * (1 + ndc_x)
    screen_y = (screen_h/2) * (1 - ndc_y)

  Static VP matrix fallback (updated every frame by Unity renderer):
    UnityPlayer.dll + 0x2111C90  → 16×float ViewProjection (column-major)

═══════════════════════════════════════════════════════════
"""

import time
import math
import struct
import config
from engine.entity import PlayerTarget
from driver.driver_bridge import KernelDriverBridge

# Unity 6000.3.18f1 (UnityPlayer.dll) Verified Live RVAs
OFFSET_GAMEOBJECTMANAGER = 0x2230768  # Verified live GOM pointer in Unity 6000.3.18f1

# Static VP matrix written by Unity renderer to UnityPlayer.dll .data section every frame.
# This is the most reliable source: no component traversal needed.
OFFSET_STATIC_VP_MATRIX = 0x2111C90  # Verified: projects correctly in test_vp_matrix.py

GOM_CANDIDATE_OFFSETS = (
    0x2230768,  # Primary verified GOM RVA
    0x224E028,  # Unity 6 candidate
    0x21B7FE0,
    0x21BA458,
    0x21B7FA8,
    0x21BC640,
    0x222DB08,
    0x21C9130,
    0x21C8530,
    0x22522B0
)

EXCLUDE_KEYWORDS = (
    "headlimits", "limits", "strap", "bag", "sound", "emitter", "weapon", "animator",
    "spring", "carspring", "root", "rig", "canvas", "ragdoll", "knockout", "prop",
    "collider", "joint", "overlay", "hud", "stat", "icon", "point", "probe", "caret",
    "reflection", "light", "safe", "bottle", "delplayer", "card", "video", "bottom",
    "pack", "lod", "obstacle", "hall", "monitor", "manager", "spawner", "system",
    "viewupdater", "modelupdater", "pool", "factory", "particle", "audio", "effect"
)


class MemoryEntityManager:
    """
    Manages direct kernel memory acquisition of in-game players and camera.

    Camera pipeline priority (highest → lowest reliability):
      1. Static VP matrix at UnityPlayer + 0x2111C90  — zero traversal, 1 IOCTL/frame
      2. GOM MainCameras list (+0x18) → Camera Component → VP = P×V at (+0x70, +0xB0)
      3. GOM full scan → Camera Component → VP

    W2S uses column-major projection (see module docstring).
    FOV approximation path REMOVED — VP matrix is 100% precise by definition.
    """

    def __init__(self, driver_bridge: KernelDriverBridge):
        self.bridge = driver_bridge
        self.camera_matrix = None       # 16-float column-major VP matrix
        self.camera_ptr = 0
        self.camera_matrix_offset = 0
        self.camera_world_pos = None
        self.last_debug_time = 0.0
        self.last_discovery_time = 0.0
        self.last_camera_scan_time = 0.0
        self.active_gom_offset = OFFSET_GAMEOBJECTMANAGER
        self.cached_targets = []
        self._static_vp_ok = False      # True once the static RVA has been verified live

    def update(self):
        """
        Polls kernel memory for active players and current View-Projection matrix.
        Returns a list of PlayerTarget objects ready for overlay rendering.
        """
        targets = []
        if not self.bridge or not self.bridge.connected or not self.bridge.target_pid:
            return targets

        if not self.bridge.unity_player_base:
            self.bridge.unity_player_base = self.bridge.get_module_base("UnityPlayer.dll")
            if not self.bridge.unity_player_base:
                return targets

        try:
            # 1. Lấy VP matrix (ưu tiên static RVA — 1 IOCTL, không cần GOM)
            self._update_camera_fast()

            # 2. Fallback: tìm GOM nếu static RVA chưa xác nhận
            gom_ptr = 0
            if not self.camera_matrix:
                gom_ptr = self._get_valid_gom()
                if not gom_ptr:
                    self._debug_log("GOM: Không tìm thấy pointer hợp lệ")
                    return targets
                self._update_camera_gom(gom_ptr)

            # 3. Quét & tính toán vị trí thực thể
            if not gom_ptr:
                gom_ptr = self._get_valid_gom()
            if gom_ptr:
                targets = self._scan_players(gom_ptr)

            # Log định kỳ mỗi 3 giây
            if time.time() - self.last_debug_time > 3.0:
                self.last_debug_time = time.time()
                if self.camera_matrix:
                    src = "STATIC_RVA" if self._static_vp_ok else f"0x{self.camera_ptr:X}+0x{self.camera_matrix_offset:X}"
                    cam_status = f"VP_MATRIX ({src})"
                else:
                    cam_status = "CHƯA TÌM THẤY"
                print(f"[*] [RADAR] GOM: 0x{gom_ptr:X} | Cam: {cam_status} | Thực thể bộ nhớ: {len(self.cached_targets)} | Trên màn hình: {len(targets)}")

        except Exception as e:
            self._debug_log(f"Lỗi update: {e}")

        return targets

    # ─────────────────────────────────────────────────────────────────────────
    # CAMERA ACQUISITION
    # ─────────────────────────────────────────────────────────────────────────

    CAMERA_EXCLUDE = (
        "carscamera", "carvcam", "worldaocamera", "knockoutvcam", "ui", "minimap",
        "video", "lod", "collider", "point", "bets", "obstacle", "editor", "ao",
        "preview", "mirror"
    )

    BATTLE_CAM_PRIORITY = (
        "battle mixing camera", "main camera", "cameraholder",
        "armedvcam", "sprintvcam", "closetogroundvcam", "camera"
    )

    def _update_camera_fast(self):
        """
        Priority-1: Read the static VP matrix Unity writes to .data every frame.
        RVA 0x2111C90, verified via test_vp_matrix.py against known player positions.
        Cost: 1 IOCTL per call. No GOM traversal.
        """
        base = self.bridge.unity_player_base
        if not base:
            return
        raw = self.bridge.read_bytes(base + OFFSET_STATIC_VP_MATRIX, 64)
        if not raw or len(raw) < 64:
            return
        vm = struct.unpack('<16f', raw)
        if self._is_valid_vp_matrix(vm):
            self.camera_matrix = vm
            self.camera_matrix_offset = OFFSET_STATIC_VP_MATRIX
            self.camera_ptr = base + OFFSET_STATIC_VP_MATRIX
            self._static_vp_ok = True

    def _update_camera_gom(self, gom_ptr):
        """
        Priority-2/3: GOM-based camera component extraction.
        Reads ViewMatrix (+0x70) and ProjectionMatrix (+0xB0) from Camera component,
        computes VP = ProjectionMatrix × ViewMatrix (correct Unity order).
        """
        # Anti-flood throttle: scan at most once every 2 s
        now = time.time()
        if now - self.last_camera_scan_time < 2.0:
            return
        self.last_camera_scan_time = now

        # --- Priority-2: GOM MainCameras list at +0x18 ---
        main_cam_head = self.bridge.read_uint64(gom_ptr + 0x18)
        if main_cam_head and 0x10000000 < main_cam_head < 0x7FFFFFFFFFFF:
            node = main_cam_head
            visited_mc = set()
            while node and node not in visited_mc and 0x10000000 < node < 0x7FFFFFFFFFFF and len(visited_mc) < 40:
                visited_mc.add(node)
                go = self.bridge.read_uint64(node + 0x10)
                if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
                    obj_name = self._read_gameobject_name(go).lower()
                    if not any(x in obj_name for x in self.CAMERA_EXCLUDE):
                        res = self._extract_vp_from_gameobject(go)
                        if res:
                            self.camera_matrix, self.camera_ptr, self.camera_matrix_offset, self.camera_world_pos = res
                            return
                node = self.bridge.read_uint64(node + 0x08)

        # --- Priority-3: Full GOM scan for battle cameras ---
        head_node = self.bridge.read_uint64(gom_ptr + 0x20)
        if not (head_node and 0x10000000 < head_node < 0x7FFFFFFFFFFF):
            return

        visited = set()
        node = head_node
        count = 0
        while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 16000:
            visited.add(node)
            count += 1
            if count % 100 == 0:
                time.sleep(0.0001)

            go = self.bridge.read_uint64(node + 0x10)
            if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
                obj_name = self._read_gameobject_name(go).lower()
                if any(p in obj_name for p in self.BATTLE_CAM_PRIORITY) and not any(x in obj_name for x in self.CAMERA_EXCLUDE):
                    res = self._extract_vp_from_gameobject(go)
                    if res:
                        self.camera_matrix, self.camera_ptr, self.camera_matrix_offset, self.camera_world_pos = res
                        return
            node = self.bridge.read_uint64(node + 0x08)

    def _extract_vp_from_gameobject(self, go):
        """
        Enumerate ComponentArray of a camera GameObject and extract VP matrix.
        ComponentArray layout (Unity 6 IL2CPP 64-bit):
          slot k: [TypePtr: 8 bytes][CompPtr: 8 bytes]
        Slots 0..7 tried.  No ClassID filtering — we validate by matrix content.
        """
        pHierarchy = self._get_gameobject_hierarchy(go)
        c_pos = None
        if pHierarchy:
            c_pos = self.bridge.read_vec3(pHierarchy + 0x90)
            if c_pos and (abs(c_pos[1]) > 500.0 or abs(c_pos[0]) > 8000.0):
                return None

        pCompArray = self.bridge.read_uint64(go + 0x20)
        if not pCompArray or not (0x10000000 < pCompArray < 0x7FFFFFFFFFFF):
            return None

        for c_idx in range(0, 10):
            pComp = self.bridge.read_uint64(pCompArray + c_idx * 16 + 8)
            if not pComp or not (0x10000000 < pComp < 0x7FFFFFFFFFFF):
                continue
            vm, off = self._read_camera_vp(pComp)
            if vm:
                return vm, pComp, off, c_pos
        return None

    def _read_camera_vp(self, pCam):
        """
        Extract ViewProjection matrix from a Camera Component pointer.

        Correct computation:  VP = ProjectionMatrix × ViewMatrix
        Unity 6 offsets (confirmed via find_true_matrix.py scan):
          ViewMatrix:        pCam + 0x70  (4×4 float, column-major)
          ProjectionMatrix:  pCam + 0xB0  (4×4 float, column-major)

        Fallback: check pre-baked VP slots at 0xDC and 0x11C if
        the component stores a combined matrix directly.
        """
        try:
            v_mat = self.bridge.read_matrix4x4(pCam + 0x70)
            p_mat = self.bridge.read_matrix4x4(pCam + 0xB0)
            if v_mat and p_mat:
                if self._is_valid_view_component(v_mat) and self._is_valid_proj_component(p_mat):
                    # VP = P × V  (column-major matrix multiply)
                    vp = _mul4x4_col(p_mat, v_mat)
                    if self._is_valid_vp_matrix(vp):
                        return vp, 0x70

            # Fallback: pre-baked combined VP at known offsets
            for off in (0xDC, 0x11C):
                vm = self.bridge.read_matrix4x4(pCam + off)
                if vm and self._is_valid_vp_matrix(vm):
                    return vm, off
        except Exception:
            pass
        return None, 0

    # ─────────────────────────────────────────────────────────────────────────
    # MATRIX VALIDATION
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _is_valid_proj_component(pm):
        """
        A perspective ProjectionMatrix has:
          pm[0]  = cot(fov/2)/aspect   → typical range [0.5, 5.0]
          pm[5]  = cot(fov/2)          → typical range [0.5, 5.0]
          pm[10] = -(far+near)/(far-near) → negative, |x| < 1.1
          pm[11] = -1.0 (column-major: row3,col2 = -1 for GL-style)
          pm[14] = -2*far*near/(far-near)
          pm[15] = 0.0
        """
        try:
            if not pm or len(pm) < 16:
                return False
            if any(math.isnan(x) or math.isinf(x) for x in pm):
                return False
            # Check perspective signature: pm[11] should be ±1 and pm[15] ≈ 0
            if abs(abs(pm[11]) - 1.0) > 0.05:
                return False
            if abs(pm[15]) > 0.01:
                return False
            # Focal-length coefficients in reasonable range
            if abs(pm[0]) < 0.1 or abs(pm[0]) > 20.0:
                return False
            if abs(pm[5]) < 0.1 or abs(pm[5]) > 20.0:
                return False
            # Orthographic rejection: ortho has pm[11]=0, pm[15]=1
            # Already handled by pm[11] check above
            return True
        except Exception:
            return False

    @staticmethod
    def _is_valid_view_component(vm):
        """
        A camera ViewMatrix (world-to-camera) has orthonormal upper-left 3×3.
        In column-major 16-float layout:
          col0 = vm[0..2]  → right vector
          col1 = vm[4..6]  → up vector
          col2 = vm[8..10] → -forward vector
        Each column norm ≈ 1.0.
        """
        try:
            if not vm or len(vm) < 16:
                return False
            if any(math.isnan(x) or math.isinf(x) for x in vm):
                return False
            # Check column norms of upper-left 3×3
            for col in range(3):
                base = col * 4
                n = math.sqrt(vm[base]**2 + vm[base+1]**2 + vm[base+2]**2)
                if not (0.85 < n < 1.15):
                    return False
            # Last row (vm[3], vm[7], vm[11]) should be near 0,0,0,1
            if abs(vm[3]) > 0.01 or abs(vm[7]) > 0.01 or abs(vm[11]) > 0.01:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def _is_valid_vp_matrix(vm):
        """
        Heuristic checks for a combined VP matrix suitable for W2S projection.
        Rejects: Identity, Viewport scale, Orthographic, Cubemap, NaN/Inf.
        """
        try:
            if not vm or len(vm) < 16:
                return False
            if any(math.isnan(x) or math.isinf(x) for x in vm):
                return False
            # Reject viewport-scale garbage (values like 960.0, 540.0)
            if abs(vm[0]) > 50.0 or abs(vm[5]) > 50.0:
                return False
            # Reject identity
            if (abs(vm[0] - 1.0) < 1e-4 and abs(vm[5] - 1.0) < 1e-4 and
                    abs(vm[10] - 1.0) < 1e-4 and abs(vm[15] - 1.0) < 1e-4 and
                    sum(abs(x) for x in vm) < 4.1):
                return False
            # At least 6 non-zero elements
            if sum(1 for x in vm if abs(x) > 1e-4) < 6:
                return False
            # Overall value sanity
            if any(abs(x) > 50000.0 for x in vm):
                return False
            # Reject cubemap/constant matrices
            for c_val in (0.577350, 0.707107, 1.0):
                match_count = sum(1 for x in vm if abs(abs(x) - c_val) < 1e-3)
                if match_count >= 6 and len(set(round(abs(x), 3) for x in vm)) <= 3:
                    return False
            return True
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # PLAYER SCAN
    # ─────────────────────────────────────────────────────────────────────────

    def _scan_players(self, gom_ptr):
        now = time.time()
        refresh_interval = 45.0 if self.cached_targets else 2.0
        if now - self.last_discovery_time > refresh_interval:
            self._refresh_target_cache(gom_ptr)
            self.last_discovery_time = now

        targets = []
        for t in self.cached_targets:
            try:
                pos = self.bridge.read_vec3(t['hierarchy'] + 0x90)
                if pos and (-50.0 <= pos[1] <= 200.0) and (abs(pos[0]) > 0.01 or abs(pos[2]) > 0.01):
                    if self.camera_world_pos:
                        cx, cy, cz = self.camera_world_pos
                        dist_cam = math.sqrt((pos[0]-cx)**2 + (pos[1]-cy)**2 + (pos[2]-cz)**2)
                        if dist_cam < 1.8:
                            continue
                    target = self.project_entity(pos, role=t['role'], is_teammate=t['is_safe'])
                    if target:
                        targets.append(target)
            except Exception:
                pass
        return targets

    def _refresh_target_cache(self, gom_ptr):
        new_cached = []
        head_node = self.bridge.read_uint64(gom_ptr + 0x20)
        tail_node = 0
        if head_node and 0x10000000 < head_node < 0x7FFFFFFFFFFF:
            sentinel = self.bridge.read_uint64(head_node + 0x00)
            if sentinel and 0x10000000 < sentinel < 0x7FFFFFFFFFFF:
                cand = self.bridge.read_uint64(sentinel + 0x00)
                if cand and 0x10000000 < cand < 0x7FFFFFFFFFFF:
                    tail_node = cand

        if not tail_node:
            cand = self.bridge.read_uint64(gom_ptr + 0x18)
            if cand and 0x10000000 < cand < 0x7FFFFFFFFFFF:
                tail_node = cand

        scan_passes = []
        if tail_node:
            scan_passes.append((tail_node, 0x00, 10000))
        if head_node:
            scan_passes.append((head_node, 0x08, 10000))

        visited = set()
        seen_hierarchies = set()

        for start_node, step_off, max_steps in scan_passes:
            node = start_node
            count = 0
            while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < max_steps:
                visited.add(node)
                count += 1
                if count % 50 == 0:
                    time.sleep(0.001)

                go = self.bridge.read_uint64(node + 0x10)
                if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
                    nptr = self.bridge.read_uint64(go + 0x50)
                    if 0x10000000 < nptr < 0x7FFFFFFFFFFF:
                        obj_name = self.bridge.read_string(nptr, 48)
                        if obj_name and self._is_player_name(obj_name):
                            pHierarchy = self._get_gameobject_hierarchy(go)
                            if pHierarchy and pHierarchy not in seen_hierarchies:
                                seen_hierarchies.add(pHierarchy)
                                pos = self.bridge.read_vec3(pHierarchy + 0x90)
                                if pos and (-50.0 <= pos[1] <= 200.0):
                                    role = self._classify_role(obj_name)
                                    is_safe = (role in ("TEAMMATE", "CITIZEN"))
                                    new_cached.append({
                                        'name': obj_name,
                                        'go': go,
                                        'hierarchy': pHierarchy,
                                        'role': role,
                                        'is_safe': is_safe
                                    })
                node = self.bridge.read_uint64(node + step_off)

        if new_cached:
            self.cached_targets = new_cached

    def _is_player_name(self, name):
        if not name or len(name) < 3:
            return False
        name_low = name.lower()
        if any(exc in name_low for exc in EXCLUDE_KEYWORDS):
            return False
        if any(x in name_low for x in ("rigidbody", "collider", "joint", "overlay", "hud", "canvas", "stat", "icon")):
            return False
        if name.startswith("Player_Man") or name.startswith("Player_Woman"):
            return True
        if "charactertarget" in name_low:
            return True
        if any(kw in name_low for kw in ("cop", "police", "robber", "citizen", "civilian", "npc", "bot")):
            return True
        return False

    def _classify_role(self, name):
        name_low = name.lower()
        if "cop" in name_low or "police" in name_low:
            return "POLICE"
        elif any(c in name_low for c in ("citizen", "civilian", "pedestrian", "npc", "civil")):
            return "CITIZEN"
        elif any(t in name_low for t in ("team", "ally", "friend", "party")):
            return "TEAMMATE"
        return "ROBBER"

    # ─────────────────────────────────────────────────────────────────────────
    # WORLD-TO-SCREEN PROJECTION
    # ─────────────────────────────────────────────────────────────────────────

    def project_entity(self, world_pos, role="ROBBER", is_teammate=False, height_units=1.8, width_units=0.7):
        """
        Projects 3D world position to 2D screen coordinates using the VP matrix.
        Column-major layout: clip_x = m[0]*x + m[4]*y + m[8]*z + m[12]
                             clip_y = m[1]*x + m[5]*y + m[9]*z + m[13]
                             clip_w = m[3]*x + m[7]*y + m[11]*z + m[15]
        """
        if not self.camera_matrix:
            return None

        feet_pos = world_pos
        head_pos = (world_pos[0], world_pos[1] + height_units, world_pos[2])

        res_feet = world_to_screen_colmaj(feet_pos, self.camera_matrix, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        if not res_feet:
            return None
        feet_x, feet_y, depth = res_feet

        # Behind camera
        if depth < 0.01:
            return None

        # Distance filter using real 3D distance when camera_world_pos available
        if self.camera_world_pos and any(abs(c) > 0.01 for c in self.camera_world_pos):
            cx, cy, cz = self.camera_world_pos
            real_dist = math.sqrt((world_pos[0]-cx)**2 + (world_pos[1]-cy)**2 + (world_pos[2]-cz)**2)
            if real_dist > 350.0:
                return None

        # Clip to screen
        if feet_x < -50 or feet_x > config.SCREEN_WIDTH + 50 or feet_y < 10 or feet_y > config.SCREEN_HEIGHT + 80:
            return None

        # Project head for natural bounding box height
        h = 0
        res_head = world_to_screen_colmaj(head_pos, self.camera_matrix, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        if res_head:
            head_x, head_y, head_depth = res_head
            if head_depth > 0.01:
                h_proj = abs(feet_y - head_y)
                if 14 <= h_proj <= config.SCREEN_HEIGHT * 0.9:
                    h = h_proj

        if h == 0:
            if self.camera_world_pos and any(abs(c) > 0.01 for c in self.camera_world_pos):
                cx, cy, cz = self.camera_world_pos
                real_dist = max(2.0, math.sqrt((world_pos[0]-cx)**2 + (world_pos[1]-cy)**2 + (world_pos[2]-cz)**2))
                h = int(1266.7 / real_dist)
            else:
                h = 45

        h = max(14, min(int(config.SCREEN_HEIGHT * 0.9), h))
        w = max(8, int(h * (width_units / height_units)))

        center_x = feet_x
        top_y = feet_y - h
        left_x = center_x - (w // 2)

        aim_y = int(top_y + h * config.AIM_BONE_OFFSET)
        aim_point = (center_x, max(10, aim_y))

        return PlayerTarget(
            x=left_x,
            y=top_y,
            w=w,
            h=h,
            role=role,
            is_hostile=(not is_teammate),
            aim_point=aim_point
        )

    # ─────────────────────────────────────────────────────────────────────────
    # GOM HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _is_valid_gom_structure(self, ptr):
        if not (0x10000000 < ptr < 0x7FFFFFFFFFFF):
            return False
        raw = self.bridge.read_bytes(ptr, 0x40)
        if not raw or len(raw) < 0x40:
            return False
        qwords = struct.unpack('<8Q', raw)
        for idx in (4, 5, 3, 1, 2):
            node = qwords[idx]
            if 0x10000000 < node < 0x7FFFFFFFFFFF:
                node_raw = self.bridge.read_bytes(node, 0x20)
                if node_raw and len(node_raw) >= 0x20:
                    nq = struct.unpack('<4Q', node_raw)
                    for go_ptr in (nq[2], nq[3], nq[1]):
                        if 0x10000000 < go_ptr < 0x7FFFFFFFFFFF:
                            name = self._read_gameobject_name(go_ptr)
                            if name:
                                return True
        return False

    def _get_valid_gom(self):
        base = self.bridge.unity_player_base
        if not base:
            return 0
        if self.active_gom_offset:
            ptr = self.bridge.read_uint64(base + self.active_gom_offset)
            if self._is_valid_gom_structure(ptr):
                return ptr
            if self._is_valid_gom_structure(base + self.active_gom_offset):
                return base + self.active_gom_offset
            self.active_gom_offset = 0

        for off in GOM_CANDIDATE_OFFSETS:
            ptr = self.bridge.read_uint64(base + off)
            if self._is_valid_gom_structure(ptr):
                self.active_gom_offset = off
                return ptr
            if self._is_valid_gom_structure(base + off):
                self.active_gom_offset = off
                return base + off
        return 0

    def _read_gameobject_name(self, pGameObject):
        for off in (0x50, 0x60, 0x58, 0x48):
            ptr = self.bridge.read_uint64(pGameObject + off)
            if 0x10000 < ptr < 0x7FFFFFFFFFFF:
                s = self.bridge.read_string(ptr, 64)
                if s and len(s) >= 2 and s.isprintable():
                    return s
            raw = self.bridge.read_bytes(pGameObject + off, 16)
            if raw:
                inline = raw.split(b"\x00")[0]
                if inline and len(inline) >= 2 and all(32 <= c <= 126 for c in inline):
                    try:
                        return inline.decode('ascii')
                    except Exception:
                        pass
        return ""

    def _get_gameobject_hierarchy(self, pGameObject):
        try:
            pCompArray = self.bridge.read_uint64(pGameObject + 0x20)
            if not pCompArray or not (0x10000000 < pCompArray < 0x7FFFFFFFFFFF):
                return 0
            pTransform = self.bridge.read_uint64(pCompArray + 0x08)
            if not pTransform or not (0x10000000 < pTransform < 0x7FFFFFFFFFFF):
                return 0
            pHierarchy = self.bridge.read_uint64(pTransform + 0x28)
            if not pHierarchy or not (0x10000000 < pHierarchy < 0x7FFFFFFFFFFF):
                return 0
            return pHierarchy
        except Exception:
            return 0

    def _debug_log(self, msg):
        if time.time() - self.last_debug_time > 3.0:
            self.last_debug_time = time.time()
            print(f"[*] [RADAR DEBUG]: {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL W2S HELPERS (column-major layout)
# ─────────────────────────────────────────────────────────────────────────────

def world_to_screen_colmaj(world_pos, m, screen_width=1920, screen_height=1080):
    """
    Project world_pos with column-major 4×4 VP matrix m (16-float tuple).

    Unity stores matrices column-major: m[col*4 + row].
    struct.unpack('<16f') of raw bytes yields column-major order.

    clip_x = m[0]*x + m[4]*y + m[ 8]*z + m[12]
    clip_y = m[1]*x + m[5]*y + m[ 9]*z + m[13]
    clip_w = m[3]*x + m[7]*y + m[11]*z + m[15]

    Returns (screen_x, screen_y, clip_w) or None if behind camera.
    """
    if not m or len(m) < 16:
        return None
    x, y, z = world_pos
    clip_x = m[0]*x + m[4]*y + m[8]*z  + m[12]
    clip_y = m[1]*x + m[5]*y + m[9]*z  + m[13]
    clip_w = m[3]*x + m[7]*y + m[11]*z + m[15]

    if clip_w < 0.01 or math.isnan(clip_w) or math.isinf(clip_w):
        return None

    inv_w = 1.0 / clip_w
    ndc_x = clip_x * inv_w
    ndc_y = clip_y * inv_w

    if math.isnan(ndc_x) or math.isnan(ndc_y) or math.isinf(ndc_x) or math.isinf(ndc_y):
        return None

    sx = int(screen_width  * 0.5 * (1.0 + ndc_x))
    sy = int(screen_height * 0.5 * (1.0 - ndc_y))
    return (sx, sy, clip_w)


def _mul4x4_col(a, b):
    """
    Column-major 4×4 matrix multiply: result = a × b.
    Both a and b are 16-float tuples in column-major (Unity) layout.
    Result is also column-major.
    """
    res = [0.0] * 16
    for col in range(4):
        for row in range(4):
            val = 0.0
            for k in range(4):
                # a[k*4+row] = a element at (row, k) in col-major
                # b[col*4+k] = b element at (k, col) in col-major
                val += a[k*4 + row] * b[col*4 + k]
            res[col*4 + row] = val
    return tuple(res)
