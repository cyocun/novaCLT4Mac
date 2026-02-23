import SwiftUI

struct ContentView: View {
    @State private var selectedTab: Tab = .layout

    enum Tab {
        case layout, brightness
    }

    var body: some View {
        HStack(spacing: 0) {
            // サイドバー
            VStack(spacing: 0) {
                // ヘッダー
                HStack(spacing: 8) {
                    Image(systemName: "display.2")
                        .font(.system(size: 16))
                        .foregroundColor(.white)
                    Text("Nova Controller")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.white)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 24)
                .background(Color(hex: "#1a1a2e"))

                // 接続ステータス
                ConnectionStatusView()
                    .padding(.horizontal, 12)
                    .padding(.vertical, 10)

                Divider()
                    .background(Color.white.opacity(0.1))

                // ナビゲーション
                VStack(spacing: 2) {
                    NavItem(icon: "square.grid.3x3", title: "レイアウト", isSelected: selectedTab == .layout) {
                        selectedTab = .layout
                    }
                    NavItem(icon: "sun.max", title: "輝度調整", isSelected: selectedTab == .brightness) {
                        selectedTab = .brightness
                    }
                }
                .padding(.top, 8)

                Spacer()
            }
            .frame(width: 180)
            .background(Color(hex: "#16213e"))

            // コンテンツエリア
            Group {
                switch selectedTab {
                case .layout:
                    LayoutView()
                case .brightness:
                    BrightnessView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(hex: "#f5f6fa"))
        }
        .frame(width: 860, height: 600)
    }
}

// MARK: - ConnectionStatusView

struct ConnectionStatusView: View {
    @ObservedObject private var usbManager = USBManager.shared

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(usbManager.isConnected ? Color.green : Color.orange)
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 1) {
                Text(usbManager.isConnected ? "MSD300 接続中" : "未接続")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(.white)
                if usbManager.isConnected {
                    Text("USB")
                        .font(.system(size: 9))
                        .foregroundColor(.white.opacity(0.5))
                }
            }

            Spacer()

            Button(action: {
                if usbManager.isConnected {
                    usbManager.stopMonitoring()
                } else {
                    usbManager.startMonitoring()
                }
            }) {
                Image(systemName: usbManager.isConnected ? "xmark.circle" : "arrow.clockwise")
                    .font(.system(size: 12))
                    .foregroundColor(.white.opacity(0.6))
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(Color.white.opacity(0.06))
        .cornerRadius(8)
    }
}

// MARK: - NavItem

struct NavItem: View {
    let icon: String
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 13))
                Text(title)
                    .font(.system(size: 13))
                Spacer()
            }
            .foregroundColor(isSelected ? .white : .white.opacity(0.5))
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(isSelected ? Color(hex: "#0f3460") : Color.clear)
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
        .padding(.horizontal, 8)
    }
}

#Preview {
    ContentView()
}
