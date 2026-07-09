# feishu-doc-mirror

A Claude Code skill that **mirrors a shared Feishu/Lark article into your own
Feishu space** as a faithful, editable doc — text, structure, and all images —
even when the source author has disabled copy/export.

## Why it exists

A Feishu community link (`feishu.cn/community/prompts?id=...`) is only a *card*;
the real article lives in a docx it links to (`worksLink`). That docx often has
copy/export turned off, so:

- `drive +export` → `no permission` (1069902)
- `media-download` → 403

But the **read API still works**, and a community-shared doc **renders for
anonymous viewers**. This skill exploits exactly those two facts: pull the full
text via the read API, and recover every image by rendering the public page in a
headless browser and intercepting the image bytes — then rebuild the article in
your space.

## Pipeline

```
resolve_source.py   URL            -> raw/source.json (real docx token + meta)
(lark-cli fetch)    docx token     -> raw/doc_content.md (full body, markdown)
capture_images.py   public docx    -> clone_imgs/ + clone_manifest.json
preprocess.py       md + manifest  -> seg/ + plan.json (ordered text/image build)
build.py            plan.json      -> new clone doc (create + append + insert)
verify.py           clone vs source-> count + integrity report
```

See [SKILL.md](SKILL.md) for the full operating procedure and the strategy
ladder (try native export first, fall back to rebuild), and
[references/pitfalls.md](references/pitfalls.md) for every hard-won gotcha.

## Requirements

- `lark-cli`, authenticated (`lark-cli auth login`, user identity)
- Python 3.10+, `pip install playwright` + `playwright install chromium`
  (only the image-recovery step needs Playwright)
- Image recovery requires the source doc to be anonymously viewable

## Install

Auto-discovered when placed under `~/.claude/skills/feishu-doc-mirror/`. Invoke
by giving Claude a Feishu URL and asking to "镜像/克隆/完整下载这篇文章".
