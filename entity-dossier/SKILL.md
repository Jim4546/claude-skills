---
name: entity-dossier
description: Use when the user requests $entity-dossier, 企业背调, 公司背调, 人物背调, 信息整理稿, or asks to research a company plus founder/executive/investor and produce a sourced Feishu/Lark cloud document with shareholding, role timelines, public records, diagrams, and China/overseas source coverage.
---

# Entity Dossier

## Overview

Create a high-confidence company/person dossier as an information整理稿, not an investment memo. Default output is a Feishu/Lark cloud document titled `{公司简称}与{人物名}信息整理YYYYMMDD`, with diagrams and a final source appendix.

## Hard Stops

Generate through ordinary gaps. Stop and ask the user only when one of these cannot be confirmed from reliable public information:

- Company legal subject: which entity is the target company.
- Person identity: which person with the same or similar name is in scope.
- Core relationship: why the person is connected to the company.

For all other missing items, write `公开资料未显示` or omit the unsupported claim.

## Intake

Capture these inputs before research when available:

- Target company, aliases, English names, website, jurisdiction, and any entities to exclude.
- Target person, aliases, titles, school/company clues, and suspected relationship.
- Reference Feishu/Lark docs or final-style docs to mirror. Read them with the Feishu/Lark document skill or CLI when accessible.
- Output destination: default to a new Feishu/Lark doc unless the user names a wiki node or doc.

If the user says to exclude a topic, company, person, or relation, remove that material from the narrative and diagrams unless it is necessary to disambiguate the target. Do not leave distracting validation notes in the report body.

## Research Workflow

1. Build an alias map for the company and person in Chinese, English, old names, investment vehicles, labs, and controlled entities.
2. Search public reliable sources broadly. Use the source ladder in `references/source-policy.md`; browse the web for current facts.
3. Extract facts into evidence notes before drafting: company basics, timeline, financing/policy/capital events, equity/governance, people/shareholding, products/IP, person education, roles, external appointments, publications/patents, and the company-person relationship.
4. Separate confirmed facts, unconfirmed gaps, and explicit inference. Only write inference when it is useful, label it `推测`, and explain the basis.
5. Calculate direct and indirect holdings. For multi-layer holdings, use `scripts/calc_equity.py` or an equivalent Decimal calculation and preserve the formula in the table.
6. Assemble the Feishu/Lark document using `references/report-structure.md`.
7. Add diagrams only when the evidence supports them: ownership graph, company/person timeline, role network, product/capital map, or source coverage map. Prefer Feishu whiteboard/canvas tools when available; otherwise embed Mermaid/source diagrams in the doc.
8. Finish with a complete source appendix. Every factual table row or non-obvious claim should trace to at least one source.

## Truth Rules

- Never fabricate names, dates, titles, share percentages, financing events, investors, products, or relationships.
- Do not promote low-confidence data into the main narrative. Either corroborate it, move it to `公开资料未确认`, or omit it.
- Do not write mid-report caveats such as "需要进一步核实来源真实性". Assess source reliability internally and reflect uncertainty by wording the fact correctly.
- Use exact dates for appointments when public sources show them. If only month/year is available, write that precision explicitly.
- For people with the same name, require at least two identity anchors such as employer, school, title, location, patent author affiliation, or disclosure biography.

## Report Shape

Read `references/report-structure.md` before drafting. Default modules:

1. 核心结论
2. 公司信息
3. 人物背景
4. 附录：信息来源

Keep the report dense and sourced. Avoid generic market education, investment recommendation language, and risk sections unless the user asks for them.

## Verification

Before delivering the Feishu/Lark link, run the checklist in `references/verification-checklist.md`. At minimum, verify:

- Title, requested exclusions, and target identities are correct.
- Direct/indirect holdings add up and formulas are visible.
- Person appointment dates are present for each company where public data supports dates.
- Diagrams match the facts and do not introduce unsupported links.
- Source appendix links are reachable enough to identify title/publisher/date, and source count covers the document.

## Resources

- `references/source-policy.md`: free reliable source ladder for China and overseas searches.
- `references/report-structure.md`: reusable Feishu/Lark dossier outline and table requirements.
- `references/verification-checklist.md`: final QA checklist.
- `scripts/calc_equity.py`: deterministic direct/indirect shareholding calculator.
