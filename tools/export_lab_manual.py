"""将课程的输入、判定、参考解与正式来源导出为可复查手册。"""
from pathlib import Path
import sys
import json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from silicon_professor.data.lab_courses import COURSES
from silicon_professor.data.sources import SOURCES
from silicon_professor.engine.isa import instruction_catalog
from silicon_professor.data.architectures import ARCHITECTURES,MODES
from silicon_professor.version import GAME_VERSION,MODEL_VERSION

lines=['# 实验室手册\n\n',
    f'当前游戏版本 `{GAME_VERSION}`，模型 `{MODEL_VERSION}`。九个可运行工作台：核心与指令、GPU、NPU、ISP、缓存、互连、时序、功耗/热和数字逻辑。{len(COURSES)}节进阶实验课与14节产品设计课程互补。下面给出输入、观察目标、参考解、原文定位和实现边界。\n\n',
    '## 先设计核心，再用实验验证\n\n',
    'LAB默认打开核心设计台，可独立新建、命名、复制CPU/GPU/NPU/ISP。选择结构模块编辑硬件，在验证页运行固定向量，再发布.cor或加入研究沙盒SoC。测试程序/矩阵/校准值不参与硬件身份。具体步骤与可复现设计比较见[设计台指南](CORE_STUDIO.md)。\n\n',
    '本手册的课程位于设计台“实验与教学”。课程配置是学习样例；核心设计不要求先完成课程。新的.sil同时携带自定义核心和模板名称/全参数，设计台IP页可直接编辑SoC内嵌核心。\n\n',
    '## 从第一节实验开始\n\n',
    '1. 在LAB点击“实验与教学”选择课程，读清要观察的寄存器、周期或图像输出。\n',
    '2. 运行初始输入，记录结果；初始配置可能故意没有完成任务。\n',
    '3. 每次只改变一个因素，再运行，对照输出与轨迹。先说明原因，再查看参考解。\n',
    '4. 完成任务后给CPU/GPU/NPU/ISP命名，验证并保存至IP库；其他工作台导出实验记录。\n',
    '5. 在研究沙盒实例化已保存IP。跨ISA替换应用CPU集群时，明确选择替换原集群。\n\n',
    '学习模式只控制提示与参数展开程度，实验输入和底层计算相同。随时可以展开全部资源参数。\n\n',
    '| 模式 | 入口重点 |\n| --- | --- |\n',
    *(f"| {mode['name']} | {mode['description']} |\n" for mode in MODES.values()),
    '\n',
    '## 结果的含义\n\n',
    '- CPU有RV32、IA-32和AArch64整数子集；汇编经过解析再执行，不从二进制取指。各自的指令编码用于学习与核对。单执行上下文、小端、64KiB数据内存；未执行第三方完整合规测试。\n',
    '- IA-32显示原生算术标志；双操作数IMUL后的未定义标志保留为未知，不能用它推导条件分支。A64区分W写入清零高32位、X64位、零寄存器与NZCV；不支持的SP形式明确报错。MOV立即数只接受一次MOVZ/MOVN能表示的值。\n',
    '- 功能解释器产生动态轨迹；时序器按依赖与资源调度。结果值来自正确功能轨迹，不能把内部提交一致性检查当成独立硬件验证。\n',
    '- ALU为1周期、乘除延迟由输入指定，发射单元均按教学流水化模型处理；不是真实乘除器设计。访存串行，没有store buffer/MSHR、分支推测、异常恢复或有限物理寄存器。\n',
    '- 回放按已生成轨迹的提交时间更新架构寄存器，不是交互式执行环境，也不展现投机寄存器状态。\n',
    '- 默认时序的cold cache对每次运行重新初始化；HALT不计为标准指令。顺序落出程序末尾视为实验结束，显式跳转出代码区报错。\n',
    '- 三类CPU及GPU/NPU/ISP均能保存为实验IP，在研究沙盒实例化。模型分不能证明完整ISA兼容、驱动可用或商业授权；面积/功耗/Fmax仍来自未校准公式。\n',
    '- GPU执行逐lane FP32 AXPY与分支分歧，未实现完整GPU ISA、shader与图形流水线；NPU执行整数GEMM并检查有限累加器与scratchpad。\n',
    '- ISP实现RGGB raw12、黑电平、增益、基本双线性去马赛克和幂gamma/量化；黑帧和范围检查不能证明图像质量。它没有实现MHC算法、自动曝光/白平衡或完整sRGB传递函数。\n',
    '- 独立PicoRV32入口编译固定上游RTL并观察ADDI/ADDI/SW后的写入42，只是冒烟测试。解析核心与其RTL时序独立；玩家配置不会自动生成可制造的RTL。\n\n',
    '## 可运行架构与原文\n\n']
for key,arch in ARCHITECTURES.items():
    if arch['execution']!='implemented_subset':continue
    lines.extend([f"### {arch['name']}\n\n",arch['scope']+'\n\n'])
    for sid in arch['sources']:
        s=SOURCES[sid]
        lines.append(f"- [{s['title']}]({s['url']})；{s['verification']}。定位：{s['locator']}\n")
    lines.append('\n')
lines.extend([
    f"历史目录目前{len(ARCHITECTURES)}项家族/模式。其余仅为目录，不能保存为可执行架构IP，也不声称已经收录所有历史ISA。\n\n",
    '## 文件与IP复用\n\n',
    '`.cor`是CPU/GPU/NPU/ISP定义，`kind`区分类别；`.sil`是完整SoC，内嵌所用IP，换机器不依赖本地库。两者是UTF-8 JSON，旧扩展名也可读取。游戏、结构、模型版本作为诊断信息保留，读取依据实际字段。导入重新运行模型与固定功能向量，不信任文件中的评分或验证标志。详见[格式说明](FORMAT.md)与[可直接导入的示例](examples/README.md)。\n\n',
    '## 编码与扩展目录\n\n']
)
for family,ops in instruction_catalog().items():
    lines.append(f'### {family} — {len(ops)} 条\n\n'+', '.join(f'`{op}`' for op in ops)+'\n\n')
lines.append('未实现的A/F/D/C/V/Zicsr/Zifencei不能启用。规范中的完整B还包含其它子扩展；RV64的W类指令不属于此RV32实现。\n\n')
for course in COURSES:
    lines.extend([f"## {course['title']}\n\n",course['lecture']+'\n\n',
        '### 必须观察的结果\n\n'])
    for goal in course['goals']:lines.append('- '+goal['label']+'\n')
    lines.append('\n### 初始输入\n\n```json\n'+json.dumps(course['initial'],ensure_ascii=False,indent=2)+'\n```\n\n')
    lines.append('### 参考解\n\n'+course['explanation']+'\n\n```json\n'+json.dumps(course['solution'],ensure_ascii=False,indent=2)+'\n```\n\n')
    lines.append('### 原文与使用范围\n\n')
    for sid in course['sources']:
        s=SOURCES[sid]
        lines.extend([f"- [{s['title']}]({s['url']})；{s['verification']}。\n",
            f"- 定位：{s['locator']}\n",f"- 支持：{s['supports']}\n",
            f"- 不支持：{s['does_not_support']}\n",f"- 本作使用：{s['model_use']}\n\n"])
Path(ROOT/'docs/LAB_MANUAL.md').write_text(''.join(lines),'utf-8')
print(f'Exported {len(COURSES)} lab lessons with explicit reference solutions and source scopes.')
