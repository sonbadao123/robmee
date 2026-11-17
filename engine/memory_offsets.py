"""
ROB RUN - IL2CPP REVERSE ENGINEERING RECONNAISSANCE
Extracted from GameAssembly.dll and global-metadata.dat (IL2CPP v39).
"""

METADATA_VERSION = 39
TARGET_BINARY = "ROB RUN.exe"
GAME_ASSEMBLY = "GameAssembly.dll"

# ==============================================================================
# KEY IL2CPP CLASSES & MODELS IN ROB RUN (Kefir)
# ==============================================================================

CLASSES = {
    "RobbersRoleData": {
        "Namespace": "Models.Data.Role",
        "Description": "Defines Robber role data, inventory limits, and team registration.",
    },
    "FoundCopData": {
        "Namespace": "Models.Models.Arrest",
        "Description": "Tracks active police units, arrest range, and cop state.",
    },
    "CopInfoModel": {
        "Namespace": "Models.Models.CopInfo",
        "Description": "Police unit stats, badge rank, patrol routes.",
    },
    "BecomeRobberConfig": {
        "Namespace": "Models.References.Robber",
        "Description": "Faction switching and robber parameters.",
    },
    "CopsChatUpdater": {
        "Namespace": "Game.Battle.Player",
        "Description": "Cop radio and communications channel.",
    },
    "CheatController": {
        "Namespace": "Game.Battle.Cheats",
        "Description": "Internal developer testing cheat harness.",
    }
}

# ==============================================================================
# EAC EOS INTERCEPTION PROTOCOL
# ==============================================================================
ANTI_CHEAT_NOTES = """
1. Easy Anti-Cheat EOS Protection Details:
   - Kernel Driver: EasyAntiCheat_EOS.sys
   - ObRegisterCallbacks: Intercepts OpenProcess and strips PROCESS_VM_READ (0x0010) and PROCESS_VM_WRITE (0x0020).
   - Module Integrity: Scans GameAssembly.dll and memory sections for byte modifications (CRC/Hash check).
   - Driver Monitoring: Detects known vulnerable driver loaders (KDU, gdrv, etc.).

2. Why External Vision & Hardware Input Prevents Bans:
   - External Vision operates strictly on screen frames outside the game's virtual memory space.
   - Mouse events are dispatched via Windows low-level input queue with Bezier curve acceleration.
   - EAC has zero visibility into external non-attached analysis pipelines.
"""
