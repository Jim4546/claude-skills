# wechat2lark

微信公众号归档 skill。它会把微信公众号文章转成飞书云文档，并归档到指定团队知识库节点，图片会嵌入文档，文档标题默认使用 `{文章标题}_{YYYYMMDD}`。

## 适合什么场景

- 需要把公众号文章沉淀到飞书知识库。
- 需要保留正文、图片、列表和表格，而不是只保存链接。
- 团队希望统一把外部文章归档到指定 wiki 节点。

## 工作流程

1. 抓取公众号 HTML。
2. 解析标题、作者、发布时间和正文区域。
3. 下载正文图片。
4. 用 `python-docx` 构建 docx，图片直接嵌入。
5. 通过 `lark-cli drive +import` 上传成飞书文档。
6. 通过 `lark-cli wiki +move` 挂到知识库节点。
7. 返回新的 wiki 链接。

## 一次性准备

需要 Python 3.10+：

```bash
pip install -r scripts/requirements.txt
```

需要已登录的 `lark-cli`：

```bash
lark-cli auth login --domain docs
```

首次使用前，把 `config.example.json` 复制为 `config.json`，填入团队知识库配置。详细说明见 [references/setup.md](references/setup.md)。

## 常用说法

- “帮我把这篇公众号转到知识库：<URL>”
- “公众号转飞书：<URL>”
- “把这篇微信文章归档成飞书文档：<URL>”

## 也可以手动运行

```bash
python scripts/convert.py --url <article_url> --config config.json
```

## 关键文件

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 触发条件和整体流程 |
| `config.example.json` | 配置样例 |
| `references/setup.md` | 首次配置说明 |
| `scripts/convert.py` | 主入口 |
| `scripts/wechat.py` | 抓取和解析公众号文章 |
| `scripts/docx_builder.py` | 构建 Word 文档 |
| `scripts/lark.py` | 上传和归档到飞书 |
| `用户手册.md` | 更详细的使用说明 |

## 限制

- 不支持“关注后可见”的私密文章。
- 微信可能短时间限流，批量归档时建议错开时间。
- 视频卡片、小程序卡片等复杂组件只保留文本提示。
- 复杂排版会尽量保留内容，不承诺像素级还原。
