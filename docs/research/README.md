# 证据核验记录

当前资料库49条，状态为`fulltext_checked`（正文与使用范围已核验）、`bibliography_checked`（仅书目/摘要已核验）或`unverified_locator`（仅定位待核验）。原有23条资料的初始审计单独保留；没有把某篇论文存在、某个URL返回200当成数值模型得到验证。

- [正式资料与原文范围](../REFERENCES.md)
- [99条遗留引用逐项处置](LEGACY_AUDIT.md)
- [机器可读审计](audit.json)
- `legacy_sources.json`保留本轮审查之前的题名、链接与状态，供比较。
- `silicon_professor/data/evidence.json`是运行时的正式注册表，含版本、原文定位、支持/不支持结论和获取文件的SHA-256。

本次读取了RISC-V规范固定版本、CACTI作者稿、gem5作者稿、热感知布局原文、Roofline技术报告、SPEC/Geekbench方法文档以及Apple/SiFive官方案例。Murphy、Amdahl、Dark Silicon、Borkar与Roofline出版版只核验书目/摘要，没有假装取得其全文。Murphy型良率式保留为模型假设，未称已逐字复现原论文。

原始下载和全文提取副本保留在本机`.research-cache/`中，已加入忽略规则，不随游戏或公开资料文档分发。正规阅读入口为正式来源的URL；哈希可用于核对本次获取版本，不证明链接将永久可访问。页面壳、访问检查和错误PDF也保留在此本地目录，用于解释审查为何拒绝它们。

视频记录仅确认接口返回的题名、作者、发布日期和时长；没有逐段观看或核对测试条件，因此退出正式性能/故障证据链。它们不是被判为虚构。所有数值参数的出处不再借用“同厂商”或“同主题”的文献标签。

重新生成审计与手册：

```bash
.venv/bin/python tools/build_source_audit.py
.venv/bin/python tools/export_sources.py
.venv/bin/python tools/export_lab_manual.py
```

审计工具只组织已取得的记录，不会自动认证或联网修改文献结论。新增正式来源需要人工读取身份与正文、填写定位和使用范围，再通过证据完整性测试。
