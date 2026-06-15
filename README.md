# claude-skills

个人 [Claude Code](https://claude.com/claude-code) Skill 集合。把成熟、可复用的工作流封装成 Skill，跨项目复用、版本化维护。

## 收录的 Skill

| Skill | 作用 | 触发 |
|---|---|---|
| [devflow](./devflow) | 文档驱动开发工作流：`idea→plan→RU→verify→simplify→commit` 六步法，强制「需求(PRD)↔文档(SPEC/原型)↔代码」三方永远对齐。任何项目通用，支持小任务轻量模式 | `/devflow <阶段> <任务>` |
| [daily-report](./daily-report) | 自动日报：扫多个 Claude Code 窗口在不同项目下的工作，按项目分组汇总，发布到飞书知识库「开发日报」 | 「写日报」「发布日报」 |
| [personal-worklog](./personal-worklog) | 个人工作小结（全天版）：提炼「你本人」做了什么（拆需求、拍板、纠正 AI、把控节奏），写入飞书 wiki | 「写今天的 worklog」 |
| [minutes-clip-resummary](./minutes-clip-resummary) | 裁剪长录音/飞书妙记指定片段并重新生成智能会议纪要 | 「裁剪录音重做纪要」 |
| [image-recolor-transparent](./image-recolor-transparent) | 图片配色改造+精细透明底：红→橙、灰黑→蓝灰(68,84,106)，连通域+迭代吸收抠白底（含封闭白区/文字镂空），羽化去白边，双底色预览验收 | 「按模板色系改色抠透明底」 |
| [article-origin-finder](./article-origin-finder) | 给定文章 URL（常被反爬/被墙、或属中文转载/编译稿），本机浏览器绕反爬抓正文、溯源到英文原文、多源交叉核实真伪，整理成飞书云文档（信息表+英文原文全文+中英核对表）；拿不到飞书时降级本地文件。需 `pip install playwright && playwright install chromium` | 「找原文」「英文原文」「溯源」 |

> daily-report / personal-worklog 内含个人飞书知识库节点配置，使用前按各自 SKILL.md 改成你自己的节点。

## 单一真相源 + 自动部署（重要）

**本仓库是 skill 的唯一真相源**；`~/.claude/skills/<name>` 是部署产物，**请勿手改**（改了会在下次部署时被覆盖）。

Windows 不允许无管理员创建 symlink，且 Claude Code 不识别 Junction，所以这里用「仓库 + git 钩子自动部署」消除两份漂移：

- `hooks/post-commit`、`hooks/post-merge` 会在 **commit / pull 后自动**把每个 skill 拷到 `~/.claude/skills/`（已通过 `core.hooksPath=hooks` 启用，钩子本身纳入版本管理）。
- 日常流程：**只在本仓库里改 skill → `git commit`** → 自动部署，skills 目录立即同步。
- 需要时手动部署：`bash deploy.sh`（Git Bash）或 `powershell -File deploy.ps1`。

### 首次在新机器上启用

```bash
git clone https://github.com/Jim4546/claude-skills.git
cd claude-skills
git config core.hooksPath hooks   # 启用自动部署钩子
bash deploy.sh                    # 先部署一次
```

之后在任意项目用 `/<skill 名>` 调起（如 `/devflow`）。

## 维护约定

- 一个 skill 一个目录，目录名 = `SKILL.md` frontmatter 的 `name`（kebab-case）。
- **只在本仓库编辑**，不要直接改 `~/.claude/skills/` 下的副本。
- 改 skill 后在 `SKILL.md` 的 `version` 递增（若有）。
- 成熟改动走 commit / PR，保持可追溯。
