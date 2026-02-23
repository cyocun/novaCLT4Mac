# NovaController - Claude Code ガイド

## プロジェクト概要
NovaStar MSD300 LEDコントローラーをmacOSから操作するSwiftUIネイティブアプリ。

## 技術スタック
- Swift / SwiftUI
- macOS 14 Sonoma以降
- Xcode 15以降
- IOKit (USB通信)

## プロジェクト構成
```
NovaController/
├── NovaController.xcodeproj/
└── NovaController/
    ├── NovaControllerApp.swift   # エントリポイント
    ├── ContentView.swift          # メインレイアウト+サイドバー
    ├── LayoutView.swift           # キャビネット配置エディター+共有コンポーネント
    ├── BrightnessView.swift       # 輝度調整UI
    ├── Extensions.swift           # Color(hex:) 拡張
    ├── USBManager.swift           # USB通信マネージャー（IOKit）
    ├── NovaController.entitlements # App Sandbox + USB権限
    └── Assets.xcassets/           # アプリアイコン、AccentColor
```

## カラーパレット
- サイドバー背景: `#16213e` / ヘッダー: `#1a1a2e`
- アクセント: `#0f3460` / グラデーション終端: `#e94560`
- コンテンツ背景: `#f5f6fa` / グリッド背景: `#e8ecf0`
- 成功: `#27ae60` / ボーダー: `#b2bec3`

## ビルド
```bash
xcodebuild -project NovaController/NovaController.xcodeproj -scheme NovaController build
```

## 実装状況
- [x] UIレイアウト（サイドバー+コンテンツ）
- [x] キャビネット配置グリッドエディター
- [x] 輝度調整メーター+スライダー
- [x] USBManager（IOKit構造、USB監視、コマンド送信スタブ）
- [x] USBManager のView統合（ConnectionStatusView/LayoutView/BrightnessView接続済み）
- [ ] 実機でのVendor/Product ID確認
- [ ] MSD300プロトコルの実装
- [ ] エラーハンドリング（接続断時のUI表示）
