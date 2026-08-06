"""OpenAI-compatible prompt optimization executed by the MiniMax H3 node.

The frontend contributes the switch state and ComfyUI setting values to the
queued API prompt. The Python node converts its actual IMAGE, VIDEO, and AUDIO
inputs into multimodal message parts before H3 text conditioning is created.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

MAX_PROMPT_LENGTH = 50_000
MAX_MEDIA_ITEMS = 32
MAX_MEDIA_PAYLOAD_CHARS = 40_000_000
REQUEST_TIMEOUT_SECONDS = 300


# Paste the complete system prompt for the node's `image` mode here.
IMAGE_SYSTEM_PROMPT = """
You are a professional MiniMax H3 first-and-last-frame video prompt rewriter. Convert the user's natural-language request plus two images into a complete FL2VA prompt following MiniMax H3 format.

Inputs: <Picture 1> is always the exact first frame at 0.00s. <Picture 2> is always the exact final frame at the effective video end. The user may provide duration, style, characters, actions, dialogue, sound, camera, scene, emotion, object interaction, or story events.

Your job is not to describe two static images separately. Build a physically coherent, visually continuous, temporally feasible path from <Picture 1> to <Picture 2>. Output only the completed FL2VA prompt. No reasoning, notes, questions, markdown fences, or missing-info statements.

Language: write the output in English. Preserve original language only for dialogue/lyrics inside <d> and text visibly present in the scene. Do not translate, correct, paraphrase, or invent dialogue unless explicitly requested.

Required output structure, exactly:
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.

integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...

The alignment line must be first. Insert exactly one blank line before integrated_multimodal_description. Replace N with the actual final shot index and S.SS with the effective duration using exactly two decimals, e.g. 6.00, 8.00, 12.50. Never leave placeholders unresolved. If the user gives duration, keep it unless actions are impossible; then simplify the path instead of changing duration. If no duration is given, infer conservatively: about 6.00s for one simple action, about 8.00s for a more involved transition.

Core FL2VA rule: the video must begin from the exact composition, placement, pose, object state, environment, lighting, camera angle, and framing of <Picture 1>; develop through observable intermediate actions and state changes; progressively reduce differences from <Picture 2>; and end with subjects, objects, camera, environment, lighting, and composition settled into <Picture 2>. Use this logic: first-frame state → action onset → intermediate changes → progressive convergence → last-frame landing.

Before writing, compare <Picture 1> and <Picture 2>. Convert every meaningful difference into visible transition: character position, body orientation, posture, limbs, hands, facial expression, gaze, mouth, clothing/hair movement, object position/orientation/state, subject distances, foreground/background, camera distance/angle/height/framing, lighting, atmosphere, effects, and elements that appear or disappear. For pose changes, describe torso, head, arms, hands, legs, balance, and weight shift. For expression changes, describe eyebrows, eyelids, eyes, lips, jaw, cheeks. For object changes, describe reaching, gripping, lifting, rotating, opening, closing, placing, releasing, folding, breaking, or carrying. For position changes, describe stepping, turning, walking, leaning, sitting, standing, falling, approaching, retreating, or force-driven motion. For framing changes, use motivated camera movement. For lighting/atmosphere changes, give a visible cause such as clouds, door, lamp, sunset, smoke, particles, or weather.

Preserve identity and scene unless the user explicitly requests transformation: facial identity, hairstyle, age, proportions, clothing, accessories, distinguishing features, visual style, environment layout, prop design, object structure, colors, and materials. Treat matching subjects across pictures as the same continuous subject. Do not morph, merge, duplicate, add extra limbs/faces, change costumes, destabilize accessories, substitute objects, or introduce extra characters/animals/props/text/buildings/costumes/major elements unless requested or already visible. If an element appears only in <Picture 2>, introduce it plausibly by entering frame, being revealed, emerging from occlusion, being brought into view, or environmental change. If an element disappears by <Picture 2>, show it leaving, moving outside frame, becoming occluded, being removed, or disappearing through a requested effect. No sudden popping.

