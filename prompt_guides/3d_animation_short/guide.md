---
name: 3d-animation-short-prompt-guide
description: |
  Create complete stylized 3D animated shorts from a story idea through an ordered production workflow covering project brief, story outline, character and environment cards, standardized shot planning, text or optional pencil storyboards, video-model selection, single-shot generation, assembly, BGM matching, and final review. Use when the user wants an end-to-end narrative animation workflow with strong character consistency, scene continuity, timing, camera, performance, and audio control. Not for single images, simple edits, photorealistic live action, or one standalone clip.
---

# 3D Animation Short Generator

Use this Prompt Guide for a complete story-first animated short prompt, from a one-line idea through story, character, environment, shot, camera, performance, continuity, and audio planning.

Core rule: **story first; use the node's aspect ratio, duration, mode, and connected-reference context; build a six-column standardized shot table with per-second directives, audio cues, and a spatial anchor chain; then produce one coherent H3 prompt with exact character, environment, continuity, camera, performance, dialogue, sound, and music instructions. The final video must contain no storyboard artifacts.**

## Global Visual Style Lock

Unless the user explicitly requests another visual style, all character cards, scene cards, shot tables, text storyboards, optional pencil storyboards, single-shot video clips (regardless of which video model is selected), assembled videos, and final composites must use this visual style:

- Rendering style: Pixar-inspired 3D cartoon rendering, C4D + Octane renderer look, high-end animated feature quality.
- Character design: exaggerated geometric simplification balanced with excellent material detail. Avoid 100% realistic human anatomy; use high-level shape language, large readable silhouettes, and Q-version proportions when appropriate.
- Proportion language: friendly stylized proportions, often 2.5–3 head-tall for cute or childlike characters, with big heads, compact bodies, clear silhouettes, and high recognizability.
- Hair / fur: combine strong sculpted clumps and clean block shapes with fine edge flyaway hairs or fuzzy rim details, so hair/fur feels designed but tactile under light.
- Skin / material: warm subsurface scattering skin quality, soft translucent reddish light through ears, cheeks, nose, and fingertips; avoid hard plastic skin.
- Acting style: exaggerated, lively Disney/Pixar-style character animation performance with squash and stretch, strong brows, eye corners, pupils, lips, and cheek shape changes.
- Motion style: high-energy poses, clear line of action, forward lean, strong anticipation, fast but readable timing, elastic body mechanics, and vivid micro-expressions.
- Emotional range: balance cuteness and explosive expressiveness; intense emotions may use dramatic facial deformation while preserving character appeal.

Negative style constraints: no photorealistic live-action, no flat 2D anime, no plastic toy skin, no stiff mannequin posing, no realistic anatomical stiffness, no lifeless facial expressions.

## STEP 0: Intake and Format Context

Capture:

- One-line idea or rough premise
- Desired output: blueprint only, assets only, standardized shot table with per-second directives, single text storyboards document (default) + extracted single-shot text storyboard nodes for heavy-iteration shots + multi-panel pencil storyboards (opt-in), single-shot video clips (with video model chosen in Step 7), assembled main video, or final BGM-composited film
- Approximate length, if the user already stated it
- Screen size / aspect ratio, if the user already stated it
- Visual tone: default warm stylized 3D animation
- Dialogue requirement: whether the film has dialogue, voiceover, or no speech
- Dialogue language only if the user explicitly states it; do not default to English dialogue

Use the aspect ratio and total duration supplied by the node. Reuse them consistently in shot timing, transition continuity, per-second directives, dialogue timing, sound design, music planning, and final composition.

## STEP 1: Project Brief

Produce a concise project brief.

Include:

- Working title
- One-line What-if
- Emotional premise
- Target audience feeling
- Main deliverables planned
- Approved screen size / aspect ratio
- Approved total duration
- Dialogue mode and language: only use a specific language when the user explicitly requested it; otherwise write `language not specified` and keep dialogue minimal or ask later when needed
- Initial risks
- Dialogue intent when present

## STEP 2: Story Outline and Gates

Create a story outline.

Include:

- Protagonist Want / Need / Flaw
- Core world rule
- 8-beat causal story spine
- Emotional anchor and payoff
- Dialogue beats if the user requested dialogue
- Red-line checks

Gate checks:

- Protagonist is active
- Crisis is intensified by protagonist flaw
- Coincidence never solves the problem
- Ending reuses an earlier emotional anchor
- Antagonistic pressure is not a flat villain
- Dialogue reveals relationship change instead of explaining the theme

