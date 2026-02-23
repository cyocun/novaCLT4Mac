#!/usr/bin/env python3
"""右→左 と 左→右 のレイアウトコマンドを比較して、可変部分を特定する"""

import struct

def parse_payload(hex_str):
    data = bytes.fromhex(hex_str.strip())
    if len(data) < 14:
        return None
    src = data[0]
    dest = data[1]
    devtype = data[2]
    port = data[3]
    board = struct.unpack_from('<H', data, 4)[0]
    direction = data[6]
    reg = struct.unpack_from('<I', data, 8)[0]
    dlen = struct.unpack_from('<H', data, 12)[0]
    payload = data[14:14+dlen] if dlen > 0 else b''
    return {
        'dest': dest, 'port': port, 'board': board,
        'dir': 'W' if direction == 1 else 'R',
        'reg': reg, 'len': dlen, 'data': payload,
        'raw': data
    }

# Read both files
with open('/Users/cyocun/Dropbox/__WORKS/_own_services/novaCLT4Mac/analysis/layout_preset_rightToLeft.txt') as f:
    rtl_lines = [l.strip() for l in f if l.strip()]

# The file contains both sequences - split at line 43 (0-indexed: 42)
# R→L: lines 0-41 (42 commands), L→R: lines 42-83 (42 commands)
rtl = rtl_lines[:42]
ltr = rtl_lines[42:]

print(f"R→L commands: {len(rtl)}")
print(f"L→R commands: {len(ltr)}")
print()

# Compare
print("=== Command-by-command comparison ===")
print(f"{'#':>3} {'Same':>4} {'Reg':>12} {'Dest':>4} {'Board':>5} {'Len':>4} {'Diff'}")
print("-" * 80)

for i in range(min(len(rtl), len(ltr))):
    r = parse_payload(rtl[i])
    l = parse_payload(ltr[i])
    if r is None or l is None:
        continue

    same = rtl[i] == ltr[i]
    diff_parts = []
    if r['dest'] != l['dest']: diff_parts.append(f"dest:{r['dest']:02X}→{l['dest']:02X}")
    if r['board'] != l['board']: diff_parts.append(f"board:{r['board']}→{l['board']}")
    if r['reg'] != l['reg']: diff_parts.append(f"reg:{r['reg']:08X}→{l['reg']:08X}")
    if r['data'] != l['data']:
        rd = r['data'].hex()[:20]
        ld = l['data'].hex()[:20]
        diff_parts.append(f"data:{rd}→{ld}")

    print(f"{i:>3} {'✓' if same else '✗':>4} 0x{r['reg']:08X} {r['dest']:>4X} {r['board']:>5} {r['len']:>4} {' | '.join(diff_parts)}")

# Identify the 3 sections
print("\n=== Section Analysis ===")
print("\n--- Section 1: Global settings (dest=00) ---")
for i, line in enumerate(rtl[:14]):
    r = parse_payload(line)
    if r:
        data_hex = r['data'].hex() if r['data'] else '-'
        print(f"  [{i:2}] reg=0x{r['reg']:08X} dest={r['dest']:02X} board={r['board']:>5} len={r['len']} data={data_hex}")

print("\n--- Section 2: Mapping table (16 blocks) ---")
for i in range(14, 30):
    r = parse_payload(rtl[i])
    l = parse_payload(ltr[i])
    if r and l:
        same = r['data'] == l['data']
        print(f"  [{i:2}] reg=0x{r['reg']:08X} len={r['len']} data_same={'✓' if same else '✗ DIFFERENT'}")

print("\n--- Section 3: Per-card settings ---")
for i in range(30, min(42, len(rtl))):
    r = parse_payload(rtl[i])
    l = parse_payload(ltr[i])
    if r and l:
        same = rtl[i] == ltr[i]
        r_data = r['data'].hex() if r['data'] else '-'
        l_data = l['data'].hex() if l['data'] else '-'
        board_diff = f"board:{r['board']}→{l['board']}" if r['board'] != l['board'] else ""
        print(f"  [{i:2}] reg=0x{r['reg']:08X} board_R={r['board']} board_L={l['board']} "
              f"data_R={r_data} data_L={l_data} {'✓' if same else '✗'}")
