import Foundation
import IOKit
import IOKit.usb

/// NovaStar MSD300 USB通信マネージャー
/// MSD300のVendor/Product IDでUSBデバイスを検出し、コマンドを送信する。
class USBManager: ObservableObject {
    static let shared = USBManager()

    // MSD300 USB識別子（実機で要確認）
    private let vendorID: Int = 0x0D8C  // placeholder
    private let productID: Int = 0x0001 // placeholder

    @Published var isConnected: Bool = false
    @Published var deviceName: String = ""

    private var notificationPort: IONotificationPortRef?
    private var addedIterator: io_iterator_t = 0
    private var removedIterator: io_iterator_t = 0

    private init() {}

    // MARK: - 接続管理

    /// USB監視を開始する
    func startMonitoring() {
        let matchingDict = IOServiceMatching(kIOUSBDeviceClassName) as NSMutableDictionary
        matchingDict[kUSBVendorID] = vendorID
        matchingDict[kUSBProductID] = productID

        notificationPort = IONotificationPortCreate(kIOMainPortDefault)
        guard let notificationPort = notificationPort else {
            print("[USBManager] Failed to create notification port")
            return
        }

        let runLoopSource = IONotificationPortGetRunLoopSource(notificationPort).takeUnretainedValue()
        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .defaultMode)

        // デバイス接続の監視
        let addedCallback: IOServiceMatchingCallback = { (refcon, iterator) in
            let manager = Unmanaged<USBManager>.fromOpaque(refcon!).takeUnretainedValue()
            manager.deviceAdded(iterator: iterator)
        }

        let removedCallback: IOServiceMatchingCallback = { (refcon, iterator) in
            let manager = Unmanaged<USBManager>.fromOpaque(refcon!).takeUnretainedValue()
            manager.deviceRemoved(iterator: iterator)
        }

        let selfPtr = Unmanaged.passUnretained(self).toOpaque()

        // 接続通知の登録
        IOServiceAddMatchingNotification(
            notificationPort,
            kIOFirstMatchNotification,
            matchingDict,
            addedCallback,
            selfPtr,
            &addedIterator
        )
        deviceAdded(iterator: addedIterator)

        // 切断通知の登録（matchingDictは再利用不可なのでコピー）
        let removeMatchingDict = IOServiceMatching(kIOUSBDeviceClassName) as NSMutableDictionary
        removeMatchingDict[kUSBVendorID] = vendorID
        removeMatchingDict[kUSBProductID] = productID

        IOServiceAddMatchingNotification(
            notificationPort,
            kIOTerminatedNotification,
            removeMatchingDict,
            removedCallback,
            selfPtr,
            &removedIterator
        )
        deviceRemoved(iterator: removedIterator)

        print("[USBManager] Monitoring started for VID=\(String(format: "0x%04X", vendorID)) PID=\(String(format: "0x%04X", productID))")
    }

    /// USB監視を停止する
    func stopMonitoring() {
        if addedIterator != 0 {
            IOObjectRelease(addedIterator)
            addedIterator = 0
        }
        if removedIterator != 0 {
            IOObjectRelease(removedIterator)
            removedIterator = 0
        }
        if let port = notificationPort {
            IONotificationPortDestroy(port)
            notificationPort = nil
        }
        isConnected = false
        print("[USBManager] Monitoring stopped")
    }

    private func deviceAdded(iterator: io_iterator_t) {
        var service = IOIteratorNext(iterator)
        while service != 0 {
            DispatchQueue.main.async {
                self.isConnected = true
                self.deviceName = "MSD300"
            }
            print("[USBManager] Device connected")
            IOObjectRelease(service)
            service = IOIteratorNext(iterator)
        }
    }

    private func deviceRemoved(iterator: io_iterator_t) {
        var service = IOIteratorNext(iterator)
        while service != 0 {
            DispatchQueue.main.async {
                self.isConnected = false
                self.deviceName = ""
            }
            print("[USBManager] Device disconnected")
            IOObjectRelease(service)
            service = IOIteratorNext(iterator)
        }
    }

    // MARK: - コマンド送信

    /// レイアウト設定を送信する
    /// - Parameters:
    ///   - columns: 列数
    ///   - rows: 行数
    ///   - cabinetWidth: キャビネット幅 (px)
    ///   - cabinetHeight: キャビネット高さ (px)
    ///   - enabled: 有効なキャビネット位置のセット
    func setLayout(columns: Int, rows: Int, cabinetWidth: Int, cabinetHeight: Int, enabled: Set<CabinetPosition>) {
        // MSD300プロトコル: レイアウト設定コマンド
        // TODO: 実際のプロトコルに合わせてバイト列を構築
        var packet = Data()
        packet.append(contentsOf: [0x55, 0xAA]) // ヘッダー
        packet.append(contentsOf: [0x00, 0x00]) // コマンドID（レイアウト設定）
        packet.append(UInt8(columns))
        packet.append(UInt8(rows))
        packet.append(contentsOf: withUnsafeBytes(of: UInt16(cabinetWidth).bigEndian) { Array($0) })
        packet.append(contentsOf: withUnsafeBytes(of: UInt16(cabinetHeight).bigEndian) { Array($0) })

        // 有効/無効のビットマップ
        for r in 0..<rows {
            for c in 0..<columns {
                packet.append(enabled.contains(CabinetPosition(row: r, col: c)) ? 0x01 : 0x00)
            }
        }

        sendCommand(packet)
        print("[USBManager] setLayout: \(columns)x\(rows), cabinet: \(cabinetWidth)x\(cabinetHeight), enabled: \(enabled.count)")
    }

    /// 輝度を設定する
    /// - Parameter brightness: 輝度値 (0〜100)
    func setBrightness(_ brightness: Int) {
        let clamped = max(0, min(100, brightness))
        // MSD300プロトコル: 輝度設定コマンド
        // TODO: 実際のプロトコルに合わせてバイト列を構築
        var packet = Data()
        packet.append(contentsOf: [0x55, 0xAA]) // ヘッダー
        packet.append(contentsOf: [0x00, 0x01]) // コマンドID（輝度設定）
        packet.append(UInt8(clamped))

        sendCommand(packet)
        print("[USBManager] setBrightness: \(clamped)%")
    }

    /// USBデバイスにコマンドを送信する
    private func sendCommand(_ data: Data) {
        guard isConnected else {
            print("[USBManager] Not connected, command dropped")
            return
        }
        // TODO: IOUSBInterfaceを使って実際のUSB転送を実装
        // 現在はログ出力のみ
        print("[USBManager] Sending \(data.count) bytes: \(data.map { String(format: "%02X", $0) }.joined(separator: " "))")
    }
}
