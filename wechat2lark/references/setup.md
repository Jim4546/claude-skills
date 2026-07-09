# 首次配置指南

本 skill 需要一个 `config.json` 来记录团队共享知识库的位置。每个团队成员都要做一次，5 分钟搞定。

## 1. 确认 lark-cli 已经登录

```powershell
lark-cli auth login
```

如果之前用过其他 lark-* skill，登录态可以复用。

## 2. 拿到共享知识库的 space_id

由 skill 维护者（通常是初次搭建的人）提前在飞书里创建一个共享知识库，例如「公众号文章归档」。然后：

- 打开知识库主页
- 浏览器地址栏会是 `https://feishu.cn/wiki/space/<space_id>` 或 `https://<tenant>.feishu.cn/wiki/space/<space_id>`
- 复制 `<space_id>`（一长串数字）

如果你是搭建者，第一次用脚手架建库：

```powershell
lark-cli wiki +space-create --name "公众号文章归档" --description "团队公众号文章归档"
```

把返回的 `space_id` 分享给团队成员，并通过 `lark-cli wiki +member-add` 把团队加进去。

## 3. （可选）拿到「公众号归档」父节点的 node_token

如果想把所有文章都挂在某个分组节点下（而不是直接挂到知识库根），先在飞书里创建一个分组节点，然后：

- 打开该节点
- URL 形如 `https://feishu.cn/wiki/<node_token>`
- 复制 `<node_token>`

不需要分组的话，跳过这步，归档直接挂到知识库根目录。

## 4. 创建 config.json

把 skill 安装目录下的 `config.example.json` 拷贝为 `config.json`，填入上一步拿到的值：

```json
{
  "wiki_space_id": "7234567890123456789",
  "parent_node_token": "wikcn1234567890abcdef",
  "lark_identity": "user"
}
```

- `parent_node_token` 留空字符串表示挂到知识库根目录
- `lark_identity` 一般填 `user`；如果需要用机器人身份归档，改成 `bot`

## 5. 验证

随便找一篇公众号文章 URL，让 Claude Code 帮你跑：

> 帮我把这篇公众号转到知识库：https://mp.weixin.qq.com/s/xxxxx

Claude 会自动触发本 skill，输出 wiki 链接。
