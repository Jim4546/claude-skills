---
name: work-review
description: 精简日报（work review）：一次扫全当天所有 Claude Code 对话窗口 + 飞书会话 + 今日会议，按大项目聚类，直接产出「王佳玮工作日报_YYYYMMDD」DocxXML，发布到飞书知识库「开发日报」节点并推送到「每日日报组」群。当用户要写精简日报、工作日报精简版、总结今天干了什么并直接出对外汇报稿时使用。触发词：精简日报、写今天的精简日报、工作日报精简版、recap、work review、jjrb。
version: 1.0.0
---

# work-review · 精简日报

把当天的工作**一次过**汇成一篇对外汇报的「精简版日报」，直接发飞书。取代过去「先写详细日报 + 详细 worklog，再手动合并删减」的三步流程。

## 设计要点（与用户审计后定稿）

- **三个数据源**：本地 Claude Code 对话日志 + 飞书会话 + 今日会议（日历/妙记）。
- **纯项目进展**：照搬参考文档 `https://t2rvx54o5x.feishu.cn/docx/IcAjdUYu5og3bnxBhhDcUuElnlc` 的结构——按项目分组、`✅ 主题` + 2-4 条要点；**不含**个人视角（「否决 AI / 原话证据」那套留给休眠的 `personal-worklog`）。
- **全自动直发**：不设成稿复核关；不准的地方用户到飞书手改。唯一的例外确认见步骤 7「重跑覆盖」。
- **文档链接尽量保留**：每个项目末尾附 `<h3>相关文档</h3>` 小列表；该项目当天确实没有任何飞书链接时，此节省略。链接文字用文档**原始标题**（`drive +inspect` 取，不编名）。
- **自动开权限**：发布后给两位 mentor（陈曦、刘涛瑜）对报告内全部飞书链接（含妙记）开「可管理」权限（见步骤 8.5）。
- **标题命名**：统一 `王佳玮工作日报_YYYYMMDD`（如 `王佳玮工作日报_20260612`），单一来源 `$title`。
- **6 点定时**：Windows Task Scheduler 每天 18:00 跑 `claude -p "/work-review"`，当天**无条件权威版**（见 [references/schedule-setup.md](references/schedule-setup.md)）。

依赖 `lark-cli`（须先经 `lark-shared` 完成 `auth login`）。

## 参数

```
/work-review [--date YYYY-MM-DD] [--dry-run]
```

- `--date`：默认今天（北京时间 +08:00）。
- `--dry-run`：只把最终 DocxXML 打印/落到 `C:\temp\work-review_<date>.xml`，不调用任何写接口。供调试或定时草稿。

## 端到端流程

> 三源采集的确切命令见 [references/sources.md](references/sources.md)；输出格式/翻译/口吻见 [references/condense-format.md](references/condense-format.md)；发布机制见 [references/publish.md](references/publish.md)。

### 1. 采集本地对话（必做，全量）

一把扫全 `~/.claude/projects/*/*.jsonl`，**双重过滤**：
- 过滤 1（mtime）：文件最后修改时间在本地今天 00:00 之后。
- 过滤 2（内容）：至少含一条 `timestamp` 在今天的 `type=="user"` 且 `isSidechain!=true` 的消息。

只取项目目录下一层的 `.jsonl`，忽略 `<uuid>/` 子目录里的 subagent 记录。**绝不按当前 cwd 过滤**——必须扫全所有窗口（daily-report 曾踩坑：只扫当前项目、漏发其他窗口）。

每个 jsonl 当一个窗口，提取 `cwd`、全部 user 真文本消息、时间范围。逐窗并行 subagent 提炼「做了什么」（见 sources.md §本地）。

### 2. 采集飞书会话（Q7）

`lark-cli im +chat-list` 列出账号内会话 → 过滤出今天有真人消息、非纯机器人/通知类、且不在 `config.chat_exclude` 里的会话 → 并行子任务逐个 `+chat-messages-list` 拉今日消息 → 提炼工作相关结论（拍板、对齐、结论）。命令见 sources.md §飞书会话。

### 3. 采集今日会议（Q9）

`lark-cli calendar +agenda` 拉今天会议（名/时间/参会人）；对有妙记的会用 `lark-cli minutes +search` 取一句结论 + 妙记链接。命令见 sources.md §会议。

### 4. 跨源聚类成大项目

把三源内容按「项目名 / 飞书 token / 人名 / 路径关键词」等专有名词重叠归到大项目（并查集；本地窗口用 `cwd` 末两段 + 前 5 条消息里的专有名词做指纹）。
- 飞书群结论 → **并入对应项目**（Q8）。
- 会议 → **并入相关项目**（Q9）。
- 映射不到任何项目的纯沟通 / 杂会 → 末尾兜底节「其他：沟通与会议」。

> 全自动直发，**不做聚类预览确认**（Q3）。

> **0 活动早退**：若三源全空（本地 0 窗口 + 飞书 0 条工作相关 + 0 会议），不要发布空日报。手动跑 → 告知「今天没扫到工作活动，是否仍要发占位日报？」等确认；定时跑（`WORK_REVIEW_SCHEDULED=1`）→ 直接跳过发布、只在 cron.log 记一行，不建节点、不推群。

