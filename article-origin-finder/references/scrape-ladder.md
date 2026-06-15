# 抓取策略阶梯 + 失败特征

目标：拿到文章**正文全文 + 它自报的出处链接**。从最轻的手段开始，命中"墙"就升级。不要一上来就开浏览器，也不要在被墙后死磕同一档。

## 阶梯（从轻到重）

| 档 | 手段 | 何时用 | 代价 |
|-|-|-|-|
| 1 | **WebFetch 直连** | 任何 URL 第一次 | 最低；但数据中心 IP 常被墙 |
| 2 | **本机 Playwright**：`python scripts/fetch_article.py <url>` | 第 1 档命中失败特征时 | 中；用你本机住宅 IP + 真实 Chrome 指纹，绕过绝大多数墙 |
| 3 | **reader 代理**：`https://r.jina.ai/<url>` 经 WebFetch | 第 2 档对某些 JS 站仍不全时 | 低；但对 X / 微信常被 451/登录墙挡 |
| 4 | **改抓"自报出处"或"全文转载源"** | 原帖本身就锁登录（典型：X 长文 Article） | 低；见 trace-origin.md |

> 经验（本 skill 的来历）：抓微信公众号文章时，**第 1 档 WebFetch 直接撞上"环境异常"验证页**（正文全无）。升级到**第 2 档本机 Playwright 一次成功**——同一条 URL、同样的网络，差别只在"真实浏览器 + 住宅 IP"。这就是为什么本 skill 把 Playwright 抓取打包成脚本，而不是指望每次临场写。

## 失败特征清单（命中任一 = 当前档失败，升级）

- 正文出现 **"环境异常""完成验证""去验证"** / `captcha` / `verify you are human`，且正文极短（< 800 字）。
- HTTP **451**（Unavailable For Legal Reasons）/ **402** / **403**。
- 最终 URL 跳转到 **`/login`、`/onboarding`、`accounts.*`、`*/i/flow/login`**（登录墙）。
- 正文被截断，停在 **"...read more""登录后查看全文""Sign up to continue"**。
- `fetch_article.py` 输出的 JSON 里 `"blocked": true`。

## scripts/fetch_article.py 速查

```bash
python scripts/fetch_article.py "<URL>" --out article.json
# 可选：--wait 6000（JS 重的站多等会儿）；--headful（需要人工点验证时弹出窗口）
```

- 输出 **UTF-8 JSON 文件**（不 print，避免 Windows GBK 控制台乱码）。字段：
  `title / author / body / body_selector / source_links / source_context / blocked / block_reason / final_url`。
- **读结果用 Read 工具读那个 JSON 文件**，不要在 PowerShell/bash 里 `print` 中文（控制台是 GBK，会乱码——这只是显示问题，文件本身是好的）。
- 选择器顺序：微信 `#js_content` 优先，回退 `article/main/.../body`。
- `source_links` = 正文里所有外链；`source_context` = 命中"原文链接/来源/编译自/source"的行——这是溯源的起点。

## 登录墙资源（如 X 长文 Article）

X 的长文 Article 未登录时只渲染**开头一段**就截断，正文藏在 `x.com/i/article/<id>`，需登录态。**不要硬抓**——改走 trace-origin.md：
- 用开头那段的 distinctive 句子去搜**全文转载源 / 新闻复述 / Substack / 博客**；
- 常见可读转载：作者个人站、`*.substack.com`、新闻聚合（36Kr EN、Benzinga、BusinessToday 等）。

## 合规

抓取走你本机的网络与浏览器身份。仅用于合理引用 / 个人研究 / 溯源核实，遵守目标站点条款。不要用它绕过付费墙做再分发。
