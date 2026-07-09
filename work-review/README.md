# work-review · 精简日报 skill

一个 Claude Code / oh-my-claudecode skill：**一次扫全当天三源 → 直接产出对外汇报用的「精简版工作日报」→ 发布到飞书**。

取代过去「先写详细日报 + 详细 worklog，再手动合并删减成精简版」的三步流程。

## 它做什么

一次过采集三个数据源：

1. **本地对话日志** — 当天所有 Claude Code 窗口（`~/.claude/projects/*/*.jsonl`，mtime + 内容双过滤）
2. **飞书会话** — 当天有活动的群/会话（`lark-cli im`）
3. **今日会议** — 日历会议 + 妙记结论（`lark-cli calendar +agenda` / `lark-cli minutes`）

按大项目聚类，浓缩成 `✅ 主题 + 2-4 条要点 + 相关文档链接` 的精简稿（DocxXML），发布到飞书知识库「开发日报」节点，并可推送到指定群。

## 产物格式

```xml
<title>王佳玮工作日报_YYYYMMDD</title>
<hr/>
<h2>一、项目名</h2>
<p>✅ 子主题</p>
<ul><li>2-4 条精简要点</li></ul>
<h3>相关文档</h3>
<ul><li><a href="...">文档原始标题（drive +inspect 取，不编名）</a></li></ul>
<hr/>
...
<h2>N、其他：沟通与会议</h2>   <!-- 兜底节：映射不到项目的纯沟通 + 杂会 -->
```

发布后会自动给两位 mentor（陈曦、刘涛瑜）对报告内全部飞书链接（含妙记）开「可管理」权限，并把链接推到群（文案：「✨今日实习日报已更新 / 请各位mentor查收🫡 / 详见：日报链接」）。

## 文件

| 文件 | 作用 |
|------|------|
| `SKILL.md` | 主入口 + 触发词 + 端到端流程 |
| `references/sources.md` | 三源采集逻辑与 lark-cli 命令 |
| `references/condense-format.md` | 精简版格式 + 业务语言翻译 + 口吻硬约束 |
| `references/publish.md` | 飞书发布机制 + Windows GBK 编码绕坑 + 重跑覆盖确认 |
| `references/schedule-setup.md` | Windows Task Scheduler 每天 18:00 本机定时 + 白名单权限 |
| `config.example.json` | 配置样例（真实 config 放在 `~/.claude/data/work-review/config.json`） |

## 触发词

`精简日报` / `写今天的精简日报` / `工作日报精简版` / `recap` / `work review` / `jjrb`

## 依赖

- [`lark-cli`](https://github.com/) 飞书命令行（须先 `auth login`）
- Windows + PowerShell 5.1（发布走 `Set-Location` + `--content "@./file.xml"` 绕过管道 GBK 乱码）

## 设计要点

- **纯项目进展**：不含个人/worklog 视角（绩效留痕交给休眠的 `personal-worklog`）。
- **全自动直发**：仅手动重跑且当天文档已存在时确认一次（防覆盖手改）；定时无人值守跑不确认。
- **每天 18:00 本机定时**：云端调度看不到本机日志和 lark-cli 登录态，必须本机 Task Scheduler。
