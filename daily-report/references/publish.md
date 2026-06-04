# `+发布日报` 工作流

**目的**：把当日所有片段汇总成 DocxXML，发布到飞书知识库（新建当日 docx 节点，或重写已存在的当日 docx）。

## 命令参数

```
+发布日报 [--date YYYY-MM-DD] [--dry-run]
```

- `--date` 默认今天（北京时间）
- `--dry-run` 只打印最终 DocxXML，不调用任何写接口

## 步骤

### 1. 读 config

`C:\Users\jiawei.wang\.claude\data\daily-report\config.json`。不存在 → 提示：

> 尚未配置飞书知识库位置，请先运行 `+配置`。

### 2. 收集片段

扫描 `C:\Users\jiawei.wang\.claude\data\daily-report\<date>\*.md`（排除 `_published.json`）。

> **⚠️ 必须扫全目录的所有 `*.md`，不要按项目名前缀过滤。**
> 一天里可能有多个项目、多个窗口各自写片段（`cvabase__*.md`、`scholarscup-2026__*.md`…）。
> 曾踩坑：复用了 capture 阶段的 `<project>__*.md` 通配，只扫到当前项目、漏发了其他项目的片段。
> 正确做法：`Get-ChildItem "<date>\*.md"` 一把扫全，再按 frontmatter 的 `project` 字段分组。

- 没有任何片段 → 告诉用户"<date> 没有日报片段，是否要发布？"，等用户确认后允许发布一个"今日无开发产出"占位文档（或直接跳过）
- 有片段 → 进入下一步

### 3. 按项目分组

读每个片段的 frontmatter `project` 字段，归组成：

```
{
  "cvabase": [片段1, 片段2, ...],
  "5月学习计划": [片段3],
  "__misc": [片段4]
}
```

同一项目内按 `captured_at` 升序排列。

### 4. 组装 DocxXML

**严格按照 [template-example.md](template-example.md) 的格式**，由 Claude 边读片段边重写润色：

```xml
<title>日报 · {date}</title>

<!-- 每个项目一节 -->
<h2>一、{项目1名称}项目进展</h2>
<p>{一句导语：今日该项目推进了哪几条工作线、各自什么性质}</p>

  <!-- 把该项目下所有片段的 ### 子任务合并、去重、按主题归并 -->
  <h3>1. {子任务标题}（commit <code>xxx</code>，已push）</h3>
  <ul>
    <li><b>背景</b>：{要解决什么问题 / 为什么做，一句话}</li>
    <li><b>核心动作</b>：
      <ul><li>...</li><li>...</li></ul>
    </li>
    <li><b>核心决策</b>：{关键取舍及理由，一句话；可与「核心动作」二选一或并存}</li>
    <li><b>改动内容</b>：{落地了什么——文件数 / 字段数 / 文档数等可核对的客观结果}</li>
  </ul>
  <h3>2. {另一个子任务}</h3>
  ...
  <h3>{项目1简称}项目总结产出</h3>
  <ul>
    <li>...</li>
    <li>待办：{该项目的下一步，逗号分隔}</li>
  </ul>

<hr/>

<h2>二、{项目2名称}项目进展</h2>
...

<hr/>

<!-- 跨项目汇总，编号紧接项目 -->
<h2>{N}、今日总产出清单</h2>
<h3>代码 / 技术产出</h3>
<ul><li>...</li></ul>
<h3>文档 / 飞书产出</h3>
<ul><li>...</li></ul>
<h3>数据 / 决策产出</h3>
<ul><li>...</li></ul>

<hr/>

<h2>{N+1}、整体待办事项</h2>
<table>
  <colgroup><col/><col/><col/><col/></colgroup>
  <thead><tr>
    <th><p>优先级</p></th><th><p>事项</p></th>
    <th><p>责任人</p></th><th><p>截止时间</p></th>
  </tr></thead>
  <tbody>
    <tr><td><p>高</p></td><td><p>...</p></td><td><p>...</p></td><td><p>...</p></td></tr>
    ...
  </tbody>
</table>

<hr/>

<!-- 固定末节：技术学习板块 -->
<h2>{N+2}、收获与判断（技术学习）</h2>
<p>本板块面向刚入门编程的同事，把今天踩到 / 用到的技术概念拆开讲明白，便于从实践中积累。</p>
<ul>
  <li><b>{术语中文}（{术语英文}）</b>：{白话解释这是什么} + {今天哪个任务用到 / 踩到它}。<b>记忆点</b>：{一句可迁移的经验}。</li>
  ...
</ul>
```

