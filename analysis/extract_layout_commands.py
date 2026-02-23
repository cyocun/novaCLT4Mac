#!/usr/bin/env python3
"""layout3.pcap からレイアウトコマンドシーケンスを抽出し、Swiftコードを生成する。

layout3.pcap: 4列×1行, 右→左/左→右のスキャン方向変更キャプチャ。
USBPcap形式のpcapファイルを解析し、MSD300宛の55AAコマンドを抽出。
"""

import struct
import sys
import os

def read_pcap(filepath):
    """pcapファイルを読み込んでパケット一覧を返す"""
    packets = []
    with open(filepath, 'rb') as f:
        # Global header (24 bytes)
        magic = f.read(4)
        if magic == b'\xd4\xc3\xb2\xa1':
            endian = '<'  # little-endian
        elif magic == b'\xa1\xb2\xc3\xd4':
            endian = '>'  # big-endian
        else:
            print(f"Not a pcap file: {filepath}")
            return []

        ver_major, ver_minor, tz, sigfigs, snaplen, network = struct.unpack(
            f'{endian}HHiIII', f.read(20)
        )

        # Read packets
        pkt_num = 0
        while True:
            hdr = f.read(16)
            if len(hdr) < 16:
                break
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack(f'{endian}IIII', hdr)
            data = f.read(incl_len)
            if len(data) < incl_len:
                break
            pkt_num += 1
            packets.append((pkt_num, ts_sec, ts_usec, data))

    return packets


def extract_usbpcap_payload(raw_data):
    """USBPcapパケットからペイロードを抽出する"""
    if len(raw_data) < 27:
        return None, None

    # USBPcap header: headerLen at offset 0 (2 bytes LE)
    header_len = struct.unpack_from('<H', raw_data, 0)[0]
    if header_len > len(raw_data):
        return None, None

    # Function at offset 8
    function = struct.unpack_from('<H', raw_data, 8)[0]

    # Direction: info at offset 21 (0=out, 1=in for URB_FUNCTION_BULK_OR_INTERRUPT_TRANSFER)
    info = raw_data[21] if len(raw_data) > 21 else 0

    # endpoint at offset 22
    endpoint = raw_data[22] if len(raw_data) > 22 else 0
    direction = 'OUT' if (endpoint & 0x80) == 0 else 'IN'

    payload = raw_data[header_len:]
    return payload, direction


def is_novastar_command(payload):
    """55 AA で始まるNovaStar書き込みコマンドか判定"""
    return len(payload) >= 4 and payload[0] == 0x55 and payload[1] == 0xAA


def verify_checksum(payload):
    """チェックサムを検証"""
    if len(payload) < 6:
        return False
    body = payload[2:-2]
    chk = payload[-2:]
    s = (0x5555 + sum(body)) & 0xFFFF
    expected = struct.pack('<H', s)
    return chk == expected


def parse_command(payload):
    """コマンドパケットを解析"""
    if len(payload) < 18:
        return None

    seq = (payload[2] << 8) | payload[3]
    source = payload[4]
    dest = payload[5]
    dev_type = payload[6]
    port = payload[7]
    board = (payload[8] << 8) | payload[9]
    direction = payload[10]
    reserved = payload[11]
    reg = struct.unpack_from('<I', payload, 12)[0]
    data_len = struct.unpack_from('<H', payload, 16)[0]
    data = payload[18:18 + data_len] if data_len > 0 else b''

    return {
        'seq': seq,
        'source': source,
        'dest': dest,
        'dev_type': dev_type,
        'port': port,
        'board': board,
        'dir': 'W' if direction == 0x01 else 'R',
        'register': reg,
        'data_len': data_len,
        'data': data,
        'raw': payload,
    }


def extract_payload_for_preset(payload):
    """プリセット用ペイロードを抽出 (seq 2B と checksum 2B を除く)"""
    # 55 AA [seq 2B] [payload...] [chk 2B]
    # プリセットは seq と chk を除いた部分: payload[4:-2]
    return payload[4:-2]


def commands_to_swift(commands, preset_name, columns, rows, direction):
    """コマンドリストをSwiftコードに変換"""
    lines = []
    lines.append(f'    // {preset_name}: {columns}列×{rows}行 {direction}')
    lines.append(f'    static let preset_{preset_name} = LayoutPreset(')
    lines.append(f'        name: "{preset_name}",')
    lines.append(f'        columns: {columns},')
    lines.append(f'        rows: {rows},')
    lines.append(f'        direction: .{direction},')
    lines.append(f'        commands: [')

    for i, cmd in enumerate(commands):
        payload = extract_payload_for_preset(cmd['raw'])
        hex_bytes = ', '.join(f'0x{b:02X}' for b in payload)
        dest_label = "送信カード" if cmd['dest'] == 0x00 else "受信カード"
        reg_hex = f"0x{cmd['register']:08X}"
        comment = f"// #{i}: {cmd['dir']} reg={reg_hex} len={cmd['data_len']} dest={dest_label}"

        lines.append(f'            [{hex_bytes}], {comment}')

    lines.append(f'        ]')
    lines.append(f'    )')
    return '\n'.join(lines)


