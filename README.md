# ai-workflow-skills

AI 工作流 Skill 合集。这里集中维护一组成熟、可复用的 Claude Code / Codex 工作流能力，用来处理日常办公、研究尽调、内容归档、日报生成、文档转换和图片处理。

本仓库采用“一个 skill 一个根目录”的结构：每个目录里都有 `SKILL.md`，安装后会被 Claude Code 自动识别。仓库是唯一真相源，`~/.claude/skills/<name>` 只是部署产物。

## 收录的 Skill

| 分组 | Skill | 能做什么 | 常用说法 |
|---|---|---|---|
| 开发流程 | [devflow](./devflow) | 文档驱动开发工作流：`idea -> plan -> RU -> verify -> simplify -> commit`，让需求、文档和代码保持一致。 | `/devflow`、`/plan`、`/verify` |
| 日报与复盘 | [daily-report](./daily-report) | 汇总多个 Claude Code 窗口的当天工作，按项目发布到飞书开发日报。 | “写日报”“发布日报” |
| 日报与复盘 | [personal-worklog](./personal-worklog) | 写个人工作小结，强调“我本人”如何拆需求、拍板、纠正 AI、把控节奏。 | “写今天的 worklog”“总结我今天做了什么” |
| 日报与复盘 | [work-review](./work-review) | 一次扫本地对话、飞书会话和今日会议，产出对外汇报用的精简日报并发布到飞书。 | “精简日报”“工作日报精简版”“jjrb” |
| 研究尽调 | [entity-dossier](./entity-dossier) | 做企业、人物、投资方信息整理稿，生成带来源、时间线、股权和图示的飞书文档。 | `$entity-dossier`、“企业背调”“人物背调” |
| 研究尽调 | [ipo-peer-intelligence](./ipo-peer-intelligence) | 对拟上市公司、同行、竞对、供应商或投资标的做证据优先的 IPO / 产业尽调分析。 | “IPO 尽调”“同行对标”“竞对分析” |
| 内容归档 | [article-origin-finder](./article-origin-finder) | 给定文章 URL，抓正文、找英文原文、多源核实，并整理成飞书或本地文档。 | “找原文”“英文原文”“溯源” |
| 内容归档 | [feishu-doc-mirror](./feishu-doc-mirror) | 把飞书分享文档或社区文章镜像到自己的飞书空间，复制正文、结构和图片。 | “镜像这篇飞书文章”“克隆到我的空间” |
| 内容归档 | [wechat2lark](./wechat2lark) | 把微信公众号文章转成飞书云文档，并归档到团队知识库。 | “公众号转飞书”“转存公众号” |
| 文档转换 | [spa-to-pdf](./spa-to-pdf) | 抓取 JS 渲染的 SPA 页面，生成带目录和链接的 Word / PDF。 | “把这个网页导出成 Word 和 PDF” |
| 会议处理 | [minutes-clip-resummary](./minutes-clip-resummary) | 裁剪长录音或飞书妙记片段，并重新生成智能会议纪要。 | “裁剪录音重做纪要”“妙记截取片段” |
| 图片处理 | [image-recolor-transparent](./image-recolor-transparent) | 按 PPT 模板色系给图片重映射配色，并精细抠成透明底。 | “按模板色系改色抠透明底” |

## 安装

首次安装：

```bash
git clone https://github.com/Jim4546/ai-workflow-skills.git
cd ai-workflow-skills
git config core.hooksPath hooks
bash deploy.sh
```

Windows PowerShell 用户也可以运行：

```powershell
git clone https://github.com/Jim4546/ai-workflow-skills.git
cd ai-workflow-skills
git config core.hooksPath hooks
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

部署后，每个含 `SKILL.md` 的根目录都会被复制到 `~/.claude/skills/<skill-name>`。Claude Code 重启或刷新后即可按自然语言触发。

更多面向同事的步骤见 [安装指南_图文.md](./安装指南_图文.md)，常用话术见 [使用手册_话术.md](./使用手册_话术.md)。

## 更新

本仓库启用了 git hooks：

- `hooks/post-commit`：提交后自动部署到本机 `~/.claude/skills/`。
- `hooks/post-merge`：`git pull` 或 merge 后自动部署。

日常更新：

```bash
git pull
bash deploy.sh
```

如果使用 PowerShell：

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

## 目录结构

```text
ai-workflow-skills/
├── <skill-name>/
│   ├── SKILL.md
│   ├── README.md              # 可选，面向使用者的中文说明
│   ├── references/            # 可选，模板、坑位说明、输出规范
│   ├── scripts/               # 可选，skill 需要调用的脚本
│   └── requirements.txt       # 可选，Python 依赖
├── deploy.ps1                 # Windows 部署脚本
├── deploy.sh                  # Git Bash / macOS / Linux 部署脚本
├── hooks/                     # commit / merge 后自动部署
├── 使用手册_话术.md
├── 安装指南_图文.md
└── README.md
```

## 维护约定

- 一个 skill 一个根目录，目录名必须等于 `SKILL.md` frontmatter 里的 `name`。
- 新增 skill 时至少提供 `SKILL.md`，建议同时写中文 `README.md`。
- 复杂工作流的坑位、模板和验收标准放在 `references/`。
- 脚本放在 `scripts/`，路径按 skill 目录内相对路径处理。
- 只在本仓库编辑 skill，不要直接改 `~/.claude/skills/` 下的部署副本。
- 改完后提交到仓库，hooks 会自动同步到本机 skills 目录。

## 依赖提示

不同 skill 的依赖不一样：

- 飞书相关 skill 通常需要 `lark-cli auth login`。
- 抓网页、镜像图片、公众号归档等能力可能需要 Python 3.10+。
- `spa-to-pdf` 的 PDF 和目录刷新依赖 Windows + Microsoft Word。
- `feishu-doc-mirror` 和 `article-origin-finder` 的浏览器抓取需要 Playwright。

具体依赖以各目录的 `README.md`、`SKILL.md` 和 `requirements.txt` 为准。
