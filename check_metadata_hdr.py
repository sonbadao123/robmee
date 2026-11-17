import struct

meta_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\ROB RUN_Data\il2cpp_data\Metadata\global-metadata.dat'
with open(meta_path, 'rb') as f:
    hdr = f.read(128)

sanity, version = struct.unpack_from('<II', hdr, 0)
print(f"Sanity: 0x{sanity:08X} (expected 0xFAB11BAF)")
print(f"Version: {version}")

# Read first 16 int32s in header
ints = struct.unpack_from('<16I', hdr, 0)
for i, v in enumerate(ints):
    print(f"[{i:02d}] 0x{v:08X} ({v})")
