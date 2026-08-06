# ComfyUI-MiniMaxH3-Easy

[中文说明 / Chinese documentation](README_CN.md)

`ComfyUI-MiniMaxH3-Easy` integrates MiniMax H3 text-to-video, image-to-video,
and reference-to-video generation into one streamlined ComfyUI workflow surface.
The interaction layer has been deliberately polished to make media input,
reference selection, and prompt editing simple to understand and quick to use.

The idea is simple: keep the power of ComfyUI, while removing the repetitive
media wiring and reference bookkeeping that normally make MiniMax H3 workflows
hard to read and harder to learn.

## Highlights

### One `Media` input for mixed media

The main node uses one visible `Media` input for images, videos, and audio.
Multiple links can enter the same port. Image, video, and audio order numbers
are tracked independently, and each media type has its own wire color and
preview style.

<p align="center">
  <img src="images/mixed-media-input-en.png" alt="Mixed media input" width="560">
</p>

This keeps the graph compact without losing ordering information. Drag from
`Media` to an empty area of the canvas to quickly create a compatible media
node. Click the number in the middle of a virtual media wire to open the small
delete menu.

<p align="center">
  <img src="images/quick-create-node-en.png" alt="Quick-create media node" width="460">
</p>

### A complete `@` reference editor

`@` is available in **Reference Video** mode. Type `@` to select a connected
image, video, or standalone audio resource. The popup presents images first,
videos second, and audio last, with a preview for each item.

<p align="center">
  <img src="images/mention-popup-en.png" alt="Reference popup" width="320">
</p>

<p align="center">
  <img src="images/reference-editor-en.png" alt="Reference editor" width="720">
</p>

References use **By index** by default because it is concise and easy to scan.
**By filename** is available when the filename itself is more meaningful.

The chips are an editing interface only. When the workflow runs, the node
automatically converts them into the reference format recommended by MiniMax,
including `<Picture N>`, `<Video N>`, and `<Audio N>`. Users do not need to
manually write or maintain those tags.

A video's synchronized soundtrack is handled together with that video. A
standalone audio input remains an independent reference, so users only need to
connect the media they actually want to use.

### Simple dialogue blocks

Type `#` in the prompt editor to insert an editable dialogue block.

<p align="center">
  <img src="images/dialogue-block-en.png" alt="Dialogue block" width="560">
</p>

- Press `Enter` to finish the block.
- Press `Shift+Enter` to add a line break inside it.
- Click the block at any time to edit it again.

The block is automatically converted to MiniMax's recommended dialogue format
`<d>...</d>` when the prompt is sent. The rest of the prompt stays ordinary
prompt text, so users can describe the scene naturally without learning the
underlying markup.

### H3 prompt optimization

The main node includes an **Optimize prompt** switch. It can use any
OpenAI-compatible `chat/completions` API to expand a short idea into a
MiniMax H3 audiovisual prompt. The switch is a native BOOLEAN node input. When
enabled, the Python node optimizes the prompt inside `generate()` before creating
H3 conditioning. It selects one of two hard-coded system prompts
from the node's top-level mode: `IMAGE_SYSTEM_PROMPT` for `image`, and
`REFERENCE_SYSTEM_PROMPT` for `reference`, while preserving every `@` reference
in Reference Video mode. Both complete prompt constants live in
`prompt_optimizer.py`.

Before first use, configure these instance-wide values under
**MiniMaxH3Easy → PromptOptimizer** in the ComfyUI settings panel:

- `Base URL`, for example `https://api.openai.com/v1`;
- `Model`, using the model ID supplied by the provider;
- `API Key`, which may be empty for an unauthenticated local compatible API;
- video transport: `Auto`, `Native`, or `Sampled frames`;
- audio transport: `Auto`, `input_audio`, or `Video wrapper`.

The backend stores these values in `user/__minimax_h3_easy/`. The API key field is
always shown blank; the settings page reports whether a key is configured and
provides a clear action. `GET` responses never contain the key. Base URL, model,
and key can instead be supplied with `MINIMAX_H3_OPTIMIZER_BASE_URL`,
`MINIMAX_H3_OPTIMIZER_MODEL`, and `MINIMAX_H3_OPTIMIZER_API_KEY`; environment
variables take priority. Optimizer configuration is never placed in `/prompt` or
queue history. This is instance-wide configuration shared by every workflow and
user of the same ComfyUI server, so only trusted administrators should manage it.

The request reads the node's actual multimodal inputs in Python. Native video is an
in-memory H.264/AAC MP4 with its frame rate and synchronized soundtrack preserved,
scaled to a 720-pixel longest edge. Sampled mode attaches three representative
frames. Audio can use `input_audio` or an in-memory 512×512 waveform MP4 wrapper.
`Auto` starts with native video and `input_audio`; only a 400/415/422 response that
explicitly says `video_url` or `input_audio` is unsupported triggers one fallback
request. Explicit modes and ambiguous errors never retry.

