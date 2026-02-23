#!/usr/bin/env python3
"""マッピングテーブルの構造を詳細に解析する"""
import struct

with open('/Users/cyocun/Dropbox/__WORKS/_own_services/novaCLT4Mac/analysis/layout_preset_rightToLeft.txt') as f:
    lines = [l.strip() for l in f if l.strip()]

rtl = lines[:42]
ltr = lines[42:]

def get_data(line):
    data = bytes.fromhex(line)
    dlen = struct.unpack_from('<H', data, 12)[0]
    return data[14:14+dlen]

# Compare mapping blocks side by side
print("=== Mapping Table Block 0 (256 bytes) ===")
rtl_data = get_data(rtl[14])
ltr_data = get_data(ltr[14])

print(f"\nR→L first 64 bytes (as 8-byte groups):")
for i in range(0, 64, 8):
    chunk = rtl_data[i:i+8]
    print(f"  [{i:3}] {chunk.hex()}")

print(f"\nL→R first 64 bytes (as 8-byte groups):")
for i in range(0, 64, 8):
    chunk = ltr_data[i:i+8]
    print(f"  [{i:3}] {chunk.hex()}")

# Interpret as 16-bit LE pairs
print(f"\n=== Interpreted as LE uint16 pairs (first 32 entries) ===")
print(f"{'idx':>3} {'R→L val1':>8} {'R→L val2':>8} {'R→L val3':>8} {'R→L val4':>8} | {'L→R val1':>8} {'L→R val2':>8} {'L→R val3':>8} {'L→R val4':>8}")
for i in range(0, min(128, len(rtl_data)), 8):
    r_vals = struct.unpack_from('<4H', rtl_data, i)
    l_vals = struct.unpack_from('<4H', ltr_data, i)
    print(f"{i//8:>3} {r_vals[0]:>8} {r_vals[1]:>8} {r_vals[2]:>8} {r_vals[3]:>8} | {l_vals[0]:>8} {l_vals[1]:>8} {l_vals[2]:>8} {l_vals[3]:>8}")

# Check if all 16 blocks are identical within each direction
print(f"\n=== Are all 16 mapping blocks identical within each direction? ===")
rtl_block0 = get_data(rtl[14])
ltr_block0 = get_data(ltr[14])
for i in range(1, 16):
    rtl_block = get_data(rtl[14+i])
    ltr_block = get_data(ltr[14+i])
    print(f"  Block {i:2}: R→L same_as_0={'✓' if rtl_block == rtl_block0 else '✗'}, L→R same_as_0={'✓' if ltr_block == ltr_block0 else '✗'}")

# Check per-card reg values more carefully
print(f"\n=== Per-card settings detail ===")
print("R→L:")
for i in range(31, 39):
    d = bytes.fromhex(rtl[i])
    board = struct.unpack_from('<H', d, 4)[0]
    reg = struct.unpack_from('<I', d, 8)[0]
    dlen = struct.unpack_from('<H', d, 12)[0]
    data = d[14:14+dlen]
    val = struct.unpack_from('<H', data, 0)[0] if dlen >= 2 else data[0]
    reg_name = "X_size" if (reg & 0xFF) == 0x17 else "Y_size"
    print(f"  board={board} reg=0x{reg:08X} ({reg_name}) val={val} (0x{val:04X})")

print("L→R:")
for i in range(31, 39):
    d = bytes.fromhex(ltr[i])
    board = struct.unpack_from('<H', d, 4)[0]
    reg = struct.unpack_from('<I', d, 8)[0]
    dlen = struct.unpack_from('<H', d, 12)[0]
    data = d[14:14+dlen]
    val = struct.unpack_from('<H', data, 0)[0] if dlen >= 2 else data[0]
    reg_name = "X_size" if (reg & 0xFF) == 0x17 else "Y_size"
    print(f"  board={board} reg=0x{reg:08X} ({reg_name}) val={val} (0x{val:04X})")

# Check global settings values
print(f"\n=== Global settings values ===")
reg_names = {
    0x02000024: "total_width_area1",
    0x02000026: "total_height_area1",
    0x02000028: "offset_x_area1",
    0x0200002A: "offset_y_area1",
    0x0200002C: "total_width_area2?",
    0x02000051: "total_width_area3?",
    0x02000053: "total_height_area3?",
    0x02000055: "offset_x_area3?",
    0x02000057: "offset_y_area3?",
    0x03100000: "column_count",
}
for i in range(2, 14):
    d = bytes.fromhex(rtl[i])
    reg = struct.unpack_from('<I', d, 8)[0]
    dlen = struct.unpack_from('<H', d, 12)[0]
    data = d[14:14+dlen]
    if dlen == 2:
        val = struct.unpack_from('<H', data, 0)[0]
    elif dlen == 1:
        val = data[0]
    else:
        val = int.from_bytes(data, 'little')
    name = reg_names.get(reg, "?")
    print(f"  reg=0x{reg:08X} ({name:>20}) val={val} (0x{val:X})")
