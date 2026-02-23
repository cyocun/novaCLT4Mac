# Nova Controller — Claude Code 指示書

NovaStar MSD300 LEDコントローラーを macOS から操作するネイティブアプリを作る。
UIのみ実装済み（USB通信部分は未実装のスタブ）。

---

## 作るもの

- **言語**: Swift / SwiftUI
- **対象OS**: macOS 14 Sonoma 以降
- **Xcode**: 15 以降
- **ウィンドウサイズ**: 860×600（固定）

---

## プロジェクトのセットアップ

Xcodeで新規プロジェクトを作成する:
- Template: macOS → App
- Product Name: `NovaController`
- Interface: SwiftUI
- Language: Swift
- Include Tests: オフ

---

## ファイル構成

以下の5ファイルを作成する（Xcodeが自動生成するファイルは上書きまたは削除して差し替える）:

```
NovaController/
├── NovaControllerApp.swift
├── ContentView.swift
├── LayoutView.swift
├── BrightnessView.swift
└── Extensions.swift
```

---

## 各ファイルの実装内容

### NovaControllerApp.swift

```swift
import SwiftUI

@main
struct NovaControllerApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
    }
}
```

---

### Extensions.swift

`Color(hex: "#RRGGBB")` で色を指定できるようにする拡張。

```swift
import SwiftUI

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(.sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
```

---

### ContentView.swift

**全体レイアウト**: 左サイドバー（幅180）＋右コンテンツエリア（可変幅）の HStack。

**サイドバー** (背景色 `#16213e`):
- ヘッダー: `display.2` アイコン＋「Nova Controller」テキスト。背景色 `#1a1a2e`、縦padding 24。
- `ConnectionStatusView`: 接続状態バッジ。横padding 12、縦padding 10。
- `Divider`（白 10% 透過）
- `NavItem` x2: 「レイアウト」（`square.grid.3x3`）と「輝度調整」（`sun.max`）。選択中は `#0f3460` 背景。

**コンテンツエリア** (背景色 `#f5f6fa`):
- `selectedTab` に応じて `LayoutView` か `BrightnessView` を表示。

**ConnectionStatusView**:
- `@State private var isConnected = false`
- 接続中: 緑の丸＋「MSD300 接続中」＋「USB」サブテキスト
- 未接続: オレンジの丸＋「未接続」
- 右端にトグルボタン（接続中は `xmark.circle`、未接続は `arrow.clockwise`）
- 背景: 白 6% 透過、cornerRadius 8

**NavItem**:
- `icon: String`, `title: String`, `isSelected: Bool`, `action: () -> Void`
- 選択中: 白テキスト、`#0f3460` 背景
- 非選択: 白 50% テキスト、透明背景

---

### LayoutView.swift

**状態変数**:
```swift
@State private var columns: Int = 4
@State private var rows: Int = 3
@State private var cabinetWidth: Int = 128
@State private var cabinetHeight: Int = 128
@State private var selectedCabinet: CabinetPosition? = nil
@State private var enabledCabinets: Set<CabinetPosition> = []
```

**全体レイアウト**: 左メインエリア（可変幅）＋右設定パネル（幅200、白背景）の HStack。

**左メインエリア** (padding 24):
- ヘッダー: 「キャビネット配置」テキスト＋右に「合計: N / M キャビネット」
- `GridEditorView`（グリッドエディター、高さ280）
- フッター: `aspectratio` アイコン＋「出力解像度: W × H px」
  - `enabledCabinets.count > 0` のときのみ計算値を表示。それ以外は `0 × 0`。
- 「レイアウトを適用」ボタン（`#0f3460` 背景、全幅）

**右設定パネル**:
- 「設定」ヘッダー（secondary色）
- `SettingsSection("グリッドサイズ")`: `StepperField` で列数（1〜16）、行数（1〜16）
- `SettingsSection("キャビネットサイズ (px)")`: `StepperField` で幅・高さ（32〜512、step 8）
- `selectedCabinet` が非nilのとき `SettingsSection("選択中のキャビネット")`: 位置・有効/無効状態を表示
- `SettingsSection("クイック操作")`: 「全て有効」「全て無効」ボタン

**CabinetPosition**:
```swift
struct CabinetPosition: Hashable {
    let row: Int
    let col: Int
}
```

**GridEditorView**:
- `GeometryReader` でセルサイズを動的計算。最大80px。
- セル間隔 4px。
- 背景色 `#e8ecf0`、cornerRadius 12。
- **タップ挙動**:
  - 未選択セルをタップ → そのセルを選択状態に
  - 選択済みセルをタップ → 有効/無効をトグル

**CabinetCell**:
- 状態による見た目:
  - 選択中かつ有効: 背景 `#0f3460`、白アイコン＋座標テキスト
  - 選択中かつ無効: 背景 `#dfe6e9`、ボーダー `#0f3460`
  - 未選択かつ有効: 背景 `#d6eaf8`、`#0f3460` アイコン＋座標テキスト（セルサイズ > 50のとき）
  - 未選択かつ無効: 白 60% 背景、`#b2bec3` の × アイコン
- アニメーション: `easeInOut(duration: 0.15)` で状態変化をアニメート

**共有コンポーネント**（LayoutView.swift 内に定義し、BrightnessView.swiftでも使う）:

`SettingsSection<Content: View>`:
- タイトル（11pt、semibold、secondary、uppercase）
- コンテンツを `#f5f6fa` 背景のカード内（padding 12、cornerRadius 8）に表示

