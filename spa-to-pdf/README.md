# spa-to-pdf

SPA 网页导出 skill。它会抓取 JavaScript 渲染的单页应用网页，把多章节内容整理成 Word 文档和 PDF，并尽量保留标题层级、段落、列表、表格和正文里的链接。

## 适合什么场景

- 页面 URL 带 `#/...`，普通抓取只能拿到空壳。
- 页面由折叠面板、章节卡片或前端路由动态渲染。
- 需要把整站或单页内容交付成 Word / PDF。
- 需要自动生成目录，并让 PDF 里的目录和链接可点击。

## 工作流程

1. 探测页面结构：用浏览器渲染页面，查看标题和内容选择器。
2. 抓取章节：按 selector 提取每个章节的 HTML、链接和标题。
3. 构建 Word：生成封面、目录、标题、正文、列表和链接。
4. 验证文档：检查章节数、标题数、链接数和正文完整性。
5. 转成 PDF：用 Microsoft Word 刷新目录并导出 PDF。

## 一次性准备

需要 Windows、Microsoft Word 和 Python 3.10+。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

## 常用说法

- “把这个 SPA 网页导出成 Word 和 PDF：<URL>”
- “把 `https://example.com/#/page` 的所有章节整理成文档”
- “这个网页 curl 抓不到内容，帮我浏览器渲染后导出”

## 也可以手动运行

```powershell
python scripts/probe.py <URL>
python scripts/scrape.py <URL>
python scripts/build_doc.py --in raw/index.json --out output.docx
python scripts/verify.py --in raw/index.json --docx output.docx
python scripts/to_pdf.py output.docx output.pdf
```

## 关键文件

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 触发条件、完整流程和参数说明 |
| `scripts/probe.py` | 探测页面结构和候选选择器 |
| `scripts/scrape.py` | 浏览器渲染并抓取章节内容 |
| `scripts/build_doc.py` | 生成 Word 文档 |
| `scripts/verify.py` | 验证章节、链接和文档完整性 |
| `scripts/to_pdf.py` | 调用 Word 导出 PDF |
| `references/pitfalls.md` | SPA、Word 目录和字体相关坑位 |

## 限制

- PDF 步骤依赖 Windows + Microsoft Word。
- 页面结构特别复杂时，需要先用 `probe.py` 确认 selector。
- 只处理可访问页面，不负责绕过付费墙或登录权限。
