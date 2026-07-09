# wechat2lark

一个 Claude Code skill：把微信公众号文章转成飞书云文档（docx），自动归档到团队共享知识库。

## 这是什么

在 Claude Code 里贴一个公众号链接，说一声「转到知识库」，skill 会：

1. 抓取文章 HTML、解析正文 + 图片
2. 把图片下载下来，embed 到 docx
3. 上传 docx 到飞书云空间
4. 挂到团队共享知识库节点下，命名 `{文章标题}_{YYYYMMDD}`
5. 返回 wiki 链接

## 安装

```bash
npx skills add <github_owner>/wechat2lark
```

或克隆到本地：

```bash
git clone https://github.com/<github_owner>/wechat2lark ~/.claude/skills/wechat2lark
```

## 前置依赖

- Claude Code
- [`lark-cli`](https://github.com/larksuite/cli) 已登录（团队应已用其他 lark-* skill 装过）
- Python 3.10+ 和：`pip install requests beautifulsoup4 python-docx`

## 配置（团队成员各自一次）

详见 [references/setup.md](references/setup.md)。简单说就是把 `config.example.json` 拷为 `config.json` 并填入团队共享知识库的 `wiki_space_id`。

## 使用

在 Claude Code 里说：

> 帮我把这篇公众号转到知识库：https://mp.weixin.qq.com/s/abcdef

Claude 会自动触发本 skill。或者直接：

```bash
python scripts/convert.py --url <article_url> --config config.json
```

## 限制

- 不支持「关注后可见」的私密文章（需要登录态）
- 短时间内转多篇可能被微信临时限流，错开几分钟即可
- 文章中的视频卡片、小程序卡片只保留占位文本
- 复杂排版的 `<section>` 嵌套样式不完全保真（保留文字 + 图片 + 列表 + 表格）

## License

MIT