## STEP 3: Character Cards

Define character reference cards in this recommended order:

1. Protagonist card
2. Contrast / pressure character card
3. Optional supporting character card

Each character card should be a 16:9 production reference sheet when possible. Unlike final rendered video, character cards should include clear readable labels so downstream generation can bind the correct person and props:

- Character name label in English and/or the project language
- Role label, such as protagonist, grandma, thief, sidekick, pressure character
- Main 3/4 view
- Front / side / back views
- Expressions
- Material / costume / prop details
- Important prop labels, such as handbag, wallet, skateboard, apple basket, scarf, shoes, glasses
- Identity lock repeated in the prompt
- A short visual-ID note listing age range, body type, hairstyle, outfit colors, signature props, and do-not-change traits

For stylized 3D animation, keep the character soft, readable, and consistent across later images and videos.

Treat the defined character identity, costume, proportions, colors, and signature props as locked continuity anchors throughout the prompt.

## STEP 4: Scene Cards

Define scene reference cards after character cards. Scene cards must show environments only: do not include characters, people, crowd figures, silhouettes, hands, faces, or character cameos. Character action belongs in the shot table, single-shot multi-panel pencil storyboards, and single-shot video clips, not scene cards.

Include:

- Main environment overview
- Key light states, such as day / night
- Emotional sub-spaces
- Continuity landmarks (fixed objects whose screen position must persist across shots in the same scene, e.g. kitchen island, sofa, door frame, tree, mailbox)
- Important props in the environment

Treat the chosen environment layout, lighting state, continuity landmarks, and prop positions as locked spatial anchors throughout the prompt.

## STEP 5: Standardized Shot Table Video Prompts (Six Columns)

After character cards and scene cards are locked, output standardized video prompts as a shot information table. This step is mandatory and cannot be swapped with storyboard or video generation.

Required reference: read and follow `references/shot-table-spec.md` for the exact six-column schema, per-second directive requirements, table-wide rules, and mandatory Step 5.5 self-check.

Minimum runtime contract:

- Create a standardized shot information table named `标准镜头信息表` or `standard-shot-table`.
- Use exactly six columns: `Shot ID & Duration`, `Continuity Handoff`, `Reference Anchors (Spatial + Identity)`, `Hook Type`, `Shot Description (Per-Second Directives)`, `Audio & Dialogue Track`.
- Every row must include complete per-second directives, continuity handoff, reference anchors, hook type, and audio/dialogue timing.
- Run the Step 5.5 self-check from `references/shot-table-spec.md` before storyboarding. Do not enter Step 6 until the self-check passes.

## STEP 6: Text Storyboards Document (Default) + Pencil Image Storyboards (Opt-in)

After the Step 5.5 self-check passes, use the text-storyboard structure before writing the final H3 prompt.

Required reference: read and follow `references/storyboard-guidelines.md` for the authoritative text-storyboard structure, optional visual-storyboard rules, shot-level detail, and visualization fallback rules.

Minimum runtime contract:

- Default mode is one authoritative text storyboards document containing one section per shot.
- Pencil storyboard images are opt-in visualization artifacts only; they never override the text storyboard.
- Extract a shot into a standalone text node only when the user flags that shot for heavy iteration.
- Step 7 must read the matching text storyboard section or extracted standalone node, not the pencil image.

## STEP 7: H3 Single-Shot Prompt Preparation

Required references:

- Read `references/model-selection.md` for the H3 default, Seedance 2.0 fallback, per-shot mixed mode, resolution choices, and model-specific prompt shaping.
- Read `references/fallback-policy.md` for per-model retry ladders, drift handling, and escalation choices.

Minimum runtime contract:

- H3 is the recommended default model.
- Seedance 2.0 is the fallback for high-stakes animation performance or repeated H3 failure.
- Per-shot mixed mode is allowed only when the shot table marks the model per row; unmarked rows default to H3.
- Strip all storyboard-only labels before video render.
- Bind each clip to the approved text storyboard section, exact character cards, and exact scene card.
- If a clip drifts from the approved `Reference Anchors`, follow `references/fallback-policy.md`; do not silently assemble incorrect clips.

## Boundaries

Do not use this Skill for a single image, a simple edit, a single clip animation, logo design, or pure prompt consultation. If the user only wants a prompt, use a video prompt workflow instead. If the user only wants a character card, use a character breakdown workflow instead.
