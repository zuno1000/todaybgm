#!/usr/bin/env python3
"""アプリアイコンのPNG生成(要 Pillow)

デザイン: 白基調のジオメトリック・ミニマリズム版。
ごく淡いクールグレーへのグラデーションを敷いた白地に、
青バイオレットのグラデーション(#6B7BFF→#4353E8)で描いた連桁音符(♫)を1つ置く。
フォーカルポイントは音符グリフのみ。足元にわずかな青の落ち影で浮遊感を出す。
icon.svg と同一ジオメトリ(512グリッド × SS/512 倍)。

フル塗り(角丸なし)で出力する — iOSは自動で角丸マスク、Androidのmaskableにも対応。
グリフはmaskableのセーフゾーン(中央80%)内に収める。

出力: icon-512.png / icon-192.png / icon-180.png (リポジトリ直下)
"""

import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = 2048          # スーパーサンプリング解像度(縮小してアンチエイリアス)
K = SS / 512       # 512グリッド(icon.svg と共通)→ SS への倍率

BG_TOP = (255, 255, 255)      # #FFFFFF
BG_BOTTOM = (242, 245, 250)   # #F2F5FA
GLYPH_TOP = (107, 123, 255)   # #6B7BFF
GLYPH_BOTTOM = (67, 83, 232)  # #4353E8
SHADOW = (67, 83, 232)        # 落ち影(青)

# 512グリッド上のグリフ形状(icon.svg と一致させること)
STEM_W = 30
BEAM_W = 58
STEMS = [((188, 360), (188, 174)), ((360, 332), (360, 146))]
BEAM = ((188, 174), (360, 146))
HEADS = [(163, 360), (335, 332)]  # 中心座標
HEAD_RX, HEAD_RY, HEAD_ROT = 45, 34, 18  # 半径と回転角(度)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(size, top, bottom):
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        d.line([(0, y), (size, y)], fill=lerp(top, bottom, y / (size - 1)))
    return img


def capped_line(draw, p1, p2, width):
    """丸キャップ付きの太線"""
    draw.line([p1, p2], fill=255, width=width)
    r = width / 2
    for x, y in (p1, p2):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=255)


def glyph_mask():
    """連桁音符(♫)のマスク。座標は512グリッド→K倍"""
    mask = Image.new("L", (SS, SS), 0)
    d = ImageDraw.Draw(mask)
    for p1, p2 in STEMS:
        capped_line(d, tuple(v * K for v in p1), tuple(v * K for v in p2), round(STEM_W * K))
    capped_line(d, tuple(v * K for v in BEAM[0]), tuple(v * K for v in BEAM[1]), round(BEAM_W * K))
    # 符頭: 回転楕円は「レイヤーに水平楕円を描いて中心回転」で作る
    for cx, cy in HEADS:
        layer = Image.new("L", (SS, SS), 0)
        ld = ImageDraw.Draw(layer)
        ld.ellipse([(cx - HEAD_RX) * K, (cy - HEAD_RY) * K,
                    (cx + HEAD_RX) * K, (cy + HEAD_RY) * K], fill=255)
        layer = layer.rotate(HEAD_ROT, center=(cx * K, cy * K), resample=Image.BICUBIC)
        mask = ImageChops.lighter(mask, layer)
    return mask


def build():
    img = vertical_gradient(SS, BG_TOP, BG_BOTTOM).convert("RGBA")
    mask = glyph_mask()

    # 落ち影(下方向にわずかな青。opacity 0.18相当)
    shadow = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    tint = Image.new("RGBA", (SS, SS), SHADOW + (46,))
    shadow.paste(tint, (0, round(10 * K)), mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(round(14 * K)))
    img = Image.alpha_composite(img, shadow)

    # グリフ本体(縦グラデをマスク越しに)
    grad = vertical_gradient(SS, GLYPH_TOP, GLYPH_BOTTOM).convert("RGBA")
    img.paste(grad, (0, 0), mask)

    img = img.convert("RGB")
    for size in (512, 192, 180):
        out = img.resize((size, size), Image.LANCZOS)
        path = os.path.join(ROOT, f"icon-{size}.png")
        out.save(path, "PNG")
        print("wrote", path)


if __name__ == "__main__":
    build()