**编号规则**：
- 项目按片段总字符量倒序，最大的工作放最前
- h2 用中文数字「一、二、三、四…」
- 子任务 h3 用阿拉伯数字「1. 2. 3.」
- 三个固定末节永远在项目之后，顺序固定：「今日总产出清单」→「整体待办事项」→「收获与判断（技术学习）」，编号紧接项目数
- 每个 h2 之间用 `<hr/>` 分隔

**子任务三要素（固定结构，对齐历史日报）**：
- `<b>背景</b>`：一句话——要解决什么问题、为什么做
- `<b>核心动作</b>`：嵌套 `<ul>`，3-5 条，写做了什么；动作多时用此项
- `<b>核心决策</b>`：一句话——关键取舍及理由（如"上限选 20MB 而非更大，因为…"）；可与「核心动作」并存，也可只用其一
- `<b>改动内容</b>` 或 `<b>产出</b>`：落地的可核对结果（文件数 / 字段数 / 文档数 / 交付物）
- commit hash 写进 h3 标题尾括号：`（commit <code>xxx</code>，已push）`，不要散在正文 bullet 里
- **不在子任务里写「下一步」**——子任务级的后续统一收到「{项目}项目总结产出」末尾一条「待办：…」，跨项目待办收到「整体待办事项」表

**片段三要素 → 报告三要素的映射**（片段是 capture 阶段产物，格式不同，发布阶段须转换）：
- 片段「完成事项」 → 报告「背景」（提炼问题）+「核心动作」+「改动内容」
- 片段「收获与判断」 → 报告「核心决策 / 核心判断」（精简成一句）；技术性内容另喂给末节「收获与判断（技术学习）」
- 片段「下一步」 → 项目「待办：…」+「整体待办事项」表

**润色要求**：
- 同一项目多个片段中重复的子任务合并；一个项目控制在 3-5 个子任务，过细的合并
- **精简优先**：每个子任务核心动作 3-5 条 bullet，不写大段方法论反思——这是给领导扫读的汇报，不是开发复盘文档
- 待办事项从每个片段的「下一步」字段抽取并按优先级排序
- 不要凭空捏造内容，没说的就不写
- `__misc` 项目命名为「杂项 / 工具性任务」单独成节

**「收获与判断（技术学习）」板块要求（固定末节）**：
- 受众是刚入门编程的同事，目标是让其从当天实践中学技术
- 从当天所有片段里挑 6-9 个技术概念（优先挑"有踩坑故事"的，便于结合实践记忆）
- 每条结构：`<b>术语中文（术语英文）</b>` → 白话解释这是什么 → 今天哪个任务用到/踩到 → `<b>记忆点</b>`：一句可迁移经验
- 概念来源举例：异步处理、数据库迁移 / 索引、轮询、git 暂存区、字符编码与乱码、HTTP 状态码、反向代理、SPA、绝对 / 相对路径等
- 解释要白话、可结合生活类比（索引≈书的目录、反向代理≈门卫），不堆术语

**口吻硬约束（对外汇报，不是对话回顾）**：
- 全文禁用第一人称（我 / 我们）
- 禁止出现 "Claude 帮我"、"由 AI"、"和 AI 协作"、"用户提到"、"用户表态" 等把人/AI 摆出来的表述
- 主语统一为项目 / 模块 / 工作本身；用"完成 X"、"新增 Y"、"事故复盘表明 Z"等客观陈述
- 若片段里出现违规表述（多见于 capture 阶段没把握好），**重写为客观陈述再装入文档**
- 避免口语词："OK"、"那么"、"其实"、"是不是"

