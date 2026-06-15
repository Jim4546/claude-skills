# 输出模板：三层飞书文档（可降级本地）

固定三层结构，每次产出一致：① 原文信息表 → ② 英文原文全文(verbatim) → ③ 中英核对表。

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

## 版权与边界

- **不全文复制中文译稿**——只在核对表里按需引用片段。
- 英文原文标注 verbatim 来源（原帖 + 可读转载源）。
- 若英文原文受版权保护且来源明令禁止转载，文档里给出**出处与可读链接 + 关键段落引用**，而非整篇搬运。
- "无英文原文"分支：文档只出信息表 + 结论（说明为何判定无原文），不编造正文。
