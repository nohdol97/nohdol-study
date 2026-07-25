---
name: study-video
description: Turn an explicitly selected lecture or technical video into a durable study note using a transcript-first pass, focused timestamp frames, immutable transcript capture, and claim verification. Use when the user asks to study, 노트화, or learn from a video. This is explicit-use only because frames cost tokens and transcription may transmit audio.
---

# study-video — Two-pass video learning

## Why

Full-video frame sampling is expensive, while transcripts omit diagrams and
demonstrations. A transcript-first pass spends visual attention only where it
improves understanding and keeps transcription data transfer explicit.

## Safety gate

This workflow is explicit-use only. Native captions are preferred. Always pass
`--no-whisper` unless the user explicitly approves sending that video's audio
to the configured Groq or OpenAI transcription service. Corporate or sensitive
recordings remain captions-only or frames-only.

## Procedure

1. Locate the installed `watch/SKILL.md` and its sibling `scripts/watch.py`.
2. Run its setup check. Confirm `yt-dlp`, `ffmpeg`, and `ffprobe`.
3. Pass 1 — low-cost structure:

```sh
python3 WATCH_SKILL/scripts/watch.py SOURCE \
  --detail transcript --no-whisper \
  --out-dir _workspace/study-video/SLUG-pass1
```

4. Read the timestamped transcript. Identify:
   - section boundaries and central explanations;
   - visually dependent moments ("look here", diagrams, demonstrations);
   - claims that require evidence outside the video.
5. Pass 2 — focused visual evidence. Reuse the downloaded local file when
   available and request only important ranges or timestamps:

```sh
python3 WATCH_SKILL/scripts/watch.py LOCAL_VIDEO \
  --detail transcript --timestamps T1,T2,T3 --no-whisper \
  --out-dir _workspace/study-video/SLUG-pass2
```

6. Save an immutable timestamped transcript snapshot under
   `vault/raw/videos/DATE-SLUG-transcript.md`, including the source URL, title,
   capture date, caption language, and whether transcription was used.
   YouTube auto-captions roll, so each line repeats in the next cue: drop the
   repeats and group the remainder into timed paragraphs before saving, or the
   snapshot is several times its real length. Auto-captions also mistranscribe
   proper nouns heavily (`epoll`, `Pub/Sub`, `RESP`, `NVMe` all come back
   wrong). Record the corrections you relied on in a table at the top of the
   snapshot and leave the transcript text itself unedited - it is raw material.
7. Copy only pedagogically useful frames to
   `vault/wiki/assets/SLUG/`. Record timestamps in filenames or captions.
8. Use `note-writer` for the study note. Link timestamps, transcript, and
   frames. Separate "the speaker says" from "the claim is externally
   supported"; verify material factual claims independently.
9. Update index, log, and hot context.

The installed watch downloader must request `ko.*,en.*` captions in that order.
`study-install` verifies and reapplies this patch after watch updates.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Frame cost | Broad sampling | Transcript-guided timestamps |
| Privacy | Whisper may run as fallback | `--no-whisper` unless explicitly approved |
| Accuracy | Speaker claim treated as fact | Speech and external evidence separated |
