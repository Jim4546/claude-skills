# 发布机制（移植自 daily-report，含 GBK 陷阱 + 重跑覆盖确认）

发布到飞书知识库「开发日报」节点，新建当天 docx 或覆盖已存在的当天 docx，再推送到「每日日报组」群。

## 1. 读 config

`C:\Users\jiawei.wang\.claude\data\work-review\config.json`：

```json
{
  "wiki_space_id": "7631109155675196628",
  "parent_node_token": "JjvDwQ2HEig2LZkRRjlcK713nbf",
  "title_format": "王佳玮工作日报_{yyyymmdd}",
  "group_chat_id": "oc_03cc17c6ca043704f9fc252e6fe86623",
  "chat_exclude": [],
  "manage_grant_users": [
    { "name": "陈曦", "open_id": "" },
    { "name": "刘涛瑜", "open_id": "" }
  ]
}
```

不存在则用上面默认值兜底（节点取自历史 daily-report 配置）。`manage_grant_users` 是发布后要开「可管理」权限的 mentor 列表（见 §5.5）。

## 2. 落 XML 到临时文件

把组装好的 DocxXML 写到 `C:\temp\work-review_<date>.xml`（UTF-8）。`--dry-run` 时到此为止，打印路径与内容即结束。

## 3. 查当天节点是否已存在

**标题单一来源**：

```powershell
$ymd   = "<date>" -replace '-',''      # 2026-06-12 -> 20260612
$title = $config.title_format -replace '\{yyyymmdd\}', $ymd -replace '\{date\}', "<date>"
# 默认 title_format = "王佳玮工作日报_{yyyymmdd}" -> $title = "王佳玮工作日报_20260612"
```

`{yyyymmdd}` = date 去横线的 8 位；同时兼容旧占位符 `{date}`（YYYY-MM-DD），向后兼容历史 config。建节点、查重、推群、DocxXML 的 `<title>` **都用同一个 `$title`**，不要各处硬编码，否则查重和实际标题对不上会建出重复节点。

> **标题格式已从「`<date> 工作日报（精简版）`」改为「`王佳玮工作日报_YYYYMMDD`」**：历史用旧标题建的节点不会被新 `$title` 命中，属预期——从此用新命名建新节点，旧节点保留不动，不要误判为「漏查重复」而去做额外清理。

```powershell
lark-cli wiki +node-list --as user --format json --page-all `
  --space-id <wiki_space_id> --parent-node-token <parent_node_token>
```

> `--page-all` 必加：node-list 默认只返一页，「开发日报」子节点多时已存在的当天节点可能在第 2 页，漏查会建出重复节点 + 群里发两条。

在子节点里找 title == `$title` 的节点。

## 4. 覆盖策略（Q5 / Q6）

- **不存在** → 走 4a 新建。
- **已存在 + 手动跑** → 先问：
  > ⚠️ 当天「$title」已存在，重跑会整篇覆盖（你在飞书里的手改、当天的评论会没，但飞书版本历史可恢复正文）。确认继续？
  用户确认后复用 `obj_token` 走 4b 写正文。
- **已存在 + 定时跑（无人值守）** → **无条件**复用 `obj_token` 覆盖，不问。
  - 判定无人值守**唯一依据**：环境变量 `WORK_REVIEW_SCHEDULED=1`（定时任务里设，见 schedule-setup.md）。**只认这个**——不要用「传了 `--date` 就当定时」之类的推断，否则人工调试带 `--date` 会被静默覆盖手改。

### 4a. 新建节点

```powershell
lark-cli wiki +node-create --as user --format json `
  --space-id <wiki_space_id> `
  --parent-node-token <parent_node_token> `
  --obj-type docx `
  --title "$title"
```

返回值取**顶层** `data.obj_token`（写正文用）、`data.node_token`。**注意**：node-create 不返回 `data.node` 嵌套对象，也**不返回 url**——url 自己拼：`https://t2rvx54o5x.feishu.cn/wiki/<node_token>`。

### 4b. 写正文（GBK 绕坑，必读）

```powershell
Set-Location C:\temp
lark-cli docs +update --api-version v2 `
  --doc <obj_token> `
  --command overwrite `
  --content "@./work-review_<date>.xml" `
  --as user
```

> `--command overwrite` / `--content` / 默认 `--doc-format xml` 是有意为之（这几个是 hidden flag，`docs +update --help` 只列 `--mode`/`--markdown`，别被误导去「修正」成那两个而改坏）。

**⚠️ 编码陷阱（必须遵守）**：

| 写法 | 结果 |
|------|------|
| `Get-Content <tmp> -Raw -Encoding UTF8 \| lark-cli ... --content -` | ❌ 中文全乱码（PS 5.1 管道把 UTF-8 转 GBK 再写 stdin） |
| `--content @C:\temp\file.xml` | ❌ lark-cli 拒收绝对路径 |
| `Set-Location C:\temp; --content "@./file.xml"` | ✅ CLI 自己按字节（UTF-8）读文件，绕过管道编码转换 |

机制：先 `Set-Location C:\temp` 进到 xml 所在目录，再传 `--content "@./file.xml"`（相对路径、带引号）。lark-cli 见 `@` 前缀即把后面当文件路径、二进制读入，不经 PowerShell 管道，故不会 GBK 乱码；绝对路径会被拒。

## 5. 写回发布记录