**受众与措辞硬约束（非计算机专业、但有些技术背景的同事 / 上级）**：

capture 阶段的片段里有大量 API 名 / 函数名 / 文件路径 / 代码标识符（如 `setImmediate`、`extractText`、`schema.prisma`、`src/app/api/documents/route.ts`、`COMPILE_SYSTEM_PROMPT`），那些是给写代码的人看的。发布阶段**必须翻译成业务语言**再装入文档，否则收件人看不懂。

翻译规则：
- 代码标识符 → 业务行为：`setImmediate` 兜底 → "上传后立即返回、后台慢慢解析"；`extractText` → "提取正文"；`updateMany` 标 failed → "顺手把卡住的记录标成失败"
- 文件路径 → 模块名：`src/app/api/documents/route.ts` → "上传 API"；`prisma/schema.prisma` → "数据库结构定义文件"
- 常量/枚举 → 解释含义：`tier=official` → "权威等级标为「官方」"；`status='processing'` → "状态为「处理中」"
- API 接口路径可以保留（如 `/api/briefing`、`/api/stats`），但首次出现时带一句解释
- 缩写/术语首次出现要解释：SPA → "用 JS 动态渲染的现代网页"；Serverless → "按请求计费、用完函数就冻结的部署平台"；413 → "请求体过大"
- commit hash + push 状态保留（汇报必备），但减少代码标识符的密度

什么必须保留：commit hash、版本号（v3.0d）、生产环境标识（如 IP / 域名）、数据库字段数量 / 数据源数量等可核对的客观数据、第三方系统名（港交所、巨潮、Caddy、pm2）。

判断标准：把每个子任务的 h3 标题和首段读一遍——非程序员同事能不能看懂"做了什么、为什么这么做、解决了什么问题"？看不懂就改。子任务标题尤其重要，不要写"v3.0d 信息源拓展阶段 1 — 官方公告源 + 来源可信度双维标签端到端交付"这种密度，改成"把港交所、巨潮两个官方公告源接进来，并给每条简报打上「来源权威等级」标签"。

### 5. `--dry-run` 短路

如果是 `--dry-run`：直接把 DocxXML 打印到终端（用代码块包起来方便复制），流程结束。

### 6. 发布到飞书

读 `C:\Users\jiawei.wang\.claude\data\daily-report\<date>\_published.json`：

#### 情况 A：首次发布（文件不存在）

```bash
# Step 1：新建 wiki 节点（docx 类型）
lark-cli wiki +node-create \
  --space-id <wiki_space_id> \
  --parent-node-token <parent_node_token> \
  --obj-type docx \
  --title "日报 · <date>" \
  --as user --format json
```

从返回的 `data.node` 取 `obj_token`（doc 写接口用这个）、`node_token`、`url`。

```powershell
# Step 2：写入正文（用 overwrite，确保整篇覆盖空白模板）
# Windows PowerShell 5.1 必读：必须先 cd 到临时文件目录，然后用 --content @./<filename> 相对路径
Set-Location C:\temp
lark-cli docs +update --api-version v2 `
  --doc <obj_token> `
  --command overwrite `
  --content `@./<filename>.xml `
  --as user
```

**⚠️ 编码陷阱（曾经踩过）**：

| 写法 | 结果 |
|------|------|
| `Get-Content <tmp> -Raw -Encoding UTF8 \| lark-cli ... --content -` | ❌ 中文全部乱码（PS 5.1 管道把 UTF-8 转成系统 GBK 再写 stdin） |
| `--content @C:\temp\file.xml` | ❌ lark-cli 拒收绝对路径，报 "must be a relative path within the current directory" |
| `Set-Location C:\temp; --content @./file.xml` | ✅ 让 CLI 自己以二进制读文件，绕过管道编码转换 |

所以**默认走 `Set-Location` + `@./<file>` 相对路径**，不要用 stdin 管道。

PowerShell 里 `@` 是 splatting 操作符，传给原生 exe 时必须用反引号转义：`--content \`@./file.xml`。