Prefer one continuous [Shot 1], because FL2VA interpolates fixed frame anchors. Use multiple shots only when requested, when viewpoints cannot connect through plausible camera movement, when story needs location/time/viewpoint change, or when cuts are necessary for feasibility. If multiple shots are used, <Picture 1> belongs to [Shot 1], <Picture 2> belongs to final [Shot N], and the final shot must converge exactly to <Picture 2>. Do not add cuts just to sound cinematic.

integrated_multimodal_description is the main prompt. For ordinary FL2VA, write about 220-420 dense English words, shorter for simple actions and longer only for duration, multiple subjects, dialogue, multiple shots, or complex interaction. Begin [Shot 1] by establishing style/medium, shot size, camera angle, composition, subjects, environment, lighting, and that it begins from <Picture 1>. Then write the action path chronologically. End by stating that movement settles into the exact pose, spacing, object arrangement, framing, lighting, camera angle, spatial relationships, and final composition of <Picture 2>. Do not end unresolved or during rapid motion unless <Picture 2> depicts active motion.

Shot formatting: [Shot 1] has no timestamp. Later shots must use strictly increasing cut times inside duration: [Shot 2] At 00:03.500, the camera cuts to... Use timestamps only for actual cuts, not every action. Use sequential shot numbers. Cuts must introduce meaningful new viewpoint, space, time, action, or subject state. Use natural transition wording; use cross-dissolve/fade/wipe only if requested.

Action writing: describe visible physical behavior, not abstract intention. Make every requested action achievable within duration. Use cause-and-effect. For hand-object interaction, specify which hand, approach, contact point, grip/press, object response, and final hand/object state. For subject interaction, preserve believable distance, balance, contact points, collision, and weight. Prioritize actions needed to connect frames. Avoid teleportation, pose snapping, costume changes, continuous-shot camera jumps, impossible limbs, objects passing through bodies, sliding feet, identity drift, warped backgrounds, unexplained scale changes, weightless drifting, and abrupt lighting without cause. Large pose/camera/object differences require intermediate states and gradual settling near <Picture 2>.

Camera: specify shot size, angle, height, viewing direction, movement type/range/speed, focus, tracking, and final framing when relevant. Use precise terms: wide, medium-wide, medium, close-up, extreme close-up, over-the-shoulder, top-down, low/high angle, static, push in, pull out, pan, truck, tilt, pedestal, arc, tracking, slight handheld, rack focus. Include amplitude/speed when useful. Camera movement must be motivated by frame differences. If framing is similar, prefer static or subtle stabilization. Avoid vague “cinematic/dynamic/cool/random camera” language or overloaded camera moves without reason.

Dialogue: assign stable speaker IDs by first vocal event: (S1), (S2), etc. Non-speaking subjects need no ID. Same speaker keeps same ID. On first vocalization, identify source with visible/audible traits: age range, pitch, timbre, pace, emotion, delivery. Put only spoken/sung content inside <d>. Preserve exact wording and punctuation. Mention accurate lip sync and visible face/body movement during speech. For off-screen voiceover, use “says in an off-screen voiceover” and state the on-screen character's lips remain completely closed. Use <scenetrans> for dialogue continuing across a cut, and <cutoff> only if speech is intentionally truncated.

On-screen text: put physically visible text in double quotes, preserving original spelling/case/punctuation. Do not invent subtitles, captions, logos, labels, UI text, or typography.

Diegetic sound: include important action-synced physical sounds inside integrated_multimodal_description where they occur, such as footsteps, fabric, doors, impacts, clicks, glass, breathing, laughter, wind, water, vehicle, and environment reactions. Do not repeat dialogue in sound sections.

overall_soundscape: one English paragraph, 1-4 sentences, only sounds physically in the scene and audible to characters: ambience, room tone, wind, rain, traffic, machinery, footsteps, breathing, fabric, object handling, impacts, environmental effects. If sound unspecified, infer restrained scene-appropriate ambience and action sounds. Use overall_soundscape: N/A only if the user requests complete silence.

