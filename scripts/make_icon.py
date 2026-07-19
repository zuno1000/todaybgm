#!/usr/bin/env python3
"""アプリアイコンのPNG生成(要 Pillow)

デザイン: Soft UI(ニューモーフィズム)版。
淡青グレー(#E8EDF5系)の面に、2方向の影(左上=白い光/右下=青灰の陰)で
浮き上がる円盤を置き、その上に青グラデ(#5B6CFF→#4353E8)の角丸プレイボタン。
アプリ本体のデザイントークン(デザインリニューアル手順書 SoftUI版)と同一パレット。

フル塗り(角丸なし)で出力する — iOSは自動で角丸マスク、Androidのmaskableにも対応。
モチーフはmaskableのセーフゾーン(中央80%)内に収める。

出力: icon-512.png / icon-192.png / icon-180.png (リポジトリ直下)
"""

import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = 2048  # スーパーサンプリング解像度(縮小してアンチエイリアス)

BG_TOP = (238, 242, 249)      # #EEF2F9
BG_BOTTOM = (226, 232, 242)   # #E2E8F2
DISC_TOP = (241, 245, 251)    # #F1F5FB(光の当たる側)
DISC_BOTTOM = (228, 234, 244) # #E4EAF4
SH_DARK = (136, 152, 184)     # 右下の陰(青灰)
SH_LIGHT = (255, 255, 255)    # 左上の光
TRI_TOP = (91, 108, 255)      # #5B6CFF
TRI_BOTTOM = (67, 83, 232)    # #4353E8


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(size, top, bottom):
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        d.line([(0, y), (size, y)], fill=lerp(top, bottom, y / (size - 1)))
    return img


def circle_mask(size, cx, cy, r):
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    return mask


def rounded_triangle_mask(size, pts, radius):
    """角丸三角形のマスク(頂点に円+辺に太線+中を塗り)"""
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.polygon(pts, fill=255)
    d.line(pts + [pts[0]], fill=255, width=radius * 2, joint="curve")
    for x, y in pts:
        d.ellipse([x - radius, y - radius, x + radius, y + radius], fill=255)
    return mask


def soft_shadow(base, mask, offset, blur, color, alpha):
    """maskの形の影を offset だけずらして base に合成する"""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tint = Image.new("RGBA", base.size, color + (alpha,))
    shadow.paste(tint, offset, mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(shadow)
    return Image.alpha_composite(base, layer)


def build():
    img = vertical_gradient(SS, BG_TOP, BG_BOTTOM).convert("RGBA")

    # --- 円盤(浮き): 左上に光・右下に陰の2方向影 ---
    cx = cy = SS // 2
    r = int(SS * 0.31)  # maskableセーフゾーン(中央80%)内
    disc_mask = circle_mask(SS, cx, cy, r)
    off = int(SS * 0.024)
    blur = int(SS * 0.030)
    img = soft_shadow(img, disc_mask, (off, off), blur, SH_DARK, 115)
    img = soft_shadow(img, disc_mask, (-off, -off), blur, SH_LIGHT, 230)
    disc_grad = vertical_gradient(SS, DISC_TOP, DISC_BOTTOM).convert("RGBA")
    img.paste(disc_grad, (0, 0), disc_mask)

    # --- プレイボタン(角丸・青グラデ)+青グロー ---
    tri_pts = [(int(SS * 0.435), int(SS * 0.385)),
               (int(SS * 0.435), int(SS * 0.615)),
               (int(SS * 0.645), int(SS * 0.50))]
    tri_mask = rounded_triangle_mask(SS, tri_pts, int(SS * 0.024))
    img = soft_shadow(img, tri_mask, (int(SS * 0.008), int(SS * 0.014)),
                      int(SS * 0.018), TRI_TOP, 110)
    tri_grad = vertical_gradient(SS, TRI_TOP, TRI_BOTTOM).convert("RGBA")
    img.paste(tri_grad, (0, 0), tri_mask)

    img = img.convert("RGB")
    for size in (512, 192, 180):
        out = img.resize((size, size), Image.LANCZOS)
        path = os.path.join(ROOT, f"icon-{size}.png")
        out.save(path, "PNG")
        print("wrote", path)


if __name__ == "__main__":
    build()
