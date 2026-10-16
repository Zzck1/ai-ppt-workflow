# AI 辅助做 PPT

一个面向大学生课程汇报、读书报告和其他演示任务的中文 Skill 工作流，用于把主题、资料或已有演示稿转成适合目标受众的 PPT。支持 Codex 技能调用，也提供可复制到 Trae、WorkBuddy 等通用助手的纯提示词入口。

它可以从任务的任意阶段开始：

- 从零梳理需求、资料、大纲和逐页内容
- 根据已有大纲继续制作
- 修改已有 PPT 的指定页面
- 生成原创配图提示词和视觉素材
- 检查事实、数字、可编辑性和交付文件

如果使用的平台不支持 Codex Skill，可以直接复制 [`PROMPT.md`](PROMPT.md)。它把完整工作流整理成一条自包含的主提示词，不依赖技能目录或其他引用文件。

这是一套制作方法与检查辅助，不是独立的 PPT 生成软件。助手需要实际的文件生成/编辑能力才可交付 PPTX；只有聊天能力时可完成大纲和逐页稿。本项目不要求购买某个平台，也不自带图像生成、渲染器或云账户。

工作流会区分确认事实、计划目标、教学设定和待确认项。参考教程中的方法可以迁移，但原教程图片不会作为默认素材；“校园旧物交换周”也不会成为新任务的默认案例。

## 安装

将整个仓库目录复制到个人 Codex 技能目录：

```text
~/.codex/skills/ai-ppt-workflow/
```

Windows 的常见位置为：

```text
C:\Users\你的用户名\.codex\skills\ai-ppt-workflow\
```

安装后重启或刷新 Codex。在对话中可以这样调用：

```text
使用 $ai-ppt-workflow，根据我上传的资料制作一份给管理层看的 12 页汇报。
先核对资料和数字，再给我大纲；这一步不要生成图片或 PPT 文件。
```

## 文件

- `SKILL.md`：工作流入口、任务路由与交付规则
- `PROMPT.md`：可以直接复制到通用 AI 对话中的纯提示词版
- `agents/openai.yaml`：Codex 中显示的名称和默认调用提示
- `references/content-and-evidence.md`：资料、数字、逐页内容与提示词规则
- `references/visual-prompts.md`：原创配图、改图、透明素材、动态封面和 3D 的规则
- `references/production-and-handoff.md`：制作、验证与交付检查
- `references/provenance.md`：教程方法来源与原创案例边界
- `references/design-contract.md`：规划、制作、渲染与交付的轻量交接记录
- `references/validation.md`：能力检测、本地制作路线与检查命令
- `scripts/check_workflow.py`：零第三方依赖的规划/PPTX 结构检查
- `examples/course-report.plan.json`：3 页课程规划，含教学模拟数据
- `CHANGELOG.md`：升级记录

## Trae、WorkBuddy 与其他助手

把 `PROMPT.md` 全文复制到对话，再追加自己的资料、受众、总页数和本轮结束位置。若助手可以读本地文件，也可把本仓库放在独立目录，让它先读取 `SKILL.md`，按需读取 references；本项目不假设这些产品有同名 Skill 安装路径或固定工具接口。

完整制作时先检测能力。有演示文稿工具就使用其受支持后端；有本地 Python 时可选择已安装的 `python-pptx` 等库，渲染另用实际可用的 PowerPoint/WPS/LibreOffice。没有制作能力时交付文案并说明缺口。具体命令和限制见 [工具选择与可执行检查](references/validation.md)。

## 两分钟检查样例

在仓库根目录运行（Python 3.10+；Windows 无 `python` 时可试 `py`）：

```console
python scripts/check_workflow.py doctor
python scripts/check_workflow.py plan examples/course-report.plan.json
python -m unittest discover -s tests -v
```

规划检查预期 `errors: []`、退出码 0；故意改错图表数值应返回非零。样例只验证规划交接，不包含已渲染的 PPT。生成实际 PPTX 后可运行：

```console
python scripts/check_workflow.py pptx "你的文件.pptx" --expected-slides 3
```

脚本不联网、不修改输入，也不替代真实渲染和逐页视觉检查。制作请求及验收步骤见 [复现说明](references/validation.md)。

## 调用示例

```text
使用 $ai-ppt-workflow，把这份研究报告整理成 10 页课程汇报。
受众是不了解该领域的本科生，最后要讲清研究问题、方法、主要发现和局限。
保留原始数据及出处，最终交付可编辑 PPTX。
```

页数、主题、配色和版式按每次任务确定，不使用固定案例模板。

## 来源与许可

升级参考了 [PPT Master](https://github.com/hugohe3/ppt-master) 的工作流方法，自主改写为本项目适用的轻量规则和检查器，未引入其代码或素材。原教程来源、固定上游提交及许可边界见 [来源说明](references/provenance.md)。本仓库尚未声明整体开源许可证；上游的 MIT 不自动适用于本仓库或所有第三方素材。
