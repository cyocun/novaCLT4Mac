import SwiftUI

// MARK: - BrightnessSchedule

struct BrightnessSchedule: Identifiable {
    let id = UUID()
    var time: String
    var brightness: Double
}

// MARK: - BrightnessView

struct BrightnessView: View {
    @State private var brightness: Double = 80
    @State private var autoMode: Bool = false
    @State private var scheduleEnabled: Bool = false
    @State private var schedules: [BrightnessSchedule] = [
        BrightnessSchedule(time: "08:00", brightness: 80),
        BrightnessSchedule(time: "22:00", brightness: 30),
    ]
    @State private var lastApplied: Double? = nil

    var isApplied: Bool {
        lastApplied == brightness
    }

    var body: some View {
        HStack(spacing: 0) {
            // 左メインエリア
            VStack(alignment: .leading, spacing: 28) {
                // ヘッダー
                Text("輝度調整")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(Color(hex: "#2d3436"))

                // 円弧メーター + スライダーカード
                VStack(spacing: 20) {
                    // 円弧メーター
                    BrightnessGaugeView(brightness: brightness)
                        .frame(width: 180, height: 180)

                    // スライダー
                    HStack(spacing: 12) {
                        Image(systemName: "sun.min")
                            .foregroundColor(.secondary)
                        Slider(value: $brightness, in: 0...100, step: 1)
                            .disabled(autoMode)
                            .opacity(autoMode ? 0.4 : 1.0)
                        Image(systemName: "sun.max.fill")
                            .foregroundColor(Color(hex: "#f39c12"))
                    }
                    .padding(.horizontal, 20)

                    // プリセットボタン
                    HStack(spacing: 8) {
                        ForEach([25, 50, 75, 100], id: \.self) { preset in
                            Button(action: { brightness = Double(preset) }) {
                                Text("\(preset)%")
                                    .font(.system(size: 12, weight: .medium))
                            }
                            .buttonStyle(PresetButtonStyle(isSelected: Int(brightness) == preset))
                            .disabled(autoMode)
                        }
                    }
                }
                .padding(24)
                .background(Color.white)
                .cornerRadius(16)
                .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)

                // 適用ボタン
                Button(action: applyBrightness) {
                    Text(isApplied ? "適用済み" : "輝度を適用")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(isApplied ? Color(hex: "#27ae60") : Color(hex: "#0f3460"))
                        .cornerRadius(8)
                        .animation(.easeInOut(duration: 0.2), value: isApplied)
                }
                .buttonStyle(.plain)
            }
            .padding(24)
            .frame(maxWidth: .infinity)

            // 右設定パネル
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("設定")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.secondary)
                        .textCase(.uppercase)

                    SettingsSection(title: "自動輝度") {
                        Toggle("センサー連動", isOn: $autoMode)
                            .font(.system(size: 12))
                        if autoMode {
                            Text("外部センサーに連動して自動的に輝度を調整します")
                                .font(.system(size: 10))
                                .foregroundColor(.secondary)
                        }
                    }

                    SettingsSection(title: "スケジュール") {
                        Toggle("スケジュール有効", isOn: $scheduleEnabled)
                            .font(.system(size: 12))

                        if scheduleEnabled {
                            ForEach($schedules) { $schedule in
                                ScheduleRow(schedule: $schedule)
                            }

                            Button(action: {
                                schedules.append(BrightnessSchedule(time: "12:00", brightness: 50))
                            }) {
                                Text("追加")
                                    .font(.system(size: 11, weight: .medium))
                            }
                            .buttonStyle(SmallButtonStyle(color: Color(hex: "#0f3460")))
                        }
                    }

                    SettingsSection(title: "状態") {
                        StatusRow(label: "現在の輝度", value: "\(Int(brightness))%")
                        StatusRow(label: "動作モード", value: autoMode ? "自動" : "手動")
                    }
                }
                .padding(16)
            }
            .frame(width: 200)
            .background(Color.white)
        }
    }

    private func applyBrightness() {
        lastApplied = brightness
        print("Apply brightness: \(Int(brightness))%")
    }
}

// MARK: - BrightnessGaugeView

struct BrightnessGaugeView: View {
    let brightness: Double

    var body: some View {
        ZStack {
            // 背景の円弧
            Circle()
                .trim(from: 0.15, to: 0.85)
                .stroke(
                    Color(hex: "#e8ecf0"),
                    style: StrokeStyle(lineWidth: 16, lineCap: .round)
                )
                .rotationEffect(.degrees(90))

            // 値の円弧
            Circle()
                .trim(from: 0.15, to: 0.15 + 0.7 * (brightness / 100))
                .stroke(
                    LinearGradient(
                        colors: [Color(hex: "#0f3460"), Color(hex: "#e94560")],
                        startPoint: .leading,
                        endPoint: .trailing
                    ),
                    style: StrokeStyle(lineWidth: 16, lineCap: .round)
                )
                .rotationEffect(.degrees(90))
                .animation(.easeOut(duration: 0.2), value: brightness)

            // 中心テキスト
            VStack(spacing: 0) {
                Text("\(Int(brightness))")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(Color(hex: "#2d3436"))
                Text("%")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.secondary)
            }
        }
    }
}

// MARK: - ScheduleRow

struct ScheduleRow: View {
    @Binding var schedule: BrightnessSchedule

    var body: some View {
        HStack(spacing: 6) {
            TextField("HH:MM", text: $schedule.time)
                .font(.system(size: 11, design: .monospaced))
                .frame(width: 50)
                .textFieldStyle(.roundedBorder)

            Slider(value: $schedule.brightness, in: 0...100, step: 5)

            Text("\(Int(schedule.brightness))%")
                .font(.system(size: 11, design: .monospaced))
                .frame(width: 30, alignment: .trailing)
        }
    }
}

// MARK: - StatusRow

struct StatusRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .font(.system(size: 12, weight: .semibold))
        }
    }
}

// MARK: - PresetButtonStyle

struct PresetButtonStyle: ButtonStyle {
    let isSelected: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundColor(isSelected ? .white : Color(hex: "#636e72"))
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(isSelected ? Color(hex: "#0f3460") : Color(hex: "#f0f3f7"))
            .cornerRadius(6)
    }
}

#Preview {
    BrightnessView()
}
