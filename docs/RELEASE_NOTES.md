# 0.1.0-alpha.4 · 源码与脚本发行

公开alpha源码发行。先安装Python3.12，Windows10/11 x64双击run.bat，macOS14+ Intel/M系列双击run.command或运行bash run.command。首次创建虚拟环境并安装固定依赖；本次不提供exe/app。

- LAB成为CPU/GPU/NPU/ISP核心设计台：命名、自动保存、复制、结构参数、固定验证、发布、.cor交换与SoC复用。
- 7个自由产品项目（包含x86工作站）之外新增12项挑战：分档、热、带宽、串行上限、RISC-V迁移、自研顺序核、相机加速器、SIMT驻留、面积、Chiplet、供应约束与固定售价毛利。
- .sil携带自定义核心与模板的名称/完整参数，导入优先文件快照；缺失定义或摘要损坏明确报错。
- x86正式进入SoC设计与LAB：三个包含完整硬件的教学模板、工作站项目。名称优先显示x86/Intel-AMD、RISC-V、Arm64，技术简称附解释；当前x86为32位IA-32整数子集，不是商业CPU或x86-64实现。
- CPU性能套件分别测试独立吞吐、相关链、缓存重用和乘法，显示真实指令数/模型周期/IPC、硬件配置与基线变化。默认短访存程序对加宽可能不敏感，不人为改分。
- 修复架构页添加核心菜单透明背景，以及Windows UTF-8、存档路径与固定RTL文件换行校验。
- 三个平台分别运行全量测试、平台启动脚本和图文手册检查，只发布源码。版本与模型元数据分别记载，读取不因版本数字不同而拒绝。

下载源码ZIP后先完整解压，安装Python3.12，再运行平台脚本。Release附件额外包含生成好的docs/player-guide/index.html离线图文手册；安装/设计/导出/分享见手册。SHA256SUMS.txt可核对附件完整性。

本作是教学游戏。CPU只有明确整数子集；GPU/NPU/ISP不是完整商业IP；PPA、签核与市场为估算。没有玩家RTL生成、PDK签核或实际流片能力，模拟硅片图不是实物显微图。

[玩家手册](https://github.com/qi-1021/silicon-immortal/blob/main/docs/guide/README.md) · [问题反馈](https://github.com/qi-1021/silicon-immortal/issues)
