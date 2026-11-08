# 0.1.0-alpha.3

首个公开alpha发行。Windows10/11 x64、macOS14+ Apple Silicon与Intel提供原生便携包；包内含离线图文玩家手册和可导入设计例子。

- LAB成为CPU/GPU/NPU/ISP核心设计台：命名、自动保存、复制、结构参数、固定验证、发布、.cor交换与SoC复用。
- 6个自由产品项目之外新增12项挑战：分档、热、带宽、串行上限、RISC-V迁移、自研顺序核、相机加速器、SIMT驻留、面积、Chiplet、供应约束与固定售价毛利。
- .sil携带自定义核心与模板的名称/完整参数，导入优先文件快照；缺失定义或摘要损坏明确报错。
- 三个平台分别运行全量测试、原生打包和打包GUI冒烟。版本与模型元数据分别记载，读取不因版本数字不同而拒绝。

下载后先完整解压，再运行exe或app。阅读包内README_FIRST.txt和docs/player-guide/index.html。Mac包未Apple身份签名/公证，Windows包无商业签名；首次系统打开提示处理见玩家手册。SHA256SUMS.txt可用于核对下载完整性。

本作是教学游戏。CPU只有明确整数子集；GPU/NPU/ISP不是完整商业IP；PPA、签核与市场为估算。没有玩家RTL生成、PDK签核或实际流片能力，模拟硅片图不是实物显微图。

[玩家手册](https://github.com/qi-1021/silicon-immortal/blob/main/docs/guide/README.md) · [问题反馈](https://github.com/qi-1021/silicon-immortal/issues)
