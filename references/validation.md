# 可执行检查与工具选择

这是可选的本地检查辅助，不改变原有自然语言调用；纯对话任务可直接按相同原则人工核对。检查器只依赖 Python 3.10+ 标准库，运行时不联网、不安装软件、不修改输入。先定位仓库根目录；下列命令在该目录运行，换目录时使用完整路径并加引号。Windows 无 `python` 命令时试用 `py`，macOS/Linux 通常为 `python3`。

## 能力检测和制作路线

```console
python scripts/check_workflow.py doctor
```

还要检查助手实际暴露的文件工具、终端和演示文稿工具。doctor 只报告 Python、可导入的 `python-pptx`、PATH 上的 Node/LibreOffice；不会检测付费账户、PowerPoint 安装或工具调用权限。没在 PATH 上找到不代表软件未安装，可由用户已知安装路径调用。

| 本次实际能力 | 选择 |
| --- | --- |
| 有演示文稿技能/编辑工具 | 使用其支持的后端与当前文档，保留已有模板和编辑对象 |
| 无技能，有 Python 与本地文件执行 | 可用公开的 [python-pptx](https://python-pptx.readthedocs.io/en/latest/user/quickstart.html) 创建原生文字、表格和常规图表；先做最小新稿再扩展。它不负责渲染，也不保证复杂原稿的所有特性无损往返 |
| 有 Node 与已配置的 PPT 库 | 按该库当前官方文档制作；不从本项目推断依赖已经安装 |
| 只有对话/文本输出 | 交付大纲、逐页文案、设计规范与数据；明确未制作 PPTX，提供可复制到本地助手的后续指令 |

Python 后端需要 `python-pptx` 时，可在独立虚拟环境安装 `python -m pip install python-pptx`，先遵守当前环境安装约束，不修改全局 Python 或索取云平台凭据。此库是可选制作后端，本仓库没有绑定它，也未内置从任意主题自动生成 PPT 的引擎。Trae/WorkBuddy 能执行哪些命令以当前版本和权限为准。

## 规划 smoke test

```console
python scripts/check_workflow.py plan examples/course-report.plan.json
```

预期退出 0、`errors: []`。该样例是 3 页课程规划，包含明确标注的自造教学数据和单系列图表；它不是已生成的 PPT。把第二页图表的 12 改成 13 再运行，应退出 1 并报告数值与 F01 不一致；恢复样例再运行。检查页数、ID 唯一性、事实引用、数值/单位映射、基础设计字段；不核验事实真假、结论、未声明的数字、颜色对比或统计口径。表格/多系列等复杂任务可保留 Markdown 工作稿，不必强行迁就此小型 schema。

给本地制作助手的复现请求：

```text
使用 ai-ppt-workflow，以 examples/course-report.plan.json 为规划制作总共3页PPTX。
先检查实际工具；无内置演示工具时，若本地已具备 Python 与 python-pptx，
用该库制作原生文字与第二页原生柱形图，并保留内嵌数据。
每页明显标注教学模拟，不生成照片，不加入真实实验结论。
先运行规划检查，再制作并渲染最终PPTX，逐页核对中文和图表。
若没有渲染器，明确报告视觉未验收，不把规划检查称为成品验收。
```

## PPTX 包检查

```console
python scripts/check_workflow.py pptx "工作区/课程汇报.pptx" --expected-slides 3
```

输出最终文件 SHA256、发布顺序中的页数、每页文本 run/图片/graphic frame 数量，并检查 ZIP CRC、XML 可解析和内部关系目标。非零退出必须处理；零退出只代表这些结构条件通过，不证明所有 OOXML 合法或 PowerPoint 一定打开。graphic frame 也可能是表格等对象，不能据此认定有可编辑图表；文本 run 数量也不能证明所有可见文字可编辑。无关的遗留 slide XML 不计为发布页。

渲染可使用目标应用导出，或已安装的 LibreOffice：

```console
soffice --headless --convert-to pdf --outdir "工作区/预览" "工作区/课程汇报.pptx"
```

先创建独立预览目录，检查命令退出状态、PDF 是否新生成、页数是否一致，再逐页查看；不要误用同名旧 PDF。需要图片时用已有 PDF 渲染工具转换。LibreOffice 渲染可能与 PowerPoint/WPS 存在差异，目标应用兼容性仍单独说明。

按 [制作与验收](production-and-handoff.md) 记录 SHA256 与真实预览。修改后的文件会有新 SHA256；旧结构报告、旧 PDF 或旧截图不能沿用为新文件的验收依据。

## 维护检查

```console
python -m unittest discover -s tests -v
```

测试涵盖有效规划、坏输入、引用/数值漂移、PPTX 发布页顺序和缺失关系目标，以及本仓库相对文档链接。测试中的临时 ZIP 是检查器夹具，不是可交付的演示稿。仓库 CI 只运行这些检查，不声称自动通过视觉验收。
