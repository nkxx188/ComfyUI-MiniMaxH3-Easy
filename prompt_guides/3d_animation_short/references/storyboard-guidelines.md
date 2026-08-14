# Text and Pencil Storyboard Guidelines

## STEP 6: Text Storyboards Document (Default) + Pencil Image Storyboards (Opt-in)

After the Step 5.5 self-check passes, use one authoritative text-storyboard document containing all shot storyboards as in-document sections. It mirrors the half-narrated-drama storyboard structure: per-shot fields (title / hook / scene / characters / spatial anchors / continuity / performance) plus Pixar's per-panel four-quadrant content and optional ASCII layout. Optional visual-storyboard descriptions may supplement it for pose and silhouette checks, but they never override the text storyboard.

Store the chosen storyboard mode in the Project Brief and reuse it in Step 7, Step 9, and the Regeneration discipline.

### Default path: single text storyboards document

Create one text-storyboards document named `<title> text storyboards` for the whole short. This document is the authoritative H3 prompt reference. Every shot is a section in the same document so cross-shot continuity remains explicit.

Document top matter (header block at the top of the document):

- Project title, approved video model, approved resolution, storyboard mode, and self-check status (e.g. `shot-table self-check: passed at <timestamp>`).
- A short table-of-contents listing every shot, its hook, and its section anchor (`S01`, `S02`, …) so the user can jump.

Per-shot section structure (one `##` heading per shot, in shot order). Every section must contain these fields, in this order — direct adaptation of the half-narrated-drama storyboard:

1. **Shot title & duration** — short human-readable title for the shot, plus `S<N> / <duration>s` (e.g. `S03 / 6s`).
2. **Hook type** — one of the controlled vocabulary: `setup` / `visual-joke` / `reversal` / `reveal` / `callback` / `suspense` / `tender` / `chase` / `expression-beat` / `climax`. Used by the per-episode hook distribution self-check.
3. **Scene & characters** — exact scene card name and exact on-screen character names (binding to character cards).
4. **Spatial anchor card** (mandatory, four sub-fields — directly adapted from half-narrated):
   - `Fixed landmarks` — named landmarks and their screen-relative positions (e.g. `door-frame: right third`, `kitchen-island: center bottom`).
   - `Character positions (camera view)` — for every on-screen character, screen-relative position, facing direction, and initial pose.
   - `Exited character status` — characters who were on screen in the previous shot but not in this one, with their off-screen position and reason.
   - `Lighting baseline` — inherited key/fill/rim direction from the scene card, plus per-shot modifier.
