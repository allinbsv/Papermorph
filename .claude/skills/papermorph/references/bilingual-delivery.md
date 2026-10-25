# 两种语言，一个作品标准 / Two languages, one editorial standard

This is a delivery rule for Chinese and English versions of a PaperMorph lesson, picture book, or documentary. It changes no existing engine defaults until a particular release is selected and prepared.

## User choice comes first

Before presenting a new finished text, narrated video, interactive page or export to the user, ask this **two-choice question** if no explicit choice exists for that artifact:

> 这次成品要输出 **中文版（普通话配音）** 还是 **英文版（英语配音）**？

Do not infer a preference from the language in which the user writes, the source book's language, the last release, or `style.json.book.language`. If the user already chose explicitly **for this exact artifact**, do not ask again merely to repeat the same release. If they expressly ask for both, prepare both and do two separate reviews; never claim both are available when only one is rendered. The user may change the choice for a later release without affecting previous outputs.

In the chosen book's `style.json`, set `delivery.selection` only from the user's reply:

```json
{
  "language": "zh",
  "for_artifact": "ch01-film-v1",
  "confirmed_by_user": true,
  "source": "user reply identifying Chinese for ch01-film-v1"
}
```

`for_artifact` is a stable identifier for this deliverable/revision (not merely `ch01` for every future revision). Keep the unselected template at `null`/`false`. Before a release, run:

```bash
python3 SKILL/scripts/delivery_language_gate.py books/<book>/style.json \
  --language zh --artifact ch01-film-v1
```

Change `--language en` only after confirmation for that artifact. `BLOCKED` means ask/record the choice or correct the mismatch, **not** automatically choose a default. This gate checks authorization metadata, not that voice, synchronization or aesthetics have passed QA.

## Equal intent, native expression

| Invariant for both | 中文版 | English version |
| --- | --- | --- |
| Thought | 从真实小事切入，一次解释一个机制；不装作无所不知 | Begin with something tangible; explain one mechanism at a time; acknowledge the unknown |
| Tone | 像有经验的长者真诚说话，但不刻意装老、煽情或模拟名人 | A patient, seasoned, warm original narrator, without grandiosity, performative nostalgia or impersonation |
| Evidence | 来源、修订版、条件和推断边界完整 | Same factual sources, version, conditions and inference boundaries |
| Image | 画面与语言同步，中文字体和移动端可读 | Same explanatory visuals, adapted English typography and legibility |
| Voice | 原创普通话配音，Edge/Qwen 等只作候选、真人试听批准 | Original natural English narration; Edge `en-US-GuyNeural` is only an unapproved candidate; human audition required |
| Release | 完整试听、字幕、同步及版权复核 | Independently listen, review subtitles/synchronization/rights and approve the final cut |

Keep beat IDs, mark IDs, evidence pointers and causal argument consistent when both variants are made; **do not** force equal sentence length, literal idioms or identical audio timings. Translate mathematical notation and proper names carefully. Rewrite jokes/metaphors when necessary, marking changes that could alter a factual claim for re-review. All prior user requirements about sincerity, clarity and restraint apply to **both** languages.

## Two outputs, no silent fallback

- Preserve sources `content/<book>/chNN/narration.zh.json` and `.../narration.en.json` when both exist. The template bundle contains both language examples with matching beat and mark IDs.
- Generate separate audio/timing folders (`audio/zh`, `audio/en`) and check the actual spoken language; `tts.py` reads the voice named by each narration file. If using a style template that has `delivery.voices_by_language`, copy the chosen voice into the target narration rather than passing an entire multi-language object to `tts.py`.
- For simplest releases, export **separate stand-alone language-specific builds** (`site/<book>-zh/` and `site/<book>-en/` or equivalent stable directories). Each must have matching `<html lang>`, `CHAPTER.language`, audio paths, title, subtitles, prompts and credits. Avoid a runtime language toggle until switch timing, progress and replay behavior have been explicitly agreed and tested.
- A source-language version can be edited while the other remains unchanged. Track a version-specific release record with language, artifact ID, voice, QA outcome, source versions and approval; do not promote the other version by assumption.
- If only one language is ready, say precisely which and mark the other `PENDING`. Code checks, TTS dry runs and draft translations cannot replace a human listening to the actual finished audio/video.
