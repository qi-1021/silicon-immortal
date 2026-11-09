# .sil / .cor 格式与版本策略

`.sil`保存整个SoC，`.cor`保存可复用CPU/GPU/NPU/ISP实验IP。文件均为UTF-8 JSON，扩展名不改变内容格式。旧`.spchip.json`和`.spip.json`仍可读取；不凭扩展名判断可信内容。

## 三种版本信息

- `producer.version`：游戏版本，开发版本`0.1.0-alpha.6`，第一次正式发布前使用alpha。
- `version`：文件结构版本。SoC与IP当前均为1。与游戏版本分开。
- `producer.model`：模型标识，当前`analytic-v0.9+smt-rescue-observatory-v1`。

版本不作为互相读取的硬门槛。已知的format和实际可理解字段决定能否读取。不同或未知版本会显示兼容提示；未知SoC附加字段忽略并提示，旧IP附加配置保留但不计算。未知核心硬件字段、模板模型结构或ISA不能静默忽略；错误列出字段与来源版本。

## SoC示例

```json
{
  "format": "silicon-professor/design",
  "version": 1,
  "producer": {"name": "Silicon Immortal", "version": "0.1.0-alpha.6", "release_channel": "alpha", "model": "analytic-v0.9+smt-rescue-observatory-v1"},
  "created_at": "2026-11-08T00:00:00+00:00",
  "name": "isqi / 01",
  "scenario": "sandbox",
  "design": {"scenario_id": "sandbox", "name": "isqi / 01", "node_id": "n3e", "cores": [], "embedded_ips": {}, "ip_blocks": {}},
  "summary": {},
  "provenance": {"simulation": true, "visuals": "procedural-floorplan-illustration", "signoff_ready": false}
}
```

上面是旧式最小草稿，未声明完整核心包；省略字段使用默认值，模板由本机目录解释并提示。`cores: []`表示尚未放CPU，仍可导入编辑。实际新导出包含完整Design、placements、embedded_ips、core_templates、core_bundle与摘要。导入不信任summary，会重新构建模型。

## 完整核心包

新`.sil`带`core_bundle: {"schema": "embedded-cores-v1"}`。核心定义分两类，都在同一个文件内：

| 字段 | 保存内容 | 引用方式 |
| --- | --- | --- |
| `design.embedded_ips` | 自定义`.cor`完整资产，名称、类别、硬件或旧配置、身份与验证记录 | CPU的`core_id: ip:<id>`；GPU/NPU/ISP的`ip_blocks` |
| `design.core_templates` | 以`cpu:<id>`、`gpu:<id>`、`npu:<id>`、`isp:isp`为键的模板快照 | CPU组的`core_id`、`gpu_id`、`npu_id`、ISP选项 |
| `design.custom` | 旧自研核的名称、ISA、解码/ROB/缓存/流水线/后端/扩展参数 | `core_id: custom` |

每份模板记录包含`kind/catalog_id/name/model_schema/model/reference_node/digest/producer`。`model_schema`为`catalog-ppa-v1`；`model`保存目录条目的全部游戏参数与说明，CPU/GPU另存完整参考制程对象。摘要包含类别、目录ID、名称、模型结构、模型和参考制程；版本信息不参与身份。SHA-256不能认证厂商规格真实性。

导入优先采用文件模板，目录同ID更新或缺失均不替换它。再次导出保持已有快照、补齐新选择的模板；不会修改本机全局目录。所有CPU组（含零实例组）和保留的GPU/NPU/ISP选择都有定义，自定义加速器绑定后也保留其模板选择，便于解除绑定继续编辑。相同核心多个实例只存一份定义；数量、目标频率、L2和物理实现参数存于实例。

声明完整包时，缺少引用模板、内嵌自定义资产、类别错误、未知硬件语义或摘要不符都报错，不能退回目录。旧文件没有声明时继续兼容读取并提示目录依赖。设计台IP页可直接编辑/导出当前SoC内嵌核心，无需另一份`.cor`。

这保证核心定义可携带，不承诺不同引擎版本计算相同PPA。非核心的目标工艺、封装、内存、市场等仍由本版模型解释；不含真实PDK、网表或可制造芯片数据。

## IP结构

`.cor`的`format`为`silicon-professor/ip`，含`version`、`producer`、`kind`、`name`、`id`、`digest`、`config`、`verification`与`parameter_basis`。`kind`为`cpu/gpu/npu/isp`，因此同扩展名可明确区分不同IP。

`id`是内容摘要前32个十六进制字符；`digest`为SHA-256。旧资产摘要为`kind/name/config`；设计台资产显式`identity_basis: kind/name/design`，摘要为`kind/name/design`。JSON按键排序、无多余空格，不包括版本与验证结果。改游戏版本或加顶层说明不会破坏身份，修改名称/硬件会产生新ID。

