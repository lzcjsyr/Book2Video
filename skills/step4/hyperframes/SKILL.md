---
name: embedded-hyperframes
description: Built-in HyperFrames guidance for AIGC_Video Step 4 dynamic segment rendering.
---

# Embedded HyperFrames Skill

HTML is the source of truth for video. Each segment is a standalone HyperFrames
composition rendered to `segment_i.mp4`.

## Hard Rules

- Use `data-composition-id`, `data-width`, `data-height`, `data-duration`, and `data-track-index`.
- Build the final visible layout first, then animate with GSAP.
- Layout Before Animation: static CSS positions are the ground truth.
- Never write outside the current segment work directory.
- Never modify `core/`, `text/`, `voice/`, or other project source files.
- Generate one `index.html` for the current segment only.

## Segment Contract

The caller provides JSON variables including:

- `segmentIndex`
- `title`
- `content`
- `durationSeconds`
- `width`
- `height`
- `stylePreset`
- `keywords`
- `descriptionSummary`

The composition must fit exactly within `width` x `height` and last
`durationSeconds` seconds.
