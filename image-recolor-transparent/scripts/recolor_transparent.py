# -*- coding: utf-8 -*-
"""
通用图片配色改造 + 精细透明底脚本 (image-recolor-transparent skill 的参考实现)

用法:
  python recolor_transparent.py <输入图> <输出图> [选项]

选项 (都有默认值, 对应 PPT 蓝灰橙模板):
  --hue-from-red        把红色系重映射为橙色 (默认开)
  --target-hue N        目标色相角度 0-60, 默认 32 (暖橙)
  --base-gray R,G,B     灰黑系映射基准色, 默认 68,84,106 (文字蓝灰)
  --white-thr N         近白判定亮度阈值, 默认 244
  --big-white N         封闭白区判背景的面积阈值(px), 默认 4000
  --absorb-px N         白色小块吸收半径(px), 默认 10
  --feather-px N        羽化带宽(px), 默认 3
"""
import sys
import argparse
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, label


def process(src, dst, target_hue=32.0, base_gray=(68, 84, 106),
            white_thr=244, big_white=4000, absorb_px=10, feather_px=3,
            preview_dir=None):
    BG = np.array(base_gray, dtype=float)
    BG_LUM = 0.299 * BG[0] + 0.587 * BG[1] + 0.114 * BG[2]

    img = Image.open(src).convert("RGBA")
    a = np.array(img).astype(float)
    rgb = a[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    sat = mx - mn
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    # ---- 1) 红色系 -> 目标色相 (保持明度/饱和度结构) ----
    red_mask = (sat > 18) & (r > g + 8) & (r > b + 8)
    out = rgb.copy()
    v = mx[red_mask]
    c = sat[red_mask]
    out[red_mask, 0] = v
    out[red_mask, 2] = v - c
    out[red_mask, 1] = (v - c) + c * (target_hue / 60.0)

    # ---- 2) 灰/黑色系 -> 基准色系 (按明度映射深浅) ----
    gray_mask = (~red_mask) & (sat <= 18)
    gl = lum[gray_mask]
    ratio_dark = np.clip(gl / BG_LUM, 0, 1)
    t_light = np.clip((gl - BG_LUM) / (255.0 - BG_LUM), 0, 1)
    res = np.empty((gl.shape[0], 3))
    for i in range(3):
        res[:, i] = np.where(gl <= BG_LUM, BG[i] * ratio_dark,
                             BG[i] + (255.0 - BG[i]) * t_light)
    out[gray_mask] = res

    h, w = lum.shape

    # ---- 3) 背景白区判定: 触边/大块 -> 背景, 再迭代吸收近旁白色小块 ----
    near_white = lum >= white_thr
    lbl, n = label(near_white)
    sizes = np.bincount(lbl.ravel())
    edge_ids = set(np.unique(np.concatenate(
        [lbl[0, :], lbl[-1, :], lbl[:, 0], lbl[:, -1]])))
    edge_ids.discard(0)

    is_bg = np.zeros(n + 1, dtype=bool)
    for i in range(1, n + 1):
        if i in edge_ids or sizes[i] > big_white:
            is_bg[i] = True

    for _ in range(10):
        bg_mask = is_bg[lbl]
        reach = binary_dilation(bg_mask, iterations=absorb_px)
        near_ids = np.unique(lbl[reach & near_white])
        changed = False
        for i in near_ids:
            if i != 0 and not is_bg[i]:
                is_bg[i] = True
                changed = True
        if not changed:
            break

    bg_mask = is_bg[lbl]
    kept_white = near_white & ~bg_mask  # 色块深处的白字, 强制保留

    # ---- 4) alpha: 背景透明 + 羽化带 ----
    alpha_f = np.ones((h, w))
    alpha_f[bg_mask] = 0.0
    band = (binary_dilation(bg_mask, iterations=feather_px)
            & ~bg_mask & ~kept_white & (lum >= 170))
    alpha_f[band] = np.clip((250.0 - lum[band]) / (250.0 - 170.0), 0.0, 1.0)

    # ---- 5) 去白边 (颜色去污染): F = (obs - (1-a)*255) / a ----
    sel = band & (alpha_f > 0.04)
    af = alpha_f[sel][:, None]
    out[sel] = np.clip((out[sel] - (1.0 - af) * 255.0) / af, 0, 255)

    alpha_out = (alpha_f * 255).round().astype(np.uint8)
    alpha_out = np.minimum(alpha_out, a[..., 3].astype(np.uint8))

    result = np.dstack([out.clip(0, 255).astype(np.uint8), alpha_out])
    Image.fromarray(result, "RGBA").save(dst)

    previews = []
    if preview_dir:
        import os
        for name, col in (("_preview_dark.png", (45, 45, 60, 255)),
                          ("_preview_light.png", (205, 215, 232, 255))):
            prev = Image.new("RGBA", img.size, col)
            prev.alpha_composite(Image.fromarray(result, "RGBA"))
            p = os.path.join(preview_dir, name)
            prev.convert("RGB").save(p)
            previews.append(p)
    return dst, int((alpha_out == 0).sum()), int(kept_white.sum()), previews


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--target-hue", type=float, default=32.0)
    ap.add_argument("--base-gray", default="68,84,106")
    ap.add_argument("--white-thr", type=int, default=244)
    ap.add_argument("--big-white", type=int, default=4000)
    ap.add_argument("--absorb-px", type=int, default=10)
    ap.add_argument("--feather-px", type=int, default=3)
    ap.add_argument("--preview-dir", default=None)
    ns = ap.parse_args()
    base = tuple(int(x) for x in ns.base_gray.split(","))
    dst, tp, kw, pv = process(ns.src, ns.dst, ns.target_hue, base,
                              ns.white_thr, ns.big_white, ns.absorb_px,
                              ns.feather_px, ns.preview_dir)
    print(f"saved: {dst} | transparent px: {tp} | kept white px: {kw}")
    for p in pv:
        print("preview:", p)
