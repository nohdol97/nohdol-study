---
name: study-video
description: Turn an explicitly selected lecture or technical video into a durable study note using a captions-only first pass, immutable transcript capture, claim verification, and a conditional frame check only when a named question needs the screen. Use when the user asks to study, 노트화, or learn from a video. This is explicit-use only because the frame check downloads the video and transcription may transmit audio.
---

# study-video — Two-pass video learning

## Why

Full-video frame sampling is expensive, while transcripts omit diagrams and
demonstrations. A transcript-first pass spends visual attention only where it
improves understanding and keeps transcription data transfer explicit.

Frames earn their cost by settling a question, not by illustrating a note. The
split that matters is between a picture a reader looks at and a check a writer
performs: the first belongs in the vault only when the claim is about
appearance, and the second belongs in the evidence table as a sentence. Getting
this backwards is what makes the visual pass expensive - a routine second pass
downloads the whole video, and the frames then sit in the vault carrying a
finding that prose already stated.

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
5. Pass 2 is **conditional, not routine**. `--detail transcript` alone downloads
   captions only; adding `--timestamps` pulls the whole video file, so a pass
   that produces no finding costs a full download for nothing. Run it only when
   the transcript raises a question the screen can settle - the speaker cites a
   measurement, a number, a comparison, or says "look here" - and name that
   question before running:

```sh
python3 WATCH_SKILL/scripts/watch.py SOURCE \
  --detail transcript --timestamps T1,T2,T3 --no-whisper \
  --out-dir _workspace/study-video/SLUG-pass2
```

   Do not request a range wider than the specific moments in question. Frames
   are not free and a wide sweep re-creates the cost this two-pass split exists
   to avoid. `--download-sections` is not a fix: a clipped file starts at zero,
   so frame extraction at original timestamps would silently grab the wrong
   moment.

6. Save an immutable timestamped transcript snapshot under
   `vault/raw/videos/DATE-SLUG-transcript.md`, including the source URL, title,
   capture date, caption language, and whether transcription was used.
   YouTube auto-captions roll, so each line repeats in the next cue: drop the
   repeats and group the remainder into timed paragraphs before saving, or the
   snapshot is several times its real length. Auto-captions also mistranscribe
   proper nouns heavily (`epoll`, `Pub/Sub`, `RESP`, `NVMe` all come back
   wrong). Record the corrections you relied on in a table at the top of the
   snapshot and leave the transcript text itself unedited - it is raw material.
7. Do not copy frames into the vault. A frame is how a claim was checked, not
   the evidence itself, and what the check established survives as a sentence:
   "the 6x figure appears only as a bar chart with no axis, unit, or measurement
   condition" carries the finding, while the image carries it only to a reader
   who opens it and repeats the reading. Write that sentence into the note's
   evidence table with its timestamp, and let the frames go with the work
   directory. Keep an image only when the note's claim is about what something
   looks like and prose genuinely cannot stand in - a diagram being explained,
   not a number being audited.
8. Use `note-writer` for the study note. Link timestamps and the transcript
   snapshot. Separate "the speaker says" from "the claim is externally
   supported"; verify material factual claims independently. When a pass 2
   check ran, record what the screen did or did not show - a check that found
   nothing is a result and belongs in the evidence table.
9. Update index, log, and hot context.

The installed watch downloader must request `ko.*,en.*` captions in that order.
`study-install` verifies and reapplies this patch after watch updates.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Frame cost | Broad sampling | Captions only by default; the video downloads only when a named question needs the screen |
| What frames leave behind | Images in the vault, finding unread until someone opens one | The finding as a sentence in the evidence table |
| Privacy | Whisper may run as fallback | `--no-whisper` unless explicitly approved |
| Accuracy | Speaker claim treated as fact | Speech and external evidence separated |