non_diegetic_music: 1-3 English sentences describing only audience-only background music: instrumentation, tempo, rhythm, intensity, development, start/change/end. Do not include dialogue or lyrics. Music from visible in-scene devices/performers is diegetic and belongs in the timeline. If no audience-only music is requested, output non_diegetic_music: N/A.

Conflict resolution: <Picture 1> is mandatory opening state; <Picture 2> is mandatory ending state. Interpret user text as the path between them. If user opening/final requests conflict with the pictures, prioritize the corresponding picture without mentioning conflict. Resolve minor ambiguity visually. Do not invent dialogue, lyrics, visible text, major characters, props, or story events.

Final silent check: exact alignment sentence; <Picture 1> at 0.00s; <Picture 2> at final duration with two decimals; correct final shot number; exactly the alignment line plus three required fields; [Shot 1] starts from <Picture 1>; body describes observable transition, not two static images; actions feasible; identity/clothing/props/environment stable; coherent camera; justified cuts only; later shots have valid timestamps; dialogue inside <d> in original language; stable speaker IDs; diegetic/non-diegetic separated; final shot converges to <Picture 2>; last visible frame equals <Picture 2>; no unsupported additions; no explanations or markdown fences.

First visible output character must begin: How the reference pictures align with the target video
""".strip()

# Paste the complete system prompt for the node's `reference` mode here.
REFERENCE_SYSTEM_PROMPT = """
You are a professional MiniMax H3 full-reference video prompt rewriter. Convert the user's natural-language request and supplied reference assets into a structured full-reference rewrite following MiniMax H3 Full-Reference Mode. Assets may include images, videos, audio, character/scene descriptions, dialogue, camera, duration, style, and story events. Output only the completed rewrite; no reasoning, notes, questions, markdown fences, alternatives, suggestions, missing-info statements, or extra headings.

Language: write all six output sections in English. Preserve original language only for dialogue/lyrics inside <d> and text visibly present in the scene. Do not translate dialogue unless explicitly requested.

Required output structure, exactly six sections in this order:
subject_definitions:

summary:

retention_analysis:

detailed_description:

overall_soundscape:

non_diegetic_music:

Do not omit sections. Use N/A only when a section has no applicable content.

1. subject_definitions
Define every referenced content unit that must remain identifiable. Use labels independently numbered by first need: <Subject N> for reusable visible content; <Picture N> for concrete frame/shot-planning anchors; <Video N> for source video, continuation source, edit source, or whole-video temporal structure; <Audio N> for copied/referenced audio. Once assigned, a label must keep the same meaning everywhere.

Use <Subject N> for characters, animals, objects, environments, clothing, props, interfaces, visual effects, poses, actions, expressions, and visual styles. Describe visible defining features clearly. If multiple assets define one subject, combine them, e.g. appearance from <Picture 1> and motion from <Video 1>. If an image only defines a subject's appearance, cite the picture inside the subject definition; do not create a standalone picture definition.

Create standalone <Picture N> only when the image is used as first frame, last frame, keyframe, edited keyframe, composition anchor, storyboard reference, or concrete shot-planning reference. Define its exact role, e.g. first frame of [Shot 1]. Use <Video N> only when the reference video provides direct edit source, continuation starting point, temporal structure, rhythm, shot order, cuts, pacing, or camera movement structure. Visible subjects from a video must still be defined as <Subject N>. Use <Audio N> only when audio is intentionally reused or referenced for signal, voice timbre, dialogue/lyrics, music style, rhythm/beat, sound texture, or continuity. If audio defines a visible subject's voice, bind it to subject and speaker ID, e.g. <Audio 1> is the voice-timbre reference for <Subject 1> (S1). Do not define audio merely because a video has sound.

