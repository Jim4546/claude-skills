# 输出模板：三层飞书文档（可降级本地）

固定三层结构，每次产出一致：① 原文信息表 → ② 英文原文全文(verbatim) → ③ 中英核对表。

> **输出契约（见 SKILL.md，硬规则）：** 一篇、三层齐全顺序固定；**第二层永远是英文原文逐字全文**，绝不用摘要/结论/锚点摘录/"详见链接"替代，绝不外移或拆成多篇。第二层可以是**书面文章的逐段**，也可以是**口播来源的分说话人逐字稿**——两者都必须 verbatim（全文、不改词、不删节）。发布前必须跑 `scripts/check_output.py` 过关。

## 命名

文档标题用 `名称_YYYYMMDD`（日期取当天）。
例：`Nadella英文原文_A_Frontier_Without_an_Ecosystem_Is_Not_Stable_20260615`。

## 写飞书（首选）

把内容写成 XML 文件，再用 lark-cli 创建（**内容写文件再读，避免 shell 转义和 GBK 编码问题**）：

```bash
lark-cli docs +create --api-version v2 --as user --content "$(cat content.xml)"
```

- 文档创建在**调用者的默认空间**——不要指定任何个人知识库节点 / 群 ID。
- 飞书 XML 语法以 `lark-doc/references/lark-doc-xml.md` 为准。转义：文本里的 `&`→`&amp;`、`<`→`&lt;`；标签本身不转义。

### XML 骨架（按此填充）

```xml
<title>名称_YYYYMMDD</title>

<callout emoji="📌" background-color="light-blue" border-color="blue">
  <p><b>这是什么</b>：<来源文章标题/公众号/链接> 编译/转载的英文原文。</p>
  <p><b>英文原文</b>：<原作者> 的 <b>"<英文原标题>"</b>（<日期>）。下方为逐字全文。</p>
</callout>

<h1>一、原文信息</h1>
<table>
  <colgroup><col span="2" width="140"/></colgroup>
  <tbody>
    <tr><td background-color="light-gray"><b>标题</b></td><td><英文原标题></td></tr>
    <tr><td background-color="light-gray"><b>作者</b></td><td><原作者></td></tr>
    <tr><td background-color="light-gray"><b>发布日期</b></td><td><日期></td></tr>
    <tr><td background-color="light-gray"><b>发布形式</b></td><td><平台/形式></td></tr>
    <tr><td background-color="light-gray"><b>原帖链接</b></td><td><URL></td></tr>
    <tr><td background-color="light-gray"><b>可读全文源</b></td><td><转载/复述 URL></td></tr>
  </tbody>
</table>

<h1>二、英文原文全文（Verbatim）</h1>
<h2><英文原标题></h2>
<p><逐字段落 1></p>
<p><逐字段落 2></p>
<!-- ... 每段一个 <p>，保留原始分段 ... -->

<hr/>
```

### 第二层·口播/播客/视频来源的写法

原文是口播时，第二层放**逐字稿全文**（取法见 SKILL.md 口播分支）。开头标一行来源与清洗说明，正文按说话人分段：

```xml
<h1>二、英文原文全文（Verbatim）</h1>
<callout emoji="📝" background-color="gray">
  <p>据 <来源：YouTube 字幕 / 官方 transcript> 整理：校订专名、补标点与说话人、轻去口头语，<b>用词忠于原话、未改写删节</b>。</p>
</callout>
<h2>Opening · 开场（<主持人/引言人>）</h2>
<p><逐字段落></p>
<h2>01 · <小节主题></h2>
<p><b>Interviewer:</b> <逐字问话></p>
<p><b>Guest:</b> <逐字回答，可多段></p>
<!-- ... 按访谈脉络分小节，全程逐字，不得精简 ... -->
```

```xml
<hr/>

<h1>三、与中文文章的核对</h1>
<callout emoji="⚠️" background-color="light-yellow" border-color="yellow">
  <p><一句话总评：忠实译文 / 基本忠实但有再加工 / 等></p>
</callout>
<table>
  <colgroup><col span="3" width="120"/></colgroup>
  <thead><tr>
    <th background-color="light-gray">要点</th>
    <th background-color="light-gray">判定</th>
    <th background-color="light-gray">说明</th>
  </tr></thead>
  <tbody>
    <tr><td><要点></td><td><b>真实·逐字 / 意译 / 虚构·未证实 / 再加工></b></td><td><依据></td></tr>
    <!-- ... 逐条 ... -->
  </tbody>
</table>
<p><span text-color="gray">核实方式：本机浏览器抓正文 + 原帖预览 + 多源逐句比对。整理日期 YYYYMMDD。</span></p>
```

判定档的定义见 [trace-origin.md](trace-origin.md)。忠实译文也要给一行"逐句忠实、无虚构"。

## 降级：写本地（飞书不可用时）

lark-cli 缺失 / 未登录 / 创建失败时，把**同样三层结构**写成本地 Markdown：

- 文件名 `名称_YYYYMMDD.md`，UTF-8。
- 一级/二级标题对应三层；信息表与核对表用 Markdown 表格；英文原文逐段。
- 告知用户已降级为本地文件，并给出路径。

## 发布前自检（强制关卡）

写好 `content.xml`（或降级 `名称_YYYYMMDD.md`）后、`docs +create` 之前，先人工对一遍清单，再跑脚本：

- [ ] 只有**一篇**文档，没有把任何一层另存外移；
- [ ] 三个一级标题齐全且顺序为 ① → ② → ③；
- [ ] 第二层是**英文原文逐字全文**（书面逐段或口播逐字稿），不是摘要/结论/锚点摘录，正文里没有"全文见…"之类外移措辞；
- [ ] 标题为 `名称_YYYYMMDD`。

```bash
python scripts/check_output.py content.xml            # 正常三层
python scripts/check_output.py content.xml --no-original   # "无英文原文"分支
python scripts/check_output.py 名称_YYYYMMDD.md       # 降级本地 MD 同样适用
```

`ok:false` → 按 `problems` 修正重跑，直到通过才发布。脚本只查结构，不判断忠实度。

## 版权与边界

- **不全文复制中文译稿**——只在核对表里按需引用片段。
- 英文原文标注 verbatim 来源（原帖 + 可读转载源）。
- 若英文原文受版权保护且来源明令禁止转载，文档里给出**出处与可读链接 + 关键段落引用**，而非整篇搬运。
- "无英文原文"分支：文档只出信息表 + 结论（说明为何判定无原文），不编造正文。
