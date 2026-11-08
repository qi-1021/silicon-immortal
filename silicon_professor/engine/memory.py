"""内存总线的单位换算。MT/s × x16 通道数 / 8 = MB/s。"""
from ..data.blocks import DRAMS


def memory_spec(design):
    dram = DRAMS.get(design.dram, DRAMS["lpddr4x"])
    channels = max(1, min(8, design.memory_channels or dram["channels"]))
    theoretical = dram["gbps"] * channels * 16 / 8000.0
    return dict(channels=channels, width_bits=channels * 16,
                data_rate_mts=dram["gbps"], theoretical_gbs=theoretical,
                effective_gbs=theoretical * dram["efficiency"],
                efficiency=dram["efficiency"])
