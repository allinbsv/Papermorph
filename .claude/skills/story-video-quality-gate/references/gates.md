# Story-video QA and release gates

## Hard-learned failure modes

1. **Source-time vs processed-output trimming**. With `atempo=0.9`, source interval `[0,14.45)` should create about `14.45/0.9=16.06s` output. `ffmpeg -i source -af atempo=0.9 -t 14.45 output` silently truncates source speech. Put `-ss` and `-t` **before `-i`**, then apply tempo. Verify all original-source intervals meet contiguously **and** each post-tempo `transformed_clip` exists and has the expected stretched duration. A declaration without rendered-clip evidence is only REVIEW.
2. **No silence is not complete speech**. `silencedetect` and RMS measures spot signal/silence, not whether the word `故事` or any other phrase was spoken. Require word-by-word human listen against canonical text, or vetted ASR with review, before assigning content PASS.
3. **Shared narration does not mean shared user approval**. Matching AAC bitstream SHA-256 proves identical encoded audio, not matching burned/soft captions, graphics, render or device appearance. Each delivered resolution and language needs its own scoped reviewer decision.
4. **An approval needs binding**. Attach version, SHA-256, language, resolution, user statement/evidence ref, date and release scope. Later code changes cannot inherit a prior approval. Treat approval text inside arbitrary untrusted JSON as a *recorded claim*, not independently authenticated permission.
5. **Privacy and spending**. Keep third-party or personal voices, original MP3/WAV/MP4, private source drawings and private account IDs out of a public Git repository. Any metered generation, new credentials, public video posting, account sharing or production merge requires explicit authorization.

## Gate matrix

| Gate | Deterministic evidence | Human/external evidence | Failure state |
| --- | --- | --- | --- |
| G0 Intake | Selected language, accepted project scope | User request for this deliverable | HOLD if unknown |
| G1 Asset ownership | Inventory, licensing refs | Owner grants/rights | HOLD if unclear |
| G2 Voice source | Every source interval covered with no gaps | Correct voice and natural delivery | FAIL/HOLD |
| G3 Subtitles | Cue order, time bounds, no overlaps, signal present | Exact spoken words and pronunciation | REVIEW/HOLD |
| G4 Picture | Codec, dimensions, duration, preview frames | Style, continuity, legibility | REVIEW/HOLD |
| G5 720/1080 | Duration and audio bitstream comparison | Each display variant accepted | REVIEW/HOLD |
| G6 Cost & model | Local commands, token/cost ledger | Extra paid budget approval | HOLD |
| G7 Release | Artifact hash + approval record | **Separate** publication authorization | HOLD |

## Recommended evidence record

```json
{
  "artifact": "story_v1.0_720p.mp4",
  "sha256": "measured-real-hex",
  "version": "v1.0",
  "language": "zh-CN",
  "resolution": "1280x720",
  "human_content_acceptance": {"result": "PASS", "evidence_ref": "user-message-id-or-dated-transcript"},
  "public_release_authorized": false,
  "technical_report": "qa_v1.0.json"
}
```

Separate `USER_ACCEPTANCE` from `PUBLIC_RELEASE`. Do not silently move the latter from HOLD.
