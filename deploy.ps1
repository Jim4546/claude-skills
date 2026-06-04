# 把本仓库里的每个 skill（含 SKILL.md 的顶层目录）部署到 ~/.claude/skills/
# 仓库是唯一真相源；skills 目录是生成产物，请勿手改。
$repo = Split-Path -Parent $MyInvocation.MyCommand.Definition
$dest = Join-Path $env:USERPROFILE '.claude\skills'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Get-ChildItem $repo -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
  ForEach-Object {
    $t = Join-Path $dest $_.Name
    if (Test-Path $t) { Remove-Item -Recurse -Force $t }
    Copy-Item -Recurse $_.FullName $t
    Write-Host "deployed $($_.Name) -> $t"
  }
