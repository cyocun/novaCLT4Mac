# 任意レイアウト (Freeform Layout) 実装検討

> **ステータス**: 未着手。調査のみ完了（2026-04-24）。
> 現状は `LayoutPreset` 固定。実装の判断材料としてこのドキュメントを残す。

## 背景
現在 NovaController は 3 プリセット（4×1 L→R / 4×1 R→L / 2×4 S字）のみ対応。
必要なレイアウトは追加キャプチャ→プリセット追加で対応する方針（案A）。
ただし「任意の列数 × 行数 + 任意スキャン方向」を動的生成したい場合の
実装検討を残す。参考は [sarakusha/novastar](https://github.com/sarakusha/novastar)（MIT）。

## sarakusha の実装概要

sarakusha では `ScreenConfigurator.saveImpl()` が任意レイアウトの書き込みを
担う。処理の全体像:

```
1. SetSender_ScreenConfigFlagSpace(index, false, [85, 0])   ← リセット
2. LEDDisplayInfo[] → ScreenDataInSoftSpace[] に変換
3. JSON エンコード (XML 擬似フォーマット, io-ts)
4. pack() で LZMA 圧縮
5. FileInfoObject を構築 (FileType / Version / Addr / CheckSum(CRC16))
6. FileInfoObject を JSON 化 → 再度 LZMA 圧縮
7. SoftwareSpaceHeader (20 B) を構築してヘッダに書き込み
8. SetSender_SoftwareSpace(...) で分割書き込み
```

## 圧縮アルゴリズム: LZMA

`packages/screen/src/common.ts` より:

```ts
import { compress, decompress } from '@sarakusha/lzma';

export const pack = async (data): Promise<[string, Buffer]> => {
  const compressed = await compress(data, 8, ...);  // level 8
  return [
    compressed.slice(0, 5).toString('binary'),  // props (5B)
    compressed.slice(5 + 8),                     // compressed data (先頭8Bのsize長は除去)
  ];
};
```

### フォーマット
`@sarakusha/lzma` は xz-utils の LZMA1 フォーマットを生成:

```
[props: 5B][uncompressed size: 8B LE][compressed data]
```

sarakusha は props (5B) と data 部分を分けて別々に扱う。
復号側 (`unpack`) では `props + size + data` を再結合して decompress する。

### macOS での互換性
macOS の `Compression.framework` は `COMPRESSION_LZMA` をサポートしているが、
**xz-utils の raw LZMA1 形式とそのまま互換とは限らない**。
要検証項目:

- Apple の `COMPRESSION_LZMA` が期待する入力フォーマット (xz stream ?)
- `compression_encode_buffer(COMPRESSION_LZMA, ...)` の出力先頭と
  `@sarakusha/lzma` 出力先頭の一致
- もし互換性がなければ、xz のポータブル実装 (`SWCompression` Swift パッケージ等) で代替

### 検証の最短経路
sarakusha の `unpack` を Node.js で走らせ、適当な短文字列を圧縮した結果の
バイト列を保存 → 同じバイト列が macOS 側で `decompression_decode_buffer` や
`SWCompression.LZMA.decompress()` で元に戻せるかテストする。

## 関連する構造体群 (Swift 移植が必要)

### SoftwareSpaceHeader (20 B)
```
offset  size  field
0       4     header      "NSSD" (ASCII)
4       2     crc         LE16
6       2     version     LE16 = 1001
8       2     paramSize   LE16
10      2     paramCRC    LE16
12      4     compressedSize  LE32
16      4     fileInfoSize    LE32
20 (内部: ParamSize=7)
```
→ Swift は単なる `Data` の手組みで OK。

### ScreenDataInSoftSpace (sarakusha/native)
```
UUID: string
DviSelect: DviSelectMode (enum)
OnePortLoadInfo: OnePortLoadInfo[]
CabinetInDevice: CabinetInDevice[]
ScrType?: LEDDisplyType
VirMode?: VirtualModeType
ScrX, ScrY?: Int32
CabinetCol, CabinetRow?: UInt16
PortCols, PortRows?: UInt8
DeviceID?: UInt8
CabinetWidth, CabinetHeight?: UInt16
ScreenIndex?: Int32
DVIlist?: Record<Int32, PointFromString>
```
→ Codable な Swift struct で JSON エンコード可能。XML 属性名に合わせる必要あり。

### 依存する子構造体
- `OnePortLoadInfo` — ポートごとのカード接続情報
- `CabinetInDevice` — キャビネットの物理配置
- `LEDDisplayInfo` / `SimpleLEDDisplayInfo` / `ComplexLEDDisplayInfo`
- `ComplexRegionInfo` — 複雑レイアウトの領域情報

### 変換ロジック
`convertLEDDisplayInfoToScreenDataInSoftSpace.ts` — 103 行。
シンプルなレイアウト (矩形グリッド + スキャン方向) であれば 30〜50 行程度に収まるはず。

## 書き込み先レジスタ

`SoftwareSpaceBaseAddress`:
```
BASE_ADDRESS           = 0x00
DVI_BASE_ADDRESS       = 0x36
SCREEN_BASE_ADDRESS    = 0xB6   ← 画面設定の書き込み先
REDUNDANCY_BASE_ADDRESS = 0x65000
MODULATION_BASE_ADDRESS = 0x66000
```

`SCREEN_BASE_ADDRESS (0xB6)` から始まる領域に、圧縮済みペイロードを分割書き込み。

## Swift 実装計画 (着手する場合)

### Phase 1: LZMA 互換性の確認 (1–3 時間)
1. Node で sarakusha の `pack("hello world")` の出力をバイトで保存
2. Swift で `SWCompression` or `Compression.framework` の LZMA でデコード試行
3. 互換性があれば `SWCompression.LZMA` 系を採用

### Phase 2: 構造体の Swift 移植 (3–5 時間)
- `SoftwareSpaceHeader` (単純バイナリ)
- `ScreenDataInSoftSpace` (Codable struct)
- `CabinetInDevice`, `OnePortLoadInfo` など子要素
- `FileInfoObject`

### Phase 3: 変換ロジック (2–3 時間)
- columns / rows / cabinetSize / scanDirection から
  `ScreenDataInSoftSpace` を生成
- キャビネットの座標を scanDirection に応じて並び替える

### Phase 4: 書き込みフロー (2–3 時間)
- `SetSender_ScreenConfigFlagSpace` でリセット
- JSON → LZMA → FileInfo JSON → LZMA → Header 組み立て
- 64B ずつくらいに分割して `SetSender_SoftwareSpace(addr, data)` で書き込み
- 既存の `USBManager.buildPacket` と `sendCmd` を流用可能

### Phase 5: 実機検証 (3–6 時間)
- 既存プリセット 3 種と同じ出力になるか確認 (バイナリ一致テスト)
- 新パターン (1×4 上→下 / 3×2 等) で LED が正しく光るか確認

### 工数見積合計: 半日〜2 日

## やらない理由 (現時点)

- ユーザー要件は「縦・横パターンを増やしたいだけ」
  → 追加キャプチャ→プリセット追加 (案A) の方が 1 パターン 5〜10 分で済む
- 書き込み系は LED 破損のリスクがあり、全範囲の検証コストが高い
- LZMA 互換性の未確認部分が残っており、見積もりが下振れしにくい

## 再開する場合のトリガー条件

- プリセットが 10 種以上に膨らんで管理しにくくなったとき
- ユーザー側で「列数/行数を現場でチューニングしたい」要件が出たとき
- sarakusha 側で Swift/C API wrapper が出た、あるいは LZMA 互換性が確認されたとき

## 参考資料

- sarakusha/novastar `packages/screen/src/ScreenConfigurator.ts` の `saveImpl`
- sarakusha/novastar `packages/screen/src/common.ts` の `pack` / `unpack`
- sarakusha/novastar `packages/screen/src/SoftwareSpaceHeader.ts`
- sarakusha/novastar `packages/native/generated/ScreenDataInSoftSpace.ts`
- sarakusha/novastar `packages/native/generated/SoftwareSpaceBaseAddress.ts`
- Apple Compression framework: <https://developer.apple.com/documentation/compression>
- SWCompression (Swift package): <https://github.com/tsolomko/SWCompression>
