---
name: minutes-clip-resummary
description: 裁剪长录音/飞书妙记的指定片段，再重新生成「智能会议纪要」。给定一个妙记 URL（或本地音视频）+ 要保留(或删除)的时间段，自动下载→ffmpeg 裁剪/拼接→重新上传飞书妙记→飞书自动重做智能纪要（总结/章节/待办/逐字稿）→返回新的妙记链接。触发词：「裁剪录音重做纪要」「妙记截取片段」「把这段录音去掉无关部分重做纪要」「长录音截一段重做智能会议纪要」「剪掉开头/结尾寒暄重新生成纪要」。
---

# 妙记裁剪 + 重做智能纪要

把一段长录音里无关的部分（开场寒暄、结尾闲聊、中间跑题段落等）剪掉，只留有效内容，
再让飞书重新生成一份干净的智能会议纪要。

## 何时用

- 用户给一个飞书妙记 URL / token，说要「裁掉一些无关内容」「截取其中一段」再「重做智能纪要 / 会议纪要」。
- 用户给一个本地音视频文件，要先剪辑再生成飞书纪要。
- 关键动作组合 = **截取片段 + 重新生成飞书智能纪要**。

## 依赖

- `lark-cli`（已登录 user 身份）：`minutes +download` / `drive +upload` / `minutes +upload` / `vc +notes`。
- `ffmpeg` + `ffprobe`。Windows 未装时用：
  `winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements`
  装完若没进 PATH，用绝对路径调用：
  `…\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\ffmpeg-*-full_build\bin\ffmpeg.exe`

## 输入约定

- **来源**：妙记 URL（`http(s)://<host>/minutes/<token>`，token 是末段）或本地音视频路径。
- **保留段**：一个时间段列表 `keep = [[start,end], ...]`，`HH:MM:SS`。单段是最常见特例。
  也接受「删除段」表述，自己换算成保留段。
- 时间点怎么定：先读妙记 AI 产物的 **chapters**（每章 `start_ms/stop_ms`）和**逐字稿时间戳**，
  据此向用户确认或自动判断哪些是无关段落。**切点务必和用户确认**，不要擅自猜。

## 流程

### 0. 解析来源 & 看内容定切点
```bash
# 妙记元数据（标题、duration）
lark-cli minutes minutes get --params '{"minute_token":"<token>"}'
# AI 产物 + 逐字稿（章节边界 = 天然切点候选）
lark-cli vc +notes --minute-tokens <token> --output-dir ./_clip_work
```
读 chapters 的 summary/title + 逐字稿首尾，识别开场/结尾/跑题段；用 AskUserQuestion 和用户确认保留范围。

### 1. 下载原始媒体
```bash
lark-cli minutes +download --minute-tokens <token> --output-dir ./_clip_work/src
# 落地路径见返回 saved_path（妙记常为纯音频，如 .ogg/opus）
```
本地文件来源则跳过此步。用 `ffprobe` 确认总时长与是否含视频流：
```bash
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,codec_name -of default=noprint_wrappers=1 "<file>"
```

### 2. 裁剪
**单段保留**（保留 start→end，转码音频，体积小、上传快）：
```bash
# -ss 放 -i 前快速 seek；-t 用“时长”避免绝对/相对歧义；-vn 丢视频只留音频
ffmpeg -ss <start> -i "<src>" -t <duration=end-start> -vn -c:a libmp3lame -q:a 2 -y "<out>.mp3"
```
**多段保留**（去掉中间某段→拼接，覆盖「删开头+删中间一段+删结尾」）：分段裁剪后用 concat。
```bash
ffmpeg -ss <s1> -i "<src>" -t <d1> -vn -c:a libmp3lame -q:a 2 -y part1.mp3
ffmpeg -ss <s2> -i "<src>" -t <d2> -vn -c:a libmp3lame -q:a 2 -y part2.mp3
# concat list 文件每行: file 'part1.mp3'
ffmpeg -f concat -safe 0 -i list.txt -c copy -y "<out>.mp3"
```
原格式若已是妙记支持格式（mp3/m4a/wav/aac/ogg/...），也可 `-c copy` 不转码（更快，但切点只能落在关键帧附近，音频通常 OK）。

裁完 **务必 `ffprobe` 校验时长** ≈ 各保留段之和；必要时抽听首尾确认切点。

### 3. 重新上传生成新妙记
```bash
lark-cli drive +upload --file "<out>.mp3"            # 取返回里的 file_token（>20MB 自动分片）
lark-cli minutes +upload --file-token <file_token>   # 取返回里的 minute_url
```
- `minutes +upload` 只收 `--file-token`，必须先 `drive +upload`。
- 限制：单文件 ≤6GB、≤6 小时。
- 支持音频 wav/mp3/m4a/aac/ogg/wma/amr；视频 avi/wmv/mov/mp4/m4v/mpeg/ogg/flv。
- 从 `minute_url` 末段取出新的 minute_token。

### 4. 轮询新智能纪要
飞书异步转写，未就绪时 `vc +notes` 报 **`2091003`（妙记尚未准备好）**。耐心轮询（约 1.6h 音频常需数分钟~十几分钟）：
```bash
lark-cli vc +notes --minute-tokens <new_token> --output-dir ./_clip_work/new
```
（可选）改个清晰标题：
```bash
lark-cli minutes +update --minute-token <new_token> --title "<标题>（裁剪版）"
```

### 5. 交付
把**新妙记链接** + AI 总结摘要给用户。

## 坑位备忘

- `lark-cli` 的 `--output/--output-dir` 只接受**当前工作目录下的相对路径**，绝对路径会报错；`cd` 到工作目录或用 `./...`。
- ffmpeg 刚 winget 装完往往不在 PATH，用绝对路径或把 `...\bin` 前插到 `$env:Path`。
- 妙记下载的多是纯音频（opus/ogg），`-vn` 无副作用；视频源则提音频后体积更小。
- 切点按逐字稿时间戳定即可达到秒级精度；用户抽听后想多/少切几秒就微调 `-ss`/`-t` 重裁重传。

## 关联

依赖现有 skill：`lark-minutes`（下载/上传/改标题）、`lark-drive`（上传到云空间）、`lark-vc`（拉总结/章节/待办/逐字稿）。
