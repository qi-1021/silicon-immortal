# 第三方代码与运行库

本作代码与自编文档采用MIT，见LICENSE。引用的论文、厂商商标和资料链接不因引用而改变许可；仓库不分发缓存的厂商PDF。模拟图不是芯片实物照片。

| 组件 | 用途 | 许可与来源 |
| --- | --- | --- |
| PySide6 / Shiboken6 / Qt 6.12 | 桌面界面 | LGPLv3/GPLv3或商业许可选项。本发行采用开源许可；[PySide](https://code.qt.io/cgit/pyside/pyside-setup.git/)、[Qt源码](https://download.qt.io/archive/qt/6.12/)、[Qt许可](https://doc.qt.io/qt-6/licensing.html) |
| PicoRV32固定源码 | 独立RTL学习/冒烟 | ISC；[项目](https://github.com/YosysHQ/picorv32)，原始COPYING与固定提交见third_party/picorv32 |
| riscv-opcodes固定测试掩码 | 指令编码回归 | BSD-3-Clause；tests/fixtures/RISCV_OPCODES_LICENSE，测试夹具记载固定来源 |
| PyInstaller | 发行构建工具 | GPLv2或更新，带允许应用分发的例外；[许可](https://pyinstaller.org/en/stable/license.html) |
| Python 3.12 | 发行运行时 | PSF；[源码与许可](https://www.python.org/downloads/source/) |
| Python-Markdown | 离线手册构建 | BSD；[项目](https://github.com/Python-Markdown/markdown)；仅用于生成静态手册 |

便携包保留动态Qt库及其许可文件，不把Qt静态链接到游戏。Windows发行的`_internal`与macOS应用Contents目录含动态运行库；用户可修改、调试本作或替换兼容库，替换时应保持相同架构与ABI。修改后的代码可用公开构建脚本重新打包，代码签名可能需重新生成；请勿把自行修改的包冒称官方发行。

构建脚本收集Python和构建工具许可至包内`licenses/`，并包含Qt/PySide/Shiboken采用的LGPLv3/GPLv3原文、本说明、MIT与PicoRV32原文。PySide6发布wheel未提供License-File元数据，因此LGPLv3/GPLv3从Qt6.12.0官方源码LICENSES目录保留，见third_party/qt。源码链接和版本随发行说明记录，没有分发任何第三方闭源CPU/GPU RTL或商业PDK。