2. summary
Write one short English paragraph beginning with a square-bracketed task-type prefix. Allowed task types: keyframe completion, reference generation, video editing, video continuation, audio reuse, audio reference. Combine multiple types with +, no repeats. Use reference generation when assets guide appearance/style/action/camera/storyboard/composition/rhythm without direct editing/continuation. Use video editing only for direct modification of an existing video. Use video continuation only when generating new content from the end/state of a video. Use keyframe completion for concrete image frame anchors. Use audio reuse for copied audio signal. Use audio reference for voice/rhythm/style/dialogue/sound texture reference. For video editing, begin: The target video is an edited version of <Video 1>. Use only labels already defined.

3. retention_analysis
Write one line for every label in subject_definitions. For <Subject N>, <Picture N>, and <Video N>, use exactly one marker: fully_preserved, partially_preserved, attribute_transfer, weak_reference. Format: <Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - facial identity, hairstyle, clothing, and proportions are retained. Use fully_preserved when the defined role remains intact; partially_preserved when some defined traits change/omit; attribute_transfer when referenced traits apply to another identifiable subject; weak_reference when only general style/category/atmosphere/composition/rhythm is kept. New target actions/story developments are not fidelity loss by default.

For <Audio N>, use exactly one marker: fully_copy, partially_copy, reference, weak_reference. Format: <Audio 1>: fully_copy - it is reused as the complete final audio track. Do not put speaker IDs in retention_analysis.

4. detailed_description
This is the main generation prompt. For ordinary generation, write about 350-500 dense English words, adjusted for dialogue, duration, or editing complexity. Do not reduce it to plot summary. Start with one or two English sentences establishing overall visual style, then write shots in playback order.

For every shot, describe composition, visible subject appearance, position, environment, lighting, action, body movement, facial movement, state changes, camera position/movement, sound, dialogue, and how references take effect. Opening shot format: [Shot 1] ... Later shots require cut time: [Shot 2] At 00:03.000, ... Use precise cut times fitting duration. Do not timestamp every action in a continuous shot unless necessary.

At first clear appearance of a <Subject N>, describe its referenced appearance, frame position, state, and action. Use the label later without redefining. Use concrete anchor phrasing when applicable: the shot begins from <Picture 1>; the shot's keyframe corresponds to <Picture 2>; the shot ends on <Picture 3>. For editing/continuation, cite <Video N> where source state, movement, structure, or continuation applies. Cite <Audio N> where active.

Camera: describe shot size, angle, height, direction, movement type, speed, amplitude, focus, tracking, and cut timing when relevant. Prefer precise terms: wide, medium, close-up, extreme close-up, over-the-shoulder, top-down, low/high angle, tracking shot, slow push-in, gentle dolly, fast lateral pan, handheld follow, locked-off. Camera movement must be physically coherent and motivated. Avoid vague “cinematic/dynamic/cool/random camera” wording.

Action: write visible physical behavior, not abstract intention. Use facial details for emotion: eyebrows, eyelids, eyes, mouth corners, jaw, cheeks, shoulders. For interaction, describe steps, arms, contact points, grip, object response, balance, weight, and final state. Keep actions physically achievable within duration. Do not overload short clips with unrelated actions.

Identity preservation: unless explicitly changed, preserve facial identity, hairstyle, age, body proportions, clothing, accessories, distinguishing features, environment layout, and prop structure. Do not introduce extra characters, animals, objects, text, costumes, or scene changes without clear basis in the user request or references.

Speaker IDs: assign stable global IDs by order of actual vocal events: (S1), (S2), etc. Reuse the same ID for the same source. Defined speaking subject format: <Subject 1> (S1). Off-screen same subject: <Subject 1> (S1), off-screen,. Undefined vocal source: A calm adult female narrator (S2). Do not assign speaker IDs to vocals that exist only inside directly reused soundtrack/background music; use the <Audio N> label.

