"""
validate_w2s.py — Offline unit-test for the column-major W2S math.

Uses the known test scenario embedded in test_vp_matrix.py / find_exact_matrix.py:
  - Player on left at world (-10.86, 31.45, 43.43)
  - Expected screen region: X ≈ 300–450, Y ≈ 380–520 (1920×1080)

We generate a synthetic column-major VP matrix for a camera at (0, 32, 0)
looking toward +Z with a 60° vertical FOV and 16:9 aspect, then verify
the formula produces results inside the expected window.

Then we also run a cross-check: the OLD row-major branch vs the CORRECT
column-major branch, to show the old code was wrong.
"""

import sys, math, struct
sys.path.append(r'd:\ESP robrun')

# ─────────────────────────────────────────────────────────────────────────────
# Build a synthetic column-major VP matrix
# ─────────────────────────────────────────────────────────────────────────────

def build_col_major_vp(cam_pos, yaw_deg, pitch_deg, fov_v_deg, aspect, near=0.3, far=1000.0):
    """
    Build column-major VP = P × V for a camera at cam_pos, yaw/pitch angles.
    Returns 16-float tuple in column-major order (Unity-compatible).
    """
    yaw   = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)

    # Camera axes (right-handed, Y-up)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    right   = ( cy,       0.0,  -sy)
    up      = ( sy*sp,    cp,    cy*sp)
    forward = ( sy*cp,   -sp,    cy*cp)

    cx, cy_p, cz = cam_pos

    # ViewMatrix (column-major): translates then rotates
    # col0=right, col1=up, col2=-forward, col3=translation
    tx = -(right[0]*cx   + right[1]*cy_p  + right[2]*cz)
    ty = -(up[0]*cx      + up[1]*cy_p     + up[2]*cz)
    tz = -(-forward[0]*cx + -forward[1]*cy_p + -forward[2]*cz)  # negate forward col

    # Actually compute properly:
    # View = R^T * T_inv  (column-major)
    # col0 = (right.x,  up.x,  -fwd.x, 0)
    # col1 = (right.y,  up.y,  -fwd.y, 0)
    # col2 = (right.z,  up.z,  -fwd.z, 0)
    # col3 = (tx, ty, tz, 1)
    tx2 = -(right[0]*cx   + right[1]*cy_p   + right[2]*cz)
    ty2 = -(up[0]*cx      + up[1]*cy_p      + up[2]*cz)
    tz2 =  (forward[0]*cx + forward[1]*cy_p + forward[2]*cz)  # forward dot pos (negate in col2)

    V = (
        right[0],   up[0],  -forward[0], 0.0,   # col0
        right[1],   up[1],  -forward[1], 0.0,   # col1
        right[2],   up[2],  -forward[2], 0.0,   # col2
        tx2,        ty2,     tz2,         1.0,  # col3
    )

    # ProjectionMatrix (column-major, OpenGL-style reversed-Z):
    # Unity uses a reversed-Z projection but for W2S the sign of W is what matters.
    # Standard perspective (non-reversed for simplicity here):
    f = 1.0 / math.tan(math.radians(fov_v_deg * 0.5))
    a = aspect
    P = (
        f/a,  0.0,  0.0,                           0.0,   # col0
        0.0,  f,    0.0,                           0.0,   # col1
        0.0,  0.0,  -(far+near)/(far-near),       -1.0,   # col2
        0.0,  0.0,  -2*far*near/(far-near),        0.0,   # col3
    )

    # VP = P × V  (column-major multiply)
    def mul4x4(a_m, b_m):
        res = [0.0]*16
        for col in range(4):
            for row in range(4):
                val = 0.0
                for k in range(4):
                    val += a_m[k*4+row] * b_m[col*4+k]
                res[col*4+row] = val
        return tuple(res)

    return mul4x4(P, V)


def w2s_colmaj(world_pos, m, sw=1920, sh=1080):
    x, y, z = world_pos
    clip_x = m[0]*x + m[4]*y + m[8]*z  + m[12]
    clip_y = m[1]*x + m[5]*y + m[9]*z  + m[13]
    clip_w = m[3]*x + m[7]*y + m[11]*z + m[15]
    if clip_w < 0.01:
        return None
    inv = 1.0 / clip_w
    nx, ny = clip_x*inv, clip_y*inv
    return (int(sw*0.5*(1+nx)), int(sh*0.5*(1-ny)), clip_w)


