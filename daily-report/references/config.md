# `+配置` 工作流

**目的**：把用户的飞书知识库「开发日报」节点位置写入本地 config，让后续 `+发布日报` 知道往哪里挂新文档。

## 步骤

### 1. 检查既有 config
路径：`C:\Users\jiawei.wang\.claude\data\daily-report\config.json`

- 已存在 → 读出并告诉用户当前配置（space_id + parent_node_token + 节点标题），询问是否覆盖
- 不存在 → 进入下一步

### 2. 询问知识库节点 URL

提示用户：

> 请粘贴飞书知识库中「开发日报」节点的 URL，形如 `https://xxx.feishu.cn/wiki/<node_token>`，新日报会作为这个节点的子节点创建。

### 3. 提取 node_token

正则匹配：URL 中 `/wiki/` 后到 `?` 之间的部分就是 `node_token`。

### 4. 解析 space_id

```bash
lark-cli wiki spaces get_node --params '{"token":"<node_token>"}' --format json
```

从返回的 `data.node` 取：
- `space_id`
- `title`（确认节点名是否合理，比如「开发日报」）
- `obj_type`（应为 `docx` 或允许有子节点的类型）

把 `title` 反馈给用户：

> 已识别到节点「<title>」（space_id=<space_id>），新日报会挂在这个节点下，确认吗？

### 5. 写入配置

确认后，写入 `C:\Users\jiawei.wang\.claude\data\daily-report\config.json`：

```json
{
  "wiki_space_id": "<space_id>",
  "parent_node_token": "<node_token>",
  "title_format": "日报 · {date}"
}
```

> 父目录可能不存在，PowerShell 用 `New-Item -ItemType Directory -Force -Path ...` 先创建。

### 6. 输出

> 已配置完成。后续在任意 Claude 窗口跑 `+总结本次` 记录片段，一天结束跑 `+发布日报` 即可。

## 异常处理

- `lark-cli wiki spaces get_node` 返回 permission denied：提示用户按 `lark-shared` 流程跑 `lark-cli auth login --scope wiki:node:read`
- URL 格式不匹配：直接重新问用户，不要瞎猜 token