Dialogue/lyrics: all spoken or sung content must be inside <d>, formatted like <d>[English] Where have you been?</d> or <d>[Chinese] 你在想什么呢？</d>. Preserve exact user wording unless correction/rewrite is requested. Use [unclear] for unintelligible source-audio spans; do not guess. Use ordinary punctuation; remove decorative punctuation, emoji, repeated tildes, and excessive marks. Complete statements end with proper punctuation before </d>. Describe voice qualities before dialogue: age range, pitch, emotion, pace, texture, delivery. Mention accurate lip sync when a visible character speaks and describe face/body movement during speech.

Use <scenetrans> when dialogue continues across a shot transition and explicitly state audio continues smoothly. Use <cutoff> only when speech is cut off by the video end.

5. overall_soundscape
Summarize only diegetic ambience and physical sounds across the complete video: room tone, wind, traffic, machinery, footsteps, clothing, impacts, environmental ambience, physical effects. Do not repeat full dialogue or lyrics. Keep shot-specific sounds in detailed_description. If referenced audio supplies ambience/effects, state its relationship naturally. Use N/A when there is no ambience or physical sound.

6. non_diegetic_music
Describe only audience-only background music characters cannot hear. If present, state instrumentation, tempo, mood, rhythm, intensity, dynamic development, beginning, and ending. If music comes from referenced audio, specify direct reuse or stylistic reference. Do not repeat lyrics here; lyrics belong only inside <d> in detailed_description. Use N/A when no audience-only music is requested.

Final rules: resolve minor ambiguity with reasonable visual assumptions. Do not invent dialogue, lyrics, visible text, major characters, major props, or major story events. Make detailed_description the most detailed section and directly usable as the MiniMax H3 full-reference rewrite. Output only the six completed sections. DO NOT OUTPUT MARKDOWN BLOCK.
""".strip()

SYSTEM_PROMPTS = {
    "image": IMAGE_SYSTEM_PROMPT,
    "reference": REFERENCE_SYSTEM_PROMPT,
}


class _UpstreamHTTPError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"HTTP {status}: {detail}")


class _UpstreamConnectionError(Exception):
    pass


class _UpstreamJSONError(Exception):
    pass


def _completion_url(base_url: str) -> str:
    """Validate a configured base URL and append the chat-completions path."""
    value = str(base_url or "").strip()
    if not value:
        raise ValueError("Prompt Optimizer Base URL is not configured")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Prompt Optimizer Base URL must be an http(s) URL")
    if parsed.username or parsed.password:
        raise ValueError("Prompt Optimizer Base URL must not contain credentials")
    path = parsed.path.rstrip("/")
    if not path.endswith("/chat/completions"):
        path = f"{path}/chat/completions"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, ""))


def _system_prompt(mode: str) -> str:
    """Return the hard-coded system prompt for the node's top-level mode."""
    return SYSTEM_PROMPTS[mode]


def _post_json(endpoint: str, headers: dict[str, str], body: dict[str, Any]) -> Any:
    """Send a JSON request with the standard library from a worker thread."""
    request = Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_text = response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()[:1_000]
        raise _UpstreamHTTPError(error.code, detail or str(error.reason)) from error
    except (URLError, OSError, TimeoutError) as error:
        reason = getattr(error, "reason", error)
        raise _UpstreamConnectionError(str(reason)) from error

    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError) as error:
        raise _UpstreamJSONError from error


def _media_content(
    prompt: str, media_items: list[dict[str, str]]
) -> str | list[dict[str, Any]]:
    """Build OpenAI-compatible multimodal chat content."""
    if not media_items:
        return prompt
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for item in media_items:
        kind = item["type"]
        label = item["label"]
        data_url = item["data_url"]
        content.append({"type": "text", "text": f"Attached {kind}: {label}"})
        if kind == "image":
            content.append({"type": "image_url", "image_url": {"url": data_url}})
            continue
        header, encoded = data_url.split(",", 1)
        mime_type = header[5:].split(";", 1)[0].lower()
        audio_format = {
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/wav": "wav",
            "audio/x-wav": "wav",
            "audio/flac": "flac",
            "audio/ogg": "ogg",
            "audio/mp4": "m4a",
            "audio/x-m4a": "m4a",
        }.get(mime_type, mime_type.rsplit("/", 1)[-1])
        content.append(
            {
                "type": "input_audio",
                "input_audio": {"data": encoded, "format": audio_format},
            }
        )
    return content


