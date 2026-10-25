---
name: story-video-quality-gate
description: Produce, repair, or release short narrated story animations (Papermorph, Chinese or English) with reusable storyboard/voice/subtitle settings and deterministic 720p/1080p QA. Use for new animated stories, Fish Audio or other narration, missing words/silent sections, cross-resolution consistency, cost controls, user acceptance and release handoff.
---

# Story Video Quality Gate

Use this skill together with the existing Papermorph story/puppet-film skill. **Do not rebuild its scene engine.** This skill adds production discipline, source-audio continuity checks and independent release gates.

## Workflow

1. **Intake and scope**: ask for story, audience, target 2–3 minute duration (unless overridden), aspect ratio, asset ownership, privacy and output use. **For every new deliverable ask Chinese or English first**; do not assume the last choice applies. Preserve zh/en as separately authored, voiced and accepted versions.
2. **Freeze the creative baseline**: reuse the approved `style.json`, characters, set, voices, pronunciation lexicon, caption style and tempo. For follow-up stories, clone only configuration/assets the user owns; change creative elements only with approval. Record provenance and versions.
3. **Plan storyboard and narration**: use Papermorph picture-book procedures for scenes, beats, cast/sets and animation. Store one canonical narration script and one cue ID per utterance, with role, source audio, revision and duration. Generate short review samples before committing to full renders.
4. **Route cost and token spend**: prefer existing audio/video caches and local FFmpeg/code. Record actual `Tin/Tout/Ttotal` if provided, otherwise `UNKNOWN`. Never call paid/metered TTS, image, video or cloud APIs, upgrade a plan, or create a public release without separate scope/budget approval. Even when a source clip fails, re-synthesize only the affected sentence if authorized.
5. **Assemble source-complete audio**: before tempo/loudness processing, trim each audio **input** by original source timestamps. Reuse `scripts/story_video_gate.py trim-audio`. Validate every split's coverage through `audit`; reject source gaps, overlaps, missing tails and unexplained cuts. Do not fix a missing word by adding silent padding.
6. **Export both media variants**: make 1080p master (usually soft subtitle track plus a separate SRT) and 720p mobile (burned Chinese/English subtitles), with **one canonical approved narration mix** and synchronized cuts. Preserve unmodified prior outputs; create a new version directory for each revision.
7. **Mechanical QA**: copy `assets/project.template.json`, supply the paths and source splits, then run `python3 scripts/story_video_gate.py audit --config <project.json> --out <report.json>`. Check real dimensions/durations/codecs, source split coverage, caption boundaries, audible-signal windows, long-silence warnings, cross-resolution audio bitstreams, and exact file hashes. Use synthetic fixtures for tests; never upload source voice/sensitive assets to a public repo.
8. **Human perceptual QA**: compare **every spoken line** with its caption, especially phrase endings, tonal pronunciation, accidental omissions, repetitions, cadence, voice identity, sound quality, cuts, graphics and subtitles. An RMS-active window or absence of long silence **cannot** verify exact words. Record exact file hash, user approval and evidence reference separately for 720p and 1080p. Test on phone if mobile use is intended.
9. **Release gate and archive**: keep `HOLD` until language was chosen for this deliverable, technical gates pass, both required human acceptance scopes are evidenced, copyright/privacy is cleared, and user explicitly authorizes publication. User approval of preview ≠ permission to post publicly. Upload only approved deliverables; preserve source, QC report, manifest, reviewer decisions and recoverable checkpoints.

## Tools

- Run `scripts/story_video_gate.py --help`, `trim-audio --help`, or `audit --help` for CLI options. FFmpeg and FFprobe must be installed locally. No API keys are needed.
- Read [references/gates.md](references/gates.md) whenever diagnosing missing speech, deciding whether a version is accepted, or authorizing release.
- Use [assets/project.template.json](assets/project.template.json) as a starting project manifest. Do not present template approvals as real user approvals.
- For Papermorph animation, use `.claude/skills/papermorph/SKILL.md` plus its `references/stories.md`, `references/sound.md` and `references/site.md`, and Chinese bilingual/token references if applicable.

## Failure and state discipline

- Report per-check `PASS`, `FAIL`, `REVIEW`, `UNKNOWN`, or `NOT_TESTED`; distinguish missing prerequisites from a failing check.
- Stop at `HOLD` if media, captions, source clips, approval evidence or permission is missing.
- A feature-branch/PR submission is a **reviewable code handoff**; it does not itself install the skill for every account/session, deploy a video or alter production. Verify GitHub commit/branch and PR separately.
