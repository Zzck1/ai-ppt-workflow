# AI 辅助做 PPT

一个面向 Codex 的中文 Skill 工作流，用于把主题、资料或已有演示稿转成适合目标受众的 PPT。

它可以从任务的任意阶段开始：

- 从零梳理需求、资料、大纲和逐页内容
- 根据已有大纲继续制作
- 修改已有 PPT 的指定页面
- 生成原创配图提示词和视觉素材
- 检查事实、数字、可编辑性和交付文件

如果使用的平台不支持 Codex Skill，可以直接复制 [`PROMPT.md`](PROMPT.md)。它把完整工作流整理成一条自包含的主提示词，不依赖技能目录或其他引用文件。

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

## 调用示例

```text
使用 $ai-ppt-workflow，把这份研究报告整理成 10 页课程汇报。
受众是不了解该领域的本科生，最后要讲清研究问题、方法、主要发现和局限。
保留原始数据及出处，最终交付可编辑 PPTX。
```

页数、主题、配色和版式按每次任务确定，不使用固定案例模板。
