# feishu-doc-mirror

飞书文档镜像 skill。它可以把飞书社区文章、飞书分享文档或 wiki 文档镜像到自己的飞书空间，尽量保留正文、标题结构、表格、callout 和图片；当源文档禁止复制或导出时，会走“读取正文 + 浏览器恢复图片 + 重建文档”的方案。

## 适合什么场景

- 飞书社区文章只有卡片链接，需要保存正文。
- 分享文档禁止复制、下载或创建副本，但自己需要可编辑版本。
- 想把外部飞书文档完整搬到自己的知识库或云空间。
- 需要保留图片、标题、表格、代码块、callout 等结构。

## 工作流程

1. 解析链接：识别社区卡片、docx 链接或 wiki 链接，找到真实文档 token。
2. 优先原生复制：能导出或创建副本时，先走飞书原生能力。
3. 失败后重建：若源文档禁止复制，读取 Markdown 正文，并用浏览器抓回图片。
4. 顺序构建：按原文顺序 append 文本、插入图片，生成新的飞书 docx。
5. 验证结果：检查图片数、标题数、callout、表格和中文完整性。

## 一次性准备

需要已登录的 `lark-cli`：

```bash
lark-cli auth login --domain docs
```

图片恢复步骤需要 Python 和 Playwright：

```bash
pip install -r requirements.txt
playwright install chromium
```

## 常用说法

- “把这篇飞书文章镜像到我的空间：<URL>”
- “这个飞书文档不能复制，帮我克隆一份：<URL>”
- “完整下载/保存这篇飞书社区文章：<URL>”

## 关键文件

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 主流程、触发条件和操作步骤 |
| `scripts/resolve_source.py` | 解析输入 URL，找到真实文档 |
| `scripts/capture_images.py` | 浏览器渲染源文档并恢复图片 |
| `scripts/preprocess.py` | 把正文和图片整理成构建计划 |
| `scripts/build.py` | 创建并按顺序构建新文档 |
| `scripts/verify.py` | 对比源文档和镜像文档 |
| `references/pitfalls.md` | 已踩过的飞书、编码和图片坑 |

## 限制

- 图片恢复要求源文档能匿名访问；如果必须登录，可能只能镜像文字。
- 跨租户受保护媒体不能直接下载，只能通过可见页面恢复。
- 只镜像当前文档正文，不会递归展开文中的其他文档链接。