`StepperField`:
- ラベル + [−][値][＋] の横並び
- ボタンはサイズ 24×24、背景 `#dfe6e9`
- 値表示は幅36の中央揃え
- 全体に cornerRadius 6 ＋ `#b2bec3` ボーダー

`SmallButtonStyle`:
- 全幅、縦padding 7、cornerRadius 6
- `color` パラメーターで背景色を指定
- 押下時は透明度 70%

**applyLayout()**: 現時点では `print` のみ（USB通信は未実装）。

---

### BrightnessView.swift

**状態変数**:
```swift
@State private var brightness: Double = 80
@State private var autoMode: Bool = false
@State private var scheduleEnabled: Bool = false
@State private var schedules: [BrightnessSchedule] = [
    BrightnessSchedule(time: "08:00", brightness: 80),
    BrightnessSchedule(time: "22:00", brightness: 30),
]
@State private var lastApplied: Double? = nil
```

**全体レイアウト**: 左メインエリア（可変幅）＋右設定パネル（幅200、白背景）の HStack。

**左メインエリア** (padding 24、spacing 28):
- 「輝度調整」ヘッダー
- 円弧メーター＋スライダーカード（白背景、cornerRadius 16、影）
- 「輝度を適用」ボタン

**円弧メーター** (サイズ 180×180):
- `Circle().trim` で円弧を描く。trim範囲: `from: 0.15, to: 0.85`（背景）
- 値に応じたtrim: `from: 0.15, to: 0.15 + 0.7 * (brightness / 100)`（フォアグラウンド）
- フォアグラウンドの色: `LinearGradient` で `#0f3460` → `#e94560`
- `rotationEffect(.degrees(90))` で12時スタートに
- `strokeStyle(lineWidth: 16, lineCap: .round)`
- 中心に輝度値（48pt、bold、rounded）＋「%」
- brightness変化時に `easeOut(duration: 0.2)` でアニメート

**スライダー**:
- 左に `sun.min`（secondary）、右に `sun.max.fill`（`#f39c12`）
- `Slider(value: $brightness, in: 0...100, step: 1)`
- `autoMode` が true のとき disabled、opacity 40%

**プリセットボタン**: 25, 50, 75, 100 の4つ。選択中は `#0f3460` 背景。

**「輝度を適用」ボタン**:
- `lastApplied == brightness` のとき: 背景 `#27ae60`、テキスト「適用済み」
- それ以外: 背景 `#0f3460`、テキスト「輝度を適用」
- `easeInOut(duration: 0.2)` でアニメート

**右設定パネル**:
- `SettingsSection("自動輝度")`: Toggle「センサー連動」。オンのとき説明テキスト表示。
- `SettingsSection("スケジュール")`: Toggle「スケジュール有効」。オンのとき `ScheduleRow` 一覧＋「追加」ボタン。
- `SettingsSection("状態")`: `StatusRow` で現在の輝度と動作モードを表示。

**BrightnessSchedule**:
```swift
struct BrightnessSchedule: Identifiable {
    let id = UUID()
    var time: String       // "HH:MM" 形式
    var brightness: Double // 0〜100
}
```

**ScheduleRow**:
- 時刻 TextField（幅50、monospaced）＋ Slider（0〜100、step 5）＋ 値テキスト（幅30）

**StatusRow**:
- ラベル（secondary）と値（semibold）の横並び

**PresetButtonStyle**:
- `isSelected` パラメーター。選択中は `#0f3460` 背景・白テキスト、非選択は `#f0f3f7` 背景・`#636e72` テキスト。

**applyBrightness()**: 現時点では `lastApplied = brightness` ＋ `print` のみ（USB通信は未実装）。

---

## カラーパレット

| 用途 | カラーコード |
|------|-------------|
| サイドバー背景 | `#16213e` |
| サイドバーヘッダー | `#1a1a2e` |
| アクセント（メイン） | `#0f3460` |
| アクセント（グラデーション終端） | `#e94560` |
| コンテンツ背景 | `#f5f6fa` |
| グリッド背景 | `#e8ecf0` |
| 有効キャビネット背景 | `#d6eaf8` |
| ボーダー | `#b2bec3` |
| 選択グレー | `#dfe6e9` |
| テキスト（メイン） | `#2d3436` |
| 成功（適用済み） | `#27ae60` |
| 太陽アイコン | `#f39c12` |

---

## 未実装部分（今後追加予定）

`USBManager.swift` を別途追加してUSB通信を実装する。
以下のメソッドが呼ばれる想定でスタブを残しておく:

```swift
// LayoutView.swift の applyLayout()
// → USBManager.shared.setLayout(columns:rows:enabled:) を呼ぶ

// BrightnessView.swift の applyBrightness()
// → USBManager.shared.setBrightness(Int(brightness)) を呼ぶ
```

現時点では `print` 文のみでOK。`USBManager` クラスは作らなくてよい。

---

## ビルド確認ポイント

- [ ] ウィンドウが860×600で固定表示される
- [ ] サイドバーのナビゲーションで画面が切り替わる
- [ ] 接続ステータスのトグルボタンが動作する
- [ ] グリッドのセルをタップで選択→再タップで有効/無効トグルできる
- [ ] 「全て有効」「全て無効」ボタンが動作する
- [ ] 輝度スライダーと円弧メーターが連動して動く
- [ ] プリセットボタンで輝度が変わる
- [ ] 「輝度を適用」→「適用済み」に見た目が変わる
- [ ] 自動輝度をオンにするとスライダーが無効になる
- [ ] スケジュール有効化でスケジュール一覧が表示される