设计台的`design`含`schema: parameterized-core-v1`与`hardware`。`config`是由硬件生成的固定测试映射，导入重新构建，不信任附带config。测试台程序、矩阵大小和校准值不属于硬件身份；工作草稿存档另行保存测试台。无法理解的硬件字段明确拒绝，防止导入变成另一种核心。

导入重新校验并运行固定验证任务，不信任外部passed、IPC或周期。CPU设计台验证含访存、相关链、独立运算、分支与已启用扩展；旧实验资产维持历史固定测试。旧资产未知附加配置参与原摘要并保留但不计算；新硬件以design为准。旧字段缺失按默认读取，不因producer/version不同而拒绝。

CPU新增硬件字段`smt_threads`（1/2）、`mshrs`（1..16）、`branch_predictor`（none/two_bit）。`source2`属于独立测试台，不属于硬件身份。启用两上下文时固定验证检查两份架构状态；它不证明OS或线程间一致性。

## 拯救芯片与更新包

实验JSON的`format`为`silicon-rescue`，当前模型为`rescue-chip-evidence-v2`，含案例ID、参数、边界/条件、资料快照和结果。旧`rescue-teaching-v1`可按当前代码重算，但不继承统一热模型的通关/数值，返回迁移提示。移动芯片未完成反事实校准时仍返回不通过。外部结果不能授予通关；未来未知实验模型报错。这不是SoC或CPU ISA格式兼容门槛。

源码更新ZIP根目录为`SiliconImmortal/`，含`update-manifest.json`。清单格式`silicon-source-update`、schema1，包含版本、Python最低版本和逐文件SHA-256；包外`SHA256SUMS.txt`校验整个ZIP。自动安装拒绝未知格式、路径越界、链接/重复条目、摘要不符和版本不符。更新清单不认证发布者身份，第三方代理必须可信。旧附件无清单时保持当前安装不变。

SoC的CPU组通过`core_id: ip:<id>`引用`embedded_ips`中的定义，可多次实例化；GPU/NPU/ISP通过`ip_blocks`绑定同一嵌入库。导出SoC包含它实际使用的IP，不依赖另一台机器的本地命名库。当前只有研究沙盒允许实例化实验IP，避免把研究样机当商业授权。

## 导入输入约束

`design.pdn_resistance_mohm`保存芯片/封装等效电阻，范围0..1000mΩ；0沿用历史pdn_quality映射。自由沙盒的签核是建议，`provenance.signoff_mode: advisory`且`signoff_ready: false`，不把可生成预览当物理/产品签核通过。核心分类的模板仍包含完整hardware与名称，x86_64是独立64位ISA标识，不改写旧x86_32资产。

`.sil`最多12MB，`.cor`最多2MB。先检查已知设计字段，再实例化或运行模型。数值应为JSON数字，计数为整数，开关为JSON布尔值；`"false"`不是`false`。不截断小数核数、不把未知制程或IP换成默认值，不接受NaN/Infinity。

| 字段/集合 | 当前读取范围 | 原因 |
| --- | --- | --- |
| CPU组 / 总核数 / 内嵌IP / 模板快照 / 布局项 | 64 / 256 / 64 / 128 / 1024 | 控制布局与重放资源消耗 |
| 通道数 | 0..8，0沿用代际默认 | 当前控制器教学模型的可表达范围 |
| L2/L3/SLC容量 | 0..1024 MB | 有限非负输入；不是实际SRAM可实现性保证 |
| 频率 / 环境温度 | 0..100 GHz / −50..100°C | 软件输入约束；频率0为自动，PPA未在整个区间校准 |
| 验证、PDN、调优、并行比例等 | 0..1 | 归一化投入/比例的定义域 |
| 布局坐标 / 尺寸 / 旋转 | ±10000mm / 0..10000mm / 0、90、180、270 | 有限几何输入；可保留尚未修好的越界或重叠草稿 |

完整条件定义在`engine/design_input.py`；这些范围是本版本模型/软件约束，不是真实架构或制造上限。未放CPU、布局重叠或尚未签核的合法草稿仍能导入继续修改。缺失已知字段沿用历史默认值；被引用的IP必须存在且类别匹配。

[可直接导入的十个IP与三个SoC](examples/README.md)含旧配置资产、新硬件资产、模板与混合核心包，已运行导出后重新导入检查。

## 模型字段边界

长度mm、面积mm²、频率GHz、功耗W、金额USD/百万USD。`summary.ai_score`是综合游戏分；旧`ai_tops`保留为同样的综合分，以`legacy_ai_tops_is_score`说明，不能当实测TOPS。NPU的稠密整数峰值另有明确精度和每MAC两次运算约定。

`summary.valid`表示结构/IP/机身检查，`provenance.signoff_ready`表示全部教学约束是否通过，两者都不代表实际STA/DRC/LVS通过。

## 错误定位

文件中保留游戏、结构、模型版本，结合`kind/architecture`、配置和内容摘要可以找到失配原因。来源版本缺失时提示旧文件未记录。错误不会通过默默换ISA或接受无效内容被掩盖。版本兼容并不等于能完整解释未来版本新增的硬件功能。