5. **Continuity** (mirrors half-narrated's handoff fields):
   - `Continuity from S(N-1)` — one or two sentences referencing the previous shot’s ending state.
   - `Continuity to S(N+1)` — one sentence setting up the next shot’s opening.
6. **Double-binding** — `[char:角色名-01] [char:角色名-02] ... [scene:场景名] [hook: visual-joke]` — exact character card names, scene card name, hook type. These are storyboard-only reference markers; the video model strips them at render time.
7. **Per-panel four-quadrant content** (one block per panel, in time order; this is the Pixar per-second directive, kept verbatim from the table row):
   - `Timecode` — e.g. `0–1s`.
   - `Pose + Expression` — concrete body posture, silhouette, key prop grip, eye-line, facial expression path; for elastic beats, explicitly call out squash / stretch / anticipation / overshoot. This is the largest section per panel and is what the video model reads as the visual beat.
   - `Camera` — shot size, camera movement (push / pull / pan / tilt / handheld-shake / locked / orbit), Dutch angle note when applicable.
   - `Audio + Anchor` — audio cue (`♪ narration: ...` / `dialogue: ...` / `SFX: ...` / `silent`) and spatial anchor note (`door-frame: right third` / `Mia: center midground facing camera`).
   - Performance notes (mirrors half-narrated): for narration seconds, mark `narrator-mouth-closed: true`; for on-screen dialogue, mark `mouth-open: speaker` and describe expression path / eye-line / body-action changes.
8. **Layout rules** (apply per shot):
   - 3-second shot → 3 panels (1 per second).
   - 4-second shot → 4 panels.
   - 5-second shot → 5 panels.
   - 6-second shot → 6 panels.
   - 7+ second shot → one panel per second; for sub-second critical beats, add an extra mini-panel such as `2.0–2.5s` only when the beat is the hook of the shot.
   - Panels must cover the full shot duration from first frame to last frame with no time gaps.
9. **Per-panel binding**:
   - Bind the exact character cards listed in the table row to lock appearance, face, hairstyle, body proportions, costume, signature props, and role identity. Use the same character names as the table.
   - Bind the exact scene card listed in the row to preserve environment, props, landmarks, movement paths, and spatial logic.
10. **Optional ASCII layout block (highly recommended, free)**:
    - Append a small ASCII sketch per panel (or one combined sketch for the whole shot) so the user can scan the spatial layout in seconds without rendering an image. Example:
      ```
      [0-1s]  Mia (L, mid)         door-frame (R)
              ──kneels, hands on apple basket──
              cam: low push-in, locked
              audio: silent | anchor: basket center-bottom
      [1-2s]  ...
      ```
    - The ASCII block is informational only; the video model reads the structured `Per-panel four-quadrant content` above, not the ASCII.
11. **Storyboard-only markers**:
    - When a beat is critical, append `[BEAT]` after the panel timecode.
    - When a panel must handoff a specific state to the next panel or the next shot, append `[HANDOFF → ...]` with a short label such as `[HANDOFF → S04 opening]`.

Per-shot section template (copy-paste skeleton, valid for any shot):

```markdown
## S03 / 6s — Title: 奶奶把苹果筐递给 Mia

- **Hook type**: reveal
- **Scene & characters**: scene:kitchen | char:Mia, char:Grandma
- **Spatial anchor card**:
  - Fixed landmarks: door-frame (right third), kitchen-island (center bottom)
  - Character positions: Mia (L, midground, facing camera) | Grandma (R, foreground, facing Mia)
  - Exited character status: —
  - Lighting baseline: warm overhead key + cool bounce right
- **Continuity from S02**: 奶奶弯下腰从中岛拿起苹果筐
- **Continuity to S04**: Mia 接住筐转身，门铃响起
- **Double-binding**: [char:Mia] [char:Grandma] [scene:kitchen] [hook:reveal]

### Per-panel four-quadrant content

#### 0–1s
- Pose + Expression: 奶奶弯腰双手持筐；Mia 左侧站姿，眼神好奇
- Camera: locked medium shot, eye-level
- Audio + Anchor: silent | Mia: L midground | basket: center bottom
- Performance: [BEAT]

#### 1–2s
- Pose + Expression: 奶奶手臂伸向 Mia，筐倾斜；Mia 双手前伸准备接
- Camera: locked medium shot, eye-level
- Audio + Anchor: ♪ SFX: basket rustle | anchor: door-frame: right third
- Performance: [HANDOFF → S04 opening]

#### 2–3s
...

### ASCII layout (optional)
[0-1s]  Grandma (R, fg)        door-frame (R, bg)
        ──lifts basket──        Mia (L, mid)
        cam: locked | silent
[1-2s]  ...
```

After all sections are written, use the document as the source for Step 7.

### Shot-level extraction (heavy-iteration mode)

The default single-document form is optimized for reading and cross-shot continuity. When a specific shot needs heavier revision, isolate that shot's section while keeping the single document as the continuity source of truth:

1. Copy the full shot section into an isolated working section.
2. Keep its shot ID, timing, identity bindings, spatial anchors, and incoming/outgoing continuity unchanged unless the prompt explicitly revises them.
3. Reintegrate the revised content into the authoritative document before writing the final H3 prompt.

### Opt-in path: multi-panel pencil image storyboards (visualization mode)

When visual-storyboard detail is useful, describe one multi-panel pencil storyboard per table row in addition to the text document. The text storyboards document remains authoritative; visual panels are review-only.

For each pencil image storyboard:

- **Double-binding labels (top-right corner, mandatory on image)**:
  - `[char:角色名-01] [char:角色名-02] ...` — exact character card names used in this row.
  - `[scene:场景名]` — exact scene card name.
  - `[shot: S03] [dur: 6s] [hook: visual-joke]` — shot ID, duration, and hook type.
  - These labels are storyboard-only reference markers; they are stripped at video render time.
- Bind the exact character cards listed in that row to lock character appearance, face, hairstyle, body proportions, costume, signature props, and role identity.
- Bind the exact scene card listed in that row to preserve environment, props, landmarks, movement paths, and spatial logic.
- Convert every per-second directive in the row into one storyboard panel or one clearly labeled beat panel; for a 4-second shot, normally create 4 panels; for a 6-second shot, normally create 6 panels; for sub-second critical beats, add extra mini-panels only when needed.
- **Panel physical layout (mandatory)**:
  - 3-second shot → 1×3 strip.
  - 4-second shot → 2×2 grid.
  - 5-second shot → top row 3 + bottom row 2.
  - 6-second shot → 2×3 grid.
  - 7+ second shot → 3 rows, balanced panels.
  - Each panel occupies the same canvas area; do not let one panel dominate.
- **Per-panel four-quadrant content (mandatory)**:
  - Top-left: timecode (e.g. `0–1s`).
  - Top-right: pose + expression sketch (the largest area; the actual visual beat).
  - Bottom-left: camera icon + movement arrow (push/pull/pan/orbit/locked) and a tiny note for Dutch angle.
  - Bottom-right: audio cue (e.g. `♪ narration: "I knew it."` / `SFX: door creak` / `silent`) and anchor note (e.g. `door-frame: right third`).
- Arrange panels in reading order inside the same single-shot storyboard image; do not merge multiple different shots into one image.
- Each panel must mark its timecode, such as `0–1s`, `1–2s`, and show the corresponding pose, expression, action, camera movement, prop position, SFX cue, and continuity handoff.
- Output pure black-and-white pencil line-art only: no color, no final-render lighting, no polished 3D render.
- Mark the storyboard image with the shot number and include camera-movement icon / marker per panel when useful.
- Include storyboard-only marks when useful: pencil construction lines, action arrows, camera-path icon, timing marks, and small notes.
- Keep the draft as a video-render reference asset only, not final art.

### Storyboard generation failure fallback (visualization mode only)

If a pencil-image storyboard specification cannot maintain the required quality—for example the layout collapses, labels become illegible, panels merge, or character identity drifts—apply this correction order:

1. **First retry**: regenerate the same shot storyboard with a tightened prompt that explicitly mentions the four-quadrant layout, the `[char:…] [scene:…] [shot:…]` labels, and the per-panel content rules.
2. **Second retry**: drop the bottom-right audio/anchor quadrant text (keep it as a blank cell with a tiny `♪` mark) to reduce text load; this usually fixes illegible labels without losing the visual beat.
3. **Third retry**: reduce panel count by one (e.g. 6 panels → 5 panels by merging the two least-actionable seconds) and simplify camera icons to single arrows.
4. **Final fallback**: use a block-color pose layout for that shot, rely on the authoritative text storyboard alone, or split the shot into two shorter shots and re-run Step 5.5. If a connected reference image is available, bind it explicitly instead of inventing one.

In default text mode this whole fallback is unnecessary — text storyboards fail only when the model cannot produce coherent structured text, in which case return to Step 5 to revise the table row.
