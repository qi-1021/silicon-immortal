"""圆形晶圆上的完整矩形 die。忽略 reticle 拼版与测试结构。"""
from __future__ import annotations

import math


def wafer_sites(die_w, die_h, diameter=300.0, edge_exclusion=3.0, scribe=0.08):
    radius = diameter / 2 - edge_exclusion
    pitch_x, pitch_y = max(0.1, die_w) + scribe, max(0.1, die_h) + scribe
    sites = []
    for row in range(-math.ceil(radius / pitch_y), math.ceil(radius / pitch_y)):
        for col in range(-math.ceil(radius / pitch_x), math.ceil(radius / pitch_x)):
            x, y = (col + 0.5) * pitch_x, (row + 0.5) * pitch_y
            if (abs(x) + die_w / 2) ** 2 + (abs(y) + die_h / 2) ** 2 <= radius ** 2:
                sites.append((x, y))
    return sites
