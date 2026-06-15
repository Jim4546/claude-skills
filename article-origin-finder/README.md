# article-origin-finder

给定一篇文章 URL（常被反爬 / 被墙、或属中文转载 / 编译稿），抓取正文、**溯源到其原始出处（尤其英文原文）**、多源交叉核实真伪，并整理成一份结构化的飞书云文档。拿不到飞书时降级为本地文件。

> 这是一个 [Claude Code](https://claude.com/claude-code) skill。把整个目录放进你的 `~/.claude/skills/`（或团队共享的 skills 目录），Claude Code 会自动识别。

## 它做什么

输入一条文章链接 →

1. **抓正文**：先普通抓取；命中反爬（如微信"环境异常"、HTTP 451、登录墙）就升级到本机无头浏览器（住宅 IP + 真实浏览器指纹），绕过拦截。
2. **溯源**：从正文里找它自报的出处（文末原文链接 / 原作者 / "编译自"），顺藤摸瓜取到原始英文原文；自报出处缺失或核不实时，再全网多源比对。
3. **核实**：逐条比对中文稿与英文原文，标注「真实·逐字 / 意译 / 虚构·未证实」。
4. **产出**：飞书云文档，三层结构——原文信息表 → 英文原文全文 → 中英核对表。飞书不可用则落地为本地 Markdown。

如果文章本就是原生中文、或自报出处是编造的，它会**明确告诉你"无英文原文"**，而不是硬编一篇译文。

## 一次性环境准备

这个 skill 依赖两样东西。第一次用前装好：

### 1. Python + Playwright（绕反爬抓正文用）

```bash
pip install playwright
playwright install chromium
```

> Windows 上若 `python` 指向 Microsoft Store 版本也可用；macOS / Linux 同样适用。

### 2. lark-cli（写飞书文档用，可选）

如果你想把结果**写进飞书**，需要装并登录 lark-cli：

```bash
# 安装见 lark-cli 官方说明；登录（按业务域授权）：
lark-cli auth login --domain docs
```

没有 lark-cli 也能用——skill 会自动降级，把结果存成本地 `名称_YYYYMMDD.md`。

## 用法

在 Claude Code 里直接说，例如：

- "找一下这篇文章的英文原文并整理进飞书：<URL>"
- "这篇是哪来的？帮我溯源核实：<URL>"
- "/article-origin-finder <URL>"

## 跨平台说明

脚本基于 Playwright，三大平台通用。skill 的示例命令以 Windows PowerShell / Git Bash 为主；macOS / Linux 用户把路径分隔符和 `python` 调用按本地习惯替换即可，核心逻辑不变。

## 注意

- 仅用于**合理引用 / 个人研究 / 溯源核实**。英文原文在产出文档中标注 verbatim 来源，不全文复制受版权保护的中文译稿。
- 抓取走的是你本机的网络与浏览器身份，请遵守目标站点的使用条款。
