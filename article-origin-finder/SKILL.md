---
name: article-origin-finder
description: "给定一篇文章 URL（常被反爬/被墙、或属中文转载/编译稿），抓取正文、溯源到其原始出处（尤其英文原文），多源交叉核实真伪，并整理成飞书云文档（三层结构：原文信息表+英文原文全文+中英核对表）。当用户丢来一条文章链接（微信公众号/任意网站）要求找原文/英文原文/溯源/查证/整理进飞书时使用。触发词：找原文、英文原文、溯源、原始出处、查证真伪、article origin、find original。拿不到飞书时降级为本地文件。"
metadata:
  requires:
    bins: ["python"]
    optional-bins: ["lark-cli", "yt-dlp"]
    siblings: ["lark-doc", "lark-shared"]
  cliHelp: "lark-cli docs --help"
---

# article-origin-finder

**职责：源头还原器。** 给定一篇文章 URL，抓正文 → 判定它是不是某英文原文的转载/编译 → 有原文就还原+核对+整理进飞书；原生中文/源造假/查无原文就**明确给出"无英文原文"结论，绝不编造译文**。

输入不限于微信——任意被反爬/被墙、或属中文转载的文章 URL 都适用。

## 输出契约（硬规则，不可偏离）

> 这一节凌驾于后面所有步骤之上。最终产出**必须**满足，否则不算完成。发布前用第 4 步的关卡脚本自检。

1. **一篇，且只有一篇。** 全部内容装进**同一篇**文档（飞书 docx 或降级本地 .md）。**绝不**拆成多篇、绝不把任何一层另存为旁文件（txt/第二篇 docx）后在正文里写"详见"。
2. **三层齐全、顺序固定：** ① 原文信息 → ② 英文原文全文(verbatim) → ③ 中英核对。三个一级标题分别含 `一、原文信息` / `二、英文原文全文` / `三、与中文文章的核对`。
3. **第二层永远是英文原文逐字全文。** 它就是原文本身，逐段嵌在本篇。**绝不**用以下任何东西替代第二层：摘要、AI 重写、"核对结论"、锚点摘录、关键段引用、"全文见链接/见另一篇/见本地文件"。原文长就长，照样全放。
4. **口播/播客/视频来源同样适用：** 第二层 = 逐字稿全文（清洗后），取法见[第 1 步·口播分支](#口播分支)。
5. **唯一例外——判定"无英文原文"：** 走结论分支，只出 ① + 结论（说明为何判定无原文），**不编**第二层正文，自检时加 `--no-original`。

❌ **DO-NOT（这些都曾导致事故）：** 把第二层换成结论/摘要；把逐字全文拆去另一篇或本地 txt；核对表只放锚点摘录而正文无全文；因为"原文太长/是口播/观感差"就精简或外移第二层。觉得第二层太长 → 照放，不要删。

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

<a id="口播分支"></a>
### 口播 / 播客 / 视频来源分支（重要）

当目标 URL 或溯源结果指向 **YouTube / 播客 / 视频访谈**，原文是**口播**而非书面英文文章时——这类情形最容易让人误以为"没有原文可放"，**错**。此时第二层的 verbatim 全文 = **逐字稿全文**，取法：

1. **优先官方逐字稿/transcript**：节目页常挂 transcript（DocSend、Substack、show notes 等）。能抓到就用它。
2. **否则拉字幕**（需可选依赖 `yt-dlp`，缺则提示 `pip install yt-dlp`）：
   ```bash
   yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "en.*" --sub-format vtt -o "cap.%(ext)s" "<URL>"
   ```
   再把 VTT 去时间轴/去重合并成纯文本。
3. **清洗到可读，但不改词、不删节**：校订被字幕识别错的专有名词、补标点与说话人、轻去口头语（uh/um 及重复词）。**用词忠于原话、不得改写或删减。** 这份清洗稿就是第二层 verbatim 全文，逐段嵌入**同一篇**文档；并在第二层开头标一行来源（"据 YouTube 字幕整理" / "官方 transcript"）。

> 口播来源只是"原文形态不同"，**不改变输出契约**：第二层照样是全文、照样同一篇。绝不因为"要清洗字幕/稿子长"就改成摘要或拆分。

## 第 2 步 · 溯源（轻量优先，按需升级）

照 [trace-origin.md](references/trace-origin.md)：

1. **自报出处优先**：看 `source_links` / `source_context`，顺着作者自报的"原文链接/来源/编译自"取原文并核实。原帖锁登录（X 长文等）→ 用 distinctive 句子找全文转载源/新闻复述。
2. **自报出处也要核**：它可能指向无关内容或被标注不实的贴子，不照单全收。
3. **按需升级**：无自报出处 / 核不实 / 用户要"深挖" → 多源全网扇出（distinctive phrase 多源比对，可用 Workflow 工具并行）。**只用真正抓到的英文，绝不编造**。
4. **判定真相**：确无英文原文 → 直接产出"无英文原文"结论分支（见下）。

## 第 3 步 · 中英核对分级

逐条比对中文稿与英文原文，每条标 **真实·逐字 / 意译 / 虚构·未证实 / 再加工**（判据见 trace-origin.md）。忠实译文也写一句"逐句忠实、无虚构"。把"底层事实真伪"与"叙事框架真伪"分开标。

## 第 4 步 · 输出

按 [output-template.md](references/output-template.md) 的**固定三层**：① 原文信息表 → ② 英文原文全文(verbatim) → ③ 中英核对表。标题 `名称_YYYYMMDD`。再次对照本页[输出契约](#输出契约硬规则不可偏离)。

**发布前自检关卡（强制，先过关再发布）：**

把要发布的内容写成 `content.xml`（或降级的 `名称_YYYYMMDD.md`）后，**必须**先跑校验脚本，`ok:true` 才能 `docs +create`：

```bash
python scripts/check_output.py content.xml            # 正常三层
python scripts/check_output.py content.xml --no-original   # "无英文原文"分支
```

`ok:false` → 按 `problems` 逐条修正、重跑，直到通过；**不要**绕过或忽略它。脚本只查结构（单篇、三层齐全顺序对、第二层有实质全文且未外移），语义忠实度仍由你按 trace-origin 分级把关。

- **飞书可用**：`content.xml` 内容写文件再读（避免 shell 过长 / 转义 / GBK）。命令行过长报 "Argument list too long" 时，用 `--content "@相对路径.xml"`（须为当前目录下相对路径）或 `--content -` 读 stdin：
  ```bash
  lark-cli docs +create --api-version v2 --as user --content "@./content.xml"
  ```
  创建在调用者默认空间（不指定个人节点）。返回 URL 给用户。
- **飞书不可用**：同结构写本地 `名称_YYYYMMDD.md`（UTF-8），告知路径，说明已降级；同样先跑 `check_output.py` 过关。
- **无英文原文分支**：只出信息表 + 结论（为何判定无原文），不编正文；自检加 `--no-original`。

## 收尾

- 报告：英文原文是什么/在哪、核对结论（忠实度 + 虚构/再加工点）、文档链接或本地路径。
- 按用户全局偏好：正文中文；结论处给中英对照。

---

## 边界

- 仅用于合理引用 / 个人研究 / 溯源核实；遵守目标站点条款；不全文搬运受版权保护的译稿（只引用关键段 + 给出处）。
- 抓取走调用者本机的网络与浏览器身份。
- 本 skill 自包含、无个人硬编码，可整目录分享给同事。