### 5. 逐项目浓缩 + 装链接

每个大项目压成若干 `✅ 子主题 + 2-4 条要点`，业务语言翻译、第三人称、禁 AI/「我」表述（规则见 condense-format.md）。每个项目末尾装 `<h3>相关文档</h3>`：扫该项目所有来源里的飞书 URL（正则 `https?://[^\s)]*feishu\.cn/(base|docx|wiki|sheets|file)/[A-Za-z0-9]+(\?[^\s)]*)?`），去重后按出现顺序保留前 5，调 `drive +inspect` 取原始 title 作 `<a>` 链接文字（不编名/不标类型后缀），失败则裸 URL。

### 6. 组装 DocxXML

按 condense-format.md 的格式：`<title>王佳玮工作日报_{yyyymmdd}</title>`（= `$title`） → 项目按工作量倒序、中文数字 h2、`<p>✅…</p>`+`<ul>` + `<h3>相关文档</h3>` → `<hr/>` 分隔 → 末尾兜底节「其他：沟通与会议」。

### 7. 发布（`--dry-run` 在此短路）

读 `C:\Users\jiawei.wang\.claude\data\work-review\config.json`。详细步骤（建节点 / 写正文 GBK 绕坑 / 重跑覆盖确认）见 [references/publish.md](references/publish.md)。要点：
- 标题 `$title` = config.title_format 套入 date（默认 `王佳玮工作日报_{yyyymmdd}` → `王佳玮工作日报_20260612`；`{yyyymmdd}` = date 去横线，兼容旧 `{date}`）。建节点/查重/推群/XML 都用同一个 `$title`。当天节点不存在 → `wiki +node-create --obj-type docx --title "$title"`；返回取顶层 `data.obj_token`/`data.node_token`，url 自己拼 `https://t2rvx54o5x.feishu.cn/wiki/<node_token>`。标题格式改了，旧命名的历史节点不会被新 `$title` 命中（预期，旧节点不动）。
- 已存在 + **手动跑** → 警告确认「重跑会盖掉飞书手改（版本历史可恢复），继续？」，确认后才覆盖（Q5）。
- 已存在 + **定时跑（无人值守）** → 无条件复用 obj_token 覆盖（Q6）。判定无人值守**唯一依据**：环境变量 `WORK_REVIEW_SCHEDULED=1`（见 schedule-setup.md）。不要用「传了 `--date`」之类推断，否则人工调试会被静默覆盖。
- 写正文一律 `Set-Location C:\temp` + `--content "@./file.xml"` 相对路径，绕过 PS 5.1 管道 GBK 乱码。

### 8. 写回发布记录

写 `C:\Users\jiawei.wang\.claude\data\work-review\<date>\_published.json`（date / doc_token / node_token / url / published_at / projects / source_counts）。

### 8.5 给 mentor 开「可管理」权限

把报告里全部飞书链接（相关文档 base/docx/wiki/sheets/file **+ 妙记 minutes**）去重，逐个给 `config.manage_grant_users`（陈曦、刘涛瑜）开 full_access：`drive +inspect` 取 token/type → `drive permission.members create ... perm=full_access`。open_id 为空时先 `contact +search-user` 解析回写 config。妙记类型若不被权限接口支持则记日志跳过；单条失败不中断。详见 publish.md §5.5。

### 9. 推送到「每日日报组」群

发布成功后自动把链接推到群（`config.group_chat_id`），文案「✨今日实习日报已更新 / 请各位mentor查收🫡 / 详见：[$title](url)」，`--idempotency-key "work-review-<date>"` 防当天重复刷屏。写法见 publish.md。

### 10. 输出

```
✅ 精简日报已发布：<url>
   已推送到「每日日报组」，并给陈曦、刘涛瑜开好各文档「可管理」权限。
   来源命中：本地 N 个窗口 / 飞书 M 个会话 / K 场会议
   项目：<项目1> / <项目2> / 其他
   重跑会复用同一文档（手动重跑会先问是否覆盖手改）。
```

## 异常处理

- `lark-cli` 权限报错：提示按 `lark-shared` 跑 `auth login --scope <对应scope>`（wiki:node:create、docx:document:edit、im:message、calendar:calendar:readonly、contact:user.id:readonly、drive:drive、minutes 等）。
- 中文乱码：99% 是用了 `Get-Content | lark-cli` 管道，改 `Set-Location` + `--content @./file.xml` 重发（见 publish.md）。
- 飞书会话太多导致慢：会话扫描做成并行子任务、跳过纯通知/机器人会话；单条 lark-cli 调用都很快，避免把整轮塞进一个长跑后台命令（PS 后台任务 2 分钟超时）。
- 任何写接口失败：**不要**覆盖 `_published.json`，保留上次状态以便重试。

## 相关 skill

- 个人视角留痕（绩效/复盘）→ 休眠的 `personal-worklog`，需要时手动 `/skill` 调起。
- 旧详细日报 → 休眠的 `daily-report`。
