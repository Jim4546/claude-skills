---
name: article-origin-finder
description: "给定一篇文章 URL（常被反爬/被墙、或属中文转载/编译稿），抓取正文、溯源到其原始出处（尤其英文原文），多源交叉核实真伪，并整理成飞书云文档（三层结构：原文信息表+英文原文全文+中英核对表）。当用户丢来一条文章链接（微信公众号/任意网站）要求找原文/英文原文/溯源/查证/整理进飞书时使用。触发词：找原文、英文原文、溯源、原始出处、查证真伪、article origin、find original。拿不到飞书时降级为本地文件。"
metadata:
  requires:
    bins: ["python"]
    optional-bins: ["lark-cli"]
    siblings: ["lark-doc", "lark-shared"]
  cliHelp: "lark-cli docs --help"
---

# article-origin-finder

**职责：源头还原器。** 给定一篇文章 URL，抓正文 → 判定它是不是某英文原文的转载/编译 → 有原文就还原+核对+整理进飞书；原生中文/源造假/查无原文就**明确给出"无英文原文"结论，绝不编造译文**。

输入不限于微信——任意被反爬/被墙、或属中文转载的文章 URL 都适用。

## 必读引用（按需读，不要全读）

- 抓正文遇到墙 → [`references/scrape-ladder.md`](references/scrape-ladder.md)
- 溯源与核对分级 → [`references/trace-origin.md`](references/trace-origin.md)
- 产出文档结构 → [`references/output-template.md`](references/output-template.md)
- 写飞书前 → 兄弟 skill [`../lark-doc/SKILL.md`](../lark-doc/SKILL.md)（XML 语法、`docs +create --api-version v2`）、[`../lark-shared/SKILL.md`](../lark-shared/SKILL.md)（auth）

---

## 第 0 步 · 环境自检

先探测依赖，决定后续走向。**缺啥引导装啥，不要默默失败。**

1. **Playwright（抓正文必需）**：
   ```bash
   python -c "import playwright" 2>&1
   ```
   报错 → 提示用户 `pip install playwright && playwright install chromium`（详见 README），停在这里等装好。
2. **lark-cli（写飞书可选）**：
   ```bash
   lark-cli auth status 2>&1
   ```
   - 不存在 / 未登录 → 记下「飞书不可用」，后续走**本地降级**输出；若用户明确要写飞书，按 `lark-shared` 的 split-flow 引导登录（`auth login --no-wait --json` → 给 URL/二维码 → 用户回合后 `--device-code`）。
   - 已登录 → 后续走飞书输出。

## 第 1 步 · 抓正文（策略阶梯）

1. 先 **WebFetch 直连**。
2. 命中失败特征（"环境异常" / HTTP 451 / 登录墙 / 正文空，见 scrape-ladder.md）→ 升级**本机浏览器**：
   ```bash
   python scripts/fetch_article.py "<URL>" --out article.json
   ```
3. **用 Read 工具读 `article.json`**（不要在终端 print 中文，GBK 会乱码——文件本身是干净 UTF-8）。
4. 拿到：`title / author / body / source_links / source_context / blocked`。`blocked:true` 或正文太短 → 再按阶梯升级（`--wait` 加大 / reader 代理 / `--headful`）。

## 第 2 步 · 溯源（轻量优先，按需升级）

照 [trace-origin.md](references/trace-origin.md)：

1. **自报出处优先**：看 `source_links` / `source_context`，顺着作者自报的"原文链接/来源/编译自"取原文并核实。原帖锁登录（X 长文等）→ 用 distinctive 句子找全文转载源/新闻复述。
2. **自报出处也要核**：它可能指向无关内容或被标注不实的贴子，不照单全收。
3. **按需升级**：无自报出处 / 核不实 / 用户要"深挖" → 多源全网扇出（distinctive phrase 多源比对，可用 Workflow 工具并行）。**只用真正抓到的英文，绝不编造**。
4. **判定真相**：确无英文原文 → 直接产出"无英文原文"结论分支（见下）。

## 第 3 步 · 中英核对分级

逐条比对中文稿与英文原文，每条标 **真实·逐字 / 意译 / 虚构·未证实 / 再加工**（判据见 trace-origin.md）。忠实译文也写一句"逐句忠实、无虚构"。把"底层事实真伪"与"叙事框架真伪"分开标。

## 第 4 步 · 输出

按 [output-template.md](references/output-template.md) 的**固定三层**：① 原文信息表 → ② 英文原文全文(verbatim) → ③ 中英核对表。标题 `名称_YYYYMMDD`。

- **飞书可用**：内容写成 `content.xml`，再
  ```bash
  lark-cli docs +create --api-version v2 --as user --content "$(cat content.xml)"
  ```
  创建在调用者默认空间（不指定个人节点）。返回 URL 给用户。
- **飞书不可用**：同结构写本地 `名称_YYYYMMDD.md`（UTF-8），告知路径，说明已降级。
- **无英文原文分支**：只出信息表 + 结论（为何判定无原文），不编正文。

## 收尾

- 报告：英文原文是什么/在哪、核对结论（忠实度 + 虚构/再加工点）、文档链接或本地路径。
- 按用户全局偏好：正文中文；结论处给中英对照。

---

## 边界

- 仅用于合理引用 / 个人研究 / 溯源核实；遵守目标站点条款；不全文搬运受版权保护的译稿（只引用关键段 + 给出处）。
- 抓取走调用者本机的网络与浏览器身份。
- 本 skill 自包含、无个人硬编码，可整目录分享给同事。