`C:\Users\jiawei.wang\.claude\data\work-review\<date>\_published.json`：

```json
{
  "date": "<date>",
  "doc_token": "<obj_token>",
  "node_token": "<node_token>",
  "url": "<url>",
  "published_at": "<ISO 8601 +08:00>",
  "projects": ["...", "其他"],
  "source_counts": {"local_windows": 0, "feishu_chats": 0, "meetings": 0}
}
```

**任何写接口失败：不要覆盖 `_published.json`，保留上次状态以便重试。**

## 5.5 给 mentor 开「可管理」权限（发布后、推群前必做）

把当天报告里出现的全部飞书链接，给 `config.manage_grant_users`（默认 陈曦、刘涛瑜）开「可管理（full_access）」权限。

### a. 解析 mentor open_id（首次/为空时）

`config.manage_grant_users` 里 `open_id` 为空时解析一次并回写 config 固定：

```powershell
lark-cli contact +search-user --queries "陈曦,刘涛瑜" --as user --format json
```

- 取每人结果的 `open_id`。命中唯一 → 回写 config。
- 命中多个 / 0 个 → **提示用户人工确认**，不臆测；该人本次跳过开权限。
- 之后每次直接复用 config 里固定的 open_id，不再查。

### b. 收集要开权限的链接

去重收集当天报告涉及的全部飞书链接：
- 各项目「相关文档」里的 `base/docx/wiki/sheets/file` 链接；
- **加上**会议那条里的妙记 `minutes` 链接（用户要求妙记也开）。

### c. 逐链接、逐 mentor 授予 full_access

对每条链接先 inspect 拿 token + 受支持的资源类型：

```powershell
lark-cli drive +inspect --url '<url>' --as user --format json
# 取 token / type；wiki 链接会自动 unwrap 到底层 obj_token + obj_type
```

再对每位 mentor 授予：

```powershell
lark-cli drive permission.members create --as user `
  --params '{"token":"<token>","type":"<type>"}' `
  --data '{"member_type":"openid","member_id":"<open_id>","perm":"full_access","type":"user"}'
```

- `perm=full_access` 即「可管理」。`<type>` 取 inspect 返回的资源类型（doc/docx/sheet/bitable/file/folder/wiki/slides 之一）。
- **妙记（minutes）注意**：`permission.members create` 的合法 `type` **不含 minutes**。妙记按用户要求尽量开——先 inspect 探测其底层类型，若是受支持类型则照开；若仍是 minutes/不受支持 → 记一行日志「妙记暂不支持该权限接口、跳过」，**不报错、不中断发布**。
- 单条失败（无权限 / 类型不支持 / 对方已是成员）→ 记一行日志、跳过，继续下一条。
- 幂等：full_access 对已是管理员的成员是 no-op，重跑安全。
- 权限报错 scope：`lark-cli auth login --scope drive:drive`（或对应 `drive:permission` scope）。

## 6. 推送到「每日日报组」群（每次发布后必做）

```powershell
$md = @'
✨今日实习日报已更新
请各位mentor查收🫡
详见：[<title>](<url>)
'@
lark-cli im +messages-send --as user `
  --chat-id <group_chat_id> `
  --markdown $md `
  --idempotency-key "work-review-<date>"
```

- `<title>` = 日报标题 `$title`（如 `王佳玮工作日报_20260612`），`<url>` = 报告链接；「详见」用日报原始标题做超链接，不改名。

- `--idempotency-key "work-review-<date>"` 防当天重发刷屏（重跑当天不会再发新的一条）。
- chat_id 失效/群改名：`lark-cli im +chat-search --query "每日日报" --as user` 重新查回，更新 config.group_chat_id。

## 7. 发布前自检（对照参考文档，防文风漂移）

- [ ] 第一行 `<title>王佳玮工作日报_YYYYMMDD</title>`（= `$title`）
- [ ] 项目 `<h2>中文序号、项目名</h2>`，`<hr/>` 分隔
- [ ] 项目下是 `<p>✅ 主题</p>` + `<ul>` 2-4 条，不是子任务三要素
- [ ] 每个项目末尾有 `<h3>相关文档</h3>`（有链接时），链接可点、用文档原始标题（不编名/不标类型后缀）
- [ ] 已给 mentor（陈曦、刘涛瑜）开各链接的「可管理」权限（妙记不支持则已记日志跳过）
- [ ] 没有「收获与判断（技术学习）」「整体待办表」「否决 AI/原话证据」
- [ ] 代码标识符已翻译成业务语言，非程序员看得懂
- [ ] 全文无第一人称、无 AI/对话词
- [ ] 飞书上打开正文中文无乱码（乱码 → §4b 编码陷阱）

## 异常处理

- `wiki +node-create` 权限：`lark-cli auth login --scope wiki:node:create`
- `docs +update` 权限：scope `docx:document:edit`
- `im` 权限：scope `im:message`
- `contact +search-user` 权限：scope `contact:user.id:readonly`（解析 mentor open_id）
- `drive permission.members create` 权限：scope `drive:drive`（开「可管理」失败时按提示登录）
- XML 太长超命令行限制：必须走 `@file` 相对路径，不要拼命令行字符串、不要用 PS 管道
- 打开全是 ??? / 乱码：99% 用了 `Get-Content | lark-cli` 管道，改 `Set-Location` + `@./file.xml` 重发