def main():
    pcap_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'captures')
    pcap_file = os.path.join(pcap_dir, 'layout3.pcap')

    if not os.path.exists(pcap_file):
        print(f"File not found: {pcap_file}")
        sys.exit(1)

    packets = read_pcap(pcap_file)
    print(f"Total packets in pcap: {len(packets)}")

    # MSD300宛のコマンドを抽出
    commands = []
    for pkt_num, ts_sec, ts_usec, raw_data in packets:
        payload, direction = extract_usbpcap_payload(raw_data)
        if payload is None or direction != 'OUT':
            continue
        if not is_novastar_command(payload):
            continue

        cmd = parse_command(payload)
        if cmd is None:
            continue

        valid = verify_checksum(payload)
        commands.append(cmd)

        if not valid:
            print(f"  WARNING: Checksum mismatch at packet #{pkt_num}")

    print(f"NovaStar commands found: {len(commands)}")

    # コマンドシーケンスをグループ分け
    # 連続するコマンド群を時間ギャップで分割
    # ここでは全コマンドをシーケンス番号の不連続で分割
    groups = []
    current_group = []
    prev_seq = None

    for cmd in commands:
        # 読み取りコマンドやポーリングは除外（書き込みのみ）
        if cmd['dir'] != 'W':
            continue

        # 輝度コマンド(0x02000001, 0x020001E3)は除外
        if cmd['register'] in (0x02000001, 0x020001E3):
            continue

        if prev_seq is not None:
            gap = (cmd['seq'] - prev_seq) & 0xFFFF
            if gap > 10:  # 大きなギャップ = 新しいシーケンス
                if current_group:
                    groups.append(current_group)
                current_group = []

        current_group.append(cmd)
        prev_seq = cmd['seq']

    if current_group:
        groups.append(current_group)

    print(f"\nCommand groups (layout sequences): {len(groups)}")
    for i, group in enumerate(groups):
        regs = set(f"0x{c['register']:08X}" for c in group)
        dests = set(c['dest'] for c in group)
        print(f"  Group {i}: {len(group)} commands, dest={[f'0x{d:02X}' for d in dests]}, regs={len(regs)} unique")

        # 先頭と末尾のコマンドを表示
        for j, cmd in enumerate(group[:3]):
            data_hex = cmd['data'].hex() if cmd['data'] else '-'
            print(f"    [{j}] seq={cmd['seq']:04X} dest={cmd['dest']:02X} port={cmd['port']:02X} "
                  f"reg=0x{cmd['register']:08X} len={cmd['data_len']} data={data_hex[:40]}")
        if len(group) > 6:
            print(f"    ... ({len(group) - 6} more)")
        for j, cmd in enumerate(group[-3:]):
            idx = len(group) - 3 + j
            data_hex = cmd['data'].hex() if cmd['data'] else '-'
            print(f"    [{idx}] seq={cmd['seq']:04X} dest={cmd['dest']:02X} port={cmd['port']:02X} "
                  f"reg=0x{cmd['register']:08X} len={cmd['data_len']} data={data_hex[:40]}")

    # Swift コード生成
    print("\n" + "=" * 60)
    print("Swift preset code:")
    print("=" * 60)

    # layout3.pcapの2つのグループ: 右→左 と 左→右
    direction_names = ['rightToLeft', 'leftToRight']
    for i, group in enumerate(groups[:2]):
        if i < len(direction_names):
            name = f"4x1_{direction_names[i]}"
            swift_code = commands_to_swift(group, name, 4, 1, direction_names[i])
            print(swift_code)
            print()

    # 生ペイロードをファイルに出力
    for i, group in enumerate(groups[:2]):
        if i < len(direction_names):
            outfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   f'layout_preset_{direction_names[i]}.txt')
            with open(outfile, 'w') as f:
                for cmd in group:
                    payload = extract_payload_for_preset(cmd['raw'])
                    f.write(payload.hex() + '\n')
            print(f"\nRaw payloads saved to: {outfile}")


if __name__ == "__main__":
    main()