Each binary attachment is limited to 24 MiB and the total Base64 payload to 40
million characters. Responses use SSE streaming when supported and also accept a
non-streaming JSON response. The node progress is an estimate based on accumulated
UTF-8 bytes divided by four and the selected maximum-output-token limit; it reaches
at most 95% while reading and 100% on clean completion. `Short`, `Medium`, and
`Long` send 1024, 4096, and 8192 `max_tokens`; Custom accepts 256–32768 and falls
back to 4096 when invalid.

## Nodes and connections

### MiniMax H3 Easy Loader

The four-in-one loader exposes separate choices for:

- FL2VA model;
- Ref2VA model;
- Qwen3-VL text encoder;
- video VAE;
- audio VAE.

Official and common community filename variants are recognized, including
BF16, FP8, INT8, INT4, NVFP4, NF4, and GGUF releases.

### MiniMax H3 Easy

This is the main generation node. Its existing first two output slots are unchanged,
with two text outputs appended:

- `Model` — connect this to a model-only LoRA, Sage Attention patch, or directly
  to the sampler;
- `H3 Context` — connect this to **MiniMax H3 Easy Output**.
- `Optimized prompt` — the actual optimized text, or the original prompt when
  optimization is disabled;
- `Reasoning content` — reasoning returned through `reasoning_content`, `reasoning`,
  or `reasoning_details`, otherwise empty.

Optimization failures are execution errors and never return a partial prompt.
Older API workflows that omit `optimize_prompt` continue to execute with it disabled.

### MiniMax H3 Easy Output

This node expands `H3 Context` into the standard workflow outputs:

- Conditioning;
- Latent;
- Video VAE;
- Audio VAE;
- FPS.

The sampler, acceleration nodes, video/audio processing, and save nodes remain
outside the main node so the workflow stays compatible with the rest of
ComfyUI.

## Modes

### I2V or First/Last Frame

- No media connected: text-to-video.
- One image connected: image-to-video.
- Two images connected: first/last-frame generation.
- Video and audio links are not accepted in this mode.

### Reference Video

- Up to nine reference images, three reference videos, and three standalone
  audio clips.
- The `@` editor is enabled.
- Reference order and prompt references are kept synchronized automatically.

## Parameter design

### Resolution and aspect ratio

Resolution presets follow the MiniMax H3/ComfyUI megapixel-style budgets:

`360P`, `416P`, `480P`, `540P`, `640P`, `720P`, `768P`, `832P`, `928P`,
`1024P`, `1080P`, and `Custom`.

Presets calculate the canvas from the selected aspect ratio and align the final
dimensions to multiples of 32. Available ratios are `1:1`, `2:3`, `3:2`, `3:4`,
`4:3`, `9:16`, `16:9`, and `21:9`.

Selecting `Custom` reveals width and height and hides the aspect-ratio control.
Custom width and height must be multiples of 32.

### Duration

Duration is set in seconds from **4 to 20**. The requested duration is aligned
to MiniMax H3's frame rules internally.

### Advanced options

Advanced options are off by default. When enabled, they reveal:

- first/last-frame setup in I2V or First/Last Frame mode;
- reference image size in Reference Video mode;
- `@` display mode in Reference Video mode.

Reference images use a short-edge limit of **1K** or **2K**. Images below the
limit keep their original resolution; larger images are resized proportionally
instead of being forced down to the output video's resolution.

## Installation and models

Install this directory as:

```text
ComfyUI/custom_nodes/ComfyUI-MiniMaxH3-Easy
```

Place models in the standard folders:

```text
ComfyUI/models/diffusion_models/
ComfyUI/models/text_encoders/
ComfyUI/models/vae/
```

For `.gguf` transformer or text-encoder files, install
[ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) and restart ComfyUI.
GGUF files are routed automatically to their GGUF loader; regular safetensors
files continue to use native ComfyUI loading.

## License and attribution

This project is released under the [MIT License](LICENSE). 

If you reference, reuse, or adapt a substantial part of this project, please
credit the original author and mention `ComfyUI-MiniMaxH3-Easy` in your project
documentation.

Please do not present the project's multi-media input design, `@` reference
editor, dialogue-block conversion, or related implementation as entirely your
own work.

## Important notes

- I2V or First/Last Frame mode accepts at most two images.
- Reference Video mode accepts at most nine images, three videos, and three
  standalone audio clips.
- A video's synchronized audio is paired with that video automatically and does
  not consume a separate audio slot.
- Image, video, and audio numbering is independent.
- The node supports both the legacy ComfyUI canvas and Nodes 2.0.
- Chinese browsers show Chinese parameter labels; other browsers show English
  labels.
- Model-only LoRA and attention/acceleration patches connect after the main
  node's `Model` output.