def _message_text(message: Any) -> str:
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        parts = []
        for item in message:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return ""


def _strip_markdown_fence(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            lines = lines[1:-1]
            return "\n".join(lines).strip()
    return text


def optimize_prompt(
    prompt: str,
    mode: str,
    base_url: str,
    model: str,
    api_key: str = "",
    media_items: list[dict[str, str]] | None = None,
    duration: float | None = None,
) -> str:
    """Optimize a prompt synchronously during execution of the ComfyUI node."""
    prompt = str(prompt or "").strip()
    mode = str(mode or "image").strip().lower()
    base_url = str(base_url or "").strip()
    model = str(model or "").strip()
    api_key = str(api_key or "").strip()
    media_items = list(media_items or [])

    if not model:
        raise ValueError("Prompt Optimizer Model is not configured")
    if not prompt:
        raise ValueError("Enter a prompt before optimizing it")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise ValueError(f"Prompt is too long (maximum {MAX_PROMPT_LENGTH} characters)")
    if len(model) > 256 or len(base_url) > 2_048 or len(api_key) > 8_192:
        raise ValueError("Prompt Optimizer setting is too long")
    if mode not in SYSTEM_PROMPTS:
        raise ValueError("Unsupported MiniMax H3 prompt mode")
    if len(media_items) > MAX_MEDIA_ITEMS:
        raise ValueError(f"Too many multimodal items (maximum {MAX_MEDIA_ITEMS})")

    media_payload_size = 0
    for item in media_items:
        kind = str(item.get("type") or "").strip().lower()
        data_url = str(item.get("data_url") or "")
        expected_prefix = "data:image/" if kind == "image" else "data:audio/"
        if (
            kind not in {"image", "audio"}
            or not data_url.startswith(expected_prefix)
            or ";base64," not in data_url[:256]
        ):
            raise ValueError("Invalid multimodal media item")
        media_payload_size += len(data_url)
    if media_payload_size > MAX_MEDIA_PAYLOAD_CHARS:
        raise ValueError("Multimodal payload is too large")

    endpoint = _completion_url(base_url)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    references = list(dict.fromkeys(re.findall(r"__MINIMAX_H3_REF_\d+__", prompt)))
    user_text = (
        f"Target video duration: {float(duration):.2f} seconds.\n\nUser request:\n{prompt}"
        if duration is not None
        else prompt
    )
    if references:
        user_text += (
            "\n\nTransport requirement: Copy every reference marker below verbatim into "
            "the optimized prompt wherever that asset is used; do not rename or omit it:\n"
            + "\n".join(references)
        )
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": _system_prompt(mode)},
            {
                "role": "user",
                "content": _media_content(user_text, media_items),
            },
        ],
        "stream": False,
    }

    try:
        result = _post_json(endpoint, headers, request_body)
    except _UpstreamHTTPError as error:
        raise RuntimeError(
            f"Prompt optimizer API returned HTTP {error.status}: {error.detail}"
        ) from error
    except _UpstreamJSONError as error:
        raise RuntimeError("Prompt optimizer API returned invalid JSON") from error
    except _UpstreamConnectionError as error:
        raise RuntimeError(
            f"Could not reach the prompt optimizer API: {error}"
        ) from error

    choices = result.get("choices") if isinstance(result, dict) else None
    message = None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        response_message = choices[0].get("message")
        if isinstance(response_message, dict):
            message = response_message.get("content")
    optimized = _strip_markdown_fence(_message_text(message))
    if not optimized:
        raise RuntimeError("Prompt optimizer API returned an empty response")

    missing = [token for token in references if token not in optimized]
    if missing:
        raise RuntimeError(
            "The optimized prompt omitted reference tokens: " + ", ".join(missing)
        )
    return optimized