#### 情况 B：已发布过（文件存在）

复用 `obj_token`，直接 Step 2 即可。不要再调 wiki +node-create。

### 7. 写回 `_published.json`

```json
{
  "date": "2026-05-19",
  "doc_token": "<obj_token>",
  "node_token": "<node_token>",
  "url": "<url>",
  "published_at": "<ISO 8601>",
  "fragments_count": <N>,
  "projects": ["cvabase", "5月学习计划", ...]
}
```

### 7.5 推送到「每日日报组」飞书群（固定，每次发布后必做）

发布 / 重发成功后，**自动**把日报链接发到飞书群「每日日报组」（不需要再问用户）。

```
群名：每日日报组
chat_id：oc_03cc17c6ca043704f9fc252e6fe86623
```

```powershell
$md = @'
📋 **日报 · <date>**
[日报 · <date>](<url>)
'@
lark-cli im +messages-send --as user `
  --chat-id oc_03cc17c6ca043704f9fc252e6fe86623 `
  --markdown $md `
  --idempotency-key "daily-report-<date>"
```

- 用 `--idempotency-key "daily-report-<date>"` 防止重发当天重复刷屏（重跑当天日报不会再发一条新的）。
- **若同一次会话同时也跑了 `personal-worklog`（Worklog）**：把日报和 Worklog 两条链接**合并成一条消息**发，避免群里两条。合并写法见 [personal-worklog SKILL.md](../../personal-worklog/SKILL.md) 的「推送到每日日报组」节，二者用同一 `chat_id`、同一 `--idempotency-key "report-<date>"`。
- chat_id 失效 / 群改名时，用 `lark-cli im +chat-search --query "每日日报" --as user` 重新查回。

### 8. 输出

```
日报已发布：<url>
已推送到飞书群「每日日报组」。
共 N 个片段，M 个项目（cvabase / 5月学习计划 / 杂项）。
如需修改重发，再次运行 `+发布日报` 即可（会复用同一文档）。
```

### 9. 发布后自检（对照历史日报，防止文风漂移）

发布前后用以下清单自检，任一不过就重写再发：

- [ ] 子任务三要素是「背景 / 核心动作（或核心决策）/ 改动内容（或产出）」，不是「完成事项 / 收获与判断 / 下一步」
- [ ] commit hash 在 h3 标题尾括号里，不在正文 bullet 里
- [ ] 每个项目有开头导语，子任务里没有「下一步」（已收到项目总结产出末尾的「待办」）
- [ ] 每个子任务核心动作 3-5 条 bullet，没有大段方法论反思
- [ ] h3 标题非程序员能看懂，正文代码标识符已翻译成业务语言
- [ ] 末节顺序：今日总产出清单 → 整体待办事项 → 收获与判断（技术学习）
- [ ] 「收获与判断（技术学习）」有 6-9 个技术概念，每条含术语中英文 + 白话解释 + 记忆点
- [ ] 飞书上打开正文中文无乱码（乱码 → 编码陷阱，见 §6）

## 异常处理

- `wiki +node-create` 报权限：提示跑 `lark-cli auth login --scope wiki:node:create`
- `docs +update` 报权限：提示 scope `docx:document:edit`
- DocxXML 拼装太长（> 命令行限制）：必须通过 `@file` 相对路径传入，不要拼到命令行字符串里、也不要用 PS 管道
- 发布后用户反馈"打开全是 ??? 或乱码"：99% 是用了 `Get-Content | lark-cli` 管道。改用 `Set-Location` + `--content @./file.xml` 重发即可
- 任何写接口失败：**不要** overwrite `_published.json`，保留上一次状态以便重试
