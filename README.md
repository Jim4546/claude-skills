# claude-skills

个人 [Claude Code](https://claude.com/claude-code) Skill 集合。把成熟、可复用的工作流封装成 Skill，跨项目复用、版本化维护。

## 收录的 Skill

| Skill | 作用 | 触发 |
|---|---|---|
| [devflow](./devflow) | 文档驱动开发工作流：`idea→plan→RU→verify→simplify→commit` 六步法，强制「需求(PRD)↔文档(SPEC/原型)↔代码」三方永远对齐。任何项目通用，支持小任务轻量模式 | `/devflow <阶段> <任务>` |
| [daily-report](./daily-report) | 自动日报：扫多个 Claude Code 窗口在不同项目下的工作，按项目分组汇总，发布到飞书知识库「开发日报」 | 「写日报」「发布日报」 |
| [personal-worklog](./personal-worklog) | 个人工作小结（全天版）：提炼「你本人」做了什么（拆需求、拍板、纠正 AI、把控节奏），写入飞书 wiki | 「写今天的 worklog」 |
| [minutes-clip-resummary](./minutes-clip-resummary) | 裁剪长录音/飞书妙记指定片段并重新生成智能会议纪要 | 「裁剪录音重做纪要」 |

> daily-report / personal-worklog 内含个人飞书知识库节点配置，使用前按各自 SKILL.md 改成你自己的节点。

## 安装

把需要的 skill 目录放进 Claude Code 的全局 skills 目录即可：

```bash
# Windows (PowerShell / Git Bash)
git clone https://github.com/Jim4546/claude-skills.git
# 复制单个 skill（例：devflow）到全局 skills 目录
cp -r claude-skills/devflow ~/.claude/skills/devflow
```

之后在任意项目用 `/<skill 名>` 调起（如 `/devflow`）。

## 维护约定

- 一个 skill 一个目录，目录名 = `SKILL.md` frontmatter 的 `name`（kebab-case）。
- 改 skill 后在 `SKILL.md` 的 `version` 递增（若有）。
- 成熟改动走 commit / PR，保持可追溯。
