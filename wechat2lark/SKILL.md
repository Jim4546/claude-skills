---
name: wechat2lark
description: 把微信公众号文章（mp.weixin.qq.com）转存为飞书云文档（docx），图片自动 embed，docx 自动归档到团队共享知识库节点下，命名为「{文章标题}_{YYYYMMDD}」。触发词：「公众号转飞书」「转存公众号」「公众号归档」「mp.weixin.qq.com」「微信文章转 docx」。
---

# wechat2lark — 微信公众号 → 飞书 docx 归档

当用户给出一个 `https://mp.weixin.qq.com/s/...` 链接，并希望把文章转存到飞书知识库时使用本 skill。

## 触发条件

- 用户消息里出现 `mp.weixin.qq.com/s/` URL，且表达「转存」「归档」「转飞书」「转 docx」等意图
- 明确要求把公众号文章保存到知识库

不触发的场景：
- 仅希望预览公众号内容（直接 WebFetch 即可）
- 处理本地 .md 或 .docx 文件（请用 lark-doc / lark-markdown）

## 调用方式

执行：

```powershell
python <skill_dir>\scripts\convert.py --url <文章URL> --config <skill_dir>\config.json
```

其中 `<skill_dir>` 为本 skill 安装目录。`config.json` 由用户首次使用时按 [references/setup.md](references/setup.md) 创建。

可选参数：
- `--wiki-space <id>` 覆盖配置中的知识库
- `--parent-node <token>` 覆盖配置中的父节点
- `--keep-temp` 保留中间产物（用于排查）

成功后脚本输出 JSON：`{"wiki_url": "...", "docx_token": "...", "title": "..."}`。把 `wiki_url` 反馈给用户。

## 工作流程（脚本内部，无需手动执行）

1. 抓取公众号 HTML（带浏览器 UA，处理「环境异常」拦截）
2. 解析标题 / 作者 / 发布日期 / 正文 `#js_content`
3. 下载所有 `<img data-src>` 到临时目录
4. 用 python-docx 构建 docx，图片 embed 进文档
5. `lark-cli drive +import --type docx` 上传为飞书云文档
6. `lark-cli wiki +move --obj-type docx` 挂到配置的知识库节点下
7. 返回 wiki 链接

## 常见错误处理

- **配置文件缺失**：引导用户读 [references/setup.md](references/setup.md) 完成首次配置
- **lark-cli 未登录**：提示运行 `lark-cli auth login`（参考 lark-shared）
- **HTTP 403 / 「环境异常」**：稍等几分钟重试，或换网络环境；不要短时间内连续转多篇
- **正文为空**：文章可能设了「关注后可见」，需要登录态，本 skill 不支持

## 依赖

- Python 3.10+
- pip 包：`requests beautifulsoup4 markdownify python-docx`（首次运行脚本会检查并提示）
- `lark-cli`（团队应已通过其他 lark-* skill 安装）
