# 定时任务安装（Windows Task Scheduler，每天 18:00 本机跑）

> 为什么不用云端 `/schedule`：本脚本依赖**本机**的 `~/.claude/projects/*.jsonl` 和**本机已登录的** `lark-cli`；云端远程 agent 两样都没有，必然失败。所以只能本机 Task Scheduler。

整个安装是一次性的。安装后每天 18:00 无人值守跑出当天权威版精简日报并发布、推群。

## 1. 白名单权限 settings（Q11，不用 --dangerously-skip-permissions）

把下面写到 `C:\Users\jiawei.wang\.claude\data\work-review\cron-settings.json`，只预批本脚本真正用到的操作：

```json
{
  "permissions": {
    "allow": [
      "Bash(lark-cli:*)",
      "PowerShell",
      "Read",
      "Glob",
      "Grep",
      "Task",
      "Write(C:\\temp\\**)",
      "Write(C:\\Users\\jiawei.wang\\.claude\\data\\work-review\\**)"
    ],
    "deny": []
  }
}
```

> 若实际跑时仍因某条权限被拒，把日志里被拒的那条 tool 规则补进 `allow`（最小授权原则，逐条加，不要直接开 `--dangerously-skip-permissions`）。

## 2. 包装脚本

把下面写到 `C:\Users\jiawei.wang\.claude\data\work-review\run-cron.ps1`：

```powershell
# 标记为无人值守，让发布步骤跳过「重跑覆盖确认」（见 publish.md §4）
$env:WORK_REVIEW_SCHEDULED = "1"
$today = Get-Date -Format "yyyy-MM-dd"
$settings = "C:\Users\jiawei.wang\.claude\data\work-review\cron-settings.json"
$log = "C:\Users\jiawei.wang\.claude\data\work-review\$today\cron.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null

# 无头跑精简日报；--settings 挂白名单权限；-p 非交互
claude -p "/work-review --date $today" --settings $settings *> $log
```

> 若你的 `claude` 不在 PATH 里，把 `claude` 换成绝对路径（`(Get-Command claude).Source` 查）。

## 3. 注册定时任务（每天 18:00）

PowerShell（管理员）跑一次：

```powershell
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\Users\jiawei.wang\.claude\data\work-review\run-cron.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 18:00
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "work-review-daily" `
  -Action $action -Trigger $trigger -Settings $settings `
  -Description "每天18:00自动生成并发布精简日报" -RunLevel Limited
```

- `-StartWhenAvailable`：18:00 时机器没开/休眠，开机后补跑。
- 想改时间：改 `-At`，或在「任务计划程序」GUI 里改 `work-review-daily`。

## 4. 验证

手动触发一次模拟 6 点：

```powershell
Start-ScheduledTask -TaskName "work-review-daily"
# 看日志
Get-Content "C:\Users\jiawei.wang\.claude\data\work-review\$(Get-Date -Format yyyy-MM-dd)\cron.log" -Tail 40
```

确认：无人值守下没卡在权限弹窗、飞书里出现当天精简日报、群里收到链接。

## 5. 卸载

```powershell
Unregister-ScheduledTask -TaskName "work-review-daily" -Confirm:$false
```

## 注意

- 各 lark-cli 调用分散执行、都很快；不要把整轮塞进一个长跑后台命令（PS 后台任务有 2 分钟超时坑）。
- 规矩（Q6）：**别在 18:00 前手改飞书**——18:00 这跑是当天权威版，会整篇覆盖。要手改等它跑完再改。
