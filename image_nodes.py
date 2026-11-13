"""H3 Image conditioning and prompt optimization using the shared Easy UI."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import torch
import comfy.model_management
import node_helpers
import nodes
from comfy_extras import nodes_minimax_h3 as h3

from . import nodes as easy


IMAGE_BUNDLE_TYPE = "MINIMAX_H3_IMAGE_BUNDLE"
IMAGE_CONTEXT_TYPE = "MINIMAX_H3_IMAGE_CONTEXT"
IMAGE_MAX_REFERENCES = 16
IMAGE_RESOLUTIONS = {"1K": 1024, "1.5K": 1536, "2K": 2048, "3K": 3072, "4K": 4096}
IMAGE_ASPECT_RATIOS = {
    "1:1": (1, 1),
    "16:9": (16, 9),
    "9:16": (9, 16),
    "4:3": (4, 3),
    "3:4": (3, 4),
    "3:2": (3, 2),
    "2:3": (2, 3),
    "5:4": (5, 4),
    "4:5": (4, 5),
    "21:9": (21, 9),
}
IMAGE_REF_AUTO = "auto"
IMAGE_REF_SHORT_EDGES = {"short_1k": 1024, "short_1.5k": 1536, "short_2k": 2048}
IMAGE_RULES_DIR = os.path.join(easy.PROMPT_GUIDES_DIR, "h3_image")


def image_canvas(resolution, aspect_ratio, width, height):
    if resolution == easy.RESOLUTION_CUSTOM:
        return easy._align_canvas_dimension(width), easy._align_canvas_dimension(height)
    side = IMAGE_RESOLUTIONS[resolution]
    ratio_w, ratio_h = IMAGE_ASPECT_RATIOS[aspect_ratio]
    scale = side / math.sqrt(ratio_w * ratio_h)
    return easy._align_canvas_dimension(ratio_w * scale), easy._align_canvas_dimension(ratio_h * scale)


@lru_cache(maxsize=2)
def _image_guide(edit):
    with open(os.path.join(IMAGE_RULES_DIR, "edit.txt" if edit else "t2i.txt"), encoding="utf-8") as handle:
        text = handle.read()
    # The released T2I file is a Python format template; no template braces
    # or user-query placeholder should leak into an API system message.
    return text if edit else text.format("").split("\ninput_text:", 1)[0].strip()


def _image_optimizer_system(edit):
    return _image_guide(edit) + (
        "\n\n=== COMFYUI IMAGE TASK ===\n"
        "Use only the connected pictures, in their supplied order. Keep <Picture N> and <Subject N> distinct. "
        "The node's output canvas is authoritative. Use it to plan composition; do not add resolution, "
        "aspect-ratio declarations or generation settings to expanded_caption. Describe a still image, "
        "without video timelines, audio sections, dialogue markup, or video prompt fields. "
        "All descriptive prose is English; visible lettering retains its requested language. "
        "Only describe reference contents you can actually observe. An unobserved picture's label and "
        "the user's explicit description are not permission to invent source details. "
        "\n\n=== CREATIVE SCOPE: PRESERVE THE USER'S DESIGN ===\n"
        "Determine creative freedom from explicit instructions, existing design decisions and genuinely "
        "unspecified regions, not from prompt length. A detailed prompt is an existing design to realize, "
        "not an invitation to redesign it. Preserve its subjects and counts, composition and spatial "
        "relationships, palette, medium, lighting, typography, literal wording, exclusions and intentional "
        "negative space. Translate, organize and clarify the description without dropping specifics or "
        "replacing them with your preferred design. Add only necessary execution details consistent with "
        "those choices; do not add new subjects, motifs, sections, slogans or effects merely to make it "
        "richer. Use broader invention for open-ended needs or where explicitly requested, within all "
        "constraints that the user has not asked to change. Judge each scope independently: a detailed "
        "composition can still need copy written, and a short instruction can strictly constrain a local "
        "edit. Fill a requested but unwritten text region with complete copy without inventing extra "
        "regions or rewriting supplied copy unless asked. Requests to improve quality, polish or clarity "
        "alone do not authorize a new concept. These scope limits govern all art-direction and "
        "completeness guidance below. "
        "\n\n=== VISUAL DESIGN: TASK-SCOPED ART DIRECTION ===\n"
        "Distinguish creating a new composition from making a limited edit, including when pictures are "
        "connected. Preserve explicit style, subject counts, exclusions and requested simplicity. For "
        "open-ended creative work, choose a coherent visual direction suited to the purpose and develop "
        "it into a finished design; a short brief is not a request for a sparse or generic image. "
        "When references supply identities, products or selected properties for a new composition, "
        "keep those assigned features while fully designing the new setting, layout and other creative "
        "content. Do not freeze the whole target merely because references exist. For a local recolor, "
        "text replacement, removal or other limited edit, keep unrelated layout, typography, materials "
        "and lighting stable; improve only the requested change and its necessary integration. Retain "
        "the editing guide's source definitions, independent relationships and changed-detail format. "
        "\nMake the visual decisions concrete without overriding supplied choices: focal scale and "
        "placement, a deliberate viewing angle or flat geometry, meaningful crop, relationships between "
        "primary and secondary elements, color hierarchy, spacing and rhythm. Where the task benefits "
        "and the creative scope is open, add subject-specific supporting motifs, environmental cues or "
        "crafted details with clear positions and roles. Do not rely on words such "
        "as 'premium', 'polished' or 'high-end' to supply the missing design. 'Clean' and 'readable' mean "
        "controlled hierarchy, not automatically a plain empty background, generic sans-serif lettering "
        "or identical card grids. Choose those treatments only when they fit the request. Richness comes "
        "from purposeful relationships and execution, not a quota of objects, decorations or panels. "
        "\nMatch detail to the medium. In dimensional or photographic imagery, specify relevant surface "
        "finishes, edge construction, contact, depth and coherent light. In illustration, develop "
        "consistent shape language, palette and mark-making. In flat or vector graphics, refine line "
        "rhythm, silhouette, spacing, alignment and edge quality without forcing texture or volume. "
        "Do not default every task to ivory paper, restrained neutral colors, metallic gold, glow or "
        "gradients. Honor monochrome, no-shading and other exclusions. Intentional minimalism can be "
        "fully resolved through proportions and precision without adding subjects, text or scenery. "
        "\nWhen lettering belongs in a new or redesigned composition, preserve any supplied type "
        "treatment and develop only unspecified aspects. For a prominent title without a specified "
        "treatment, choose a fitting type treatment and describe its visible letterforms: "
        "proportions, stroke contrast and weight, terminals or corner shapes, spacing and line arrangement, "
        "as relevant. Relate the lettering's scale, alignment and placement to the main visual; specify "
        "material or print treatment only when appropriate. A font name or 'bold modern type' alone "
        "does not define that treatment. Give supporting copy a compatible, legible hierarchy; intricate "
        "display styling need not extend to small text or long paragraphs. Do not distort literal "
        "wording, impair Chinese character structure, add lettering to a text-free image, or redesign "
        "reference typography outside the requested scope. "
        "\nBefore finishing, check that the allowed creative scope has specific, coherent design choices, "
        "that useful visual detail has not been replaced by generic quality claims, and that added "
        "complexity does not compete with the focal subject, required copy or preservation constraints. "
        "\n\n=== ON-IMAGE TEXT: APPROPRIATE DENSITY, COMPLETE COPY ===\n"
        "First decide how much on-image text the user's purpose and requested deliverable actually need. "
        "Respect explicit wording, text limits, minimalism, visual emphasis and intentional whitespace; "
        "do not impose a minimum word count, number of sections or checklist of labels. "
        "A broadly described information-rich poster, explainer, infographic, interface or similar design "
        "still needs substantive, relevant finished copy, not merely headings or decorative text areas. "
        "When that deliverable calls for you to author copy, a short brief is enough: choose useful "
        "content within its scope and write it yourself rather than waiting for the user to supply every line. "
        "For every text region you introduce or change, put its complete final wording in expanded_caption "
        "in quotes, with its location, reading order and hierarchy made clear. This includes any chosen "
        "headlines, explanations, callouts, captions, labels, controls, legends and data fields. "
        "If several sections or points are needed, write the actual content of every one, including "
        "the supporting explanation when the requested information density calls for it. Do not stop "
        "at titles alone or truncate text simply to make the optimized prompt short. The image model "
        "should render the finished copy, not invent or complete it. Phrases such as 'several useful tips', "
        "'a paragraph about the topic', 'supporting text', filler, placeholders and ellipses must not "
        "stand in for actual final copy; preserve such wording when the user explicitly wants it printed. "
        "Keep supplied lettering, punctuation, capitalization, numbers and spaces exact. Newly authored "
        "copy uses the requested language, otherwise the user's language, even though visual prose is English. "
        "For a sparse design, write only the few words it needs; a single title is valid. For a "
        "text-free image, explicitly keep it free of text rather than adding a title, labels or decorative "
        "lettering. Do not add text to fill empty space or turn an ordinary visual scene into an infographic. "
        "In reference editing, apply completeness to new or changed copy while keeping the guide's "
        "source-transcription and preservation rules; do not repeat fully preserved source text in the "
        "changed-detail section or erase it with a blanket no-text instruction. Do not guess unreadable text. "
        "Do not fabricate real statistics, prices, certifications or product specifications to fill a design. "
        "Use supplied or derivable facts and relevant established qualitative information; fictional or "
        "illustrative data is appropriate only when the request permits it and its status is clear. "
        "Before finishing, check that every chosen text region has its final copy, no needed explanation "
        "is delegated to the image model, and no unneeded text region was added. These scope rules also "
        "govern the guide's general suggestions to complete information regions or add supporting elements. "
        "Return the guide's JSON object; the node extracts only expanded_caption."
    )


def _image_text_part(text, api_format):
    if api_format == "gemini":
        return {"text": text}
    return {"type": "input_text" if api_format == "responses" else "text", "text": text}


def _tensor_media_part(image, api_format):
    pixels = (image[0, ..., :3].detach().cpu().clamp(0, 1).numpy() * 255).round().astype("uint8")
    preview = easy.Image.fromarray(pixels)
    preview.thumbnail((1536, 1536))
    buffer = io.BytesIO()
    preview.save(buffer, format="JPEG", quality=85)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    if api_format == "gemini":
        return {"inlineData": {"mimeType": "image/jpeg", "data": encoded}}
    url = "data:image/jpeg;base64," + encoded
    return {"type": "input_image", "image_url": url} if api_format == "responses" else {
        "type": "image_url", "image_url": {"url": url},
    }


def _image_optimizer_input(prompt, resources, items, width, height, settings):
    api_format = settings["api_format"]
    count = max(len(resources), len(items))
    evidence = []
    parts = []
    for index in range(count):
        resource = resources[index] if index < len(resources) else {}
        item = items[index] if index < len(items) else None
        asset = resource.get("asset") or {}
        path = easy._optimizer_asset_path(asset)
        ratio = "unavailable"
        if item is not None:
            source_h, source_w = item.value.shape[1:3]
            divisor = math.gcd(source_w, source_h)
            ratio = f"{source_w // divisor}:{source_h // divisor}"
        elif path and easy.Image is not None:
            with easy.Image.open(path) as source:
                source = easy.ImageOps.exif_transpose(source)
                divisor = math.gcd(*source.size)
                ratio = f"{source.width // divisor}:{source.height // divisor}"
        media = []
        if settings.get("read_media"):
            if path:
                media = easy._optimizer_media_parts([resource], api_format, 1)
            elif item is not None and easy.Image is not None:
                media = [_tensor_media_part(item.value, api_format)]
        description = f"<Picture {index + 1}> [aspect_ratio {ratio}]; image evidence {'attached' if media else 'unavailable'}."
        evidence.append(description)
        if media:
            parts.append(_image_text_part("Reference Media:\n" + description, api_format))
            parts.extend(media)
    divisor = math.gcd(width, height)
    target_ratio = f"{width // divisor}:{height // divisor}"
    user_prompt = (
        f"Reference Image Count: {count}.\n" + "\n".join(evidence)
        + f"\n\nUser Aspect Ratio Selection:\n{target_ratio}"
        + f"\nOutput canvas (settings only): {width} x {height}."
        + "\n\nUser Editing Instruction / input_text (JSON string):\n"
        + json.dumps(prompt, ensure_ascii=False)
    )
    return user_prompt, parts


def _image_caption(response):
    text = easy._strip_optimizer_thoughts(str(response or ""))
    text = re.sub(r"^```(?:json|text)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text).strip()
    if text.startswith("{"):
        data = json.loads(text)
        text = data.get("expanded_caption")
        if not isinstance(text, str):
            raise ValueError("Image optimizer JSON must contain expanded_caption")
    if not text or not text.strip():
        raise ValueError("Image optimizer returned an empty caption")
    return text.strip()


def _image_context_hash(settings, resources, items, width, height):
    signatures = easy._runtime_optimizer_resource_signature(resources, items)
    for index, item in enumerate(items):
        resource = resources[index] if index < len(resources) else {}
        if not easy._optimizer_asset_path(resource.get("asset") or {}):
            signatures[index]["image_sha256"] = hashlib.sha256(
                item.value.detach().cpu().contiguous().numpy().tobytes()
            ).hexdigest()
    context = {
        "task": "h3_image", "canvas": [width, height], "resources": signatures,
        "guide": _image_optimizer_system(bool(resources or items)),
        "api": {key: settings.get(key) for key in ("api_format", "api_url", "model", "read_media")},
    }
    return easy._optimizer_sha256(json.dumps(context, ensure_ascii=False, sort_keys=True))


def optimize_image_prompt(payload, settings, items=()):
    if not easy._prompt_optimizer_settings_complete(
        settings["api_url"], settings["api_key"], settings["model"], settings["api_format"],
    ):
        raise ValueError("Prompt optimization settings are incomplete")
    width, height = image_canvas(
        payload.get("resolution", "2K"), payload.get("aspect_ratio", "1:1"),
        payload.get("width", 2048), payload.get("height", 2048),
    )
    resources = [resource for resource in easy._runtime_optimizer_resources(
        payload.get("resources"), IMAGE_MAX_REFERENCES,
    ) if resource.get("type") == "image"]
    prompt = easy._runtime_optimizer_prompt(payload.get("prompt", ""), resources, items)
    user_prompt, media_parts = _image_optimizer_input(prompt, resources, items, width, height, settings)
    response = easy._optimizer_http_json(
        settings["api_url"], settings["api_key"], settings["model"], settings["api_format"],
        _image_optimizer_system(bool(resources or items)), user_prompt, media_parts,
        timeout_seconds=easy.PROMPT_OPTIMIZER_ON_RUN_TIMEOUT_SECONDS,
        max_output_tokens=easy.PROMPT_OPTIMIZER_MAX_OUTPUT_TOKENS,
    )
    caption = _image_caption(response)
    return {
        "ok": True, "prompt": caption,
        "marker": {
            "task": "h3_image",
            "prompt_sha256": easy._optimizer_sha256(caption),
            "context_sha256": _image_context_hash(settings, resources, items, width, height),
        },
    }


@dataclass
class MiniMaxH3ImageBundle:
    model: Any
    clip: Any
    vae: Any


@dataclass
class MiniMaxH3ImageContext:
    conditioning: Any
    latent: dict
    vae: Any


class MiniMaxH3EasyImageLoader:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "load"
    RETURN_TYPES = (IMAGE_BUNDLE_TYPE,)
    RETURN_NAMES = ("h3_image_bundle",)
    DESCRIPTION = "Load the H3 Image transformer, shared H3 text encoder and dedicated image VAE."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image_model": (easy._all_weight_choices(("diffusion_models", "unet", "unet_gguf"), ""), {
                "default": "minimax_h3_image_pruned_int8_convrot.safetensors",
            }),
            "text_encoder": (easy._clip_choices(), {"default": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"}),
            "image_vae": (easy._vae_choices(("minimax_h3_image_vae",), "minimax_h3_image_vae_fp16.safetensors"), {
                "default": "minimax_h3_image_vae_fp16.safetensors",
            }),
        }}

    def load(self, image_model, text_encoder, image_vae):
        if not hasattr(h3, "MiniMaxH3ImageConditioning"):
            raise RuntimeError("H3 Image requires ComfyUI 0.45.0 or newer. Please update ComfyUI.")
        model = easy._load_gguf_unet(image_model) if easy._is_gguf_file(image_model) else nodes.UNETLoader().load_unet(image_model, "default")[0]
        clip = easy._load_text_encoder(text_encoder)
        vae, = nodes.VAELoader().load_vae(image_vae)
        return (MiniMaxH3ImageBundle(model, clip, vae),)


def _image_conditioning(bundle, prompt, images, width, height, reference_size):
    if reference_size == IMAGE_REF_AUTO:
        result = h3.MiniMaxH3ImageConditioning.execute(
            bundle.clip, prompt, width, height, vae=bundle.vae,
            images={f"image_{index}": image for index, image in enumerate(images, start=1)},
        )
        return result[0], result[1]
    short_edge = IMAGE_REF_SHORT_EDGES[reference_size]
    _, vision_images, refs = h3._image_refs(
        {f"image_{index}": image for index, image in enumerate(images, start=1)},
        bundle.vae,
        lambda w, h: h3._size_short_edge(w, h, h3.IMAGE_REF_SHORT_EDGE, h3.IMAGE_REF_SHORT_EDGE),
        lambda w, h: h3._size_short_edge(w, h, short_edge, short_edge),
    )
    conditioning = bundle.clip.encode_from_tokens_scheduled(
        bundle.clip.tokenize(prompt, images=vision_images, picture_label="Picture %d: "),
    )
    if refs:
        conditioning = node_helpers.conditioning_set_values(conditioning, {"minimax_refs": refs})
    latent = {"samples": torch.zeros([1, 24, 1, height // 16, width // 16], device=comfy.model_management.intermediate_device())}
    return conditioning, latent


class MiniMaxH3EasyImage:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "generate"
    RETURN_TYPES = ("MODEL", IMAGE_CONTEXT_TYPE)
    RETURN_NAMES = ("model", "h3_image_context")
    DESCRIPTION = "H3 Image: text-to-image without references, image editing with references. Connect H3 Image Context to Easy Image Output, then use a standard sampler at 6 steps, CFG 1, Euler / Simple."

    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "media": ("*",),
            "prompt_optimizer_resources": ("STRING", {"default": "", "hidden": True}),
            "prompt_optimizer_marker": ("STRING", {"default": "", "hidden": True}),
            "prompt_optimizer_prompt_connected": ("BOOLEAN", {"default": False, "hidden": True}),
        }
        for index in range(1, IMAGE_MAX_REFERENCES + 1):
            optional[f"media_{index}"] = ("*", {"hidden": True})
            optional[f"media_type_{index}"] = ("STRING", {"default": "", "hidden": True})
        return {"required": {
            "h3_image_bundle": (IMAGE_BUNDLE_TYPE,),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
            "resolution": ([*IMAGE_RESOLUTIONS, easy.RESOLUTION_CUSTOM], {"default": "2K"}),
            "aspect_ratio": (list(IMAGE_ASPECT_RATIOS), {"default": "1:1"}),
            "width": ("INT", {"default": 2048, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
            "height": ("INT", {"default": 2048, "min": 32, "max": nodes.MAX_RESOLUTION, "step": 32}),
            "advanced": ("BOOLEAN", {"default": False}),
            "ref_image_size": ([IMAGE_REF_AUTO, *IMAGE_REF_SHORT_EDGES], {
                "default": IMAGE_REF_AUTO,
                "tooltip": "Official strategy keeps the VAE reference short edge within 1024-2048 pixels. Fixed short-edge modes resize it to 1024, 1536 or 2048 pixels, including upscaling small pictures. Text-encoder references always use a 1024-pixel short edge. Independent of output resolution.",
            }),
            "reference_mention_mode": ([easy.REFERENCE_MENTION_FILENAME, easy.REFERENCE_MENTION_INDEX], {"default": easy.REFERENCE_MENTION_INDEX}),
            "prompt_optimizer": ("BOOLEAN", {"default": False}),
            "prompt_optimizer_api_format": (["openai", "responses", "gemini"], {"default": "openai"}),
            "prompt_optimizer_api_url": ("STRING", {"default": ""}),
            "prompt_optimizer_api_key": ("STRING", {"default": "", "multiline": False, "password": True}),
            "prompt_optimizer_model": ("STRING", {"default": ""}),
            "prompt_optimizer_read_media": ("BOOLEAN", {"default": False}),
            "prompt_optimizer_optimize_on_run": ("BOOLEAN", {"default": False}),
        }, "optional": optional}

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        settings = easy._workflow_prompt_optimizer_settings(kwargs)
        return float("nan") if settings["enabled"] and settings["optimize_on_run"] else False

    @classmethod
    def generate(cls, h3_image_bundle, prompt, resolution, aspect_ratio, width, height, advanced=False,
                 ref_image_size=IMAGE_REF_AUTO, reference_mention_mode="index", **kwargs):
        if not isinstance(h3_image_bundle, MiniMaxH3ImageBundle):
            raise ValueError("Connect a MiniMax H3 Easy Image Loader bundle")
        width, height = image_canvas(resolution, aspect_ratio, width, height)
        items = [item for item in easy.MiniMaxH3Easy._collect_media(kwargs, IMAGE_MAX_REFERENCES) if item.media_type == "image"]
        settings = easy._workflow_prompt_optimizer_settings(kwargs)
        resources = [resource for resource in easy._runtime_optimizer_resources(
            kwargs.get("prompt_optimizer_resources"), IMAGE_MAX_REFERENCES,
        ) if resource.get("type") == "image"]
        prompt = easy._runtime_optimizer_prompt(prompt, resources, items)
        marker = None
        if settings["enabled"] and settings["optimize_on_run"] and prompt.strip() and not kwargs.get("prompt_optimizer_prompt_connected"):
            previous = easy._runtime_optimizer_marker(kwargs.get("prompt_optimizer_marker"))
            context_hash = _image_context_hash(settings, resources, items, width, height)
            if previous.get("task") != "h3_image" or previous.get("prompt_sha256") != easy._optimizer_sha256(prompt) or previous.get("context_sha256") != context_hash:
                try:
                    optimized = optimize_image_prompt({
                        "prompt": prompt, "resources": resources, "resolution": "custom",
                        "width": width, "height": height,
                    }, settings, items)
                    prompt, marker = optimized["prompt"], optimized["marker"]
                except Exception as exc:
                    print(f"[MiniMax H3 Image] Prompt optimization failed; using the original prompt: {exc}")
        conditioning, latent = _image_conditioning(
            h3_image_bundle, prompt, [item.value for item in items], width, height, ref_image_size,
        )
        context = MiniMaxH3ImageContext(conditioning, latent, h3_image_bundle.vae)
        result = (h3_image_bundle.model, context)
        if marker:
            return {"result": result, "ui": {
                "auto_optimized_prompt": [prompt],
                "auto_optimization_marker": [json.dumps(marker, sort_keys=True)],
            }}
        return result


class MiniMaxH3EasyImageOutput:
    CATEGORY = "MiniMax H3 Easy"
    FUNCTION = "unpack"
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT", "VAE")
    RETURN_NAMES = ("positive", "negative", "latent", "vae")
    DESCRIPTION = "Unpack H3 Image conditioning, zero negative conditioning, image latent and VAE for standard sampling and decoding."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"h3_image_context": (IMAGE_CONTEXT_TYPE,)}}

    @staticmethod
    def unpack(h3_image_context):
        if not isinstance(h3_image_context, MiniMaxH3ImageContext):
            raise ValueError("Connect the H3 Image Context output from MiniMax H3 Easy Image")
        negative, = nodes.ConditioningZeroOut().zero_out(h3_image_context.conditioning)
        return h3_image_context.conditioning, negative, h3_image_context.latent, h3_image_context.vae
