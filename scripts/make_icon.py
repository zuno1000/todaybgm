#!/usr/bin/env python3
"""アプリアイコンのPNG生成(要 Pillow)

デザイン: 深紺のグラデーション背景+角丸プレイボタン(青グラデ)+黄色のきらめき。
フル塗り(角丸なし)で出力する — iOSは自動で角丸マスク、Androidのmaskableにも対応。
モチーフはmaskableのセーフゾーン(中央80%)内に収める。

出力: icon-512.png / icon-192.png / icon-180.png (リポジトリ直下)
"""

import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = 2048  # スーパーサンプリング解像度(縮小してアンチエイリアス)

BG_TOP = (37, 44, 68)      # #252c44
BG_BOTTOM = (15, 17, 25)   # #0f1119
TRI_TOP = (143, 176, 255)  # #8fb0ff
TRI_BOTTOM = (93, 135, 232)  # #5d87e8
SPARK = (247, 201, 72)     # #f7c948


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(size, top, bottom):
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        d.line([(0, y), (size, y)], fill=lerp(top, bottom, y / (size - 1)))
    return img


def rounded_triangle_mask(size, pts, radius):
    """角丸三角形のマスク(頂点に円+辺に太線+中を塗り)"""
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.polygon(pts, fill=255)
    d.line(pts + [pts[0]], fill=255, width=radius * 2, joint="curve")
    for x, y in pts:
        d.ellipse([x - radius, y - radius, x + radius, y + radius], fill=255)
    return mask


def sparkle(draw, cx, cy, r, fill):
    """4方向のきらめき(ダイヤ型スター)"""
    w = r * 0.28
    pts = [(cx, cy - r), (cx + w, cy - w), (cx + r, cy), (cx + w, cy + w),
           (cx, cy + r), (cx - w, cy + w), (cx - r, cy), (cx - w, cy - w)]
    draw.polygon(pts, fill=fill)


def build():
    img = vertical_gradient(SS, BG_TOP, BG_BOTTOM)

    # プレイボタン(角丸・青グラデ)。maskableセーフゾーン内に配置
    tri_pts = [(int(SS * 0.385), int(SS * 0.315)),
               (int(SS * 0.385), int(SS * 0.685)),
               (int(SS * 0.715), int(SS * 0.50))]
    tri_mask = rounded_triangle_mask(SS, tri_pts, int(SS * 0.028))
    tri_grad = vertical_gradient(SS, TRI_TOP, TRI_BOTTOM)
    img.paste(tri_grad, (0, 0), tri_mask)

    # きらめき(大小)
    d = ImageDraw.Draw(img)
    sparkle(d, SS * 0.715, SS * 0.255, SS * 0.062, SPARK)
    sparkle(d, SS * 0.795, SS * 0.345, SS * 0.028, SPARK)

    for size in (512, 192, 180):
        out = img.resize((size, size), Image.LANCZOS)
        path = os.path.join(ROOT, f"icon-{size}.png")
        out.save(path, "PNG")
        print("wrote", path)


if __name__ == "__main__":
    build()
