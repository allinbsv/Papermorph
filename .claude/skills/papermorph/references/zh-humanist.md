# Chinese productions: human voice, honest thought

Use this with every Chinese lesson, picture book or documentary. This is a production standard, **not a claim that an AI voice is indistinguishable from a person**. The desired narrator has the patience of an experienced elder, the precision of a craftsperson and the humility of someone who knows how much remains unknown. Make an original voice; do not impersonate an identifiable person or fabricate quotes, memories or eyewitness experience.

## The editorial promise

1. **Begin with something tangible.** A lamp goes dark, a seed pushes through soil, a child asks a question. Only use a scene as observed fact when there is evidence for it; otherwise frame it as an illustration.
2. **Explain one real mechanism at a time.** Move from the concrete scene to the structure beneath it. The image should earn its place by clarifying the voice, not by decorating a vague claim.
3. **Keep knowledge and uncertainty separate.** Source facts, explicit calculations, analogy and inference must remain distinguishable. For technical or safety claims, preserve the exact applicable source, revision and conditions. The narration may say "我们还不知道".
4. **Write as a person talking to one person.** Give sentences breath; vary length. Let an ordinary detail carry emotion. A silence after a difficult truth can be more honest than orchestral music.
5. **Earn the ending.** Return to a scene or change the listener's understanding. Do not tack on an inspirational slogan or pretend every question is settled.

Avoid stock openings and conclusions ("在当今社会", "首先、其次、最后", "综上所述", "让我们一起", "赋能", "不言而喻", "深刻揭示"). These are review signals, not unconditional banned words. Remove unearned grandeur, repeated rhetorical questions, fake intimacy and invented personal testimony. No factual claim may become more certain simply because the voice sounds wise.

## Chinese text and narration

- Set `<html lang="zh-CN">` (or `zh`), `CHAPTER.language = 'zh'`, and keep the audio folder and `narration.zh.json` consistent. The existing player translates interface strings for Chinese; it does not translate the book's content.
- Start with a Mandarin Edge voice for zero added TTS service cost, for example `zh-CN-YunxiNeural` as a **candidate**, not an approved voice. List available voices and have the user compare samples of the actual script. The script's rhythm, pauses and pronunciation matter more than its advertised voice name.
- Use short spoken beats; change pace between reflection and explanation. Put `[[mark]]` just before the phrase that drives a visual change; check generated word timestamps against the actual audio. A passing script check does not prove synchronization.
- Write Chinese subtitles independently of English typography. Verify all punctuation, line breaks, text clipping, stroke contrast and mathematical notation on Android and desktop. The documentary kit contains Latin-only bundled fonts; add a properly licensed CJK font or test an explicit CJK fallback stack before delivery.
- Avoid foreign-language TTS alignment assumptions: `eleven.py` documents an English word-splitting limitation, so start Chinese films with `tts.py` and verify Edge word-boundary output. A local Chinese-capable voice is an option only after availability, licence and timing are tested.
- No unauthorized cloning of a real person's voice. Use a warm, unhurried original Mandarin narration. If synthetic speech still sounds mechanical, revise text and prosody, or arrange an actual human recording; label which was used.

## Editorial gates — record actual evidence

Before approving the pilot, record in the chapter review notes:

| Gate | Required check |
|---|---|
| Source | Every consequential fact is supported, scoped and traceable; analogy is labelled |
| Script | A human reads aloud and removes clichés, exaggeration and unsupported certainties |
| Voice | A human listens to the complete audio for pronunciation, pacing, emotion and awkward pauses |
| Picture | Each scene explains the spoken idea; no mislabeled object, contradicting motion or invented footage |
| Sync | Captions and timed actions match the audio on mobile and desktop |
| Consent | Rights for images, music, text and voices are recorded; publication scope is approved |

Use `python3 SKILL/scripts/zh_review.py path/to/narration.zh.json --style books/<book>/style.json` before human review. It reports structural failures and possible writing clichés, **not** quality certification. The pilot remains `HUMAN_REVIEW_PENDING` until someone actually watches and listens. Record their comments in `books/<book>/chapters/chNN.md`, then update `style.json` only for preferences explicitly approved.

## Good first pilot

A two-minute explanation of one commonplace question is enough to test the voice, visuals and sincerity. A script should contain a precise question, one concrete example, the mechanism, a limit to what is known, and an earned ending, without mechanically repeating this sequence in later chapters. Prefer one excellent sample to many unreviewed chapters.
