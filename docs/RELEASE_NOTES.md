# 0.1.0-alpha.5 · 自由设计工作区

源码与脚本发行：Windows用run.bat，Mac用run.command，Linux用bash run.sh。需Python3.12；首次在项目虚拟环境安装固定依赖，无exe/app。Linux按用户请求新增脚本，未做平台验证；自动三平台验证已停用，只生成手册与源码附件。

- 核心表格共用列宽：名称/分类、实例数、L2容量、私有/全组共享、目标GHz和删除一一对应。频率0明确显示自动，小窗口可横向滚动。
- x86增加64位整数设计/执行器：16GPR、32位别名零扩展、REX、指定MOV/算术/IMUL/shift/Jcc/基址访存。32/64分别保存；没有OS、分页、SSE/AVX或完整x86。
- 核心模板扩充精简、均衡、宽发射、计算吞吐方向，覆盖x86-64、Arm64与RISC-V；每个模板有可编辑完整硬件定义。
- 独立自由沙盒入口与独立存档。签核给出潜在问题、原因和改善方向，不按任务/预算/许可条件阻止预览。普通项目约束保留；未知语义和无效输入仍不能解析。
- 芯片/封装PDN可输入等效电阻，以I×R展示压降。设备散热器默认折叠为整机厂商的使用场景；芯片侧负责功耗和封装取舍。
- 作者动机、联系渠道与未来愿景保留，图文手册覆盖启动、四类核心、SoC、挑战、64位x86、沙盒、诊断和导出分享。

本轮只对改变的功能做本地检查与界面截图，未重复运行平台矩阵。当前是功能与资源教学模型，没有玩家RTL生成、真实PDK签核或实际流片；自由预览不是物理验证证明。

完整解压SiliconImmortal-source.zip，先装Python3.12，再用平台脚本启动。附docs/player-guide/index.html离线手册与SHA256SUMS.txt。

[玩家手册](https://github.com/qi-1021/silicon-immortal/blob/main/docs/guide/README.md) · [问题反馈](https://github.com/qi-1021/silicon-immortal/issues)
