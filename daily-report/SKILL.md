---
name: daily-report
version: 1.0.0
description: "自动日报：把多个 Claude Code 窗口在不同项目下的工作，按项目分组汇总，最终发布到飞书知识库「开发日报」节点下，每天一个新 docx。当用户需要总结本次对话工作、生成日报片段、汇总当日多窗口工作、发布日报到飞书云文档、或配置日报飞书知识库位置时触发；触发词包括「总结本次」「写日报」「发布日报」「日报配置」「日报汇总」。"
metadata:
  requires:
    bins: ["lark-cli"]
---

# 自动日报 Skill

> **前置依赖**：飞书写操作走 `lark-cli`，第一次使用前 MUST 先读 [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md) 完成认证；本 skill 默认 `--as user`（日报归用户个人空间）。

## 设计

多个 Claude Code 窗口同时工作彼此隔离，通过**本地共享存储**做汇总点：

```
对话窗口 A ──┐
对话窗口 B ──┼─→ +总结本次 ─→ 本地片段文件 ─→ +发布日报 ─→ 飞书 wiki 新建 docx
对话窗口 C ──┘                                              (挂到「开发日报」节点下)
```

- **手动触发**：不依赖 hook，由用户在每次工作结束/一天结束时显式调用
- **按项目分组**：自动从 cwd 向上找 `.git` / `CLAUDE.md` 识别项目名
- **格式遵循用户既有模板**：见 [`references/template-example.md`](references/template-example.md)

## 数据路径

| 用途 | 路径 |
|------|------|
| 配置 | `C:\Users\jiawei.wang\.claude\data\daily-report\config.json` |
| 当日片段 | `C:\Users\jiawei.wang\.claude\data\daily-report\YYYY-MM-DD\<project>__HH-mm.md` |
| 发布记录 | `C:\Users\jiawei.wang\.claude\data\daily-report\YYYY-MM-DD\_published.json` |

## Shortcuts

| Shortcut | 触发时机 | 详细工作流 |
|----------|---------|-----------|
| `+总结本次` | 某个对话工作告一段落 | [references/capture.md](references/capture.md) |
| `+发布日报` | 一天工作结束，汇总发布 | [references/publish.md](references/publish.md) |
| `+配置` | 首次使用 / 更换知识库位置 | [references/config.md](references/config.md) |

## 快速决策

- 用户说"总结本次"/"记一下"/"写到日报里" → `+总结本次`
- 用户说"发日报"/"发布日报"/"汇总日报" → `+发布日报`
- 第一次使用，`config.json` 不存在 → 引导用户跑 `+配置`
- 用户说"重新发"/"今天日报再改改" → `+发布日报`（会复用同一文档 overwrite）

## 关键约束

- **空对话不入日报**：`+总结本次` 第一步先自评本次对话有无实质交付（代码 commit、文档、决策、数据）。无 → 直接拒绝写入，输出"本次对话无实质交付，未记录"
- **片段追加不覆盖**：同一窗口多次跑 `+总结本次` 用不同时间戳文件，发布时按项目合并
- **发布支持重跑**：同一天再次 `+发布日报` 复用 `_published.json` 里的 `obj_token`，用 `docs +update --command overwrite` 重写正文，不创建副本
- **DocxXML 是默认格式**：所有发布用 DocxXML，禁用 markdown 模式（既有日报全是 DocxXML 渲染）
