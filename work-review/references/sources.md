# 三源采集逻辑

精简日报取三个数据源：本地对话日志、飞书会话、今日会议。所有 lark-cli 调用用 `--as user`、`--format json`。日期默认今天（北京时间）。

---

## 源一：本地 Claude Code 对话日志（必做，全量）

### 扫描（移植自 personal-worklog 步骤 1）

Claude Code 每个对话窗口在 `~/.claude/projects/*/*.jsonl` 存完整记录。

**双重过滤**：
- 过滤 1（mtime）：文件最后修改时间在本地今天 00:00 之后。
- 过滤 2（内容）：至少含一条 `timestamp` 在今天的 `type=="user"` 且 `isSidechain!=true` 的消息。

只取项目目录**下一层**的 `.jsonl`；忽略 `<uuid>/` 子目录里的 subagent 记录。

> ⚠️ **必须扫全所有窗口**，不要按当前 cwd 或项目名前缀过滤——daily-report 曾踩坑「只扫当前项目、漏发其他窗口」。

每个 jsonl 当一个窗口，提取：
- `cwd`（判属于哪个项目）
- 全部 user 真文本消息（`message.content` 里 `type=="text"`）
- 时间戳范围

跳过纯 `<command-...>`、`Caveat`、`<system-reminder>`、`<task-notification>`、`tool_result` 项。`Base directory for this skill: ...` 这种 skill 加载提示，只保留末尾的 `ARGUMENTS:` 用户实际命令。

### 逐窗并行提炼（subagent）

对每个窗口并行启动一个 `Agent`（`subagent_type: general-purpose`），单条消息内多次 tool use 并行发起。每个 subagent 任务：

> 读 `<jsonl 路径>`，提炼这个窗口「今天完成/推进了什么」，返回 JSON：
> ```json
> {
>   "window_id": "<jsonl 文件 8 位前缀>",
>   "cwd": "<cwd>",
>   "time_range": "<HH:MM-HH:MM>",
>   "topics": [
>     {"title": "<一句话子主题，业务语言>", "points": ["<要点1>", "<要点2>"], "links": ["<对话里出现的飞书 URL>"]}
>   ]
> }
> ```
> 要求：只看 `type=="user"` 且 `isSidechain!=true` 的消息；客观陈述、第三人称、不写「我」、不写「AI/Claude 干了什么」，只写做成了什么、产出了什么；代码标识符/路径翻译成业务语言（详见 condense-format.md）；没做成的、纯闲聊的不写。

主 agent 收 N 份 JSON 进入聚类。

---

## 源二：飞书会话（Q7：扫今天所有有活动的会话）

### 列会话

```powershell
lark-cli im +chat-list --types=p2p,group --as user --format json --page-size 50
```

> `--types=p2p,group` 需 user 身份（`--as user` 已满足）。`im +chat-list` **不支持** `--page-all`，会话多时用 `--page-token <下一页token>` 循环翻页直到无 token。

过滤规则：
- 跳过纯机器人 / 通知类会话（名称含「通知」「机器人」「Bot」「提醒」「监控」，或对方是应用号）。
- 跳过 `config.chat_exclude` 里列出的 chat_id。
- 只保留**今天有真人消息**的会话（下一步抓消息时若今天 0 条则丢弃）。

### 逐会话抓今日消息（可并行）

```powershell
lark-cli im +chat-messages-list --chat-id <chat_id> --as user --format json `
  --start "<date>T00:00:00+08:00" --end "<date>T23:59:59+08:00" --page-size 50
```

> ⚠️ 时间 flag 是 `--start` / `--end`，值用 **ISO 8601**（不是 `--start-time`、不是 unix 秒——写错会报 unknown flag）。`<date>` 用 yyyy-MM-dd。此命令**不支持** `--page-all`；繁忙群当天消息超过一页时用 `--page-token` 循环翻页，别只取一页（会漏下午的消息）。

对每个会话，把今天的真人消息交给一个并行 subagent 提炼「和工作相关的结论」：拍板了什么、对齐了什么、给出了什么决定/数据/链接。返回：

```json
{"chat_name": "<群名>", "conclusions": [{"text": "<一句话结论>", "links": ["<飞书URL>"], "topic_hint": "<可能属于哪个项目/主题>"}]}
```

纯寒暄、与工作无关的丢弃。

---

## 源三：今日会议（Q9）

### 拉今日日程会议

```powershell
lark-cli calendar +agenda --as user --format json
```

`+agenda` 默认今天。从结果取每个事件的：标题、起止时间、参会人。**会议判定（具体信号，避免两次执行结果不同）**：保留满足任一的事件——① 参会人 ≥ 2；② 带视频会议链接/会议室。跳过：全天事件、个人提醒、无参会人的单人日程。

### 补妙记结论（有则补）

```powershell
lark-cli minutes +search --as user --format json `
  --start <date> --end <date>
```

> 同样用 `--start` / `--end`（接受 ISO 8601 或 `YYYY-MM-DD`），不是 `--start-time` unix 秒。

按标题/时间把妙记和当天会议匹配上；命中的会议补一句结论摘要 + 妙记链接（`https://<host>/minutes/<minute-token>`）。匹配不到妙记的会议只保留 标题 + 时间 + 参会人。

会议结构化为：

```json
{"title": "<会议名>", "time": "<HH:MM-HH:MM>", "attendees": ["..."], "summary": "<一句结论或空>", "link": "<妙记URL或空>", "topic_hint": "<可能属于哪个项目>"}
```

---

## 汇总交给聚类

三源产物（本地 topics / 飞书 conclusions / 会议）全部带 `topic_hint` 或专有名词，交给 SKILL.md 步骤 4 的跨源并查集聚类：
- 飞书结论、会议按 `topic_hint`/专有名词并入对应项目。
- 并不进任何项目的 → 兜底节「其他：沟通与会议」。
