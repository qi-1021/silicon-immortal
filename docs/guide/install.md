# 安装与脚本启动

当前版本仅发布源码与启动脚本。没有exe/app，也不需要购买代码签名或处理未公证app。安装Python3.12后，使用Windows的run.bat或Mac的run.command启动；首次运行会在项目内安装固定依赖。

## 系统要求

| 系统 | 运行方式 | 要求 |
| --- | --- | --- |
| Windows | 双击run.bat | Windows10/11，64位Intel/AMD，Python3.12 |
| Mac Apple Silicon或Intel | 双击run.command或终端./run.command | macOS14+，对应架构的Python3.12 |

PySide6 6.12的官方Mac wheel要求macOS14。Windows ARM未作为当前发布支持平台。最小窗口1180×760，显示缩放较大时需要足够屏幕空间；参数/结构/报告可以分别滚动。

## 1. 安装Python

从[Python官方](https://www.python.org/downloads/)安装Python3.12。Windows安装时勾选Python Launcher与Add Python to PATH；Mac安装官方对应处理器版本，或通过你熟悉的包管理器安装Python3.12。

Windows命令行`py -3.12 --version`，Mac终端`python3.12 --version`应显示3.12。脚本也能尝试PATH中的python/python3，但版本不能低于3.12。

## 2. 下载完整源码

从[GitHub Releases](https://github.com/qi-1021/silicon-immortal/releases)下载SiliconImmortal-source.zip，完整解压到可写目录，例如D:/Games/SiliconImmortal或~/Games/SiliconImmortal。不要在ZIP预览里启动，不要只复制脚本。

Release源码包额外包含生成好的离线HTML手册。GitHub“Code→Download ZIP”与git clone包含同样源码和Markdown手册，HTML可自行生成。

## 3. 启动

**Windows：** 双击run.bat。脚本优先使用项目虚拟环境，其次Python Launcher，再尝试PATH中的python。失败时窗口保留错误。

**Mac：** 双击run.command。如解压未保留执行权限，在终端进入项目目录后运行：

```bash
chmod +x run.command
./run.command
```

也可不修改权限，直接`bash run.command`。不要运行关闭系统安全保护的命令。

首次启动会创建.venv，安装requirements.txt里的PySide6==6.12.0，需要网络并可能等待一段时间。以后启动会复用环境，游戏可离线运行。安装失败会退出并显示错误，不伪装成游戏已启动。

## 4. 第一次进入

![启动页](../screens/start.png)

首页“设计自己的核心·LAB”直接设计CPU/GPU/NPU/ISP；“教学关卡”按目标学习；编号01—12是独立挑战委托，x86工作站可使用三种可编辑教学核。顶部初级/中级/高级/专业控制提示，不改变硬件。

## 手动启动

```text
Windows:
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m silicon_professor

macOS:
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m silicon_professor
```

运行正常后，浏览器打开docs/player-guide/index.html阅读离线手册。直接克隆的源码可安装requirements-docs.txt后运行`python tools/build_manual.py`生成HTML；普通游戏启动不需要文档依赖。

继续：[第一颗核心](first-core.md) · [更新与备份](sharing.md) · [排障](faq.md)