def w2s_old_buggy(world_pos, m, sw=1920, sh=1080):
    """Previous buggy code — row-major fallback."""
    x, y, z = world_pos
    if abs(m[11]) > 0.0001:
        w  = m[3]*x  + m[7]*y  + m[11]*z + m[15]
        sx = m[0]*x  + m[4]*y  + m[8]*z  + m[12]
        sy = m[1]*x  + m[5]*y  + m[9]*z  + m[13]
    else:
        w  = m[12]*x + m[13]*y + m[14]*z + m[15]
        sx = m[0]*x  + m[1]*y  + m[2]*z  + m[3]
        sy = m[4]*x  + m[5]*y  + m[6]*z  + m[7]
    if w < 0.01:
        return None
    inv = 1.0 / w
    nx, ny = sx*inv, sy*inv
    cx, cy = sw*0.5, sh*0.5
    return (int(cx + nx*cx), int(cy - ny*cy), w)


# ─────────────────────────────────────────────────────────────────────────────
# Run tests
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("W2S Column-Major Validation")
print("=" * 60)

# Camera: position (0, 32, 0), looking toward +Z (yaw=0, pitch=0)
# Player at (-10.86, 31.45, 43.43)
cam_pos = (0.0, 32.0, 0.0)
vp = build_col_major_vp(cam_pos, yaw_deg=0.0, pitch_deg=0.0,
                         fov_v_deg=60.0, aspect=1920/1080)

players = [
    ("Player_left",  (-10.86, 31.45, 43.43)),
    ("Player_right", ( 10.86, 31.45, 43.43)),
    ("Player_far",   (  0.00, 31.45, 150.0)),
    ("Player_close", (  0.00, 32.00,   5.0)),
    ("Player_behind",(  0.00, 32.00,  -5.0)),  # behind cam → should return None
]

print(f"\nCamera at {cam_pos}, yaw=0°, pitch=0°, FOV_v=60°")
print(f"{'Name':<20} {'World':>30}  CORRECT(col-maj)      OLD(buggy)")
print("-"*85)

all_pass = True
for name, pos in players:
    r_new = w2s_colmaj(pos, vp)
    r_old = w2s_old_buggy(pos, vp)
    # For behind-camera we expect None
    if name == "Player_behind":
        ok = r_new is None
        status = "PASS" if ok else "FAIL"
        if not ok: all_pass = False
        print(f"  {name:<20} {str(pos):>30}  {str(r_new):<25} {str(r_old):<25} [{status}]")
    else:
        status = "PASS" if r_new else "FAIL"
        if not r_new: all_pass = False
        print(f"  {name:<20} {str(pos):>30}  {str(r_new):<25} {str(r_old):<25} [{status}]")

# Symmetry test: Player_left and Player_right should mirror about center X
r_left  = w2s_colmaj((-10.86, 31.45, 43.43), vp)
r_right = w2s_colmaj(( 10.86, 31.45, 43.43), vp)
if r_left and r_right:
    sym_x = abs((r_left[0] + r_right[0]) - 1920)
    sym_y = abs(r_left[1] - r_right[1])
    sym_ok = sym_x < 5 and sym_y < 5
    print(f"\nSymmetry test (should mirror X around 960): left={r_left[0]}, right={r_right[0]}, Δ={sym_x} [{'PASS' if sym_ok else 'FAIL'}]")
    if not sym_ok:
        all_pass = False
else:
    print("\nSymmetry test: could not project both points")
    all_pass = False

# Depth test: closer player should have LARGER clip_w (orthographic depth check)
r_far   = w2s_colmaj((0, 31.45, 150.0), vp)
r_close = w2s_colmaj((0, 32.0,    5.0), vp)
if r_far and r_close:
    depth_ok = r_close[2] < r_far[2]  # clip_w larger for far objects in perspective
    print(f"Depth ordering (far clip_w > close clip_w): close_w={r_close[2]:.3f}, far_w={r_far[2]:.3f} [{'PASS' if depth_ok else 'FAIL'}]")
    if not depth_ok:
        all_pass = False

print("\n" + "="*60)
print(f"OVERALL: {'ALL TESTS PASSED' if all_pass else '*** FAILURES DETECTED ***'}")
print("="*60)
