#!/usr/bin/env python3
"""NovaController アプリアイコン生成スクリプト

デザイン: ダークネイビー背景にLEDグリッドモチーフ + 輝度を表すグラデーション弧
カラーパレット: #0f3460 (メイン), #e94560 (アクセント), #16213e (背景)
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

def create_icon(size):
    """指定サイズのアイコンを生成"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s = size  # 基準サイズ
    margin = s * 0.12  # 角丸矩形のマージン
    radius = s * 0.22  # 角丸の半径

    # 背景: 角丸矩形 (#16213e → #0f3460 グラデーション)
    # グラデーション背景を描画
    for y in range(size):
        t = y / size
        r = int(22 * (1 - t) + 15 * t)
        g = int(33 * (1 - t) + 52 * t)
        b = int(62 * (1 - t) + 96 * t)
        for x in range(size):
            img.putpixel((x, y), (r, g, b, 255))

    # 角丸マスクを適用
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [int(margin * 0.3), int(margin * 0.3),
         size - int(margin * 0.3), size - int(margin * 0.3)],
        radius=int(radius),
        fill=255
    )
    img.putalpha(mask)

    # LEDグリッド (3x3) を描画
    grid_size = 3
    grid_area_start_x = s * 0.2
    grid_area_start_y = s * 0.22
    grid_area_size = s * 0.58
    cell_spacing = s * 0.04
    cell_size = (grid_area_size - cell_spacing * (grid_size - 1)) / grid_size
    cell_radius = cell_size * 0.15

    # グリッドセルの色パターン
    # アクティブなセルとインアクティブなセルで区別
    cell_colors = [
        # row 0
        [(15, 52, 96, 200), (214, 234, 248, 255), (214, 234, 248, 255)],
        # row 1
        [(214, 234, 248, 255), (233, 69, 96, 255), (214, 234, 248, 255)],
        # row 2
        [(214, 234, 248, 255), (214, 234, 248, 255), (15, 52, 96, 200)],
    ]

    draw = ImageDraw.Draw(img)

    for row in range(grid_size):
        for col in range(grid_size):
            x = grid_area_start_x + col * (cell_size + cell_spacing)
            y = grid_area_start_y + row * (cell_size + cell_spacing)
            color = cell_colors[row][col]

            draw.rounded_rectangle(
                [int(x), int(y), int(x + cell_size), int(y + cell_size)],
                radius=int(cell_radius),
                fill=color
            )

    # 右下に輝度の弧を描画
    arc_center_x = s * 0.72
    arc_center_y = s * 0.78
    arc_radius = s * 0.18
    arc_width = max(2, int(s * 0.035))

    # 背景弧 (暗め)
    bbox = [
        int(arc_center_x - arc_radius), int(arc_center_y - arc_radius),
        int(arc_center_x + arc_radius), int(arc_center_y + arc_radius)
    ]
    draw.arc(bbox, start=180, end=360, fill=(255, 255, 255, 40), width=arc_width)

    # フォアグラウンド弧 (グラデーション風 - #0f3460 → #e94560)
    steps = 30
    for i in range(steps):
        t = i / steps
        angle_start = 180 + t * 150  # 180° から 330° まで (83%)
        angle_end = 180 + (i + 1) / steps * 150

        r = int(15 + t * (233 - 15))
        g = int(52 + t * (69 - 52))
        b = int(96 + t * (96 - 96))

        draw.arc(bbox, start=angle_start, end=angle_end + 1,
                fill=(r, g, b, 255), width=arc_width)

    # マスクを再適用（描画がはみ出ていないか確認）
    img.putalpha(mask)

    return img


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_dir = os.path.join(
        base_dir,
        "NovaController/NovaController/Assets.xcassets/AppIcon.appiconset"
    )

    # macOS必須サイズ
    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    for filename, size in sizes.items():
        icon = create_icon(size)
        path = os.path.join(icon_dir, filename)
        icon.save(path, 'PNG')
        print(f"  Generated: {filename} ({size}x{size})")

    print(f"\nAll icons saved to: {icon_dir}")


if __name__ == "__main__":
    main()
