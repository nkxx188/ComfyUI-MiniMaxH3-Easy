import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_CLASS = "MiniMaxH3Easy";
const CONTEXT_SEGMENTS_CLASS = "MiniMaxH3EasyContextSegments";
const SELECTED_VIDEO_CONTEXT_CLASS = "MiniMaxH3EasySelectedVideoContext";
const LOADER_CLASS = "MiniMaxH3EasyLoader";
const ADAPTER_CLASS = "MiniMaxH3EasyModelAdapter";
const MEDIA_LOADER_CLASS = "MiniMaxH3EasyMediaLoader";
const MEDIA_BRIDGE_CLASS = "MiniMaxH3EasyMediaBridge";
const MEDIA_SPLITTER_CLASS = "MiniMaxH3EasyMediaSplitter";
const SEGMENT_RENDER_CLASS = "MiniMaxH3EasySegmentRender";
const SEGMENT_REFINE_CLASS = "MiniMaxH3EasySegmentRefine";
const SEGMENT_SAMPLE_SETUP_CLASS = "MiniMaxH3EasySegmentSampleSetup";
const SEGMENT_STEP_CLASS = "MiniMaxH3EasySegmentStep";
const SEGMENT_COLLECT_CLASS = "MiniMaxH3EasySegmentCollect";
const SEGMENT_DECODE_CLASS = "MiniMaxH3EasySegmentDecode";
const OUTPUT_CLASS = "MiniMaxH3EasyOutput";
const LINKS_PROP = "minimax_h3_virtual_media_links";
const PROMPT_DOC_PROP = "minimax_h3_prompt_reference_doc";
const PROMPT_VIEW_PROP = "minimax_h3_prompt_view_mode";
const PROMPT_OPTIMIZER_PROP = "minimax_h3_prompt_optimizer";
const PROMPT_AUTO_MARKER_PROP = "minimax_h3_auto_prompt_marker";
const RUNTIME_REF_PREFIX = "__MINIMAX_H3_REF_";
const UNRESOLVED_REF_PREFIX = "__MINIMAX_H3_UNRESOLVED_REF_";
const DIALOGUE_CLASS = "h3-dialogue-block";
const PROMPT_VIEW_STRUCTURED = "structured";
const PROMPT_VIEW_RAW = "raw";
const PROMPT_GUIDES = [
    { value: "none", zh: "\u4ec5\u901a\u7528\u65b9\u6848", en: "General only" },
    { value: "3d_animation_short", zh: "3D \u52a8\u753b\u77ed\u7247", en: "3D Animation Short" },
    { value: "brand_promo", zh: "\u54c1\u724c\u5ba3\u4f20\u7247", en: "Brand Promo Video" },
    { value: "coop_game_intro", zh: "\u5408\u4f5c\u6e38\u620f\u5f00\u573a", en: "Co-op Game Intro" },
    { value: "handdrawn_live", zh: "\u624b\u7ed8\u5b9e\u62cd\u878d\u5408", en: "Hand-drawn Live-action" },
    { value: "minimalist_product_ad", zh: "\u6781\u7b80\u4ea7\u54c1\u5e7f\u544a", en: "Minimalist Product Ad" },
    { value: "music_video_subtitle", zh: "\u97f3\u4e50\u89c6\u9891\u5b57\u5e55", en: "Music Video Subtitle" },
    { value: "paper_collage", zh: "\u7eb8\u5f20\u62fc\u8d34\u89e3\u8bf4", en: "Paper Collage Explainer" },
    { value: "papercraft_stop_motion", zh: "\u7eb8\u827a\u5b9a\u683c\u89e3\u8bf4", en: "Papercraft Stop-motion" },
];
const MODE_IMAGE = "image";
const MODE_REFERENCE = "reference";
const MODE_DIGITAL_HUMAN = "digital_human";
const MODE_SEGMENTS = "context_segments";
const CONTEXT_AUDIO_GENERATED = "generated";
const CONTINUITY_GUIDE = "guide";
const CONTINUITY_LATENT = "latent_guide";
const CONTINUITY_SOFT_AV = "soft_av";
const CONTINUITY_HARD_AV = "hard_av";
const SELECTED_VIDEO_SEGMENT_WHOLE = "whole_video";
const SELECTED_VIDEO_SEGMENT_TIME_CUTS = "time_cuts";
const SELECTED_VIDEO_SEGMENT_FRAME_CUTS = "frame_cuts";
const GUIDE_CONTEXT_FRAME_GRID = Object.freeze([5, 22, 39, 56, 73]);
const AV_CONTEXT_FRAME_GRID = Object.freeze([39, 90, 141]);
const AV_CONTINUITY_MODES = new Set([CONTINUITY_SOFT_AV, CONTINUITY_HARD_AV]);
const KEYFRAME_FIRST = "first";
const RESOLUTION_CUSTOM = "custom";
const REF_IMAGE_MATCH = "match";
const REF_IMAGE_1K = "1k";
const REF_IMAGE_15K = "1.5k";
const REF_IMAGE_2K = "2k";
const REF_IMAGE_ORIGINAL = "original";
const MAX_MEDIA = 15;
const MAX_IMAGES = 9;
const MAX_VIDEOS = 3;
const MAX_AUDIOS = 3;
const SEGMENT_MAX_COUNT = 30;
const SEGMENT_MAX_MEDIA = MAX_MEDIA * 3;
const SEGMENT_MAX_IMAGES = MAX_IMAGES * 3;
const SEGMENT_MAX_VIDEOS = MAX_VIDEOS * 3;
const SEGMENT_MAX_AUDIOS = MAX_AUDIOS * 3;
const MEDIA_BUNDLE_TYPE = "MINIMAX_H3_MEDIA_BUNDLE";
const MEDIA_BRIDGE_GROUPS = Object.freeze([
    { type: "image", count: "image_count", max: MAX_IMAGES },
    { type: "video", count: "video_count", max: MAX_VIDEOS },
    { type: "audio", count: "audio_count", max: MAX_AUDIOS },
]);
const MEDIA_SPLITTER_GROUPS = Object.freeze([
    { type: "image", count: "image_count", max: 27 },
    { type: "video", count: "video_count", max: 9 },
    { type: "audio", count: "audio_count", max: 9 },
]);
const MEDIA_SPLITTER_OUTPUT_TYPES = Object.freeze({
    image: "IMAGE",
    video: "VIDEO",
    audio: "AUDIO",
});
const MEDIA_LOADER_GROUPS = Object.freeze([
    { type: "image", key: "images" },
    { type: "audio", key: "audios" },
    { type: "video", key: "videos" },
]);
const MEDIA_LOADER_INTERNAL_DRAG_TYPE = "application/x-h3-media-loader-type";
let mediaLoaderInternalDrag = null;
const MIN_SECONDS = 0.2;
const MAX_SECONDS = 30;
const PROMPT_HISTORY_LIMIT = 120;
const PROMPT_UNDO_VERSION = "2026-08-05-editor-undo-shield-v1";
const CARET_SENTINEL = "\u200B";
const AUDIO_ICON_SVG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect x='0.5' y='10' width='3' height='4' rx='1.5' fill='%2300e2bb'/%3E%3Crect x='5.5' y='7' width='3' height='10' rx='1.5' fill='%2300e2bb'/%3E%3Crect x='10.5' y='4' width='3' height='16' rx='1.5' fill='%2300e2bb'/%3E%3Crect x='15.5' y='7' width='3' height='10' rx='1.5' fill='%2300e2bb'/%3E%3Crect x='20.5' y='10' width='3' height='4' rx='1.5' fill='%2300e2bb'/%3E%3C/svg%3E";
const PRIMARY_BROWSER_LANGUAGE = String(globalThis.navigator?.language || globalThis.navigator?.languages?.[0] || "");
const ZH_BROWSER = /^(zh)(?:[-_]|$)/i.test(PRIMARY_BROWSER_LANGUAGE);
const TEXT = {
    image: ZH_BROWSER ? "\u56fe\u7247" : "Image",
    video: ZH_BROWSER ? "\u89c6\u9891" : "Video",
    audio: ZH_BROWSER ? "\u97f3\u9891" : "Audio",
    loadImage: ZH_BROWSER ? "\u52a0\u8f7d\u56fe\u7247" : "Load image",
    loadVideo: ZH_BROWSER ? "\u52a0\u8f7d\u89c6\u9891" : "Load video",
    loadAudio: ZH_BROWSER ? "\u52a0\u8f7d\u97f3\u9891" : "Load audio",
    deleteLink: ZH_BROWSER ? "\u5220\u9664" : "Delete",
    promptPlaceholder: "Prompt...",
    rawPromptPlaceholder: ZH_BROWSER ? "\u539f\u59cb\u63d0\u793a\u8bcd..." : "Raw prompt...",
    showRawPrompt: ZH_BROWSER ? "\u663e\u793a\u539f\u59cb\u63d0\u793a\u8bcd" : "Show raw prompt",
    showStructuredPrompt: ZH_BROWSER ? "\u8fd4\u56de\u7ed3\u6784\u5316\u7f16\u8f91" : "Back to structured editor",
    optimizePrompt: ZH_BROWSER ? "\u63d0\u793a\u8bcd\u4f18\u5316" : "Prompt optimization",
    regeneratePrompt: ZH_BROWSER ? "\u91cd\u65b0\u751f\u6210" : "Regenerate",
    optimizerSettings: ZH_BROWSER ? "\u63d0\u793a\u8bcd\u4f18\u5316\u8bbe\u7f6e" : "Prompt optimization settings",
    optimizerMissing: ZH_BROWSER ? "\u8bf7\u5148\u5728\u9ad8\u7ea7\u9009\u9879\u4e2d\u586b\u5199 API \u5730\u5740\u548c\u6a21\u578b\u540d\uff1bGemini \u539f\u751f\u8fd8\u9700\u8981 API Key\u3002" : "Set the API URL and model in Advanced options; Gemini Native also requires an API key.",
    optimizerFailed: ZH_BROWSER ? "\u63d0\u793a\u8bcd\u4f18\u5316\u5931\u8d25" : "Prompt optimization failed",
    optimizerRunning: ZH_BROWSER ? "\u6b63\u5728\u4f18\u5316" : "Optimizing",
    optimizerCancel: ZH_BROWSER ? "\u4e2d\u65ad\u4f18\u5316" : "Stop optimization",
    optimizerDone: ZH_BROWSER ? "\u4f18\u5316\u5b8c\u6210" : "Optimization complete",
    optimizerError: ZH_BROWSER ? "\u4f18\u5316\u5931\u8d25" : "Optimization failed",
    promptExternalConnected: ZH_BROWSER ? "\u63d0\u793a\u8bcd\u6765\u81ea\u5916\u90e8\u6587\u672c\u8fde\u63a5" : "Prompt supplied by external text input",
    referencePromptPlaceholder: ZH_BROWSER ? "Prompt... \u8f93\u5165 @ \u5f15\u7528\u5df2\u8fde\u63a5\u7d20\u6750" : "Prompt... Type @ to reference connected media",
    mentionTitle: ZH_BROWSER ? "\u5f15\u7528\u7d20\u6750" : "Reference media",
    mentionEmpty: ZH_BROWSER ? "\u5148\u5c06\u7d20\u6750\u8fde\u63a5\u5230\u4e3b\u8282\u70b9" : "Connect media to the main node first",
    mainTitle: "MiniMax H3 Easy",
    selectedVideoContextTitle: ZH_BROWSER ? "MiniMax H3 Easy 已选视频上下文" : "MiniMax H3 Easy Selected Video Context",
    loaderTitle: ZH_BROWSER ? "MiniMax H3 Easy \u52a0\u8f7d\u5668" : "MiniMax H3 Easy Loader",
    adapterTitle: ZH_BROWSER ? "MiniMax H3 Easy \u6a21\u578b\u4e2d\u8f6c" : "MiniMax H3 Easy Model Bridge",
    mediaBridgeTitle: ZH_BROWSER ? "MiniMax H3 Easy \u5a92\u4f53\u4e2d\u8f6c" : "MiniMax H3 Easy Media Bridge",
    mediaLoaderTitle: ZH_BROWSER ? "MiniMax H3 Easy \u5a92\u4f53\u52a0\u8f7d\u5668" : "MiniMax H3 Easy Media Loader",
    mediaSplitterTitle: ZH_BROWSER ? "MiniMax H3 Easy \u5a92\u4f53\u62c6\u5206" : "MiniMax H3 Easy Media Splitter",
    mediaLoaderMenuTitle: ZH_BROWSER ? "\u5a92\u4f53\u52a0\u8f7d\u5668" : "Media Loader",
    mediaLoaderAll: ZH_BROWSER ? "\u5a92\u4f53\u8d44\u6e90" : "Media resources",
    mediaLoaderImages: ZH_BROWSER ? "\u56fe\u7247" : "Images",
    mediaLoaderAudio: ZH_BROWSER ? "\u97f3\u9891" : "Audio",
    mediaLoaderVideos: ZH_BROWSER ? "\u89c6\u9891" : "Videos",
    mediaLoaderUpload: ZH_BROWSER ? "\u4e0a\u4f20\u5a92\u4f53" : "Upload media",
    mediaLoaderDrop: ZH_BROWSER ? "\u91ca\u653e\u4ee5\u6dfb\u52a0\u5a92\u4f53" : "Drop to add media",
    mediaLoaderReplace: ZH_BROWSER ? "\u66ff\u6362" : "Replace",
    mediaLoaderRemove: ZH_BROWSER ? "\u5220\u9664" : "Remove",
    mediaLoaderEmpty: ZH_BROWSER ? "\u6682\u65e0\u5a92\u4f53" : "No media",
    mediaLoaderLimit: ZH_BROWSER ? "\u5df2\u8fbe\u8be5\u5206\u533a\u4e0a\u9650" : "This section is full",
    mediaLoaderUnsupported: ZH_BROWSER ? "\u53ea\u652f\u6301\u56fe\u7247\u3001\u97f3\u9891\u6216\u89c6\u9891\u6587\u4ef6" : "Only image, audio, and video files are supported",
    outputTitle: ZH_BROWSER ? "MiniMax H3 Easy \u8f93\u51fa" : "MiniMax H3 Easy Output",
    category: "MiniMax H3 Easy",
    mode: ZH_BROWSER ? "\u6a21\u5f0f" : "Mode",
    audioMode: ZH_BROWSER ? "\u97f3\u9891\u6a21\u5f0f" : "Audio mode",
    prompt: ZH_BROWSER ? "\u63d0\u793a\u8bcd" : "Prompt",
    resolution: ZH_BROWSER ? "\u5206\u8fa8\u7387" : "Resolution",
    aspectRatio: ZH_BROWSER ? "\u5bbd\u9ad8\u6bd4" : "Aspect ratio",
    width: ZH_BROWSER ? "\u5bbd\u5ea6" : "Width",
    height: ZH_BROWSER ? "\u9ad8\u5ea6" : "Height",
    seconds: ZH_BROWSER ? "\u79d2\u6570" : "Seconds",
    advanced: ZH_BROWSER ? "\u9ad8\u7ea7\u9009\u9879" : "Advanced options",
    promptOptimizer: ZH_BROWSER ? "\u63d0\u793a\u8bcd\u4f18\u5316" : "Prompt optimizer",
    promptOptimizerApiFormat: ZH_BROWSER ? "API \u683c\u5f0f" : "API format",
    promptOptimizerApiUrl: ZH_BROWSER ? "API \u5730\u5740" : "API URL",
    promptOptimizerApiKey: "API Key",
    promptOptimizerModel: ZH_BROWSER ? "\u6a21\u578b\u540d" : "Model",
    promptOptimizerSceneGuide: ZH_BROWSER ? "\u63d0\u793a\u8bcd\u65b9\u6848" : "Prompt Guide",
    promptOptimizerReadMedia: ZH_BROWSER ? "\u8bfb\u53d6\u5df2\u8fde\u63a5\u5a92\u4f53" : "Read connected media",
    promptOptimizerOptimizeOnRun: ZH_BROWSER ? "\u8fd0\u884c\u5de5\u4f5c\u6d41\u65f6\u81ea\u52a8\u4f18\u5316" : "Optimize when workflow runs",
    contextPromptOptimizerMode: ZH_BROWSER ? "\u4f18\u5316\u65b9\u5f0f" : "Context optimization mode",
    contextPromptOptimizerConcurrency: ZH_BROWSER ? "\u5e76\u53d1\u6570" : "Optimization concurrency",
    fps: ZH_BROWSER ? "\u5e27\u7387 (FPS)" : "Frame rate (FPS)",
    keyframeRole: ZH_BROWSER ? "\u9996\u5c3e\u5e27\u8bbe\u7f6e" : "First/last frame setup",
    refImageSize: ZH_BROWSER ? "\u53c2\u8003\u56fe\u5c3a\u5bf8" : "Reference size",
    referenceMentionMode: ZH_BROWSER ? "@\u5f15\u7528\u65b9\u5f0f" : "@ reference mode",
    mentionByFilename: ZH_BROWSER ? "\u6309\u6587\u4ef6\u540d" : "By filename",
    mentionByIndex: ZH_BROWSER ? "\u6309\u5e8f\u53f7" : "By index",
    bundle: ZH_BROWSER ? "H3 \u6a21\u578b\u7ec4\u5408" : "H3 model bundle",
    fl2vaModel: ZH_BROWSER ? "FL2VA \u6a21\u578b" : "FL2VA model",
    ref2vaModel: ZH_BROWSER ? "REF2VA \u6a21\u578b" : "REF2VA model",
    textEncoder: ZH_BROWSER ? "\u6587\u672c\u7f16\u7801\u5668" : "Text encoder",
    videoVae: ZH_BROWSER ? "\u89c6\u9891 VAE" : "Video VAE",
    audioVae: ZH_BROWSER ? "\u97f3\u9891 VAE" : "Audio VAE",
    noneModel: ZH_BROWSER ? "\u65e0" : "None",
    outputModel: "Model",
    outputConditioning: "Conditioning",
    outputLatent: "Latent",
    outputVideoVae: "Video VAE",
    outputAudioVae: "Audio VAE",
    outputFps: "FPS",
    drivingAudio: ZH_BROWSER ? "\u9a71\u52a8\u97f3\u9891" : "Driving audio",
    outputContext: "H3 Context",
    inputMedia: "Media",
    selectedVideoInput: ZH_BROWSER ? "候选视频" : "Selected video",
    selectedVideoSegmentMode: ZH_BROWSER ? "候选视频分段方式" : "Candidate segmentation",
    selectedVideoTimeCuts: ZH_BROWSER ? "时间切点（秒）" : "Time cut points (seconds)",
    selectedVideoFrameCuts: ZH_BROWSER ? "帧切点（24 FPS）" : "Frame cut points (24 FPS)",
    mediaBundle: ZH_BROWSER ? "\u5a92\u4f53\u5305" : "Media bundle",
    imageCount: ZH_BROWSER ? "\u56fe\u7247\u6570\u91cf" : "Image count",
    videoCount: ZH_BROWSER ? "\u89c6\u9891\u6570\u91cf" : "Video count",
    audioCount: ZH_BROWSER ? "\u97f3\u9891\u6570\u91cf" : "Audio count",
    mediaSplitterEmptyOutputMode: ZH_BROWSER ? "\u7a7a\u7aef\u53e3\u5904\u7406" : "Empty output handling",
    seedLabel: "Seed",
    segmentSeeds: ZH_BROWSER ? "\u5206\u6bb5 Seed\uff08\u53ef\u9009\uff09" : "Segment seeds (optional)",
    segmentRenderTitle: ZH_BROWSER ? "MiniMax H3 Easy \u5206\u6bb5\u91c7\u6837" : "MiniMax H3 Easy Segment Sample",
    segmentRefineTitle: ZH_BROWSER ? "MiniMax H3 Easy \u5206\u6bb5\u4e8c\u91c7" : "MiniMax H3 Easy Segment Refine",
    segmentSampleSetupTitle: ZH_BROWSER ? "MiniMax H3 Easy \u91c7\u6837\u8bbe\u7f6e" : "MiniMax H3 Easy Sample Setup",
    segmentSampleSetupPort: ZH_BROWSER ? "\u91c7\u6837\u8bbe\u7f6e" : "Sample Setup",
    segmentStepTitle: ZH_BROWSER ? "MiniMax H3 Easy \u5206\u6bb5\u6b65\u9aa4" : "MiniMax H3 Easy Segment Step",
    segmentCollectTitle: ZH_BROWSER ? "MiniMax H3 Easy \u5206\u6bb5\u6c47\u603b" : "MiniMax H3 Easy Segment Collect",
    segmentDecodeTitle: ZH_BROWSER ? "MiniMax H3 Easy \u5206\u6bb5\u89e3\u7801" : "MiniMax H3 Easy Segment Decode",
    contextSegmentsTitle: ZH_BROWSER ? "MiniMax H3 Easy \u4e0a\u4e0b\u6587\u5206\u6bb5" : "MiniMax H3 Easy Context Segments",
    segmentSeconds: ZH_BROWSER ? "\u5206\u6bb5\u79d2\u6570" : "Segment seconds",
    segmentSecondsHint: ZH_BROWSER ? "\u9017\u53f7\u5206\u9694\u6bcf\u6bb5\u65f6\u957f\uff0c\u4f8b\u5982 10,8,5" : "Comma separated seconds per segment, e.g. 10,8,5",
     contextLength: ZH_BROWSER ? "\u4e0a\u4e0b\u6587\u5e27\u6570" : "Context frames",
    continuityMode: ZH_BROWSER ? "\u8fde\u7eed\u65b9\u5f0f" : "Continuity mode",
    segmentResult: ZH_BROWSER ? "\u5206\u6bb5\u7ed3\u679c" : "Segments",
    segmentPreview: ZH_BROWSER ? "\u9884\u89c8" : "Preview",
    refineMode: ZH_BROWSER ? "\u4e8c\u91c7\u653e\u5927\u6a21\u5f0f" : "Refine mode",
    refineExecution: ZH_BROWSER ? "\u4e8c\u91c7\u6267\u884c\u65b9\u5f0f" : "Refine execution",
    segmentIndex: ZH_BROWSER ? "\u5206\u6bb5\u5e8f\u53f7" : "Segment index",
    previousSegment: ZH_BROWSER ? "\u4e0a\u4e00\u5206\u6bb5" : "Previous segment",
    promptOverride: ZH_BROWSER ? "\u63d0\u793a\u8bcd\u8986\u76d6" : "Prompt override",
    tileWidth: ZH_BROWSER ? "Tile \u5bbd\u5ea6" : "Tile width",
    tileHeight: ZH_BROWSER ? "Tile \u9ad8\u5ea6" : "Tile height",
    tileOverlap: ZH_BROWSER ? "Tile \u91cd\u53e0\u533a" : "Tile overlap",
    tileFade: ZH_BROWSER ? "Tile \u63a5\u7f1d\u6e10\u53d8" : "Tile seam fade",
};
const OPTION_DEFS = {
    mode: {
        [MODE_IMAGE]: ZH_BROWSER ? "\u56fe\u751f\u6216\u9996\u5c3e\u5e27" : "I2V or First/Last Frame",
        [MODE_REFERENCE]: ZH_BROWSER ? "\u53c2\u8003\u751f\u89c6\u9891" : "Reference-to-video",
        [MODE_DIGITAL_HUMAN]: ZH_BROWSER ? "\u6570\u5b57\u4eba" : "Digital Human",
        [MODE_SEGMENTS]: ZH_BROWSER ? "\u4e0a\u4e0b\u6587\u5206\u6bb5" : "Context Segments",
    },
    audio_mode: {
        [CONTEXT_AUDIO_GENERATED]: ZH_BROWSER ? "\u9ed8\u8ba4" : "Default",
        [MODE_DIGITAL_HUMAN]: ZH_BROWSER ? "\u6570\u5b57\u4eba" : "Digital Human",
    },
    keyframe_role: {
        first: ZH_BROWSER ? "\u9996\u5e27\u4f18\u5148" : "First frame priority",
        last: ZH_BROWSER ? "\u5c3e\u5e27\u4f18\u5148" : "Last frame priority",
    },
    ref_image_size: {
        [REF_IMAGE_MATCH]: ZH_BROWSER ? "\u5339\u914d\u751f\u6210\u5206\u8fa8\u7387" : "Match generation size",
        [REF_IMAGE_1K]: ZH_BROWSER ? "1K \u9762\u79ef\uff08\u7ea61MP\uff09" : "1K area (~1MP)",
        [REF_IMAGE_15K]: ZH_BROWSER ? "1.5K \u9762\u79ef\uff08\u7ea62.25MP\uff09" : "1.5K area (~2.25MP)",
        [REF_IMAGE_2K]: ZH_BROWSER ? "2K \u9762\u79ef\uff08\u7ea64MP\uff09" : "2K area (~4MP)",
        [REF_IMAGE_ORIGINAL]: ZH_BROWSER ? "\u539f\u56fe\uff08\u4e0d\u7f29\u653e\uff09" : "Original (no scaling)",
    },
    reference_mention_mode: {
        filename: ZH_BROWSER ? "\u6309\u6587\u4ef6\u540d" : "By filename",
        index: ZH_BROWSER ? "\u6309\u5e8f\u53f7" : "By index",
    },
    refine_execution: {
        whole_segment: "Standard",
        tiled_low_vram: "Low VRAM Tile",
    },
    refine_mode: {
        pixel_resize: "Pixel Resize",
        latent_upscale: "Latent Upscale",
    },
    continuity_mode: {
        [CONTINUITY_LATENT]: "Latent Guide",
        [CONTINUITY_GUIDE]: "RGB Guide",
        [CONTINUITY_SOFT_AV]: "Soft AV Prefix",
        [CONTINUITY_HARD_AV]: "Hard AV Prefix",
    },
    prompt_optimizer_api_format: {
        openai: ZH_BROWSER ? "OpenAI \u517c\u5bb9" : "OpenAI Compatible",
        responses: "OpenAI Responses",
        gemini: ZH_BROWSER ? "Gemini \u539f\u751f" : "Gemini Native",
    },
    prompt_optimizer_scene_guide: {
        none: ZH_BROWSER ? "\u4ec5\u901a\u7528\u65b9\u6848" : "General only",
    },
    context_prompt_optimizer_mode: {
        whole_sequence: ZH_BROWSER ? "\u6574\u4f53\u4f18\u5316" : "Whole sequence",
        per_segment: ZH_BROWSER ? "\u9010\u6bb5\u4f18\u5316" : "Per segment",
    },
    selected_video_segment_mode: {
        [SELECTED_VIDEO_SEGMENT_WHOLE]: ZH_BROWSER ? "整段视频" : "Whole video",
        [SELECTED_VIDEO_SEGMENT_TIME_CUTS]: ZH_BROWSER ? "按时间切分" : "Split by time",
        [SELECTED_VIDEO_SEGMENT_FRAME_CUTS]: ZH_BROWSER ? "按帧切分" : "Split by frame",
    },
    empty_output_mode: {
        block_missing: ZH_BROWSER ? "默认（跳过缺失输出）" : "Default (Skip Missing Outputs)",
        allow_none: ZH_BROWSER ? "允许空输出（None）" : "Allow empty outputs (None)",
    },
    resolution: {
        "360P": "360P",
        "416P": "416P",
        "480P": "480P",
        "540P": "540P",
        "640P": "640P",
        "720P": "720P",
        "768P": "768P",
        "832P": "832P",
        "928P": "928P",
        "1024P": "1024P",
        "1080P": "1080P",
        [RESOLUTION_CUSTOM]: "Custom",
    },
    aspect_ratio: {
        "1:1": "1:1",
        "2:3": "2:3",
        "3:2": "3:2",
        "3:4": "3:4",
        "4:3": "4:3",
        "9:16": "9:16",
        "16:9": "16:9",
        "21:9": "21:9",
    },
};
const OPTION_ALIASES = {
    mode: {
        [MODE_IMAGE]: MODE_IMAGE,
        "\u56fe\u751f\u6216\u9996\u5c3e\u5e27": MODE_IMAGE,
        "\u56fe\u751f\u6216\u9996\u5c3e\u5e27\u89c6\u9891": MODE_IMAGE,
        "I2V or First/Last Frame": MODE_IMAGE,
        [MODE_REFERENCE]: MODE_REFERENCE,
        "\u53c2\u8003\u751f\u89c6\u9891": MODE_REFERENCE,
        "Reference-to-video": MODE_REFERENCE,
        [MODE_DIGITAL_HUMAN]: MODE_DIGITAL_HUMAN,
        "\u6570\u5b57\u4eba": MODE_DIGITAL_HUMAN,
        "Digital Human": MODE_DIGITAL_HUMAN,
        [MODE_SEGMENTS]: MODE_SEGMENTS,
        "\u4e0a\u4e0b\u6587\u5206\u6bb5": MODE_SEGMENTS,
        "Context Segments": MODE_SEGMENTS,
    },
    audio_mode: {
        [CONTEXT_AUDIO_GENERATED]: CONTEXT_AUDIO_GENERATED,
        "\u751f\u6210\u97f3\u9891": CONTEXT_AUDIO_GENERATED,
        "Generated Audio": CONTEXT_AUDIO_GENERATED,
        [MODE_DIGITAL_HUMAN]: MODE_DIGITAL_HUMAN,
        "\u6570\u5b57\u4eba\uff08Media \u97f3\u9891\u9a71\u52a8\uff09": MODE_DIGITAL_HUMAN,
        "Digital Human (Media Audio Drive)": MODE_DIGITAL_HUMAN,
    },
    keyframe_role: {
        first: "first",
        "\u9996\u5e27\u4f18\u5148": "first",
        "First frame priority": "first",
        last: "last",
        "\u5c3e\u5e27\u4f18\u5148": "last",
        "Last frame priority": "last",
    },
    ref_image_size: {
        [REF_IMAGE_MATCH]: REF_IMAGE_MATCH,
        "\u5339\u914d\u751f\u6210\u5206\u8fa8\u7387": REF_IMAGE_MATCH,
        "Match generation size": REF_IMAGE_MATCH,
        [REF_IMAGE_1K]: REF_IMAGE_1K,
        "\u77ed\u8fb9\u6700\u59271K\u50cf\u7d20": REF_IMAGE_1K,
        "Max 1K Short Edge": REF_IMAGE_1K,
        "1K \u9762\u79ef\uff08\u7ea61MP\uff09": REF_IMAGE_1K,
        "1K area (~1MP)": REF_IMAGE_1K,
        [REF_IMAGE_15K]: REF_IMAGE_15K,
        "1.5K \u9762\u79ef\uff08\u7ea62.25MP\uff09": REF_IMAGE_15K,
        "1.5K area (~2.25MP)": REF_IMAGE_15K,
        [REF_IMAGE_2K]: REF_IMAGE_2K,
        "\u77ed\u8fb9\u6700\u59272K\u50cf\u7d20": REF_IMAGE_2K,
        "Max 2K Short Edge": REF_IMAGE_2K,
        "2K \u9762\u79ef\uff08\u7ea64MP\uff09": REF_IMAGE_2K,
        "2K area (~4MP)": REF_IMAGE_2K,
        [REF_IMAGE_ORIGINAL]: REF_IMAGE_ORIGINAL,
        "\u539f\u56fe\uff08\u4e0d\u7f29\u653e\uff09": REF_IMAGE_ORIGINAL,
        "Original (no scaling)": REF_IMAGE_ORIGINAL,
    },
    reference_mention_mode: {
        filename: "filename",
        "\u6309\u6587\u4ef6\u540d": "filename",
        "By filename": "filename",
        index: "index",
        "\u6309\u5e8f\u53f7": "index",
        "By index": "index",
    },
    context_prompt_optimizer_mode: {
        whole_sequence: "whole_sequence",
        "\u6574\u4f53\u4f18\u5316": "whole_sequence",
        "Whole sequence": "whole_sequence",
        per_segment: "per_segment",
        "\u9010\u6bb5\u4f18\u5316": "per_segment",
        "Per segment": "per_segment",
    },
    empty_output_mode: {
        block_missing: "block_missing",
        "默认（跳过缺失输出）": "block_missing",
        "Default (Skip Missing Outputs)": "block_missing",
        "跳过缺失输出": "block_missing",
        "Skip Missing Outputs": "block_missing",
        "原有模式": "block_missing",
        "原有模式（空端口不报错）": "block_missing",
        "原有模式（阻断空端口分支）": "block_missing",
        original: "block_missing",
        "original mode": "block_missing",
        // Development builds briefly exposed a separate strict/count-check
        // choice.  Map those saved values to the preserved original mode.
        strict: "block_missing",
        "媒体数量校验": "block_missing",
        "Media Count Check": "block_missing",
        "严格模式": "block_missing",
        "严格模式（媒体不足时报错）": "block_missing",
        "Strict (error if media is missing)": "block_missing",
        "strict mode": "block_missing",
        error: "block_missing",
        allow_none: "allow_none",
        none: "allow_none",
        "允许空输出": "allow_none",
        "允许空输出（None）": "allow_none",
        "Allow empty outputs (None)": "allow_none",
        "allow empty outputs": "allow_none",
    },
};
const COLOR_IMAGE = "#5aa9f0";
const COLOR_LINK_BORDER = "rgba(0,0,0,0.5)";
const COMFY_NATIVE_LINK_COLOR = "#9A9";
const LABELS = {
    image: TEXT.image,
    video: TEXT.video,
    audio: TEXT.audio,
};
const LOADERS = {
    image: { classType: "LoadImage", label: TEXT.loadImage },
    video: { classType: "LoadVideo", label: TEXT.loadVideo },
    audio: { classType: "LoadAudio", label: TEXT.loadAudio },
};

let installed = false;
let patchedCanvas = false;
let patchedPrompt = false;
let linkMenu = null;
let createMenu = null;
let quickCreateCaptureCanvas = null;
let quickCreateCaptureCleanup = null;
let activePromptNode = null;
let lastCapturedDropAt = 0;
let deferredCreateMenuPending = false;
let deferredCreateMenuToken = 0;
const videoThumbnailCache = new Map();
let mentionPreviewRefreshTimer = null;
let suppressNativeDropUntil = 0;
let nativeSearchSuppressStyle = null;
let releaseCreateMenuLinkHold = null;
let nativeThemeWatcherInstalled = false;
let lastVueNodesMode = null;

function nodeMatchesClass(node, className, displayName, installedMarker) {
    if (!node) return false;
    if (node.constructor?.prototype?.[installedMarker]) return true;
    const candidates = [
        node.comfyClass,
        node.type,
        node.constructor?.comfyClass,
        node.constructor?.type,
        node.constructor?.nodeData?.name,
        node.constructor?.nodeData?.display_name,
        node.title,
    ];
    return candidates.some((value) => value != null && [className, displayName].includes(String(value)));
}

function isTarget(node) {
    return nodeMatchesClass(node, NODE_CLASS, TEXT.mainTitle, "__h3EasyNodeInstalled")
        || nodeMatchesClass(node, CONTEXT_SEGMENTS_CLASS, TEXT.contextSegmentsTitle, "__h3ContextSegmentsNodeInstalled")
        || nodeMatchesClass(node, SELECTED_VIDEO_CONTEXT_CLASS, TEXT.selectedVideoContextTitle, "__h3SelectedVideoContextNodeInstalled");
}

function isContextSegmentsNode(node) {
    return nodeMatchesClass(node, CONTEXT_SEGMENTS_CLASS, TEXT.contextSegmentsTitle, "__h3ContextSegmentsNodeInstalled");
}

function isSelectedVideoContextNode(node) {
    return nodeMatchesClass(node, SELECTED_VIDEO_CONTEXT_CLASS, TEXT.selectedVideoContextTitle, "__h3SelectedVideoContextNodeInstalled");
}

function isSelectedVideoContextSegmented(node) {
    if (!isSelectedVideoContextNode(node)) return false;
    const mode = canonicalOption(
        "selected_video_segment_mode",
        getWidgetValue(node, "segment_mode", SELECTED_VIDEO_SEGMENT_WHOLE),
    );
    return mode !== SELECTED_VIDEO_SEGMENT_WHOLE;
}

function isSegmentRefineNode(node) {
    return nodeMatchesClass(node, SEGMENT_REFINE_CLASS, TEXT.segmentRefineTitle, "__h3SegmentRefineInstalled");
}

function isSegmentSampleSetupNode(node) {
    return nodeMatchesClass(node, SEGMENT_SAMPLE_SETUP_CLASS, TEXT.segmentSampleSetupTitle, "__h3SegmentSampleSetupInstalled");
}

function isSegmentStepNode(node) {
    return nodeMatchesClass(node, SEGMENT_STEP_CLASS, TEXT.segmentStepTitle, "__h3SegmentStepInstalled");
}

function isSegmentCollectNode(node) {
    return nodeMatchesClass(node, SEGMENT_COLLECT_CLASS, TEXT.segmentCollectTitle, "__h3SegmentCollectInstalled");
}

function isLoader(node) {
    return nodeMatchesClass(node, LOADER_CLASS, TEXT.loaderTitle, "__h3EasyLoaderInstalled");
}

function isAdapter(node) {
    return nodeMatchesClass(node, ADAPTER_CLASS, TEXT.adapterTitle, "__h3EasyAdapterInstalled");
}

function isMediaBridge(node) {
    return nodeMatchesClass(node, MEDIA_BRIDGE_CLASS, TEXT.mediaBridgeTitle, "__h3EasyMediaBridgeInstalled");
}

function isMediaSplitter(node) {
    return nodeMatchesClass(node, MEDIA_SPLITTER_CLASS, TEXT.mediaSplitterTitle, "__h3EasyMediaSplitterInstalled");
}

function isMediaLoader(node) {
    return nodeMatchesClass(node, MEDIA_LOADER_CLASS, TEXT.mediaLoaderTitle, "__h3EasyMediaLoaderInstalled");
}

function isMediaBridgeOutput(node, sourceSlot = 0, sourceType = "") {
    if (isMediaBridge(node) || isMediaLoader(node)) return true;
    const output = node?.outputs?.[Number(sourceSlot) || 0] || {};
    const type = String(sourceType || output.type || "").trim().toUpperCase();
    return type === MEDIA_BUNDLE_TYPE || String(output.name || "").toLowerCase() === "media_bundle";
}

function isOutput(node) {
    return nodeMatchesClass(node, OUTPUT_CLASS, TEXT.outputTitle, "__h3EasyOutputInstalled");
}

function mediaBridgeGroupForInput(name) {
    const match = /^(image|video|audio)_(\d+)$/.exec(String(name || ""));
    if (!match) return null;
    return { type: match[1], index: Number(match[2]) };
}

function isMediaBridgeManagedInputName(name) {
    return Boolean(mediaBridgeGroupForInput(name));
}

function mediaBridgeCount(node, group) {
    const raw = Number(getWidget(node, group.count)?.value);
    if (!Number.isFinite(raw)) return 0;
    return Math.max(0, Math.min(group.max, Math.floor(raw)));
}

function desiredMediaBridgeInputNames(node) {
    const names = [];
    for (const group of MEDIA_BRIDGE_GROUPS) {
        for (let index = 1; index <= mediaBridgeCount(node, group); index += 1) {
            names.push(`${group.type}_${index}`);
        }
    }
    return names;
}

function clampMediaBridgeWidgetValue(widget, group, value) {
    if (!widget) return 0;
    const parsed = Number.parseInt(value ?? widget.value ?? 0, 10);
    const clamped = Number.isFinite(parsed) ? Math.max(0, Math.min(group.max, parsed)) : 0;
    widget.value = clamped;
    return clamped;
}

function mediaBridgeInputLabel(name) {
    const parsed = mediaBridgeGroupForInput(name);
    if (!parsed) return String(name || "");
    const label = TEXT[parsed.type] || parsed.type;
    return `${label} ${parsed.index}`;
}

function findInputByName(node, name) {
    return (node?.inputs || []).find((input) => input?.name === name) || null;
}

function removeMediaBridgeInputAt(node, index) {
    if (typeof node.removeInput === "function") {
        node.removeInput(index);
        return;
    }
    if (node.inputs?.[index]?.link != null) node.disconnectInput?.(index);
    node.inputs?.splice(index, 1);
}

function updateMediaBridgeInputLinkTargets(node) {
    const graph = node?.graph || app.graph;
    if (!graph || !Array.isArray(node?.inputs)) return;
    node.inputs.forEach((input, index) => {
        if (input?.link == null) return;
        const link = getNativeGraphLink(graph, input.link);
        if (link) link.target_slot = index;
    });
}

function rebuildMediaBridgeInputs(node, desiredNames) {
    const desired = new Set(desiredNames);
    const desiredOrder = new Map(desiredNames.map((name, index) => [name, index]));
    const seen = new Set();
    const removeSlots = [];

    for (let index = 0; index < (node.inputs || []).length; index += 1) {
        const input = node.inputs[index];
        if (!isMediaBridgeManagedInputName(input?.name)) continue;
        if (!desired.has(input.name) || seen.has(input.name)) removeSlots.push(index);
        else seen.add(input.name);
    }
    for (const slot of removeSlots.reverse()) removeMediaBridgeInputAt(node, slot);

    let changed = removeSlots.length > 0;
    for (const name of desiredNames) {
        if (findInputByName(node, name)) continue;
        if (typeof node.addInput === "function") node.addInput(name, "*");
        else {
            node.inputs ||= [];
            node.inputs.push({ name, type: "*", link: null });
        }
        changed = true;
    }

    const managed = [];
    const unmanaged = [];
    for (const input of node.inputs || []) {
        if (!isMediaBridgeManagedInputName(input?.name)) {
            unmanaged.push(input);
            continue;
        }
        if (!desired.has(input.name)) continue;
        input.type ||= "*";
        const label = mediaBridgeInputLabel(input.name);
        setLocalizedSlotLabel(input, label);
        input.display_name = label;
        managed.push(input);
    }
    managed.sort((a, b) => desiredOrder.get(a.name) - desiredOrder.get(b.name));
    const sorted = [...managed, ...unmanaged];
    const orderChanged = sorted.length !== (node.inputs || []).length
        || sorted.some((input, index) => input !== node.inputs[index]);
    if (changed || orderChanged) {
        node.inputs ||= [];
        node.inputs.splice(0, node.inputs.length, ...sorted);
        updateMediaBridgeInputLinkTargets(node);
        node._widgetSlotsDirty = true;
        node.setDirtyCanvas?.(true, true);
        node.graph?.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
        return true;
    }
    return false;
}

function mediaBridgeSignature(node) {
    return MEDIA_BRIDGE_GROUPS.map((group) => mediaBridgeCount(node, group)).join(":");
}

function updateMediaBridgeWidgets(node, options = {}) {
    if (!node || node.__h3MediaBridgeUpdating) return false;
    node.__h3MediaBridgeUpdating = true;
    try {
        const desiredNames = desiredMediaBridgeInputNames(node);
        const signature = mediaBridgeSignature(node);
        if (!options.force && node.__h3MediaBridgeSignature === signature) return false;
        node.__h3MediaBridgeSignature = signature;
        const changed = rebuildMediaBridgeInputs(node, desiredNames);
        localizeNodeInstance(node);
        refreshVueNodeWidgets(node);
        if (changed) repairNodeLayout(node);
        return changed;
    } finally {
        node.__h3MediaBridgeUpdating = false;
    }
}

function trimMediaBridgeNodeDataInputs(nodeData) {
    if (!nodeData?.input) return;
    const managed = /^(image|video|audio)_\d+$/;
    for (const section of ["required", "optional"]) {
        if (!nodeData.input[section] || typeof nodeData.input[section] !== "object") continue;
        for (const name of Object.keys(nodeData.input[section])) {
            if (managed.test(name)) delete nodeData.input[section][name];
        }
    }
    if (Array.isArray(nodeData.input_order?.required)) {
        nodeData.input_order.required = nodeData.input_order.required.filter((name) => !managed.test(String(name)));
    }
    if (Array.isArray(nodeData.input_order?.optional)) {
        nodeData.input_order.optional = nodeData.input_order.optional.filter((name) => !managed.test(String(name)));
    }
}

function canonicalOption(name, value) {
    const raw = String(value ?? "");
    const alias = OPTION_ALIASES[name]?.[raw];
    if (alias !== undefined) return alias;
    const definition = OPTION_DEFS[name];
    if (definition) {
        for (const [key, label] of Object.entries(definition)) {
            if (raw === key || raw === label) return key;
        }
    }
    return raw;
}

function canonicalPromptGuide(value) {
    const raw = String(value ?? "");
    const found = PROMPT_GUIDES.find((item) => raw === item.value || raw === item.zh || raw === item.en);
    return found?.value || "none";
}

function localizeComboWidget(widget, node = null) {
    const name = String(widget?.name || "");
    if (name === "prompt_optimizer_scene_guide") {
        const current = canonicalPromptGuide(widget?.value);
        widget.options ||= {};
        widget.options.values = PROMPT_GUIDES.map((item) => ZH_BROWSER ? item.zh : item.en);
        widget.value = PROMPT_GUIDES.find((item) => item.value === current)?.[ZH_BROWSER ? "zh" : "en"] || widget.value;
        widget.__h3PromptGuideLocalized = true;
        return;
    }
    let definition = name === "segment_mode"
        ? OPTION_DEFS.selected_video_segment_mode
        : OPTION_DEFS[name];
    if (name === "mode" && node) {
        definition = isContextSegmentsNode(node)
            ? { [MODE_SEGMENTS]: OPTION_DEFS.mode[MODE_SEGMENTS] }
            : {
                [MODE_IMAGE]: OPTION_DEFS.mode[MODE_IMAGE],
                [MODE_REFERENCE]: OPTION_DEFS.mode[MODE_REFERENCE],
                [MODE_DIGITAL_HUMAN]: OPTION_DEFS.mode[MODE_DIGITAL_HUMAN],
            };
    }
    if (!widget || !definition) return;
    const current = canonicalOption(name, widget.value);
    widget.__h3OptionName = name;
    widget.options ||= {};
    widget.options.values = Object.values(definition);
    widget.value = definition[current] ?? widget.value;
}

function isNoneModelValue(value) {
    const normalized = String(value ?? "").trim().toLowerCase();
    return normalized === "none" || normalized === "\u65e0";
}

function localizeOptionalModelWidget(widget) {
    if (!widget) return;
    widget.options ||= {};
    const values = Array.isArray(widget.options.values) ? widget.options.values : [];
    widget.options.values = [...new Set(values.map((value) => isNoneModelValue(value) ? TEXT.noneModel : value))];
    if (isNoneModelValue(widget.value)) widget.value = TEXT.noneModel;
}

function installPasswordWidgetMask(widget) {
    if (!widget) return;
    widget.options ||= {};
    widget.options.password = true;

    const applyPasswordInput = (input) => {
        if (!input) return;
        input.type = "password";
        input.autocomplete = "off";
        input.spellcheck = false;
    };
    applyPasswordInput(widget.inputEl || widget.element);

    if (!widget.__h3PasswordDisplayMasked) {
        try {
            Object.defineProperty(widget, "_displayValue", {
                configurable: true,
                get() {
                    if (this.computedDisabled) return "";
                    return "\u2022".repeat(Array.from(String(this.value ?? "")).length);
                },
            });
            widget.__h3PasswordDisplayMasked = true;
        } catch {
            // Older widget implementations may not expose a configurable display layer.
        }
    }

    if (!widget.__h3PasswordClickMasked && typeof widget.onClick === "function") {
        widget.__h3PasswordClickMasked = true;
        const originalOnClick = widget.onClick;
        widget.onClick = function onClickH3Password(options) {
            const result = originalOnClick.apply(this, arguments);
            applyPasswordInput(options?.canvas?.prompt_box?.querySelector?.("input.value"));
            return result;
        };
    }
}

function setLocalizedSlotLabel(slot, label) {
    if (!slot || !label) return;
    slot.label = label;
    slot.localized_name = label;
}

function localizeNodeInstance(node) {
    if (!node) return;
    if (isMediaSplitter(node)) {
        node.title = TEXT.mediaSplitterTitle;
        const countLabels = {
            image_count: TEXT.imageCount,
            video_count: TEXT.videoCount,
            audio_count: TEXT.audioCount,
            empty_output_mode: TEXT.mediaSplitterEmptyOutputMode,
        };
        for (const widget of node.widgets || []) {
            if (countLabels[widget.name]) widget.label = countLabels[widget.name];
            localizeComboWidget(widget, node);
        }
        for (const input of node.inputs || []) {
            if (input.name === "media_bundle") setLocalizedSlotLabel(input, TEXT.mediaBundle);
        }
        for (const output of node.outputs || []) {
            if (mediaSplitterGroupForOutput(output.name)) {
                setLocalizedSlotLabel(output, mediaSplitterOutputLabel(output.name));
            }
        }
        return;
    }
    if (isMediaLoader(node)) {
        node.title = TEXT.mediaLoaderTitle;
        for (const output of node.outputs || []) {
            if (String(output.name || "").toLowerCase() === "media_bundle") setLocalizedSlotLabel(output, TEXT.mediaBundle);
        }
        return;
    }
    if (isMediaBridge(node)) {
        node.title = TEXT.mediaBridgeTitle;
        const countLabels = {
            image_count: TEXT.imageCount,
            video_count: TEXT.videoCount,
            audio_count: TEXT.audioCount,
        };
        for (const widget of node.widgets || []) {
            if (countLabels[widget.name]) widget.label = countLabels[widget.name];
        }
        for (const input of node.inputs || []) {
            if (isMediaBridgeManagedInputName(input.name)) setLocalizedSlotLabel(input, mediaBridgeInputLabel(input.name));
        }
        for (const output of node.outputs || []) {
            if (String(output.name || "").toLowerCase() === "media_bundle") setLocalizedSlotLabel(output, TEXT.mediaBundle);
        }
        return;
    }
    if (isLoader(node)) {
        node.title = TEXT.loaderTitle;
        const labels = { fl2va_model: TEXT.fl2vaModel, ref2va_model: TEXT.ref2vaModel, text_encoder: TEXT.textEncoder, video_vae: TEXT.videoVae, audio_vae: TEXT.audioVae };
        for (const widget of node.widgets || []) {
            if (labels[widget.name]) widget.label = labels[widget.name];
            if (widget.name === "fl2va_model" || widget.name === "ref2va_model") localizeOptionalModelWidget(widget);
        }
        for (const input of node.inputs || []) if (labels[input.name]) setLocalizedSlotLabel(input, labels[input.name]);
        return;
    }
    if (isAdapter(node)) {
        node.title = TEXT.adapterTitle;
        const labels = { fl2va_model: TEXT.fl2vaModel, ref2va_model: TEXT.ref2vaModel, text_encoder: TEXT.textEncoder, video_vae: TEXT.videoVae, audio_vae: TEXT.audioVae };
        for (const input of node.inputs || []) if (labels[input.name]) setLocalizedSlotLabel(input, labels[input.name]);
        for (const output of node.outputs || []) if (String(output.name || "").toLowerCase() === "h3_bundle") setLocalizedSlotLabel(output, TEXT.bundle);
        return;
    }
    if (isOutput(node)) {
        node.title = TEXT.outputTitle;
        for (const input of node.inputs || []) {
            if (input.name === "h3_context") setLocalizedSlotLabel(input, TEXT.outputContext);
        }
        const outputLabels = { positive: TEXT.outputConditioning, latent: TEXT.outputLatent, video_vae: TEXT.outputVideoVae, audio_vae: TEXT.outputAudioVae, fps: TEXT.outputFps, driving_audio: TEXT.drivingAudio };
        for (const output of node.outputs || []) {
            const key = String(output.name || "").toLowerCase();
            if (outputLabels[key]) setLocalizedSlotLabel(output, outputLabels[key]);
        }
        return;
    }
    if (nodeMatchesClass(node, SEGMENT_RENDER_CLASS, TEXT.segmentRenderTitle, "__h3SegmentRenderInstalled")) {
        node.title = TEXT.segmentRenderTitle;
        const widgetLabels = { seed: TEXT.seedLabel, segment_seeds: TEXT.segmentSeeds };
        for (const widget of node.widgets || []) {
            if (widgetLabels[widget.name]) widget.label = widgetLabels[widget.name];
        }
        const inputLabels = { h3_context: TEXT.outputContext, model: TEXT.outputModel };
        for (const input of node.inputs || []) {
            if (inputLabels[input.name]) setLocalizedSlotLabel(input, inputLabels[input.name]);
        }
        const outputLabels = { segments: TEXT.segmentResult };
        for (const output of node.outputs || []) {
            if (outputLabels[output.name]) setLocalizedSlotLabel(output, outputLabels[output.name]);
        }
        return;
    }
    if (isSegmentStepNode(node)) {
        node.title = TEXT.segmentStepTitle;
        const widgetLabels = {
            seed: TEXT.seedLabel,
        };
        for (const widget of node.widgets || []) {
            if (widgetLabels[widget.name]) widget.label = widgetLabels[widget.name];
            localizeComboWidget(widget, node);
        }
        const inputLabels = {
            sample_setup: TEXT.segmentSampleSetupPort,
            previous_segment: TEXT.previousSegment,
            prompt_override: TEXT.promptOverride,
        };
        for (const input of node.inputs || []) {
            if (inputLabels[input.name]) setLocalizedSlotLabel(input, inputLabels[input.name]);
        }
        for (const output of node.outputs || []) {
            if (output.name === "segment") setLocalizedSlotLabel(output, TEXT.segmentResult);
        }
        return;
    }
    if (isSegmentSampleSetupNode(node)) {
        node.title = TEXT.segmentSampleSetupTitle;
        const inputLabels = {
            h3_context: TEXT.outputContext,
            model: TEXT.outputModel,
        };
        for (const input of node.inputs || []) {
            if (inputLabels[input.name]) setLocalizedSlotLabel(input, inputLabels[input.name]);
        }
        for (const [index, output] of (node.outputs || []).entries()) {
            if (index === 0 || output.name === "setup" || output.name === "sample_setup") {
                setLocalizedSlotLabel(output, TEXT.segmentSampleSetupPort);
            }
        }
        return;
    }
    if (isSegmentCollectNode(node)) {
        node.title = TEXT.segmentCollectTitle;
        for (const input of node.inputs || []) {
            if (input.name === "final_segment") setLocalizedSlotLabel(input, TEXT.segmentResult);
        }
        for (const output of node.outputs || []) {
            if (output.name === "segments") setLocalizedSlotLabel(output, TEXT.segmentResult);
        }
        return;
    }
    if (nodeMatchesClass(node, SEGMENT_REFINE_CLASS, TEXT.segmentRefineTitle, "__h3SegmentRefineInstalled")) {
        node.title = TEXT.segmentRefineTitle;
        const widgetLabels = {
            refine_mode: TEXT.refineMode,
            refine_execution: TEXT.refineExecution,
            tile_width: TEXT.tileWidth,
            tile_height: TEXT.tileHeight,
            tile_overlap: TEXT.tileOverlap,
            tile_fade: TEXT.tileFade,
            segment_seeds: TEXT.segmentSeeds,
        };
        for (const widget of node.widgets || []) {
            if (widgetLabels[widget.name]) widget.label = widgetLabels[widget.name];
            localizeComboWidget(widget, node);
        }
        const inputLabels = { h3_context: TEXT.outputContext, segments: TEXT.segmentResult, model: TEXT.outputModel };
        for (const input of node.inputs || []) {
            if (inputLabels[input.name]) setLocalizedSlotLabel(input, inputLabels[input.name]);
        }
        const outputLabels = { refined_segments: TEXT.segmentResult };
        for (const output of node.outputs || []) {
            if (outputLabels[output.name]) setLocalizedSlotLabel(output, outputLabels[output.name]);
        }
        return;
    }
    if (nodeMatchesClass(node, SEGMENT_DECODE_CLASS, TEXT.segmentDecodeTitle, "__h3SegmentDecodeInstalled")) {
        node.title = TEXT.segmentDecodeTitle;
        for (const input of node.inputs || []) {
            if (input.name === "segments") setLocalizedSlotLabel(input, TEXT.segmentResult);
        }
        const outputLabels = { preview: TEXT.segmentPreview };
        for (const output of node.outputs || []) {
            if (outputLabels[output.name]) setLocalizedSlotLabel(output, outputLabels[output.name]);
        }
        return;
    }
    if (!isTarget(node)) return;
    node.title = isContextSegmentsNode(node)
        ? TEXT.contextSegmentsTitle
        : isSelectedVideoContextNode(node)
            ? TEXT.selectedVideoContextTitle
            : TEXT.mainTitle;
    const labels = {
        mode: TEXT.mode,
        prompt: TEXT.prompt,
        selected_video: TEXT.selectedVideoInput,
        segment_mode: TEXT.selectedVideoSegmentMode,
        segment_cuts: TEXT.selectedVideoTimeCuts,
        audio_mode: TEXT.audioMode,
        resolution: TEXT.resolution,
        aspect_ratio: TEXT.aspectRatio,
        width: TEXT.width,
        height: TEXT.height,
        seconds: TEXT.seconds,
        advanced: TEXT.advanced,
        prompt_optimizer: TEXT.promptOptimizer,
        prompt_optimizer_api_format: TEXT.promptOptimizerApiFormat,
        prompt_optimizer_api_url: TEXT.promptOptimizerApiUrl,
        prompt_optimizer_api_key: TEXT.promptOptimizerApiKey,
        prompt_optimizer_model: TEXT.promptOptimizerModel,
        prompt_optimizer_scene_guide: TEXT.promptOptimizerSceneGuide,
        prompt_optimizer_read_media: TEXT.promptOptimizerReadMedia,
        prompt_optimizer_optimize_on_run: TEXT.promptOptimizerOptimizeOnRun,
        context_prompt_optimizer_mode: TEXT.contextPromptOptimizerMode,
        context_prompt_optimizer_concurrency: TEXT.contextPromptOptimizerConcurrency,
        fps: TEXT.fps,
        keyframe_role: TEXT.keyframeRole,
        ref_image_size: TEXT.refImageSize,
        reference_mention_mode: TEXT.referenceMentionMode,
        segment_seconds: TEXT.segmentSeconds,
        context_length: TEXT.contextLength,
        continuity_mode: TEXT.continuityMode,
    };
    for (const widget of node.widgets || []) {
        if (labels[widget.name]) widget.label = labels[widget.name];
        localizeComboWidget(widget, node);
        if (widget.name === "prompt_optimizer_api_key") installPasswordWidgetMask(widget);
    }
    for (const input of node.inputs || []) {
        if (input.name === "h3_bundle") setLocalizedSlotLabel(input, TEXT.bundle);
        if (input.name === "media") setLocalizedSlotLabel(input, TEXT.inputMedia);
        if (input.name === "selected_video") setLocalizedSlotLabel(input, TEXT.selectedVideoInput);
    }
    const outputLabels = { model: TEXT.outputModel, h3_context: TEXT.outputContext };
    for (const output of node.outputs || []) {
        const key = String(output.name || "").toLowerCase();
        if (outputLabels[key]) setLocalizedSlotLabel(output, outputLabels[key]);
    }
}

function localizeNodeDefinition(nodeData) {
    if (!nodeData || ![NODE_CLASS, CONTEXT_SEGMENTS_CLASS, SELECTED_VIDEO_CONTEXT_CLASS, LOADER_CLASS, ADAPTER_CLASS, MEDIA_LOADER_CLASS, MEDIA_BRIDGE_CLASS, MEDIA_SPLITTER_CLASS, OUTPUT_CLASS, SEGMENT_RENDER_CLASS, SEGMENT_SAMPLE_SETUP_CLASS, SEGMENT_STEP_CLASS, SEGMENT_COLLECT_CLASS, SEGMENT_REFINE_CLASS, SEGMENT_DECODE_CLASS].includes(nodeData.name)) return;
    nodeData.display_name = nodeData.name === LOADER_CLASS
        ? TEXT.loaderTitle
        : nodeData.name === ADAPTER_CLASS
            ? TEXT.adapterTitle
            : nodeData.name === MEDIA_LOADER_CLASS
                ? TEXT.mediaLoaderTitle
            : nodeData.name === MEDIA_BRIDGE_CLASS
            ? TEXT.mediaBridgeTitle
            : nodeData.name === MEDIA_SPLITTER_CLASS
            ? TEXT.mediaSplitterTitle
            : nodeData.name === OUTPUT_CLASS
            ? TEXT.outputTitle
              : nodeData.name === SEGMENT_RENDER_CLASS
              ? TEXT.segmentRenderTitle
              : nodeData.name === SEGMENT_SAMPLE_SETUP_CLASS
              ? TEXT.segmentSampleSetupTitle
              : nodeData.name === SEGMENT_STEP_CLASS
             ? TEXT.segmentStepTitle
             : nodeData.name === SEGMENT_COLLECT_CLASS
             ? TEXT.segmentCollectTitle
             : nodeData.name === SEGMENT_REFINE_CLASS
            ? TEXT.segmentRefineTitle
            : nodeData.name === SEGMENT_DECODE_CLASS
            ? TEXT.segmentDecodeTitle
            : nodeData.name === CONTEXT_SEGMENTS_CLASS
            ? TEXT.contextSegmentsTitle
            : nodeData.name === SELECTED_VIDEO_CONTEXT_CLASS
            ? TEXT.selectedVideoContextTitle
            : TEXT.mainTitle;
    nodeData.category = TEXT.category;
}

function getWidget(node, name) {
    return node?.widgets?.find((widget) => widget?.name === name) || null;
}

function getWidgetValue(node, name, fallback = "") {
    const widget = getWidget(node, name);
    return widget?.value ?? fallback;
}

function asBoolean(value, fallback = false) {
    if (typeof value === "boolean") return value;
    if (typeof value === "number") return value !== 0;
    if (typeof value === "string") {
        const normalized = value.trim().toLowerCase();
        if (["", "0", "false", "off", "no"].includes(normalized)) return false;
        if (["1", "true", "on", "yes"].includes(normalized)) return true;
    }
    return value == null ? fallback : Boolean(value);
}

function isReferenceMode(node) {
    const mode = canonicalOption("mode", getWidgetValue(node, "mode", MODE_IMAGE));
    return mode === MODE_REFERENCE || mode === MODE_DIGITAL_HUMAN;
}

function mediaSplitterGroupForOutput(name) {
    const match = /^(image|video|audio)_(\d+)$/.exec(String(name || ""));
    if (!match) return null;
    return { type: match[1], index: Number(match[2]) };
}

function mediaSplitterCount(node, group) {
    const raw = Number(getWidget(node, group.count)?.value);
    if (!Number.isFinite(raw)) return 0;
    return Math.max(0, Math.min(group.max, Math.floor(raw)));
}

function desiredMediaSplitterOutputNames(node) {
    const names = [];
    for (const group of MEDIA_SPLITTER_GROUPS) {
        for (let index = 1; index <= mediaSplitterCount(node, group); index += 1) {
            names.push(`${group.type}_${index}`);
        }
    }
    return names;
}

function clampMediaSplitterWidgetValue(widget, group, value) {
    if (!widget) return 0;
    const parsed = Number.parseInt(value ?? widget.value ?? 0, 10);
    const clamped = Number.isFinite(parsed) ? Math.max(0, Math.min(group.max, parsed)) : 0;
    widget.value = clamped;
    return clamped;
}

function mediaSplitterOutputLabel(name) {
    const parsed = mediaSplitterGroupForOutput(name);
    if (!parsed) return String(name || "");
    const label = TEXT[parsed.type] || parsed.type;
    return `${label} ${parsed.index}`;
}

function mediaSplitterOutputType(name) {
    const parsed = mediaSplitterGroupForOutput(name);
    return parsed ? (MEDIA_SPLITTER_OUTPUT_TYPES[parsed.type] || "*") : "*";
}

function trimMediaSplitterNodeDataOutputs(nodeData) {
    if (!nodeData) return;
    const managed = /^(image|video|audio)_\d+$/;
    const names = Array.isArray(nodeData.output_name) ? nodeData.output_name : null;
    const outputTypes = Array.isArray(nodeData.output) ? nodeData.output : null;
    if (names && outputTypes) {
        const keep = names
            .map((name, index) => ({ name: String(name || ""), index }))
            .filter(({ name }) => !managed.test(name))
            .map(({ index }) => index);
        const filterByKeep = (value) => Array.isArray(value) ? keep.map((index) => value[index]) : value;
        nodeData.output = filterByKeep(outputTypes);
        nodeData.output_name = filterByKeep(names);
        if (Array.isArray(nodeData.output_is_list)) nodeData.output_is_list = filterByKeep(nodeData.output_is_list);
        if (Array.isArray(nodeData.output_tooltips)) nodeData.output_tooltips = filterByKeep(nodeData.output_tooltips);
        return;
    }
    // Older ComfyUI builds may expose a frontend `outputs` array instead of
    // the object-info parallel arrays. Keep the same cleanup compatible there.
    if (Array.isArray(nodeData.outputs)) {
        nodeData.outputs = nodeData.outputs.filter((output) => !managed.test(String(output?.name || "")));
    }
}

function updateMediaSplitterOutputLinkTargets(node) {
    const graph = node?.graph || app.graph;
    if (!graph || !Array.isArray(node?.outputs)) return;
    node.outputs.forEach((output, index) => {
        const rawLinks = Array.isArray(output?.links)
            ? output.links
            : output?.link == null ? [] : [output.link];
        for (const linkId of rawLinks) {
            const link = getNativeGraphLink(graph, linkId);
            if (!link) continue;
            // LiteGraph uses origin_slot. The aliases cover the current Vue
            // graph adapter and older workflow snapshots without changing
            // the link's identity.
            link.origin_slot = index;
            if ("originSlot" in link) link.originSlot = index;
            if ("from_slot" in link) link.from_slot = index;
            if ("fromSlot" in link) link.fromSlot = index;
        }
    });
}

function resizeMediaSplitterToContent(node) {
    if (!node || typeof node.computeSize !== "function" || typeof node.setSize !== "function") return;
    const measured = node.computeSize();
    if (!Array.isArray(measured) || !Number.isFinite(Number(measured[1]))) return;
    const currentWidth = Math.max(240, Number(node.size?.[0]) || 0, Number(measured[0]) || 0);
    const currentHeight = Number(node.size?.[1]) || 0;
    const targetHeight = Math.max(1, Math.ceil(Number(measured[1])));
    // Splitter has no expandable content area, so keeping the height equal to
    // its active output list avoids the giant 45-port box left by the static
    // backend schema. Width is preserved when the user made it wider.
    if (Math.abs(currentHeight - targetHeight) > 1) node.setSize([currentWidth, targetHeight]);
}

function removeMediaSplitterOutputAt(node, index) {
    const output = node?.outputs?.[index];
    const graph = node?.graph || app.graph;
    const links = Array.isArray(output?.links)
        ? [...output.links]
        : output?.link == null ? [] : [output.link];
    if (typeof node.removeOutput !== "function" && graph?.removeLink) {
        for (const linkId of links) graph.removeLink(linkId);
    }
    if (typeof node.removeOutput === "function") {
        node.removeOutput(index);
        return;
    }
    node.outputs?.splice(index, 1);
}

function rebuildMediaSplitterOutputs(node, desiredNames) {
    const desired = new Set(desiredNames);
    const desiredOrder = new Map(desiredNames.map((name, index) => [name, index]));
    const removeSlots = [];
    const seen = new Set();
    for (let index = 0; index < (node.outputs || []).length; index += 1) {
        const output = node.outputs[index];
        if (!mediaSplitterGroupForOutput(output?.name)) continue;
        if (!desired.has(output.name) || seen.has(output.name)) removeSlots.push(index);
        else seen.add(output.name);
    }
    for (const slot of removeSlots.reverse()) removeMediaSplitterOutputAt(node, slot);

    let changed = removeSlots.length > 0;
    for (const name of desiredNames) {
        if (node.outputs?.some((output) => output?.name === name)) continue;
        if (typeof node.addOutput === "function") node.addOutput(name, mediaSplitterOutputType(name));
        else {
            node.outputs ||= [];
            node.outputs.push({ name, type: mediaSplitterOutputType(name), links: null });
        }
        changed = true;
    }

    const managed = [];
    const unmanaged = [];
    for (const output of node.outputs || []) {
        if (!mediaSplitterGroupForOutput(output?.name)) {
            unmanaged.push(output);
            continue;
        }
        if (!desired.has(output.name)) continue;
        output.type = mediaSplitterOutputType(output.name);
        const label = mediaSplitterOutputLabel(output.name);
        setLocalizedSlotLabel(output, label);
        output.display_name = label;
        managed.push(output);
    }
    managed.sort((a, b) => desiredOrder.get(a.name) - desiredOrder.get(b.name));
    const sorted = [...managed, ...unmanaged];
    const orderChanged = sorted.length !== (node.outputs || []).length
        || sorted.some((output, index) => output !== node.outputs[index]);
    if (changed || orderChanged) {
        node.outputs ||= [];
        node.outputs.splice(0, node.outputs.length, ...sorted);
        updateMediaSplitterOutputLinkTargets(node);
        node._widgetSlotsDirty = true;
        node.setDirtyCanvas?.(true, true);
        node.graph?.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
        return true;
    }
    return false;
}

function mediaSplitterSignature(node) {
    return MEDIA_SPLITTER_GROUPS.map((group) => mediaSplitterCount(node, group)).join(":");
}

function updateMediaSplitterWidgets(node, options = {}) {
    if (!node || node.__h3MediaSplitterUpdating) return false;
    node.__h3MediaSplitterUpdating = true;
    try {
        const signature = mediaSplitterSignature(node);
        if (!options.force && node.__h3MediaSplitterSignature === signature) return false;
        node.__h3MediaSplitterSignature = signature;
        const changed = rebuildMediaSplitterOutputs(node, desiredMediaSplitterOutputNames(node));
        localizeNodeInstance(node);
        refreshVueNodeWidgets(node);
        if (changed) {
            resizeMediaSplitterToContent(node);
            repairNodeLayout(node);
        }
        return changed;
    } finally {
        node.__h3MediaSplitterUpdating = false;
    }
}

function mediaReferenceMode(node) {
    return isReferenceMode(node) || isContextSegmentsNode(node) || isSelectedVideoContextNode(node);
}

// Context Segments uses the same media-mention editor as reference mode, but
// remains a separate execution mode and does not inherit reference-only UI.
function canUseMediaMentions(node) {
    return isReferenceMode(node) || isContextSegmentsNode(node) || isSelectedVideoContextNode(node);
}

function isSegmentMode(node) {
    return canonicalOption("mode", getWidgetValue(node, "mode", MODE_IMAGE)) === MODE_SEGMENTS;
}

function isCustomResolution(node) {
    return canonicalOption("resolution", getWidgetValue(node, "resolution", "480P")) === RESOLUTION_CUSTOM;
}

function isAdvancedEnabled(node) {
    return asBoolean(getWidgetValue(node, "advanced", false));
}

function referenceMentionMode(node) {
    const value = canonicalOption("reference_mention_mode", getWidgetValue(node, "reference_mention_mode", "index"));
    return value === "index" ? "index" : "filename";
}

function ensureLinks(node) {
    node.properties ||= {};
    if (!Array.isArray(node.properties[LINKS_PROP])) {
        node.properties[LINKS_PROP] = [];
    }
    return node.properties[LINKS_PROP];
}

function isSameNode(left, right) {
    if (!left || !right) return false;
    if (left === right) return true;
    const leftId = Number(left.id);
    const rightId = Number(right.id);
    return Number.isFinite(leftId) && Number.isFinite(rightId) && leftId === rightId;
}

function resequence(node) {
    const counts = { image: 0, video: 0, audio: 0 };
    ensureLinks(node).forEach((link) => {
        const mediaType = String(link.media_type || "image").toLowerCase();
        const sequenceType = Object.hasOwn(counts, mediaType) ? mediaType : "image";
        counts[sequenceType] += 1;
        link.order = counts[sequenceType];
    });
}

function normalizeLinks(node, removeMissing = true) {
    const links = ensureLinks(node);
    const normalized = [];
    const seen = new Set();
    for (const link of links) {
        const sourceId = Number(link?.source_id);
        const sourceSlot = Number(link?.source_slot) || 0;
        const mediaType = String(link?.media_type || "image").toLowerCase();
        if (!Number.isFinite(sourceId) || !["image", "video", "audio"].includes(mediaType)) continue;
        if (Number.isFinite(Number(node?.id)) && sourceId === Number(node.id)) continue;
        const key = `${sourceId}:${sourceSlot}:${mediaType}`;
        if (seen.has(key)) continue;
        const canResolveSource = typeof app.graph?.getNodeById === "function";
        const source = canResolveSource ? app.graph.getNodeById(sourceId) : null;
        if (removeMissing && canResolveSource && !source) continue;
        seen.add(key);
        normalized.push({ ...link, source_id: sourceId, source_slot: sourceSlot, media_type: mediaType });
    }
    const changed = normalized.length !== links.length || normalized.some((link, index) => {
        const previous = links[index];
        return !previous
            || Number(previous.source_id) !== link.source_id
            || Number(previous.source_slot) !== link.source_slot
            || String(previous.media_type || "image").toLowerCase() !== link.media_type;
    });
    if (changed) node.properties[LINKS_PROP] = normalized;
    else if (links.some((link) => !Number.isFinite(Number(link?.order)))) node.properties[LINKS_PROP] = normalized;
    resequence(node);
    return ensureLinks(node);
}

function getSlotType(slot) {
    return String(slot?.type || slot?.datatype || slot?.label || "").toUpperCase();
}

function getMediaType(sourceType, sourceNode = null) {
    const type = String(sourceType || "").toUpperCase();
    if (type.includes("AUDIO")) return "audio";
    if (type.includes("VIDEO")) return "video";
    if (type.includes("IMAGE")) return "image";
    const name = String(sourceNode?.comfyClass || sourceNode?.type || "").toLowerCase();
    if (name.includes("audio")) return "audio";
    if (name.includes("video")) return "video";
    return "image";
}

function mediaLimits(node) {
    if (isContextSegmentsNode(node)) {
        // The context node owns one media library for the full sequence. Each
        // prompt block selects its own H3-sized subset, so the library scales
        // with the maximum thirty blocks instead of the single-shot limit.
        const digitalAudio = canonicalOption("audio_mode", getWidgetValue(node, "audio_mode", CONTEXT_AUDIO_GENERATED)) === MODE_DIGITAL_HUMAN;
        return {
            image: SEGMENT_MAX_IMAGES,
            video: SEGMENT_MAX_VIDEOS,
            audio: digitalAudio ? 1 : SEGMENT_MAX_AUDIOS,
            total: SEGMENT_MAX_MEDIA,
        };
    }
    if (isSelectedVideoContextNode(node)) {
        return { image: MAX_IMAGES, video: MAX_VIDEOS, audio: MAX_AUDIOS, total: MAX_MEDIA };
    }
    if (canonicalOption("mode", getWidgetValue(node, "mode", MODE_IMAGE)) === MODE_DIGITAL_HUMAN) {
        return { image: MAX_IMAGES, video: MAX_VIDEOS, audio: 1, total: MAX_MEDIA };
    }
    if (!isReferenceMode(node)) {
        return { image: MAX_IMAGES, video: MAX_VIDEOS, audio: MAX_AUDIOS, total: MAX_MEDIA };
    }
    return { image: 9, video: 3, audio: 3, total: MAX_MEDIA };
}

function transportMediaLimit(node) {
    return isContextSegmentsNode(node) ? SEGMENT_MAX_MEDIA : MAX_MEDIA;
}

function hasVirtualMediaLinks(node) {
    return isTarget(node) && normalizeLinks(node).length > 0;
}

function canCreateMediaLoaderFor(node) {
    return isTarget(node) && !hasVirtualMediaLinks(node) && !getNativeMediaBridgeLink(node);
}

function canAccept(node, mediaType) {
    if (!isTarget(node) || getNativeMediaBridgeLink(node)) return false;
    const limits = mediaLimits(node);
    if (!limits[mediaType]) return false;
    const links = ensureLinks(node);
    if (links.length >= limits.total) return false;
    const count = links.filter((link) => String(link.media_type || "image") === mediaType).length;
    return count < limits[mediaType];
}

function pruneLinksForMode(node) {
    const limits = mediaLimits(node);
    const counts = { image: 0, video: 0, audio: 0 };
    const kept = [];
    for (const link of ensureLinks(node)) {
        const type = String(link.media_type || "image");
        if (!limits[type] || counts[type] >= limits[type] || kept.length >= limits.total) continue;
        counts[type] += 1;
        kept.push(link);
    }
    node.properties[LINKS_PROP] = kept;
    resequence(node);
}

function getMediaInputIndex(node) {
    return node?.inputs?.findIndex((input) => String(input?.name || "") === "media") ?? -1;
}

function getConnectionPosition(node, isInput, slotIndex) {
    const normalize = (point) => Array.isArray(point) && Number.isFinite(point[0]) && Number.isFinite(point[1])
        ? [point[0], point[1]]
        : null;
    const modern = isInput
        ? normalize(node?.getInputPos?.(slotIndex))
        : normalize(node?.getOutputPos?.(slotIndex));
    if (modern) return modern;
    const out = [0, 0];
    try {
        if (typeof node?.getConnectionPos === "function") {
            const legacy = normalize(node.getConnectionPos(isInput, slotIndex, out)) || normalize(out);
            if (legacy) return legacy;
        }
    } catch {
        // Fall through to stable LiteGraph geometry.
    }
    const slot = 40 + Math.max(0, slotIndex) * 20;
    return isInput
        ? [Number(node?.pos?.[0] || 0), Number(node?.pos?.[1] || 0) + slot]
        : [Number(node?.pos?.[0] || 0) + Number(node?.size?.[0] || 160), Number(node?.pos?.[1] || 0) + slot];
}

function getMediaDot(node) {
    const index = getMediaInputIndex(node);
    if (index < 0) return null;
    const point = getConnectionPosition(node, true, index);
    return { x: point[0], y: point[1] };
}

function graphPosition(canvas, event) {
    try {
        canvas.adjustMouseEvent?.(event);
    } catch {
        // Older LiteGraph builds do not expose adjustMouseEvent.
    }
    if (Array.isArray(canvas?.graph_mouse)) return [canvas.graph_mouse[0], canvas.graph_mouse[1]];
    if (Number.isFinite(event?.canvasX) && Number.isFinite(event?.canvasY)) return [event.canvasX, event.canvasY];
    const rect = canvas?.canvas?.getBoundingClientRect?.();
    const scale = canvas?.ds?.scale || 1;
    const offset = canvas?.ds?.offset || [0, 0];
    if (rect && Number.isFinite(event?.clientX) && Number.isFinite(event?.clientY)) {
        return [(event.clientX - rect.left) / scale - offset[0], (event.clientY - rect.top) / scale - offset[1]];
    }
    return [0, 0];
}

function pointerGraphPosition(canvas, event) {
    if (Number.isFinite(event?.canvasX) && Number.isFinite(event?.canvasY)) return [event.canvasX, event.canvasY];
    const rect = canvas?.canvas?.getBoundingClientRect?.();
    if (rect && Number.isFinite(event?.clientX) && Number.isFinite(event?.clientY)) {
        const scale = canvas?.ds?.scale || 1;
        const offset = canvas?.ds?.offset || [0, 0];
        return [(event.clientX - rect.left) / scale - offset[0], (event.clientY - rect.top) / scale - offset[1]];
    }
    return graphPosition(canvas, event);
}

function clientPosition(canvas, point) {
    const rect = canvas?.canvas?.getBoundingClientRect?.();
    if (!rect) return null;
    const scale = canvas?.ds?.scale || 1;
    const offset = canvas?.ds?.offset || [0, 0];
    return { x: rect.left + (point[0] + offset[0]) * scale, y: rect.top + (point[1] + offset[1]) * scale };
}

function connectingOutput(canvas) {
    const node = canvas?.connecting_node || canvas?.connectingNode;
    if (!node) return null;
    const raw = canvas.connecting_output ?? canvas.connecting_slot ?? canvas.connecting_output_slot;
    if (raw == null && canvas.connecting_input) return null;
    const index = typeof raw === "number" ? raw : Number(raw?.slot_index ?? raw?.slot ?? 0);
    const output = node.outputs?.[Number.isFinite(index) ? index : 0] || raw || {};
    return {
        sourceNode: node,
        sourceSlot: Number.isFinite(index) ? index : 0,
        sourceType: getSlotType(output),
    };
}

function connectingInput(canvas) {
    const node = canvas?.connecting_node || canvas?.connectingNode;
    const input = canvas?.connecting_input || canvas?.connectingInput;
    if (!node || !input || !isTarget(node)) return null;
    const index = typeof input === "number" ? input : node.inputs?.indexOf(input);
    const slot = node.inputs?.[Number.isFinite(index) ? index : -1];
    if (String(slot?.name || input?.name || "") !== "media") return null;
    return { targetNode: node };
}

function clearConnecting(canvas) {
    canvas.connecting_node = null;
    canvas.connecting_output = null;
    canvas.connecting_slot = null;
    canvas.connecting_pos = null;
    canvas.connecting_input = null;
}

function addVirtualLink(targetNode, sourceNode, sourceSlot, sourceType, mediaType = null) {
    if (!targetNode || !sourceNode || isSameNode(targetNode, sourceNode)) return false;
    if (isMediaBridgeOutput(sourceNode, sourceSlot, sourceType) || getNativeMediaBridgeLink(targetNode)) return false;
    const sourceId = Number(sourceNode.id);
    if (!Number.isFinite(sourceId)) return false;
    mediaType ||= getMediaType(sourceType, sourceNode);
    if (!canAccept(targetNode, mediaType)) return false;
    const links = ensureLinks(targetNode);
    const exists = links.some((link) => Number(link.source_id) === sourceId && Number(link.source_slot) === Number(sourceSlot));
    if (exists) return false;
    links.push({
        source_id: sourceId,
        source_slot: Number(sourceSlot) || 0,
        source_type: sourceType || "*",
        media_type: mediaType,
        order: links.length + 1,
    });
    resequence(targetNode);
    targetNode.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    app.graph?.change?.();
    requestMentionPreviewRefresh();
    return true;
}

function removeVirtualLink(node, index) {
    const links = ensureLinks(node);
    if (index < 0 || index >= links.length) return false;
    links.splice(index, 1);
    resequence(node);
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    app.graph?.change?.();
    requestMentionPreviewRefresh();
    return true;
}

function getNativeGraphLink(graph, linkId) {
    if (!graph || linkId == null) return null;
    for (const links of [graph.links, graph._links]) {
        if (!links) continue;
        if (typeof links.get === "function") {
            const link = links.get(linkId) ?? links.get(String(linkId));
            if (link) return link;
        }
        const link = links[linkId] ?? links[String(linkId)];
        if (link) return link;
    }
    return null;
}

function getNativeMediaBridgeLink(node) {
    if (!isTarget(node)) return null;
    const inputIndex = getMediaInputIndex(node);
    const input = inputIndex >= 0 ? node.inputs?.[inputIndex] : null;
    if (input?.link == null) return null;
    const graph = node.graph || app.graph;
    const link = getNativeGraphLink(graph, input.link);
    if (!link) return null;
    const sourceId = link.origin_id ?? link.originId ?? link.from_id ?? link.fromId;
    const sourceNode = link.origin_node || link.originNode || link.fromNode || link.sourceNode
        || graph?.getNodeById?.(Number(sourceId));
    if (!sourceNode) return null;
    const resolvedSourceId = sourceId ?? sourceNode.id;
    if (resolvedSourceId == null) return null;
    const rawSourceSlot = link.origin_slot ?? link.originSlot ?? link.from_slot ?? link.fromSlot ?? 0;
    const parsedSourceSlot = Number(rawSourceSlot);
    const sourceSlot = Number.isFinite(parsedSourceSlot) ? parsedSourceSlot : 0;
    const sourceOutput = sourceNode?.outputs?.[sourceSlot] || {};
    const sourceType = link.type ?? link.origin_type ?? link.originType ?? sourceOutput.type ?? "";
    if (!isMediaBridgeOutput(sourceNode, sourceSlot, sourceType)) return null;
    return {
        source_id: resolvedSourceId,
        source_slot: sourceSlot,
    };
}

function getMediaBridgeLink(node) {
    return getNativeMediaBridgeLink(node);
}

function enforceMediaInputExclusivity(node) {
    if (!isTarget(node) || !getNativeMediaBridgeLink(node)) return false;
    const links = ensureLinks(node);
    if (!links.length) return false;
    node.properties[LINKS_PROP] = [];
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    app.graph?.change?.();
    requestMentionPreviewRefresh();
    return true;
}

function connectionSource(output, originNode, originSlot = 0) {
    const sourceNode = originNode && typeof originNode === "object"
        ? originNode
        : output?.node || output?.origin_node || output?.originNode || null;
    const parsedSlot = Number(originSlot ?? output?.slot_index ?? output?.slot ?? 0);
    return {
        node: sourceNode,
        slot: Number.isFinite(parsedSlot) ? parsedSlot : 0,
        type: getSlotType(output),
    };
}

function rejectsMixedMediaConnection(targetNode, inputIndex, output, originNode, originSlot) {
    const input = targetNode?.inputs?.[Number(inputIndex)];
    if (!isTarget(targetNode) || String(input?.name || "") !== "media") return false;
    const source = connectionSource(output, originNode, originSlot);
    if (!source.node) return false;
    if (isMediaBridgeOutput(source.node, source.slot, source.type)) return hasVirtualMediaLinks(targetNode);
    return Boolean(getNativeMediaBridgeLink(targetNode));
}

function convertNativeMediaConnection(targetNode, inputIndex, linkInfo = null) {
    if (!isTarget(targetNode) || targetNode.__h3VirtualWireClearing) return false;
    const input = targetNode.inputs?.[inputIndex];
    if (!input || !/^media(?:_\d+)?$/i.test(String(input.name || ""))) return false;

    const graph = targetNode.graph || app.graph;
    const linkId = input.link ?? linkInfo?.id ?? linkInfo?.link_id ?? linkInfo?.linkId;
    const nativeLink = getNativeGraphLink(graph, linkId) || linkInfo;
    if (!nativeLink) return false;

    const directSourceCandidate = nativeLink.origin_node || nativeLink.originNode
        || nativeLink.fromNode || nativeLink.sourceNode;
    const directSource = directSourceCandidate && typeof directSourceCandidate === "object"
        ? directSourceCandidate
        : null;
    const sourceId = nativeLink.origin_id ?? nativeLink.originId
        ?? nativeLink.from_id ?? nativeLink.fromId
        ?? (directSourceCandidate && typeof directSourceCandidate !== "object" ? directSourceCandidate : directSource?.id);
    const sourceNode = directSource || graph?.getNodeById?.(Number(sourceId));
    if (!sourceNode || isSameNode(targetNode, sourceNode)) return false;

    const rawSourceSlot = nativeLink.origin_slot ?? nativeLink.originSlot
        ?? nativeLink.from_slot ?? nativeLink.fromSlot ?? nativeLink.from?.slot ?? 0;
    const parsedSourceSlot = Number(rawSourceSlot);
    const sourceSlot = Number.isFinite(parsedSourceSlot) ? parsedSourceSlot : 0;
    const output = sourceNode.outputs?.[sourceSlot] || {};
    const sourceType = getSlotType(output)
        || String(nativeLink.type || nativeLink.origin_type || nativeLink.originType || "*").toUpperCase();
    if (isMediaBridgeOutput(sourceNode, sourceSlot, sourceType)) return false;

    const added = addVirtualLink(targetNode, sourceNode, sourceSlot, sourceType);
    targetNode.__h3VirtualWireClearing = true;
    try {
        if (targetNode.inputs?.[inputIndex]?.link != null && typeof targetNode.disconnectInput === "function") {
            targetNode.disconnectInput(inputIndex);
        } else if (linkId != null && typeof graph?.removeLink === "function") {
            graph.removeLink(linkId);
        }
        if (targetNode.inputs?.[inputIndex]) targetNode.inputs[inputIndex].link = null;
    } finally {
        targetNode.__h3VirtualWireClearing = false;
    }

    targetNode.setDirtyCanvas?.(true, true);
    graph?.setDirtyCanvas?.(true, true);
    requestMentionPreviewRefresh();
    return added;
}

function scheduleNativeMediaConnectionConversion(targetNode, inputIndex, linkInfo = null) {
    setTimeout(() => convertNativeMediaConnection(targetNode, inputIndex, linkInfo), 0);
    if (!linkInfo) setTimeout(() => convertNativeMediaConnection(targetNode, inputIndex), 50);
}

function cubicPoint(start, end, t) {
    const cp1 = [start[0] + 80, start[1]];
    const cp2 = [end[0] - 80, end[1]];
    const mt = 1 - t;
    return [
        mt * mt * mt * start[0] + 3 * mt * mt * t * cp1[0] + 3 * mt * t * t * cp2[0] + t * t * t * end[0],
        mt * mt * mt * start[1] + 3 * mt * mt * t * cp1[1] + 3 * mt * t * t * cp2[1] + t * t * t * end[1],
    ];
}

function linkGeometry(targetNode, link) {
    const sourceNode = targetNode.graph?.getNodeById?.(Number(link.source_id));
    const dot = getMediaDot(targetNode);
    if (!sourceNode || !dot) return null;
    const source = getConnectionPosition(sourceNode, false, Number(link.source_slot) || 0);
    const target = [dot.x, dot.y];
    return { sourceNode, source, target, mid: cubicPoint(source, target, 0.5) };
}

function getComfyLinkTypeColor(type) {
    const colors = globalThis.LGraphCanvas?.link_type_colors || {};
    const raw = String(type || "");
    const candidates = [raw, raw.toUpperCase(), raw.toLowerCase()].filter(Boolean);
    for (const candidate of candidates) {
        if (colors[candidate]) return colors[candidate];
    }
    return "";
}

function getComfyDefaultLinkColor(canvas) {
    return canvas?.default_link_color || globalThis.LiteGraph?.LINK_COLOR || COMFY_NATIVE_LINK_COLOR;
}

function linkColor(canvas, targetNode, sourceNode, link) {
    if (linkHighlighted(canvas, targetNode, sourceNode)) return "#FFF";
    const typedColor = getComfyLinkTypeColor(link?.source_type);
    if (typedColor) return typedColor;
    return String(link?.media_type || "image") === "image" ? COLOR_IMAGE : getComfyDefaultLinkColor(canvas);
}

function linkHighlighted(canvas, targetNode, sourceNode) {
    return Boolean(
        targetNode?.selected || sourceNode?.selected ||
        canvas?.selectedItems?.has?.(targetNode) || canvas?.selectedItems?.has?.(sourceNode) ||
        canvas?.selected_nodes?.[targetNode?.id] || canvas?.selected_nodes?.[sourceNode?.id]
    );
}

function hitTestLinks(graph, x, y) {
    let best = null;
    for (const targetNode of graph?._nodes || []) {
        if (!isTarget(targetNode)) continue;
        const links = ensureLinks(targetNode);
        links.forEach((link, index) => {
            const geometry = linkGeometry(targetNode, link);
            if (!geometry) return;
            const distance = Math.hypot(x - geometry.mid[0], y - geometry.mid[1]);
            if (distance <= 18 && (!best || distance < best.distance)) best = { targetNode, index, point: geometry.mid, distance };
        });
    }
    return best;
}

function closeContextMenuCompat(menu) {
    menu?.close?.();
    menu?.remove?.();
    globalThis.LiteGraph?.ContextMenu?.closeAllContextMenus?.(globalThis.window);
    if (typeof document !== "undefined") {
        document.querySelectorAll(".litecontextmenu").forEach((element) => element.remove());
    }
}

function closeLinkMenu() {
    linkMenu?.close?.();
    linkMenu?.remove?.();
    linkMenu = null;
}

function openLinkMenu(canvas, hit, event) {
    closeLinkMenu();
    const anchor = clientPosition(canvas, hit.point) || { x: event?.clientX || 0, y: event?.clientY || 0 };
    const menuEvent = typeof PointerEvent === "function"
        ? new PointerEvent("pointerdown", { clientX: anchor.x + 8, clientY: anchor.y + 8, bubbles: true, cancelable: true })
        : new MouseEvent("mousedown", { clientX: anchor.x + 8, clientY: anchor.y + 8, bubbles: true, cancelable: true });
    let menuInstance = null;
    const remove = () => {
        removeVirtualLink(hit.targetNode, hit.index);
        closeContextMenuCompat(menuInstance);
        if (linkMenu === menuInstance) linkMenu = null;
    };
    if (globalThis.LiteGraph?.ContextMenu) {
        menuInstance = new globalThis.LiteGraph.ContextMenu([
            { content: TEXT.deleteLink, callback: remove },
        ], { event: menuEvent });
        linkMenu = menuInstance;
    }
}

function openCreateMenu(canvas, targetNode, event, allowedTypes) {
    if (!targetNode) return;
    closeContextMenuCompat(createMenu);
    createMenu = null;
    releaseCreateMenuLinkHold?.();
    releaseCreateMenuLinkHold = null;
    const [x, y] = Number.isFinite(event?.canvasX) && Number.isFinite(event?.canvasY)
        ? [event.canvasX, event.canvasY]
        : graphPosition(canvas, event);
    const anchor = clientPosition(canvas, [x, y]) || { x: event?.clientX || 0, y: event?.clientY || 0 };
    const menuEvent = typeof PointerEvent === "function"
        ? new PointerEvent("pointerdown", { clientX: anchor.x, clientY: anchor.y, bubbles: true, cancelable: true })
        : new MouseEvent("mousedown", { clientX: anchor.x, clientY: anchor.y, bubbles: true, cancelable: true });
    let menuInstance = null;
    const finish = () => {
        closeContextMenuCompat(menuInstance);
        if (createMenu === menuInstance) createMenu = null;
        releaseCreateMenuLinkHold?.();
        releaseCreateMenuLinkHold = null;
        deferredCreateMenuPending = false;
        setNativeSearchVisualSuppression(false);
        clearTemporaryRenderLink(canvas);
    };
    const items = [];
    items.push(...allowedTypes.filter((type) => canAccept(targetNode, type)).map((type) => ({
        content: LOADERS[type].label,
        callback: () => {
            createResourceNode(canvas, targetNode, type, [x, y]);
            finish();
        },
    })));
    if (canCreateMediaLoaderFor(targetNode)) {
        items.push({
            content: TEXT.mediaLoaderMenuTitle,
            callback: () => {
                createMediaLoaderNode(canvas, targetNode, [x, y]);
                finish();
            },
        });
    }
    if (!globalThis.LiteGraph?.ContextMenu || !items.length) {
        deferredCreateMenuPending = false;
        setNativeSearchVisualSuppression(false);
        clearTemporaryRenderLink(canvas);
        return;
    }
    releaseCreateMenuLinkHold = holdDroppedLinkForMenu(canvas, { canvasX: x, canvasY: y });
    setNativeSearchVisualSuppression(true);
    menuInstance = new globalThis.LiteGraph.ContextMenu(items, { event: menuEvent });
    createMenu = menuInstance;
    menuInstance.controller?.signal?.addEventListener?.("abort", () => {
        if (createMenu === menuInstance) createMenu = null;
        releaseCreateMenuLinkHold?.();
        releaseCreateMenuLinkHold = null;
        deferredCreateMenuPending = false;
        setNativeSearchVisualSuppression(false);
        clearTemporaryRenderLink(canvas);
    }, { once: true });
}

function alignNodeOutputToDrop(node, slot, position) {
    if (!node || slot < 0 || !Number.isFinite(position?.[0]) || !Number.isFinite(position?.[1])) return false;
    const current = node.pos || [0, 0];
    const connection = getConnectionPosition(node, false, slot);
    if (!Number.isFinite(connection?.[0]) || !Number.isFinite(connection?.[1])) return false;
    node.pos = [current[0] + position[0] - connection[0], current[1] + position[1] - connection[1]];
    node.setDirtyCanvas?.(true, true);
    return true;
}

function createResourceNode(canvas, targetNode, mediaType, position) {
    const spec = LOADERS[mediaType];
    const graph = canvas?.graph || app.graph;
    const LiteGraph = globalThis.LiteGraph;
    if (!spec || !graph || !LiteGraph?.createNode) return false;
    const node = LiteGraph.createNode(spec.classType);
    if (!node) return false;
    node.pos = [position[0], position[1]];
    graph.add(node);
    const slot = node.outputs?.findIndex((output) => getMediaType(getSlotType(output), node) === mediaType) ?? 0;
    alignNodeOutputToDrop(node, slot, position);
    if (isVueNodesMode() && typeof requestAnimationFrame === "function") {
        const placedPosition = [Number(node.pos?.[0]) || 0, Number(node.pos?.[1]) || 0];
        requestAnimationFrame(() => {
            const stillAtPlacedPosition = Math.abs((Number(node.pos?.[0]) || 0) - placedPosition[0]) < 0.5
                && Math.abs((Number(node.pos?.[1]) || 0) - placedPosition[1]) < 0.5;
            if (stillAtPlacedPosition) alignNodeOutputToDrop(node, slot, position);
        });
    }
    const output = node.outputs?.[slot] || {};
    addVirtualLink(targetNode, node, slot, getSlotType(output) || mediaType.toUpperCase(), mediaType);
    graph.setDirtyCanvas?.(true, true);
    return true;
}

function createMediaLoaderNode(canvas, targetNode, position) {
    if (!canCreateMediaLoaderFor(targetNode)) return false;
    const graph = canvas?.graph || app.graph;
    const LiteGraph = globalThis.LiteGraph;
    if (!graph || !LiteGraph?.createNode) return false;
    const node = LiteGraph.createNode(MEDIA_LOADER_CLASS);
    if (!node) return false;
    node.pos = [position[0], position[1]];
    graph.add(node);
    const outputSlot = node.outputs?.findIndex((output, index) => isMediaBridgeOutput(node, index, getSlotType(output))) ?? -1;
    const inputSlot = getMediaInputIndex(targetNode);
    if (outputSlot < 0 || inputSlot < 0) {
        graph.remove?.(node);
        return false;
    }
    alignNodeOutputToDrop(node, outputSlot, position);
    const connected = node.connect?.(outputSlot, targetNode, inputSlot);
    if (!connected) {
        graph.remove?.(node);
        return false;
    }
    graph.setDirtyCanvas?.(true, true);
    return true;
}

function getSlotIndex(slots, rawSlot) {
    if (typeof rawSlot === "number") return slots?.[rawSlot] ? rawSlot : -1;
    for (const key of ["slot_index", "slot", "index"]) {
        const value = rawSlot?.[key];
        if (typeof value === "number" && slots?.[value]) return value;
    }
    if (Array.isArray(slots) && rawSlot) {
        const direct = slots.indexOf(rawSlot);
        if (direct >= 0) return direct;
        const name = typeof rawSlot === "string" ? rawSlot : rawSlot?.name;
        if (name) return slots.findIndex((slot) => slot?.name === name);
    }
    return -1;
}

function getPendingConnectorLink(canvas) {
    const link = canvas?.linkConnector?.renderLinks?.at?.(0);
    if (!link) return null;
    const endpointNode = link.node || link.fromNode || link.originNode || link.sourceNode || link.toNode || link.targetNode
        || link.inputNode || link.outputNode;
    const endpointSlot = link.fromSlot ?? link.slot ?? link.output ?? link.input ?? link.toSlot ?? {};
    const toType = String(link.toType || link.targetType || link.targetSlotType || "").toLowerCase();
    let direction = toType.includes("output") ? "from_input" : "from_output";
    const inputIndex = getSlotIndex(endpointNode?.inputs, endpointSlot);
    const outputIndex = getSlotIndex(endpointNode?.outputs, endpointSlot);
    if (inputIndex >= 0 && outputIndex < 0) direction = "from_input";
    if (outputIndex >= 0 && inputIndex < 0) direction = "from_output";
    if (direction === "from_input") {
        const input = endpointNode?.inputs?.[inputIndex] || endpointSlot;
        if (!isTarget(endpointNode) || String(input?.name || "") !== "media") return null;
        return { direction, targetNode: endpointNode, targetSlot: inputIndex };
    }
    const output = endpointNode?.outputs?.[outputIndex] || endpointSlot || {};
    return {
        direction,
        sourceNode: endpointNode,
        sourceSlot: Math.max(0, outputIndex),
        sourceType: getSlotType(output),
    };
}

function nodeAtGraphPoint(canvas, x, y, ignoredNode = null) {
    const nodes = canvas?.graph?._nodes || app.graph?._nodes || [];
    for (let index = nodes.length - 1; index >= 0; index -= 1) {
        const node = nodes[index];
        if (!node || node === ignoredNode) continue;
        const pos = node.pos || [0, 0];
        const size = node.size || node.computeSize?.() || [0, 0];
        if (x >= pos[0] && y >= pos[1] && x <= pos[0] + Number(size[0] || 0) && y <= pos[1] + Number(size[1] || 0)) return node;
    }
    return null;
}

function findNativeSearchContainer() {
    const active = document.activeElement;
    const activeRoot = active?.closest?.("[role='search'], .node-search-box-dialog-mask, .invisible-dialog-root, .p-dialog, [data-pc-name='dialog']");
    return document.querySelector(".node-search-box-dialog-mask .comfy-vue-node-search-container")
        || document.querySelector(".invisible-dialog-root .comfy-vue-node-search-container")
        || document.querySelector(".comfy-vue-node-search-container")
        || activeRoot
        || document.querySelector("[role='search']");
}

function findNativeSearchInput(container) {
    const active = document.activeElement;
    if (active?.tagName === "INPUT" && (!container || container.contains(active))) return active;
    return container?.querySelector?.('input[id^="comfy-vue-node-search-box-input-"]')
        || container?.querySelector?.(".comfy-vue-node-search-box input")
        || container?.querySelector?.("input")
        || document.querySelector('input[id^="comfy-vue-node-search-box-input-"]');
}

function setNativeSearchVisualSuppression(enabled) {
    const className = "minimax-h3-easy-hide-native-search";
    if (enabled) {
        if (!nativeSearchSuppressStyle) {
            nativeSearchSuppressStyle = document.createElement("style");
            nativeSearchSuppressStyle.textContent = `
body.${className} .node-search-box-dialog-mask,
body.${className} .p-dialog-mask:has(.comfy-vue-node-search-container),
body.${className} .invisible-dialog-root:has(.comfy-vue-node-search-container),
body.${className} .comfy-vue-node-search-container {
    opacity: 0 !important;
    pointer-events: none !important;
}`;
            document.head?.appendChild(nativeSearchSuppressStyle);
        }
        document.body?.classList?.add(className);
    } else {
        document.body?.classList?.remove(className);
    }
}

function closeNativeNodeSearchSoon() {
    const close = () => {
        const container = findNativeSearchContainer();
        const input = findNativeSearchInput(container);
        if (!container && !input) return;
        const init = { key: "Escape", code: "Escape", keyCode: 27, which: 27, bubbles: true, cancelable: true };
        input?.dispatchEvent?.(new KeyboardEvent("keydown", init));
        container?.dispatchEvent?.(new KeyboardEvent("keydown", init));
        document.dispatchEvent(new KeyboardEvent("keydown", init));
    };
    for (const delay of [0, 16, 50, 120]) setTimeout(close, delay);
}

function holdDroppedLinkForMenu(canvas, detail) {
    const events = canvas?.linkConnector?.events;
    if (!events) return null;
    const preventReset = (event) => event.preventDefault?.();
    canvas.linkConnector.state ||= {};
    if (Number.isFinite(detail?.canvasX) && Number.isFinite(detail?.canvasY)) {
        canvas.linkConnector.state.snapLinksPos = [detail.canvasX, detail.canvasY];
    }
    events.addEventListener("reset", preventReset, { once: true });
    return () => events.removeEventListener("reset", preventReset);
}

function clearTemporaryRenderLink(canvas) {
    const connector = canvas?.linkConnector;
    connector?.reset?.();
    if (Array.isArray(connector?.renderLinks)) connector.renderLinks.length = 0;
    canvas?.setDirty?.(true, true);
    (canvas?.graph || app.graph)?.setDirtyCanvas?.(true, true);
}

function shouldSuppressNativeDrop(type) {
    return type === "dropped-on-canvas"
        && (Boolean(createMenu) || deferredCreateMenuPending)
        && performance.now() < suppressNativeDropUntil;
}

function suppressNativeDrop(event) {
    event?.preventDefault?.();
    event?.stopPropagation?.();
    event?.stopImmediatePropagation?.();
    closeNativeNodeSearchSoon();
}

function primeInputDropSuppression(canvas) {
    const pending = getPendingConnectorLink(canvas);
    if (pending?.direction !== "from_input") return false;
    deferredCreateMenuPending = true;
    suppressNativeDropUntil = performance.now() + 1000;
    setNativeSearchVisualSuppression(true);
    closeNativeNodeSearchSoon();
    return true;
}

function getTargetInputLinkId(pending) {
    if (!pending?.targetNode) return null;
    const inputIndex = getSlotIndex(pending.targetNode.inputs, pending.targetSlot);
    return inputIndex >= 0 ? pending.targetNode.inputs?.[inputIndex]?.link ?? null : null;
}

function getVirtualLinkCount(node) {
    return isTarget(node) ? ensureLinks(node).length : 0;
}

function hasDeferredInputDropConnected(canvas, pending, before, nativeLinkCreated = false) {
    if (nativeLinkCreated) return true;
    const inputLinkId = getTargetInputLinkId(pending);
    if (inputLinkId != null && inputLinkId !== before.inputLinkId) return true;
    if (getVirtualLinkCount(pending?.targetNode) > before.virtualLinkCount) return true;
    const graphVersion = Number((canvas?.graph || app.graph)?._version) || 0;
    return graphVersion > before.graphVersion;
}

function buildInputDropDetail(canvas, event) {
    const [canvasX, canvasY] = pointerGraphPosition(canvas, event);
    return {
        clientX: event?.clientX,
        clientY: event?.clientY,
        canvasX,
        canvasY,
        shiftKey: Boolean(event?.shiftKey),
        ctrlKey: Boolean(event?.ctrlKey),
        metaKey: Boolean(event?.metaKey),
        altKey: Boolean(event?.altKey),
        pointerType: event?.pointerType,
        originalEvent: event,
        target: event?.target,
    };
}

function scheduleDeferredInputCreateMenu(canvas, event, pending, allowed) {
    if (pending?.direction !== "from_input") return false;
    const token = ++deferredCreateMenuToken;
    const detail = buildInputDropDetail(canvas, event);
    const linkSnapshot = { ...pending };
    const before = {
        inputLinkId: getTargetInputLinkId(linkSnapshot),
        virtualLinkCount: getVirtualLinkCount(linkSnapshot.targetNode),
        graphVersion: Number((canvas?.graph || app.graph)?._version) || 0,
    };

    deferredCreateMenuPending = true;
    suppressNativeDropUntil = performance.now() + 1000;
    setNativeSearchVisualSuppression(true);
    closeNativeNodeSearchSoon();
    const releaseDeferredHold = holdDroppedLinkForMenu(canvas, detail);
    const events = canvas?.linkConnector?.events;
    let settled = false;
    let nativeLinkCreated = false;

    const cleanupNativeListeners = () => {
        events?.removeEventListener?.("link-created", onNativeLinkCreated);
        events?.removeEventListener?.("after-drop-links", onAfterDropLinks);
    };
    const releaseHold = () => releaseDeferredHold?.();
    const finishConnected = () => {
        if (settled || token !== deferredCreateMenuToken) return false;
        if (!hasDeferredInputDropConnected(canvas, linkSnapshot, before, nativeLinkCreated)) return false;
        settled = true;
        deferredCreateMenuPending = false;
        cleanupNativeListeners();
        releaseHold();
        setNativeSearchVisualSuppression(false);
        clearTemporaryRenderLink(canvas);
        return true;
    };
    const onNativeLinkCreated = () => {
        nativeLinkCreated = true;
        setTimeout(() => finishConnected(), 0);
    };
    const onAfterDropLinks = () => setTimeout(() => finishConnected(), 0);
    const checkConnectedSoon = () => {
        if (settled || token !== deferredCreateMenuToken || finishConnected()) return;
        if (typeof requestAnimationFrame === "function") requestAnimationFrame(() => finishConnected());
    };

    events?.addEventListener?.("link-created", onNativeLinkCreated);
    events?.addEventListener?.("after-drop-links", onAfterDropLinks);
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(checkConnectedSoon);
    setTimeout(checkConnectedSoon, 16);
    setTimeout(checkConnectedSoon, 32);

    setTimeout(() => {
        if (settled) return;
        if (token !== deferredCreateMenuToken) {
            settled = true;
            cleanupNativeListeners();
            releaseHold();
            setNativeSearchVisualSuppression(false);
            return;
        }
        deferredCreateMenuPending = false;
        if (createMenu) {
            settled = true;
            cleanupNativeListeners();
            releaseHold();
            return;
        }
        if (finishConnected()) return;

        settled = true;
        cleanupNativeListeners();
        releaseHold();
        suppressNativeDropUntil = performance.now() + 800;
        openCreateMenu(canvas, linkSnapshot.targetNode, detail, allowed);
        closeNativeNodeSearchSoon();
    }, 70);
    return true;
}

function installQuickCreateCapture(canvas) {
    if (!canvas?.canvas || !canvas?.linkConnector?.events) return false;
    if (canvas === quickCreateCaptureCanvas && canvas.__h3EasyQuickCreateCaptureInstalled) return true;

    // Nodes 2.0 can replace app.canvas while the page is starting. A module-global
    // "installed" flag leaves the handlers attached to the discarded canvas and
    // makes the live canvas rely on the less reliable mouse-up fallback. Remove the
    // old global listeners and install against the current canvas instance instead.
    quickCreateCaptureCleanup?.();
    quickCreateCaptureCleanup = null;
    quickCreateCaptureCanvas = canvas;
    canvas.__h3EasyQuickCreateCaptureInstalled = true;
    const handler = (event) => {
        // A ContextMenu item click also bubbles through the global pointer-up
        // listeners while the temporary connector is still being held. Without
        // this guard, the first menu click is mistaken for another canvas drop:
        // the temporary line is reset and the menu is reopened before its item
        // callback can create the resource node.
        if (createMenu || deferredCreateMenuPending || event?.target?.closest?.(".litecontextmenu")) return;
        if (event?.button > 0 || performance.now() - lastCapturedDropAt < 80) return;
        const pending = getPendingConnectorLink(canvas);
        if (!pending) return;
        const [x, y] = pointerGraphPosition(canvas, event);
        if (pending.direction === "from_output") {
            const target = (canvas.graph?._nodes || []).find((node) => {
                if (!isTarget(node)) return false;
                const dot = getMediaDot(node);
                return dot && Math.hypot(x - dot.x, y - dot.y) <= 18;
            });
            if (!target) return;
            if (isSameNode(target, pending.sourceNode)) return;
            if (isMediaBridgeOutput(pending.sourceNode, pending.sourceSlot, pending.sourceType)) {
                if (!hasVirtualMediaLinks(target)) return;
                lastCapturedDropAt = performance.now();
                event.preventDefault?.();
                event.stopPropagation?.();
                event.stopImmediatePropagation?.();
                canvas.linkConnector.reset?.();
                return;
            }
            if (getNativeMediaBridgeLink(target)) {
                lastCapturedDropAt = performance.now();
                event.preventDefault?.();
                event.stopPropagation?.();
                event.stopImmediatePropagation?.();
                canvas.linkConnector.reset?.();
                return;
            }
            const added = addVirtualLink(target, pending.sourceNode, pending.sourceSlot, pending.sourceType);
            if (!added) return;
            lastCapturedDropAt = performance.now();
            event.preventDefault?.();
            event.stopPropagation?.();
            event.stopImmediatePropagation?.();
            canvas.linkConnector.reset?.();
            closeNativeNodeSearchSoon();
            return;
        }
        const allowed = mediaReferenceMode(pending.targetNode) ? ["image", "video", "audio"] : ["image"];
        if (scheduleDeferredInputCreateMenu(canvas, event, pending, allowed)) {
            lastCapturedDropAt = performance.now();
        }
    };
    const pointerTargets = [window, document, canvas.canvas];
    for (const target of pointerTargets) {
        target.addEventListener?.("pointerup", handler, true);
        target.addEventListener?.("mouseup", handler, true);
    }

    const events = canvas.linkConnector.events;
    const originalDispatch = typeof events.dispatch === "function" ? events.dispatch : null;
    const originalDispatchEvent = events.dispatchEvent;
    let wrappedDispatch = null;
    let wrappedDispatchEvent = null;
    if (originalDispatch) {
        wrappedDispatch = function dispatchWithMediaDropGuard(type, detail) {
            if (type === "before-drop-links") primeInputDropSuppression(canvas);
            if (shouldSuppressNativeDrop(type)) {
                closeNativeNodeSearchSoon();
                return false;
            }
            return originalDispatch.call(events, type, detail);
        };
        events.dispatch = wrappedDispatch;
    }
    wrappedDispatchEvent = function dispatchEventWithMediaDropGuard(event) {
        if (event?.type === "before-drop-links") primeInputDropSuppression(canvas);
        if (shouldSuppressNativeDrop(event?.type)) {
            suppressNativeDrop(event);
            return false;
        }
        return originalDispatchEvent.call(events, event);
    };
    events.dispatchEvent = wrappedDispatchEvent;
    const beforeDropLinksHandler = () => primeInputDropSuppression(canvas);
    const droppedOnCanvasHandler = (event) => {
        if (shouldSuppressNativeDrop(event?.type)) suppressNativeDrop(event);
    };
    events.addEventListener("before-drop-links", beforeDropLinksHandler, { capture: true });
    events.addEventListener("dropped-on-canvas", droppedOnCanvasHandler, { capture: true });

    quickCreateCaptureCleanup = () => {
        for (const target of pointerTargets) {
            target.removeEventListener?.("pointerup", handler, true);
            target.removeEventListener?.("mouseup", handler, true);
        }
        events.removeEventListener?.("before-drop-links", beforeDropLinksHandler, { capture: true });
        events.removeEventListener?.("dropped-on-canvas", droppedOnCanvasHandler, { capture: true });
        if (wrappedDispatch && events.dispatch === wrappedDispatch) events.dispatch = originalDispatch;
        if (events.dispatchEvent === wrappedDispatchEvent) events.dispatchEvent = originalDispatchEvent;
        canvas.__h3EasyQuickCreateCaptureInstalled = false;
        if (quickCreateCaptureCanvas === canvas) quickCreateCaptureCanvas = null;
    };
    return true;
}

function drawLinks(canvas, ctx) {
    const graph = canvas?.graph || app.graph;
    if (!graph?._nodes || canvas.links_render_mode === globalThis.LiteGraph?.HIDDEN_LINK) return;
    let missingLinkFound = false;
    for (const targetNode of graph._nodes) {
        if (!isTarget(targetNode)) continue;
        const links = ensureLinks(targetNode);
        for (const link of links) {
            const geometry = linkGeometry(targetNode, link);
            if (!geometry) {
                missingLinkFound = true;
                continue;
            }
            const highlighted = linkHighlighted(canvas, targetNode, geometry.sourceNode);
            const color = linkColor(canvas, targetNode, geometry.sourceNode, link);
            const width = canvas.connections_width || 3;
            ctx.save();
            ctx.lineJoin = "round";
            ctx.shadowBlur = 0;
            ctx.shadowColor = "transparent";
            ctx.beginPath();
            ctx.moveTo(geometry.source[0], geometry.source[1]);
            ctx.bezierCurveTo(geometry.source[0] + 80, geometry.source[1], geometry.target[0] - 80, geometry.target[1], geometry.target[0], geometry.target[1]);
            ctx.lineWidth = width + 4;
            ctx.strokeStyle = canvas.render_connections_border !== false && !canvas.low_quality ? COLOR_LINK_BORDER : "transparent";
            if (ctx.strokeStyle !== "transparent") ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(geometry.source[0], geometry.source[1]);
            ctx.bezierCurveTo(geometry.source[0] + 80, geometry.source[1], geometry.target[0] - 80, geometry.target[1], geometry.target[0], geometry.target[1]);
            ctx.lineWidth = width;
            ctx.strokeStyle = color;
            ctx.stroke();
            if (canvas.linkMarkerShape !== 0 && (canvas.ds?.scale ?? 1) >= 0.6 && canvas.highquality_render !== false) {
                ctx.beginPath();
                ctx.arc(geometry.mid[0], geometry.mid[1], 5, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.fillStyle = highlighted ? "#222" : "#fff";
                ctx.font = "bold 7px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(String(link.order || 1), geometry.mid[0], geometry.mid[1] + 0.3);
            }
            ctx.restore();
        }
    }
    if (missingLinkFound) requestMentionPreviewRefresh();
}

function patchCanvas() {
    const canvas = app.canvas;
    if (!canvas || canvas.__h3EasyCanvasPatched || typeof canvas.drawConnections !== "function") return;
    canvas.__h3EasyCanvasPatched = true;
    patchedCanvas = true;
    const originalDraw = canvas.drawConnections;
    canvas.drawConnections = function drawConnectionsWithH3Links(ctx) {
        const result = originalDraw?.apply(this, arguments);
        const connectionContext = ctx || this.bgctx || this.ctx;
        const onConnectionLayer = connectionContext?.canvas === this?.bgcanvas || connectionContext === this?.bgctx || !this?.bgcanvas;
        if (connectionContext && onConnectionLayer) drawLinks(this, connectionContext);
        return result;
    };

    const originalDown = canvas.processMouseDown;
    canvas.processMouseDown = function processMouseDownWithH3Links(event) {
        if (!getInputConnection(this)) {
            const [x, y] = graphPosition(this, event);
            const hit = hitTestLinks(this.graph || app.graph, x, y);
            if (hit) {
                openLinkMenu(this, hit, event);
                event?.preventDefault?.();
                event?.stopImmediatePropagation?.();
                return true;
            }
        }
        const result = originalDown?.apply(this, arguments);
        return result;
    };

    const linkPointerHandler = (event) => {
        if (getPendingConnectorLink(canvas) || connectingOutput(canvas) || connectingInput(canvas)) return;
        const [x, y] = graphPosition(canvas, event);
        const hit = hitTestLinks(canvas.graph || app.graph, x, y);
        if (!hit) return;
        openLinkMenu(canvas, hit, event);
        event.preventDefault?.();
        event.stopPropagation?.();
        event.stopImmediatePropagation?.();
    };
    canvas.canvas?.addEventListener?.("pointerdown", linkPointerHandler, true);
    installQuickCreateCapture(canvas);
}

function getInputConnection(canvas) {
    const node = canvas?.connecting_node || canvas?.connectingNode;
    const input = canvas?.connecting_input || canvas?.connectingInput;
    if (!node || !isTarget(node) || !input) return null;
    const slot = typeof input === "number" ? node.inputs?.[input] : input;
    if (String(slot?.name || "") !== "media") return null;
    return { targetNode: node };
}

function promptInputSlot(node) {
    return (node?.inputs || []).find((input) => String(input?.name || "") === "prompt") || null;
}

function promptInputIsConnected(node) {
    return promptInputSlot(node)?.link != null;
}

function buildRuntimePrompt(node, runtimeLinks) {
    const promptWidget = getWidget(node, "prompt");
    const fallback = String(promptWidget?.value || "");
    const doc = node?.properties?.[PROMPT_DOC_PROP];
    if (!Array.isArray(doc?.parts)) return fallback;
    return doc.parts.map((part) => {
        if (part?.type === "dialogue") return `<d>${String(part.text || "")}</d>`;
        if (part?.type !== "mention") return String(part?.text || "");
        const mediaType = String(part.mediaType || "image").toLowerCase();
        const partSourceId = part.sourceId != null && Number.isFinite(Number(part.sourceId)) ? Number(part.sourceId) : null;
        const partOrdinal = Number(part.ordinal);
        let index = -1;
        if ((referenceMentionMode(node) === "index" || partSourceId == null) && Number.isFinite(partOrdinal) && partOrdinal > 0) {
            let ordinal = 0;
            for (let runtimeIndex = 0; runtimeIndex < runtimeLinks.length; runtimeIndex += 1) {
                const link = runtimeLinks[runtimeIndex];
                if (String(link.media_type || "image").toLowerCase() !== mediaType) continue;
                ordinal += 1;
                if (ordinal === partOrdinal) {
                    index = runtimeIndex;
                    break;
                }
            }
        }
        if (index < 0 && partSourceId != null) {
            index = runtimeLinks.findIndex((link) =>
                Number(link.source_id) === partSourceId
                && Number(link.source_slot) === Number(part.sourceSlot || 0)
                && String(link.media_type || "image").toLowerCase() === mediaType
            );
        }
        if (index >= 0) return `${RUNTIME_REF_PREFIX}${index + 1}__`;
        if (!canUseMediaMentions(node)) return String(part.tag || part.token || "");
        return `${UNRESOLVED_REF_PREFIX}${mediaType}__`;
    }).join("");
}

function preserveLinkedPromptInput(promptNode, node, name, fallbackValue) {
    const input = node?.inputs?.find((slot) => String(slot?.name || "") === name);
    if (input?.link != null) {
        const link = getNativeGraphLink(node.graph || app.graph, input.link);
        const originId = link?.origin_id ?? link?.originId;
        const originSlot = link?.origin_slot ?? link?.originSlot ?? 0;
        if (originId != null) {
            promptNode.inputs[name] = [String(originId), Number(originSlot) || 0];
            return;
        }
    }

    const existing = promptNode?.inputs?.[name];
    if (Array.isArray(existing) && existing.length >= 2) return;
    promptNode.inputs[name] = fallbackValue;
}

function patchGraphToPrompt() {
    if (patchedPrompt || typeof app.graphToPrompt !== "function") return;
    patchedPrompt = true;
    const original = app.graphToPrompt;
    app.graphToPrompt = async function graphToPromptWithOrderedMedia() {
        const promptData = await original.apply(this, arguments);
        const output = promptData?.output || {};
        for (const node of app.graph?._nodes || []) {
            // Segment Refine has its own inputs and is intentionally excluded
            // from the main/context media patch above. Its localized combo
            // labels still need to be converted back to backend enum values.
            if (isSegmentRefineNode(node)) {
                const promptNode = output[String(node.id)];
                if (!promptNode) continue;
                promptNode.inputs ||= {};
                if (!Array.isArray(promptNode.inputs.refine_mode)) {
                    promptNode.inputs.refine_mode = canonicalOption(
                        "refine_mode",
                        getWidgetValue(node, "refine_mode", "pixel_resize"),
                    );
                }
                if (!Array.isArray(promptNode.inputs.refine_execution)) {
                    promptNode.inputs.refine_execution = canonicalOption(
                        "refine_execution",
                        getWidgetValue(node, "refine_execution", "whole_segment"),
                    );
                }
                continue;
            }
            if (!isTarget(node)) continue;
            const promptNode = output[String(node.id)];
            if (!promptNode) continue;
            promptNode.inputs ||= {};
            const mediaBridgeLink = getMediaBridgeLink(node);
            if (mediaBridgeLink) promptNode.inputs.media = [String(mediaBridgeLink.source_id), mediaBridgeLink.source_slot];
            else delete promptNode.inputs.media;
            for (let index = 1; index <= transportMediaLimit(node); index += 1) {
                delete promptNode.inputs[`media_${index}`];
                delete promptNode.inputs[`media_type_${index}`];
            }
            if (node.__h3Editor) syncPromptFromEditor(node, false);
            const runtimeLinks = mediaBridgeLink
                ? []
                : normalizeLinks(node).filter((link) => Boolean(output[String(link.source_id)]));
            runtimeLinks.forEach((link, index) => {
                const source = output[String(link.source_id)];
                const slot = Number(link.source_slot) || 0;
                promptNode.inputs[`media_${index + 1}`] = [String(link.source_id), slot];
                promptNode.inputs[`media_type_${index + 1}`] = String(link.media_type || "image");
            });
            const promptInput = promptInputSlot(node);
            const promptLinkId = promptInput?.link;
            const existingPromptLink = promptNode.inputs.prompt;
            const hasPromptConnection = promptLinkId != null || Array.isArray(existingPromptLink);
            if (!hasPromptConnection) {
                promptNode.inputs.prompt = buildRuntimePrompt(node, runtimeLinks);
            } else if (promptLinkId != null && (!Array.isArray(existingPromptLink) || existingPromptLink.length < 2)) {
                // ComfyUI normally preserves connected widget inputs in graphToPrompt.
                // Reconstruct the link as a fallback for frontends that omit it after
                // the custom DOM editor replaces the native prompt widget.
                const promptLink = getNativeGraphLink(node.graph || app.graph, promptLinkId);
                const originId = promptLink?.origin_id ?? promptLink?.originId;
                const originSlot = promptLink?.origin_slot ?? promptLink?.originSlot ?? 0;
                if (originId != null) promptNode.inputs.prompt = [String(originId), Number(originSlot) || 0];
            }
            promptNode.inputs.mode = canonicalOption("mode", getWidgetValue(node, "mode", MODE_IMAGE));
            if (!isSelectedVideoContextNode(node)) {
                promptNode.inputs.resolution = canonicalOption("resolution", getWidgetValue(node, "resolution", "480P"));
                promptNode.inputs.aspect_ratio = canonicalOption("aspect_ratio", getWidgetValue(node, "aspect_ratio", "16:9"));
                preserveLinkedPromptInput(promptNode, node, "width", Number(getWidgetValue(node, "width", 1344)));
                preserveLinkedPromptInput(promptNode, node, "height", Number(getWidgetValue(node, "height", 768)));
                preserveLinkedPromptInput(
                    promptNode,
                    node,
                    "seconds",
                    Math.min(MAX_SECONDS, Math.max(MIN_SECONDS, Number(getWidgetValue(node, "seconds", 5)) || 5)),
                );
            } else {
                // The selected-video context derives canvas and duration from
                // the connected candidate VIDEO; do not inject the legacy
                // Easy resolution widgets into its prompt payload.
                delete promptNode.inputs.resolution;
                delete promptNode.inputs.aspect_ratio;
                delete promptNode.inputs.width;
                delete promptNode.inputs.height;
                delete promptNode.inputs.seconds;
                delete promptNode.inputs.fps;
            }
            promptNode.inputs.advanced = asBoolean(getWidgetValue(node, "advanced", false));
            promptNode.inputs.prompt_optimizer = asBoolean(getWidgetValue(node, "prompt_optimizer", false));
            promptNode.inputs.prompt_optimizer_api_format = canonicalOption("prompt_optimizer_api_format", getWidgetValue(node, "prompt_optimizer_api_format", "openai"));
            promptNode.inputs.prompt_optimizer_api_url = String(getWidgetValue(node, "prompt_optimizer_api_url", "") || "");
            promptNode.inputs.prompt_optimizer_api_key = String(getWidgetValue(node, "prompt_optimizer_api_key", "") || "");
            promptNode.inputs.prompt_optimizer_model = String(getWidgetValue(node, "prompt_optimizer_model", "") || "");
            promptNode.inputs.prompt_optimizer_scene_guide = canonicalPromptGuide(getWidgetValue(node, "prompt_optimizer_scene_guide", "none"));
            promptNode.inputs.prompt_optimizer_read_media = asBoolean(getWidgetValue(node, "prompt_optimizer_read_media", false));
            promptNode.inputs.prompt_optimizer_optimize_on_run = asBoolean(getWidgetValue(node, "prompt_optimizer_optimize_on_run", false));
            promptNode.inputs.prompt_optimizer_resources = JSON.stringify(promptOptimizerResources(node));
            promptNode.inputs.prompt_optimizer_marker = JSON.stringify(node.properties?.[PROMPT_AUTO_MARKER_PROP] || {});
            promptNode.inputs.prompt_optimizer_prompt_connected = hasPromptConnection;
            if (!isSelectedVideoContextNode(node)) {
                promptNode.inputs.fps = Number(getWidgetValue(node, "fps", 24));
            }
            promptNode.inputs.keyframe_role = canonicalOption("keyframe_role", getWidgetValue(node, "keyframe_role", KEYFRAME_FIRST));
            promptNode.inputs.ref_image_size = canonicalOption("ref_image_size", getWidgetValue(node, "ref_image_size", REF_IMAGE_1K));
            promptNode.inputs.reference_mention_mode = canonicalOption("reference_mention_mode", getWidgetValue(node, "reference_mention_mode", "index"));
            if (isContextSegmentsNode(node)) {
                promptNode.inputs.audio_mode = canonicalOption(
                    "audio_mode",
                    getWidgetValue(node, "audio_mode", CONTEXT_AUDIO_GENERATED),
                );
                promptNode.inputs.segment_seconds = String(getWidgetValue(node, "segment_seconds", "") || "");
                promptNode.inputs.context_length = Number(getWidgetValue(node, "context_length", 5)) || 5;
                promptNode.inputs.continuity_mode = canonicalOption(
                    "continuity_mode",
                    getWidgetValue(node, "continuity_mode", CONTINUITY_LATENT),
                );
                promptNode.inputs.context_prompt_optimizer_mode = canonicalOption(
                    "context_prompt_optimizer_mode",
                    getWidgetValue(node, "context_prompt_optimizer_mode", "whole_sequence"),
                );
                promptNode.inputs.context_prompt_optimizer_concurrency = Math.max(
                    1,
                    Math.min(20, Number(getWidgetValue(node, "context_prompt_optimizer_concurrency", 3)) || 3),
                );
            } else if (isSelectedVideoContextNode(node)) {
                promptNode.inputs.segment_mode = canonicalOption(
                    "selected_video_segment_mode",
                    getWidgetValue(node, "segment_mode", SELECTED_VIDEO_SEGMENT_WHOLE),
                );
                promptNode.inputs.segment_cuts = String(getWidgetValue(node, "segment_cuts", "") || "");
                promptNode.inputs.context_length = Number(getWidgetValue(node, "context_length", 5)) || 5;
                promptNode.inputs.continuity_mode = canonicalOption(
                    "continuity_mode",
                    getWidgetValue(node, "continuity_mode", CONTINUITY_LATENT),
                );
                promptNode.inputs.context_prompt_optimizer_mode = canonicalOption(
                    "context_prompt_optimizer_mode",
                    getWidgetValue(node, "context_prompt_optimizer_mode", "whole_sequence"),
                );
                promptNode.inputs.context_prompt_optimizer_concurrency = Math.max(
                    1,
                    Math.min(20, Number(getWidgetValue(node, "context_prompt_optimizer_concurrency", 3)) || 3),
                );
            }
        }
        return promptData;
    };
}

function editorText(editor) {
    let result = "";
    const visit = (node) => {
        if (node.nodeType === Node.TEXT_NODE) {
            result += String(node.textContent || "").replaceAll("\u200B", "");
            return;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        if (node.classList?.contains("h3-mention-chip")) {
            result += node.dataset.token || "";
            return;
        }
        if (node.tagName === "BR") {
            result += "\n";
            return;
        }
        const block = ["DIV", "P"].includes(node.tagName);
        if (block && result && !result.endsWith("\n")) result += "\n";
        for (const child of node.childNodes || []) visit(child);
    };
    for (const child of editor.childNodes || []) visit(child);
    return result;
}

function sourceLabel(node) {
    return String(node?.title || node?.comfyClass || node?.type || "Media");
}

function widgetFilename(value) {
    const candidate = typeof value === "object" ? (value?.filename || value?.name || "") : value;
    const text = String(candidate || "").trim();
    if (!text || /^data:|^blob:|^https?:/i.test(text)) return "";
    return text.split(/[\\/]/).pop() || text;
}

function sourceFilename(node, mediaType) {
    if (!node) return "";
    const preferred = {
        image: ["image", "filename", "file"],
        video: ["video", "file", "filename", "video_file", "videofile"],
        audio: ["audio", "file", "filename", "audio_file", "audiofile"],
    }[mediaType] || ["file", "filename"];
    const preferredSet = new Set(preferred);
    const widgets = Array.isArray(node.widgets) ? node.widgets : [];
    const ordered = [
        ...widgets.filter((widget) => preferredSet.has(String(widget?.name || "").toLowerCase())),
        ...widgets,
    ];
    for (const widget of ordered) {
        const name = String(widget?.name || "").toLowerCase();
        const filename = widgetFilename(widget?.value);
        if (!filename) continue;
        if (preferredSet.has(name) || /\.(png|jpe?g|webp|gif|bmp|mp4|webm|mov|mkv|avi|m4v|mp3|wav|flac|ogg|m4a)$/i.test(filename)) return filename;
    }
    return widgetFilename(node?.properties?.filename || node?.properties?.file || "");
}

function mediaLoaderState(node) {
    if (!isMediaLoader(node)) return { images: [], audios: [], videos: [] };
    let value = getWidgetValue(node, "media_state", "");
    if (typeof value === "string") {
        try { value = JSON.parse(value || "{}"); } catch { value = {}; }
    }
    const state = { images: [], audios: [], videos: [] };
    for (const group of MEDIA_LOADER_GROUPS) {
        const values = Array.isArray(value?.[group.key]) ? value[group.key] : [];
        const normalized = values.map((entry) => {
            const filename = typeof entry === "object" ? entry?.filename : entry;
            return String(filename || "").replaceAll("\\", "/").replace(/^\/+/, "").trim();
        }).filter((filename) => filename && !filename.split("/").includes(".."))
            .filter((filename, index, list) => list.indexOf(filename) === index);
        state[group.key] = normalized;
    }
    return state;
}

function mediaLoaderEntryUrl(filename, type) {
    if (!filename || type === "audio") return "";
    const params = new URLSearchParams({ filename: String(filename), type: "input" });
    return `/view?${params.toString()}`;
}

function mediaLoaderMentionOptions(source, targetNode = source) {
    source = isMediaLoader(source) ? source : null;
    if (!source) return [];
    const state = mediaLoaderState(source);
    const result = [];
    const counts = { image: 0, video: 0, audio: 0 };
    // Match the loader bundle's serialized order exactly. H3 still assigns
    // the official type-local Picture/Video/Audio tags downstream.
    for (const type of ["image", "audio", "video"]) {
        const key = `${type}s`;
        for (const filename of state[key] || []) {
            counts[type] += 1;
            const ordinal = counts[type];
            const tag = promptMentionTag(type, ordinal);
            const mode = referenceMentionMode(targetNode);
            const fullLabel = filename.split(/[\\/]/).pop() || filename;
            const label = mode === "index" ? `${LABELS[type] || type}${ordinal}` : truncateMentionLabel(fullLabel);
            result.push({
                type, tag, token: `@${mode === "index" ? label : fullLabel}`, label, fullLabel,
                ordinal, referenceMode: mode, source: TEXT.mediaLoaderMenuTitle,
                sourceId: Number(source.id), sourceSlot: 0, mediaIndex: result.length + 1,
                previewUrl: mediaLoaderEntryUrl(filename, type), filename,
            });
        }
    }
    return result;
}

function truncateMentionLabel(value, maxLength = 22) {
    const text = String(value || "");
    if (text.length <= maxLength) return text;
    return `${text.slice(0, Math.max(4, maxLength - 1))}\u2026`;
}

function mentionOptions(node) {
    if (!mediaReferenceMode(node)) return [];
    const native = getNativeMediaBridgeLink(node);
    const loader = native ? app.graph?.getNodeById?.(Number(native.source_id)) : null;
    if (loader && isMediaLoader(loader)) return mediaLoaderMentionOptions(loader, node);
    const links = normalizeLinks(node);
    const mediaOrder = { image: 0, video: 1, audio: 2 };
    const orderedLinks = links
        .map((link, index) => ({ link, index }))
        .sort((left, right) => {
            const leftType = String(left.link.media_type || "image").toLowerCase();
            const rightType = String(right.link.media_type || "image").toLowerCase();
            return (mediaOrder[leftType] ?? 0) - (mediaOrder[rightType] ?? 0) || left.index - right.index;
        })
        .map((entry) => ({ link: entry.link, mediaIndex: entry.index + 1 }));
    const counts = { image: 0, video: 0, audio: 0 };
    const mode = referenceMentionMode(node);
    return orderedLinks.map(({ link, mediaIndex }) => {
        const type = String(link.media_type || "image");
        counts[type] = (counts[type] || 0) + 1;
        const ordinal = counts[type];
        const tag = type === "image" ? `<Picture ${ordinal}>` : type === "video" ? `<Video ${ordinal}>` : `<Audio ${ordinal}>`;
        const source = app.graph?.getNodeById?.(Number(link.source_id));
        watchMediaSourceNode(source);
        const filename = sourceFilename(source, type);
        const fullLabel = filename || sourceLabel(source);
        const label = mode === "index" ? `${LABELS[type] || type}${ordinal}` : truncateMentionLabel(fullLabel);
        return {
            type,
            tag,
            token: `@${mode === "index" ? label : fullLabel}`,
            label,
            fullLabel,
            ordinal,
            referenceMode: mode,
            source: sourceLabel(source),
            sourceId: Number(link.source_id),
            sourceSlot: Number(link.source_slot) || 0,
            mediaIndex,
            previewUrl: sourcePreviewUrl(source, type),
        };
    });
}

function findMentionOption(options, reference, mode) {
    const type = String(reference?.mediaType || reference?.type || "image").toLowerCase();
    const ordinal = Number(reference?.ordinal);
    const rawSourceId = reference?.sourceId;
    const sourceId = rawSourceId == null || rawSourceId === "" ? Number.NaN : Number(rawSourceId);
    const sourceSlot = Number(reference?.sourceSlot) || 0;
    const findByOrdinal = () => Number.isFinite(ordinal) && ordinal > 0
        ? options.find((item) => item.type === type && Number(item.ordinal) === ordinal)
        : null;
    if (mode === "index") return findByOrdinal();
    if (Number.isFinite(sourceId)) {
        return options.find((item) => Number(item.sourceId) === sourceId
            && Number(item.sourceSlot) === sourceSlot
            && item.type === type) || null;
    }
    // Official tags pasted before their media exists only carry a type and an
    // ordinal. In filename mode, use that ordinal once to claim the future
    // source; after resolution updateMentionChip stores sourceId/sourceSlot and
    // the reference becomes source-bound like any other filename-mode chip.
    return findByOrdinal();
}

function isLikelyVideoUrl(url) {
    const value = String(url || "").toLowerCase();
    return /\.(mp4|webm|mov|mkv|avi|m4v)(?:[?#].*)?$/.test(value)
        || /[?&]filename=[^&]*\.(mp4|webm|mov|mkv|avi|m4v)(?:[&#]|$)/.test(value);
}

function mediaViewUrlFromWidgets(node, preferredNames) {
    const widgets = Array.isArray(node?.widgets) ? node.widgets : [];
    const preferred = new Set(preferredNames);
    const candidates = [
        ...widgets.filter((widget) => preferred.has(String(widget?.name || "").toLowerCase())),
        ...widgets,
    ];
    for (const widget of candidates) {
        const value = widget?.value;
        if (!value) continue;
        const filename = typeof value === "object" ? value?.filename : value;
        if (!filename) continue;
        const name = String(widget?.name || "").toLowerCase();
        if (!preferred.has(name) && !/\.(mp4|webm|mov|mkv|avi|m4v)$/i.test(String(filename))) continue;
        const params = new URLSearchParams({
            filename: String(filename),
            type: typeof value === "object" ? String(value.type || "input") : "input",
        });
        if (typeof value === "object" && value.subfolder) params.set("subfolder", String(value.subfolder));
        return `/view?${params.toString()}`;
    }
    return "";
}

function getNodeVideoSrc(node) {
    for (const widget of node?.widgets || []) {
        const element = widget?.element;
        const video = element?.matches?.("video") ? element : element?.querySelector?.("video");
        if (video?.currentSrc || video?.src) return video.currentSrc || video.src;
    }
    return mediaViewUrlFromWidgets(node, ["video", "file", "filename", "video_file", "videofile"]);
}

function refreshMentionPreviews() {
    for (const node of app.graph?._nodes || []) {
        if (!isTarget(node)) continue;
        normalizeLinks(node);
        if (!canUseMediaMentions(node)) {
            closeMentionMenu(node);
            continue;
        }
        const options = mentionOptions(node);
        const currentMode = referenceMentionMode(node);
        for (const chip of node.__h3Editor?.querySelectorAll?.(".h3-mention-chip") || []) {
            const sourceId = chip.dataset.sourceId ? Number(chip.dataset.sourceId) : null;
            const ordinal = Number(chip.dataset.ordinal) || null;
            const option = findMentionOption(options, {
                mediaType: chip.dataset.mediaType || "image",
                ordinal,
                sourceId,
                sourceSlot: Number(chip.dataset.sourceSlot) || 0,
            }, currentMode);
            updateMentionChip(chip, option || {
                type: chip.dataset.mediaType || "image",
                token: chip.dataset.token || "",
                label: chip.dataset.label || chip.dataset.fullLabel || "",
                fullLabel: chip.dataset.fullLabel || chip.dataset.label || "",
                referenceMode: currentMode,
                ordinal,
                sourceId,
                sourceSlot: Number(chip.dataset.sourceSlot) || 0,
                previewUrl: "",
                unresolved: true,
                pending: sourceId == null && ordinal != null,
            });
        }
        if (node.__h3Editor) syncPromptFromEditor(node, false);
        const menu = node.__h3MentionMenu;
        if (menu) {
            const query = String(menu.mention?.query || "").toLowerCase();
            menu.options = options.filter((option) => !query || `${option.label} ${option.fullLabel || ""} ${option.source}`.toLowerCase().includes(query));
            menu.activeIndex = Math.min(menu.activeIndex, Math.max(0, menu.options.length - 1));
            renderMentionMenu(node);
        }
        node.setDirtyCanvas?.(true, true);
    }
    app.graph?.setDirtyCanvas?.(true, true);
}

function updateMentionChip(chip, option) {
    if (!chip || !option) return;
    const nextToken = option.token || option.tag || chip.dataset.token || "";
    const nextTag = option.tag || chip.dataset.tag || nextToken;
    const nextLabel = option.label || chip.dataset.label || nextToken;
    const nextFullLabel = option.fullLabel || nextLabel;
    const nextPreviewUrl = option.previewUrl || "";
    chip.classList.toggle("is-pending", Boolean(option.pending));
    chip.classList.toggle("is-unresolved", Boolean(option.unresolved) && !option.pending);
    chip.dataset.token = nextToken;
    chip.dataset.tag = nextTag;
    chip.dataset.label = nextLabel;
    chip.dataset.fullLabel = nextFullLabel;
    chip.dataset.mediaType = option.type || chip.dataset.mediaType || "image";
    chip.dataset.referenceMode = option.referenceMode || chip.dataset.referenceMode || "index";
    chip.dataset.ordinal = Number(option.ordinal) || chip.dataset.ordinal || "";
    chip.dataset.mediaIndex = Number(option.mediaIndex) || chip.dataset.mediaIndex || "";
    chip.dataset.pendingReference = option.pending ? "true" : "";
    if (option.sourceId != null) chip.dataset.sourceId = String(option.sourceId);
    if (option.sourceSlot != null) chip.dataset.sourceSlot = String(Number(option.sourceSlot) || 0);
    chip.dataset.previewUrl = nextPreviewUrl;
    chip.title = option.pending
        ? (ZH_BROWSER ? "\u7b49\u5f85\u8fde\u63a5\u5bf9\u5e94\u5e8f\u53f7\u7684\u5a92\u4f53\u7d20\u6750" : "Waiting for media with the matching index")
        : option.unresolved
            ? (ZH_BROWSER ? "\u5df2\u65ad\u5f00\uff1a\u8bf7\u91cd\u65b0\u8fde\u63a5\u6216\u5220\u9664\u8be5\u5f15\u7528" : "Disconnected: reconnect or remove this reference")
        : nextFullLabel;
    const label = chip.querySelector?.(".h3-mention-chip-label");
    if (label) label.textContent = `@${nextLabel}`;
    const thumb = chip.querySelector?.(".h3-mention-chip-thumb");
    if (thumb && (thumb.dataset?.previewUrl !== nextPreviewUrl || thumb.dataset?.mediaType !== (option.type || "image"))) {
        const replacement = makeMentionThumb(option);
        replacement.dataset.previewUrl = nextPreviewUrl;
        thumb.replaceWith(replacement);
    } else if (!thumb) {
        const replacement = makeMentionThumb(option);
        replacement.dataset.previewUrl = nextPreviewUrl;
        chip.prepend(replacement);
    }
}

function requestMentionPreviewRefresh() {
    if (mentionPreviewRefreshTimer) return;
    mentionPreviewRefreshTimer = setTimeout(() => {
        mentionPreviewRefreshTimer = null;
        refreshMentionPreviews();
    }, 0);
}

function watchMediaSourceNode(node) {
    if (!node) return;
    node.__h3MediaSourceWatchInstalled = true;
    for (const widget of node.widgets || []) {
        if (!widget || widget.__h3MediaSourceWatchInstalled) continue;
        widget.__h3MediaSourceWatchInstalled = true;
        const originalCallback = widget.callback;
        widget.callback = function onMediaSourceWidgetChange(value) {
            const result = originalCallback?.apply(this, arguments);
            requestMentionPreviewRefresh();
            return result;
        };
        const element = widget.inputEl || widget.element;
        element?.addEventListener?.("change", requestMentionPreviewRefresh, true);
        element?.addEventListener?.("input", requestMentionPreviewRefresh, true);
    }
}

function installMediaSourceNode(nodeType, nodeData) {
    const name = String(nodeData?.name || "").toLowerCase();
    if (!name.includes("loadimage") && !name.includes("loadvideo") && !name.includes("loadaudio")) return;
    if (nodeType.prototype.__h3MediaSourceInstalled) return;
    nodeType.prototype.__h3MediaSourceInstalled = true;
    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3MediaSource() {
        const result = originalCreated?.apply(this, arguments);
        watchMediaSourceNode(this);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3MediaSource(info) {
        const result = originalConfigure?.apply(this, arguments);
        watchMediaSourceNode(this);
        requestMentionPreviewRefresh();
        return result;
    };
}

function getVideoFrameThumbnail(videoUrl) {
    if (!videoUrl) return "";
    const cached = videoThumbnailCache.get(videoUrl);
    if (cached?.dataUrl) return cached.dataUrl;
    if (cached?.loading) return "";
    if (cached?.failed) {
        if (Date.now() - Number(cached.failedAt || 0) < 1800) return "";
        videoThumbnailCache.delete(videoUrl);
    }
    if (!isLikelyVideoUrl(videoUrl) && !/^blob:|^data:video\//i.test(videoUrl)) return "";

    const entry = { loading: true, dataUrl: "" };
    videoThumbnailCache.set(videoUrl, entry);
    const video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    video.preload = "metadata";
    let finished = false;
    let sampleTimes = [];
    let sampleIndex = 0;
    let bestFrame = null;

    const cleanup = () => {
        video.removeAttribute("src");
        video.load?.();
    };
    const succeed = (dataUrl) => {
        if (finished || !dataUrl) return;
        finished = true;
        entry.loading = false;
        entry.dataUrl = dataUrl;
        cleanup();
        requestMentionPreviewRefresh();
    };
    const fail = () => {
        if (finished) return;
        finished = true;
        entry.loading = false;
        entry.failed = true;
        entry.failedAt = Date.now();
        cleanup();
    };
    const measureFrame = (context, width, height) => {
        try {
            const data = context.getImageData(0, 0, width, height).data;
            let total = 0;
            let bright = 0;
            let count = 0;
            const stride = 4 * Math.max(1, Math.floor((width * height) / 1600));
            for (let index = 0; index < data.length; index += stride) {
                const luminance = (data[index] * 0.2126) + (data[index + 1] * 0.7152) + (data[index + 2] * 0.0722);
                total += luminance;
                if (luminance > 24) bright += 1;
                count += 1;
            }
            const average = count ? total / count : 0;
            const brightRatio = count ? bright / count : 0;
            return { score: average + brightRatio * 90, usable: average > 18 || brightRatio > 0.035 };
        } catch {
            return { score: 255, usable: true };
        }
    };
    const capture = () => {
        if (finished || !video.videoWidth || !video.videoHeight) return;
        try {
            const canvas = document.createElement("canvas");
            const scale = Math.min(1, 96 / Math.max(video.videoWidth, video.videoHeight));
            canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
            canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
            const context = canvas.getContext("2d");
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const quality = measureFrame(context, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL("image/jpeg", 0.8);
            if (!bestFrame || quality.score > bestFrame.score) bestFrame = { dataUrl, score: quality.score };
            if (quality.usable) succeed(dataUrl);
            else seekNextSample();
        } catch {
            fail();
        }
    };
    const captureDecodedFrame = () => {
        if (finished) return;
        if (typeof video.requestVideoFrameCallback === "function") video.requestVideoFrameCallback(capture);
        else setTimeout(capture, 80);
    };
    const seekNextSample = () => {
        if (finished) return;
        if (sampleIndex >= sampleTimes.length) {
            if (bestFrame?.dataUrl && bestFrame.score > 18) succeed(bestFrame.dataUrl);
            else fail();
            return;
        }
        const nextTime = sampleTimes[sampleIndex++];
        try {
            if (Math.abs(Number(video.currentTime || 0) - nextTime) < 0.015) captureDecodedFrame();
            else video.currentTime = nextTime;
        } catch {
            captureDecodedFrame();
        }
    };

    setTimeout(fail, 4500);
    video.addEventListener("loadedmetadata", () => {
        const duration = Number(video.duration);
        if (!Number.isFinite(duration) || duration <= 0) sampleTimes = [0];
        else {
            const end = Math.max(0, duration - 0.06);
            sampleTimes = Array.from(new Set([
                duration * 0.12,
                0.5,
                duration * 0.3,
                duration * 0.55,
                duration * 0.8,
            ].map((time) => Number(Math.min(end, Math.max(0, time)).toFixed(3)))));
        }
        seekNextSample();
    }, { once: true });
    video.addEventListener("seeked", captureDecodedFrame);
    video.addEventListener("error", fail, { once: true });
    video.src = videoUrl;
    video.load?.();
    return "";
}

function sourcePreviewUrl(node, mediaType) {
    if (!node) return "";
    if (mediaType === "audio") return "";
    if (mediaType === "image") {
        const currentImageUrl = mediaViewUrlFromWidgets(node, ["image", "file", "filename"]);
        if (currentImageUrl) return currentImageUrl;
    }
    const image = (node.imgs || []).find((item) => item?.src && !isLikelyVideoUrl(item.src));
    if (image?.src) return image.src;
    for (const widget of node.widgets || []) {
        const element = widget?.element;
        const img = element?.matches?.("img") ? element : element?.querySelector?.("img");
        if (img?.src) return img.src;
        const video = element?.matches?.("video") ? element : element?.querySelector?.("video");
        if (mediaType === "video" && video?.poster) return video.poster;
    }
    if (mediaType === "video") return getVideoFrameThumbnail(getNodeVideoSrc(node));
    const value = getWidget(node, "image")?.value;
    const filename = typeof value === "object" ? value?.filename : value;
    if (!filename) return "";
    const params = new URLSearchParams({ filename: String(filename), type: typeof value === "object" ? String(value.type || "input") : "input" });
    if (typeof value === "object" && value.subfolder) params.set("subfolder", String(value.subfolder));
    return `/view?${params.toString()}`;
}

function makeAudioIcon(className) {
    const image = document.createElement("img");
    image.className = className;
    image.alt = "";
    image.draggable = false;
    image.setAttribute("aria-hidden", "true");
    image.src = AUDIO_ICON_SVG;
    image.style.background = "transparent";
    return image;
}

function makeMentionThumb(option, menu = false) {
    const className = menu ? "h3-mention-menu-thumb" : "h3-mention-chip-thumb";
    if (option.type === "audio") {
        const audio = makeAudioIcon(className);
        audio.dataset.previewUrl = "";
        audio.dataset.mediaType = "audio";
        return audio;
    }
    if (option.previewUrl) {
        const image = document.createElement("img");
        image.className = className;
        image.alt = "";
        image.draggable = false;
        image.src = option.previewUrl;
        image.dataset.previewUrl = option.previewUrl;
        image.dataset.mediaType = option.type || "image";
        image.addEventListener("error", () => image.replaceWith(makeMentionThumb({ ...option, previewUrl: "" }, menu)), { once: true });
        return image;
    }
    const icon = document.createElement("span");
    icon.className = `${className} is-${option.type || "image"}`;
    icon.setAttribute("aria-hidden", "true");
    icon.dataset.previewUrl = "";
    icon.dataset.mediaType = option.type || "image";
    return icon;
}

function makeMentionChip(option) {
    const chip = document.createElement("span");
    chip.className = `h3-mention-chip${option.pending ? " is-pending" : option.unresolved ? " is-unresolved" : ""}`;
    chip.contentEditable = "false";
    chip.dataset.token = option.token || option.tag || "";
    chip.dataset.tag = option.tag || option.token || "";
    chip.dataset.label = option.label || "";
    chip.dataset.fullLabel = option.fullLabel || option.label || "";
    chip.dataset.mediaType = option.type || "image";
    chip.dataset.referenceMode = option.referenceMode || "index";
    chip.dataset.ordinal = Number(option.ordinal) || "";
    chip.dataset.mediaIndex = Number(option.mediaIndex) || "";
    chip.dataset.sourceId = option.sourceId != null ? String(option.sourceId) : "";
    chip.dataset.sourceSlot = String(option.sourceSlot || 0);
    chip.dataset.previewUrl = option.previewUrl || "";
    chip.dataset.pendingReference = option.pending ? "true" : "";
    chip.title = option.pending
        ? (ZH_BROWSER ? "\u7b49\u5f85\u8fde\u63a5\u5bf9\u5e94\u5e8f\u53f7\u7684\u5a92\u4f53\u7d20\u6750" : "Waiting for media with the matching index")
        : option.unresolved
            ? (ZH_BROWSER ? "\u5df2\u65ad\u5f00\uff1a\u8bf7\u91cd\u65b0\u8fde\u63a5\u6216\u5220\u9664\u8be5\u5f15\u7528" : "Disconnected: reconnect or remove this reference")
        : (option.fullLabel || option.label || "");
    const label = document.createElement("span");
    label.className = "h3-mention-chip-label";
    label.textContent = `@${option.label || ""}`;
    chip.append(makeMentionThumb(option), label);
    chip.addEventListener("pointerdown", (event) => {
        if (event.target?.closest?.(".h3-mention-chip-label")) return;
        event.preventDefault();
        event.stopPropagation();
        const selection = window.getSelection?.();
        if (!selection) return;
        const range = document.createRange();
        const before = event.clientX < chip.getBoundingClientRect().left + chip.getBoundingClientRect().width / 2;
        before ? range.setStartBefore(chip) : range.setStartAfter(chip);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
    });
    return chip;
}

function isDialogueBlock(node) {
    return node?.nodeType === Node.ELEMENT_NODE && node.classList?.contains(DIALOGUE_CLASS);
}

function dialogueBlockText(block) {
    return editorText(block);
}

function makeDialogueBlock(value = "") {
    const block = document.createElement("span");
    block.className = DIALOGUE_CLASS;
    block.spellcheck = false;
    block.dataset.dialogue = "true";
    appendTextWithBreaks(block, value);
    if (!String(value || "")) block.append(makeCaretSentinel());
    return block;
}

function ensureDialogueInnerCaret(block) {
    if (!block || dialogueBlockText(block)) return;
    if (![...(block.childNodes || [])].some((node) => isCaretSentinelText(node))) {
        block.append(makeCaretSentinel());
    }
}

function appendDialogueBlock(container, value = "") {
    container.append(makeCaretSentinel(), makeDialogueBlock(value), makeCaretSentinel());
}

function appendPromptTextWithDialogueBlocks(container, value) {
    const source = String(value || "");
    const pattern = /<d>([\s\S]*?)<\/d>/gi;
    let cursor = 0;
    let match;
    while ((match = pattern.exec(source))) {
        appendTextWithBreaks(container, source.slice(cursor, match.index));
        appendDialogueBlock(container, match[1]);
        cursor = match.index + match[0].length;
    }
    appendTextWithBreaks(container, source.slice(cursor));
}

function promptViewMode(node) {
    return String(node?.properties?.[PROMPT_VIEW_PROP] || PROMPT_VIEW_STRUCTURED) === PROMPT_VIEW_RAW
        ? PROMPT_VIEW_RAW
        : PROMPT_VIEW_STRUCTURED;
}

function isRawPromptMode(node) {
    return promptViewMode(node) === PROMPT_VIEW_RAW;
}

function setPromptViewMode(node, mode) {
    if (!node) return;
    node.properties ||= {};
    node.properties[PROMPT_VIEW_PROP] = mode === PROMPT_VIEW_RAW ? PROMPT_VIEW_RAW : PROMPT_VIEW_STRUCTURED;
}

function promptMentionTag(type, ordinal) {
    const mediaType = String(type || "image").toLowerCase();
    const index = Number(ordinal);
    if (!Number.isFinite(index) || index <= 0) return "";
    if (mediaType === "image") return "<Picture " + index + ">";
    if (mediaType === "video") return "<Video " + index + ">";
    if (mediaType === "audio") return "<Audio " + index + ">";
    return "";
}

function promptTextFromPart(part) {
    if (part?.type === "dialogue") return "<d>" + String(part.text || "") + "</d>";
    if (part?.type !== "mention") return String(part?.text || "");
    return String(part.tag || part.token || promptMentionTag(part.mediaType, part.ordinal) || "");
}

function promptDocTextFromParts(parts) {
    return (Array.isArray(parts) ? parts : []).map((part) => promptTextFromPart(part)).join("");
}

function promptPartsFromText(node, value) {
    const text = String(value || "");
    const parts = [];
    const pushText = (chunk) => {
        const next = String(chunk || "");
        if (!next) return;
        if (parts.at(-1)?.type === "text") parts[parts.length - 1].text += next;
        else parts.push({ type: "text", text: next });
    };
    let plainStart = 0;
    let cursor = 0;
    const candidates = pastedMentionCandidates(node);
    while (cursor < text.length) {
        const dialogueMatch = text.slice(cursor).match(/^<d>([\s\S]*?)<\/d>/i);
        const match = dialogueMatch ? {
            raw: dialogueMatch[0],
            kind: "dialogue",
            text: dialogueMatch[1] || "",
        } : pastedOfficialMediaTagMatch(node, text, cursor)
            || candidates.find((candidate) => text.slice(cursor, cursor + candidate.raw.length).toLocaleLowerCase() === candidate.raw.toLocaleLowerCase());
        if (!match) {
            cursor += 1;
            continue;
        }
        if (plainStart < cursor) pushText(text.slice(plainStart, cursor));
        if (match.kind === "dialogue") {
            parts.push({ type: "dialogue", text: match.text });
            cursor += match.raw.length;
            plainStart = cursor;
            continue;
        }
        const option = match.option || {};
        parts.push({
            type: "mention",
            token: match.raw || option.token || "",
            tag: option.tag || match.raw || option.token || "",
            label: option.label || "",
            fullLabel: option.fullLabel || option.label || "",
            mediaType: option.type || "image",
            referenceMode: option.referenceMode || referenceMentionMode(node),
            ordinal: Number(option.ordinal) || null,
            mediaIndex: Number(option.mediaIndex) || null,
            sourceId: option.sourceId != null ? Number(option.sourceId) : null,
            sourceSlot: Number(option.sourceSlot) || 0,
            previewUrl: option.previewUrl || "",
            unresolved: Boolean(option.unresolved),
            pending: Boolean(option.pending),
        });
        cursor += match.raw.length;
        plainStart = cursor;
    }
    if (plainStart < text.length) pushText(text.slice(plainStart));
    return parts;
}

function serializeRawPromptDoc(node, editor) {
    let text = "";
    const parts = [];
    const pushText = (value) => {
        const next = String(value || "").replaceAll(CARET_SENTINEL, "");
        if (!next) return;
        text += next;
    };
    const visit = (item) => {
        if (item.nodeType === Node.TEXT_NODE) {
            pushText(item.textContent);
            return;
        }
        if (item.nodeType !== Node.ELEMENT_NODE) return;
        if (isDialogueBlock(item)) {
            const dialogue = dialogueBlockText(item);
            text += `<d>${dialogue}</d>`;
            return;
        }
        if (isMentionChip(item)) {
            text += String(item.dataset.tag || item.dataset.token || "");
            return;
        }
        if (item.tagName === "BR") {
            text += "\n";
            return;
        }
        for (const child of item.childNodes || []) visit(child);
    };
    for (const child of editor.childNodes || []) visit(child);
    return {
        version: 1,
        text,
        parts: promptPartsFromText(node, text),
    };
}

function appendRawPromptText(container, value) {
    appendTextWithBreaks(container, String(value || ""));
}

function serializeEditorDoc(editor) {
    const node = editorPromptNode(editor);
    if (isRawPromptMode(node)) {
        const current = node?.properties?.[PROMPT_DOC_PROP];
        if (!node?.__h3RawPromptNeedsSync && current) return clonePromptDoc(current);
        return serializeRawPromptDoc(node, editor);
    }
    const parts = [];
    const pushText = (text) => {
        const value = String(text || "").replaceAll("\u200B", "");
        if (!value) return;
        if (parts.at(-1)?.type === "text") parts[parts.length - 1].text += value;
        else parts.push({ type: "text", text: value });
    };
    const visit = (item) => {
        if (item.nodeType === Node.TEXT_NODE) {
            pushText(item.textContent);
            return;
        }
        if (item.nodeType !== Node.ELEMENT_NODE) return;
        if (isDialogueBlock(item)) {
            const text = dialogueBlockText(item);
            parts.push({ type: "dialogue", text });
            return;
        }
        if (item.classList?.contains("h3-mention-chip")) {
            parts.push({
                type: "mention",
                token: item.dataset.token || "",
                tag: item.dataset.tag || item.dataset.token || "",
                label: item.dataset.label || "",
                fullLabel: item.dataset.fullLabel || item.dataset.label || "",
                mediaType: item.dataset.mediaType || "image",
                referenceMode: item.dataset.referenceMode || "index",
                ordinal: Number(item.dataset.ordinal) || null,
                mediaIndex: Number(item.dataset.mediaIndex) || null,
                sourceId: item.dataset.sourceId ? Number(item.dataset.sourceId) : null,
                sourceSlot: Number(item.dataset.sourceSlot) || 0,
                previewUrl: item.dataset.previewUrl || "",
            });
            return;
        }
        if (item.tagName === "BR") {
            pushText("\n");
            return;
        }
        const block = ["DIV", "P"].includes(item.tagName);
        if (block && parts.length && !(parts.at(-1)?.type === "text" && parts.at(-1).text.endsWith("\n"))) pushText("\n");
        for (const child of item.childNodes || []) visit(child);
    };
    for (const child of editor.childNodes || []) visit(child);
    return {
        version: 1,
        text: promptDocTextFromParts(parts),
        parts,
    };
}

function appendTextWithBreaks(container, value) {
    String(value || "").split("\n").forEach((part, index) => {
        if (index) container.append(document.createElement("br"));
        if (part) container.append(document.createTextNode(part));
    });
}

function renderEditorFromNode(node, force = false) {
    const editor = node?.__h3Editor;
    const widget = getWidget(node, "prompt");
    if (!editor || !widget || (document.activeElement === editor && !force)) return;
    const doc = node.properties?.[PROMPT_DOC_PROP];
    editor.textContent = "";
    const raw = isRawPromptMode(node);
    editor.classList.toggle("is-raw", raw);
    node.__h3EditorWrap?.classList?.toggle("is-raw", raw);
    if (raw) {
        closeMentionMenu(node);
        appendRawPromptText(editor, Array.isArray(doc?.parts) ? promptDocTextFromParts(doc.parts) : String(doc?.text ?? widget.value ?? ""));
        return;
    }
    if (!Array.isArray(doc?.parts)) {
        appendPromptTextWithDialogueBlocks(editor, String(widget.value || ""));
        return;
    }
    const live = mentionOptions(node);
    for (const part of doc.parts) {
        if (part?.type === "dialogue") {
            appendDialogueBlock(editor, String(part.text || ""));
            continue;
        }
        if (part?.type !== "mention") {
            appendTextWithBreaks(editor, part?.text || "");
            continue;
        }
        const currentMode = referenceMentionMode(node);
        const partSourceId = part.sourceId != null && Number.isFinite(Number(part.sourceId)) ? Number(part.sourceId) : null;
        const partOrdinal = Number(part.ordinal) || null;
        const option = findMentionOption(live, {
            mediaType: part.mediaType || "image",
            ordinal: partOrdinal,
            sourceId: partSourceId,
            sourceSlot: Number(part.sourceSlot) || 0,
        }, currentMode);
        editor.append(makeMentionChip({
            type: part.mediaType || option?.type || "image",
            token: option?.token || part.token || option?.tag || "",
            tag: option?.tag || part.tag || part.token || "",
            label: option?.label || part.label || part.token || "",
            fullLabel: option?.fullLabel || part.fullLabel || part.label || part.token || "",
            referenceMode: currentMode,
            ordinal: option?.ordinal ?? part.ordinal,
            sourceId: option?.sourceId ?? part.sourceId,
            sourceSlot: option?.sourceSlot ?? part.sourceSlot ?? 0,
            previewUrl: option?.previewUrl || "",
            unresolved: !option,
            pending: !option && partSourceId == null && partOrdinal != null,
        }));
    }
}

function syncPromptFromEditor(node, markDirty = true) {
    const editor = node?.__h3Editor;
    const widget = getWidget(node, "prompt");
    if (!editor || !widget || node.__h3EditorSyncing) return;
    node.__h3EditorSyncing = true;
    try {
        const doc = serializeEditorDoc(editor);
        widget.value = doc.text;
        if (widget._state) widget._state.value = doc.text;
        node.properties ||= {};
        node.properties[PROMPT_DOC_PROP] = doc;
        syncModeWidgets(node);
        if (isRawPromptMode(node)) node.__h3RawPromptNeedsSync = false;
        syncSegmentSummary(node);
        if (markDirty) {
            node.setDirtyCanvas?.(true, true);
            app.graph?.setDirtyCanvas?.(true, true);
            app.graph?.change?.();
        }
    } finally {
        node.__h3EditorSyncing = false;
    }
}

function clonePromptDoc(doc) {
    const source = doc && typeof doc === "object" ? doc : {};
    return {
        version: 1,
        text: String(source.text || ""),
        parts: Array.isArray(source.parts) ? source.parts.map((part) => ({ ...part })) : [],
    };
}

function promptDocKey(doc) {
    return JSON.stringify(clonePromptDoc(doc));
}

function editorPromptNode(editor) {
    return editor?.__h3PromptNode || null;
}

function editorFromEvent(event) {
    const target = event?.target;
    if (target?.closest) {
        const editor = target.closest(".h3-prompt-editor");
        if (editor) return editor;
    }
    const active = typeof document !== "undefined" ? document.activeElement : null;
    return active?.closest?.(".h3-prompt-editor") || activePromptNode?.__h3Editor || null;
}

function isPromptUndoRedoEvent(event) {
    if (!(event?.ctrlKey || event?.metaKey)) return false;
    const key = String(event.key || "").toLowerCase();
    const code = String(event.code || "");
    return key === "z" || key === "y" || code === "KeyZ" || code === "KeyY";
}

function ensurePromptHistory(node) {
    const editor = node?.__h3Editor;
    if (!editor) return null;
    if (node.__h3PromptHistory) return node.__h3PromptHistory;
    const doc = clonePromptDoc(serializeEditorDoc(editor));
    node.__h3PromptHistory = {
        undo: [{ doc }],
        redo: [],
        lastKey: promptDocKey(doc),
        applying: false,
    };
    return node.__h3PromptHistory;
}

function resetPromptHistory(node) {
    node.__h3PromptHistory = null;
    ensurePromptHistory(node);
}

function pushPromptHistory(node) {
    const history = ensurePromptHistory(node);
    const editor = node?.__h3Editor;
    if (!history || !editor || history.applying) return;
    const doc = clonePromptDoc(serializeEditorDoc(editor));
    const key = promptDocKey(doc);
    if (key === history.lastKey) return;
    history.undo.push({ doc });
    if (history.undo.length > PROMPT_HISTORY_LIMIT) history.undo.shift();
    history.redo = [];
    history.lastKey = key;
}

function setEditorCaretAtEnd(editor) {
    if (!editor) return;
    const selection = window.getSelection?.();
    if (!selection) return;
    const range = document.createRange();
    range.selectNodeContents(editor);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
}

function applyPromptHistoryEntry(node, entry) {
    const history = node?.__h3PromptHistory;
    const editor = node?.__h3Editor;
    const widget = getWidget(node, "prompt");
    if (!history || !editor || !entry?.doc || !widget) return false;
    history.applying = true;
    try {
        const doc = clonePromptDoc(entry.doc);
        node.properties ||= {};
        node.properties[PROMPT_DOC_PROP] = doc;
        widget.value = doc.text;
        if (widget._state) widget._state.value = doc.text;
        renderEditorFromNode(node, true);
        syncPromptFromEditor(node, false);
        history.lastKey = promptDocKey(doc);
    } finally {
        history.applying = false;
    }
    closeMentionMenu(node);
    editor.focus();
    setEditorCaretAtEnd(editor);
    return true;
}

function handlePromptHistoryKeydown(node, event) {
    if (!isPromptUndoRedoEvent(event)) return false;
    event.preventDefault?.();
    event.stopPropagation?.();
    event.stopImmediatePropagation?.();
    const history = ensurePromptHistory(node);
    if (!history) return true;
    const key = String(event.key || "").toLowerCase();
    const isRedo = key === "y" || String(event.code || "") === "KeyY" || (key === "z" && event.shiftKey);
    if (isRedo) {
        const entry = history.redo.pop();
        if (!entry) return true;
        history.undo.push(entry);
        applyPromptHistoryEntry(node, entry);
        return true;
    }
    if (history.undo.length <= 1) return true;
    const current = history.undo.pop();
    if (current) history.redo.push(current);
    applyPromptHistoryEntry(node, history.undo[history.undo.length - 1]);
    return true;
}

function handlePromptUndoRedoCapture(event) {
    if (!isPromptUndoRedoEvent(event)) return;
    const node = editorPromptNode(editorFromEvent(event));
    if (node && !node.__h3PromptComposing) {
        pushPromptHistory(node);
        handlePromptHistoryKeydown(node, event);
    }
}

function handlePromptHistoryBeforeInputCapture(event) {
    if (event?.inputType !== "historyUndo" && event?.inputType !== "historyRedo") return;
    const node = editorPromptNode(editorFromEvent(event));
    if (!node || node.__h3PromptComposing) return;
    const isRedo = event.inputType === "historyRedo";
    pushPromptHistory(node);
    handlePromptHistoryKeydown(node, {
        ctrlKey: true,
        metaKey: false,
        shiftKey: isRedo,
        key: isRedo ? "y" : "z",
        code: isRedo ? "KeyY" : "KeyZ",
        preventDefault: () => event.preventDefault?.(),
        stopPropagation: () => event.stopPropagation?.(),
        stopImmediatePropagation: () => event.stopImmediatePropagation?.(),
    });
}

function ensurePromptUndoRedoShield() {
    if (globalThis.__H3_PROMPT_UNDO_SHIELD_INSTALLED || typeof window === "undefined") return;
    globalThis.__H3_PROMPT_UNDO_SHIELD_INSTALLED = true;
    globalThis.__H3_PROMPT_UNDO_VERSION = PROMPT_UNDO_VERSION;
    window.addEventListener("keydown", handlePromptUndoRedoCapture, true);
    window.addEventListener("pointerdown", (event) => {
        const editor = event?.target?.closest?.(".h3-prompt-editor");
        activePromptNode = editorPromptNode(editor);
    }, true);
    document.addEventListener("focusin", (event) => {
        const editor = event?.target?.closest?.(".h3-prompt-editor");
        activePromptNode = editorPromptNode(editor);
    }, true);
    document.addEventListener("beforeinput", handlePromptHistoryBeforeInputCapture, true);
}

function patchLiteGraphPromptProcessKey() {
    if (globalThis.__H3_PROMPT_PROCESS_KEY_PATCHED || !globalThis.LGraphCanvas?.prototype) return;
    const proto = globalThis.LGraphCanvas.prototype;
    const originalProcessKey = proto.processKey;
    if (typeof originalProcessKey !== "function") return;
    globalThis.__H3_PROMPT_PROCESS_KEY_PATCHED = true;
    proto.processKey = function processKeyH3PromptEditorShield(event) {
        const node = editorPromptNode(editorFromEvent(event));
        if (node && isPromptUndoRedoEvent(event)) {
            pushPromptHistory(node);
            handlePromptHistoryKeydown(node, event);
            return;
        }
        return originalProcessKey.apply(this, arguments);
    };
}

function preparePromptEditorForUndo(editor) {
    if (!editor) return;
    if (editor.__h3UndoPrepared && editor.dataset?.h3UndoVersion === PROMPT_UNDO_VERSION) return;
    editor.setAttribute("data-h3-undo-version", PROMPT_UNDO_VERSION);
    try {
        Object.defineProperty(editor, "type", {
            value: "textarea",
            configurable: true,
        });
    } catch {
        editor.type = "textarea";
    }
    editor.__h3UndoPrepared = true;
}

function getMentionRange(editor) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !selection.isCollapsed) return null;
    const caret = selection.getRangeAt(0);
    if (!editor.contains(caret.startContainer)) return null;
    if (caret.startContainer.parentElement?.closest?.(`.${DIALOGUE_CLASS}`)) return null;
    // Mention chips are contentEditable=false elements whose visible text also
    // contains an "@". Reading cloneContents().textContent therefore made a
    // normal character typed after an existing chip look like an active @ query.
    // Build a small editable-text stream instead, treating chips and line breaks
    // as hard boundaries.
    const units = [];
    const visit = (node) => {
        if (node.nodeType === Node.TEXT_NODE) {
            if (!node.parentElement?.closest?.(".h3-mention-chip")) units.push({ kind: "text", node });
            return;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        if (isDialogueBlock(node)) {
            units.push({ kind: "dialogue", node });
            return;
        }
        if (node.classList?.contains("h3-mention-chip")) {
            units.push({ kind: "chip", node });
            return;
        }
        if (node.tagName === "BR") {
            units.push({ kind: "break", node });
            return;
        }
        for (const child of node.childNodes || []) visit(child);
    };
    visit(editor);

    if (caret.startContainer.nodeType !== Node.TEXT_NODE) return null;
    const currentIndex = units.findIndex((unit) => unit.kind === "text" && unit.node === caret.startContainer);
    if (currentIndex < 0) return null;

    const selected = [];
    for (let index = currentIndex; index >= 0; index -= 1) {
        const unit = units[index];
        if (unit.kind !== "text") break;
        const end = index === currentIndex ? caret.startOffset : (unit.node.textContent || "").length;
        selected.unshift({ unit, text: (unit.node.textContent || "").slice(0, end) });
    }
    const before = selected.map((entry) => entry.text).join("");
    const match = before.match(/@[^@\n]*$/);
    if (!match) return null;

    const targetStart = before.length - match[0].length;
    let offset = 0;
    const range = document.createRange();
    for (const entry of selected) {
        const next = offset + entry.text.length;
        if (targetStart <= next) {
            range.setStart(entry.unit.node, Math.max(0, targetStart - offset));
            break;
        }
        offset = next;
    }
    range.setEnd(caret.startContainer, caret.startOffset);
    return { range, query: match[0].slice(1) };
}

function closeMentionMenu(node) {
    const menu = node?.__h3MentionMenu;
    menu?.element?.remove?.();
    if (node) node.__h3MentionMenu = null;
}

function dialogueBlockAtSelection(editor) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount) return null;
    const container = selection.getRangeAt(0).startContainer;
    const element = container.nodeType === Node.ELEMENT_NODE ? container : container.parentElement;
    const block = element?.closest?.(`.${DIALOGUE_CLASS}`);
    return block && editor.contains(block) ? block : null;
}

function dialogueBoundary(block, side) {
    if (!block?.parentNode) return null;
    const sibling = side === "before" ? block.previousSibling : block.nextSibling;
    if (isCaretSentinelText(sibling)) return sibling;
    const marker = makeCaretSentinel();
    block.parentNode.insertBefore(marker, side === "before" ? block : block.nextSibling);
    return marker;
}

function setCaretAtEndOfNode(node) {
    if (!node) return;
    const selection = window.getSelection?.();
    if (!selection) return;
    const range = document.createRange();
    let target = node;
    while (target?.lastChild) target = target.lastChild;
    if (target?.nodeType === Node.TEXT_NODE) {
        range.setStart(target, target.textContent.length);
    } else if (target?.parentNode && target !== node) {
        range.setStartAfter(target);
    } else {
        range.setStart(node, node.childNodes.length);
    }
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
}

function exitDialogueBlock(node, editor, block) {
    const marker = dialogueBoundary(block, "after");
    if (!marker) return false;
    const text = String(marker.textContent || "");
    const index = text.indexOf(CARET_SENTINEL);
    editor.focus({ preventScroll: true });
    setCaretAtNode(marker, index >= 0 ? index + CARET_SENTINEL.length : text.length);
    closeMentionMenu(node);
    return true;
}

function insertDialogueBlockAtSelection(node, editor) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !editor) return false;
    const range = selection.getRangeAt(0);
    if (!editor.contains(range.commonAncestorContainer)) return false;
    if (dialogueBlockAtSelection(editor)) return false;
    range.deleteContents();
    const before = makeCaretSentinel();
    const block = makeDialogueBlock("");
    const after = makeCaretSentinel();
    const fragment = document.createDocumentFragment();
    fragment.append(before, block, after);
    range.insertNode(fragment);
    editor.focus({ preventScroll: true });
    setCaretAtEndOfNode(block);
    closeMentionMenu(node);
    return true;
}

function insertSegmentDividerAtSelection(node, editor) {
    if (!isSegmentMode(node)) return false;
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !editor) return false;
    const range = selection.getRangeAt(0);
    if (!editor.contains(range.commonAncestorContainer)) return false;
    range.deleteContents();
    const divider = document.createTextNode("\n---\n");
    range.insertNode(divider);
    range.setStartAfter(divider);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    editor.focus({ preventScroll: true });
    closeMentionMenu(node);
    return true;
}

function findDialogueAcrossWhitespace(start, root, direction) {
    let current = start;
    const skipped = [];
    while (current) {
        if (isDialogueBlock(current)) return { block: current, skipped };
        if (isIgnorableTextNode(current)) {
            skipped.push(current);
            current = adjacentLeaf(current, root, direction);
            continue;
        }
        return null;
    }
    return null;
}

function deleteLastDialogueContent(block) {
    const leaves = [];
    const visit = (node) => {
        if (node.nodeType === Node.TEXT_NODE) {
            leaves.push(node);
            return;
        }
        if (node.nodeType === Node.ELEMENT_NODE && node.tagName === "BR") {
            leaves.push(node);
            return;
        }
        for (const child of node.childNodes || []) visit(child);
    };
    for (const child of block.childNodes || []) visit(child);
    for (let index = leaves.length - 1; index >= 0; index -= 1) {
        const leaf = leaves[index];
        if (leaf.nodeType === Node.TEXT_NODE) {
            if (deleteLastVisibleChar(leaf)) {
                setCaretAtEndOfNode(block);
                return true;
            }
            if (!leaf.textContent) leaf.remove();
            continue;
        }
        if (leaf.nodeType === Node.ELEMENT_NODE && leaf.tagName === "BR") {
            const next = leaf.nextSibling;
            leaf.remove();
            if (isOnlyCaretSentinelText(next)) next.remove();
            setCaretAtEndOfNode(block);
            return true;
        }
    }
    ensureDialogueInnerCaret(block);
    setCaretAtEndOfNode(block);
    return false;
}

function removeDialogueBlock(block) {
    if (!block?.parentNode) return false;
    const parent = block.parentNode;
    const before = block.previousSibling;
    const after = block.nextSibling;
    let marker = isCaretSentinelText(before) ? before : null;
    if (!marker) {
        marker = makeCaretSentinel();
        parent.insertBefore(marker, block);
    }
    block.remove();
    if (after !== marker && isOnlyCaretSentinelText(after)) after.remove();
    setCaretAtNode(marker, marker.textContent.length);
    return true;
}

function backspaceDialogueBoundary(editor, node) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !selection.isCollapsed) return false;
    const activeBlock = dialogueBlockAtSelection(editor);
    if (activeBlock) {
        if (!dialogueBlockText(activeBlock)) {
            const removed = removeDialogueBlock(activeBlock);
            if (removed) closeMentionMenu(node);
            return removed;
        }
        return false;
    }
    const range = selection.getRangeAt(0);
    if (!editor.contains(range.startContainer)) return false;
    const scan = getDeletionScanStart(range, editor, "backward");
    if (!scan) return false;
    const found = findDialogueAcrossWhitespace(scan.start, editor, "backward");
    if (!found?.block) return false;
    for (const skipped of found.skipped) skipped.remove?.();
    const block = found.block;
    if (dialogueBlockText(block)) {
        if (!deleteLastDialogueContent(block)) return false;
        closeMentionMenu(node);
        return true;
    }
    const removed = removeDialogueBlock(block);
    if (removed) closeMentionMenu(node);
    return removed;
}

function positionMentionMenu(element, editor) {
    const selection = window.getSelection?.();
    const caret = selection?.rangeCount ? selection.getRangeAt(0).getBoundingClientRect() : null;
    const editorRect = editor.getBoundingClientRect();
    const rect = caret && (caret.width || caret.height) ? caret : editorRect;
    const width = Math.min(280, Math.max(198, element.offsetWidth || 198));
    const height = Math.min(360, element.offsetHeight || 120);
    let left = rect.left;
    let top = rect.bottom + 6;
    if (left + width > window.innerWidth - 8) left = window.innerWidth - width - 8;
    if (top + height > window.innerHeight - 8) top = Math.max(8, rect.top - height - 6);
    element.style.left = `${Math.max(8, Math.round(left))}px`;
    element.style.top = `${Math.max(8, Math.round(top))}px`;
}

function chooseMention(node, option) {
    const state = node?.__h3MentionMenu;
    const range = state?.mention?.range;
    const editor = node?.__h3Editor;
    if (!range || !editor) return;
    range.deleteContents();
    const before = document.createTextNode("\u200B");
    const chip = makeMentionChip(option);
    const after = document.createTextNode("\u200B");
    const fragment = document.createDocumentFragment();
    fragment.append(before, chip, after);
    range.insertNode(fragment);
    const selection = window.getSelection?.();
    if (selection) {
        const caret = document.createRange();
        caret.setStart(after, after.textContent.length);
        caret.collapse(true);
        selection.removeAllRanges();
        selection.addRange(caret);
    }
    closeMentionMenu(node);
    syncPromptFromEditor(node);
    pushPromptHistory(node);
    editor.focus();
}

function renderMentionMenu(node) {
    const state = node?.__h3MentionMenu;
    if (!state) return;
    const { element, options, activeIndex } = state;
    element.textContent = "";
    const title = document.createElement("div");
    title.className = "h3-mention-menu-title";
    title.textContent = TEXT.mentionTitle;
    element.append(title);
    if (!options.length) {
        const empty = document.createElement("div");
        empty.className = "h3-mention-menu-empty";
        empty.textContent = TEXT.mentionEmpty;
        element.append(empty);
        return;
    }
    options.forEach((option, index) => {
        const item = document.createElement("div");
        item.className = `h3-mention-menu-item${index === activeIndex ? " is-active" : ""}`;
        const main = document.createElement("div");
        main.className = "h3-mention-menu-main";
        main.textContent = option.label;
        main.title = option.fullLabel || option.label || "";
        const detail = document.createElement("div");
        detail.className = "h3-mention-menu-detail";
        detail.textContent = option.source;
        const text = document.createElement("div");
        text.append(main, detail);
        item.append(makeMentionThumb(option, true), text);
        item.addEventListener("pointermove", () => {
            if (!node.__h3MentionMenu || node.__h3MentionMenu.activeIndex === index) return;
            node.__h3MentionMenu.activeIndex = index;
            renderMentionMenu(node);
        });
        item.addEventListener("pointerdown", (event) => {
            event.preventDefault();
            event.stopPropagation();
            chooseMention(node, option);
        });
        element.append(item);
    });
}

function openMentionMenu(node, editor) {
    if (!canUseMediaMentions(node)) {
        closeMentionMenu(node);
        return false;
    }
    const mention = getMentionRange(editor);
    if (!mention) {
        closeMentionMenu(node);
        return false;
    }
    const query = mention.query.toLowerCase();
    const options = mentionOptions(node).filter((option) => !query || `${option.label} ${option.fullLabel || ""} ${option.source}`.toLowerCase().includes(query));
    const existing = node.__h3MentionMenu;
    if (existing) {
        existing.mention = mention;
        existing.options = options;
        existing.activeIndex = Math.min(existing.activeIndex, Math.max(0, options.length - 1));
        renderMentionMenu(node);
        positionMentionMenu(existing.element, editor);
        return true;
    }
    const element = document.createElement("div");
    element.className = "h3-mention-menu";
    applyNativeEditorTheme(element);
    document.body.append(element);
    node.__h3MentionMenu = { element, mention, options, activeIndex: 0 };
    renderMentionMenu(node);
    positionMentionMenu(element, editor);
    return true;
}

function syncMentionMenuToCaret(node, editor) {
    if (!canUseMediaMentions(node) || !getMentionRange(editor)) {
        closeMentionMenu(node);
        return false;
    }
    return openMentionMenu(node, editor);
}

function setWidgetOption(widget, key, value) {
    if (!widget) return;
    widget.options ||= {};
    if (value === undefined) delete widget.options[key];
    else widget.options[key] = value;
    if (widget._state?.options) {
        if (value === undefined) delete widget._state.options[key];
        else widget._state.options[key] = value;
    }
}

function isVueNodesMode() {
    return Boolean(globalThis.LiteGraph?.vueNodesMode);
}

function applyNativeEditorTheme(element) {
    if (!element?.style) return;
    const LiteGraph = globalThis.LiteGraph || {};
    const modern = isVueNodesMode();
    const widgetBg = LiteGraph.WIDGET_BGCOLOR || "#222";
    const widgetText = LiteGraph.WIDGET_TEXT_COLOR || "#ddd";
    const outline = LiteGraph.WIDGET_OUTLINE_COLOR || "rgba(255, 255, 255, 0.18)";
    const menuBg = LiteGraph.NODE_DEFAULT_BGCOLOR || "#1f1f1f";
    const signature = `${modern ? 1 : 0}|${widgetBg}|${widgetText}|${outline}|${menuBg}`;
    if (element.__h3NativeThemeSignature === signature) return;
    element.__h3NativeThemeSignature = signature;
    element.classList?.toggle("h3-native-vue-nodes", modern);
    element.classList?.toggle("h3-native-legacy-nodes", !modern);
    if (modern) {
        element.style.setProperty("--h3-native-widget-bg", "var(--component-node-widget-background, var(--secondary-background, #222))");
        element.style.setProperty("--h3-native-widget-text", "var(--component-node-foreground, var(--base-foreground, #ddd))");
        element.style.setProperty("--h3-native-widget-outline", "var(--component-node-widget-background-highlighted, var(--border-default, rgba(255, 255, 255, 0.18)))");
        element.style.setProperty("--h3-native-widget-focus", "var(--component-node-widget-background-highlighted, var(--border-default, rgba(255, 255, 255, 0.28)))");
        element.style.setProperty("--h3-native-widget-muted", "var(--component-node-foreground-secondary, var(--muted-foreground, rgba(255, 255, 255, 0.42)))");
        element.style.setProperty("--h3-native-menu-bg", "var(--component-node-widget-background, var(--comfy-menu-bg, #1f1f1f))");
        element.style.setProperty("--h3-native-widget-radius", "var(--radius-lg, 8px)");
        element.style.setProperty("--h3-native-widget-padding", "8px 12px");
        element.style.setProperty("--h3-native-widget-line-height", "var(--text-xs--line-height, 1.3333333)");
        element.style.setProperty("--h3-native-widget-text-size", "var(--text-xs, var(--comfy-textarea-font-size, 12px))");
        return;
    }
    element.style.setProperty("--h3-native-widget-bg", `var(--comfy-input-bg, ${widgetBg})`);
    element.style.setProperty("--h3-native-widget-text", `var(--input-text, ${widgetText})`);
    element.style.setProperty("--h3-native-widget-outline", `var(--border-color, ${outline})`);
    element.style.setProperty("--h3-native-widget-focus", `var(--border-color, ${outline})`);
    element.style.setProperty("--h3-native-widget-muted", "rgba(255, 255, 255, 0.42)");
    element.style.setProperty("--h3-native-menu-bg", `var(--comfy-menu-bg, ${menuBg})`);
    element.style.setProperty("--h3-native-widget-radius", "0px");
    element.style.setProperty("--h3-native-widget-padding", "2px");
    element.style.setProperty("--h3-native-widget-line-height", "normal");
    element.style.setProperty("--h3-native-widget-text-size", "var(--comfy-textarea-font-size, 12px)");
}

function syncEditorThemes(force = false) {
    const modern = isVueNodesMode();
    if (!force && lastVueNodesMode === modern) return;
    lastVueNodesMode = modern;
    for (const node of app.graph?._nodes || []) {
        if (!isTarget(node)) continue;
        applyNativeEditorTheme(node.__h3EditorWrap);
        applyNativeEditorTheme(node.__h3MentionMenu?.element);
    }
    app.graph?.setDirtyCanvas?.(true, true);
}

function installNativeThemeWatcher() {
    if (nativeThemeWatcherInstalled) return;
    nativeThemeWatcherInstalled = true;
    lastVueNodesMode = null;
    setInterval(() => syncEditorThemes(), 1000);
    for (const delay of [0, 60, 180]) setTimeout(() => syncEditorThemes(true), delay);
}

function patchEditorKeyHandling() {
    const proto = globalThis.LGraphCanvas?.prototype;
    if (!proto || proto.__h3PromptKeyHandlingPatched || typeof proto.processKey !== "function") return;
    proto.__h3PromptKeyHandlingPatched = true;
    const original = proto.processKey;
    proto.processKey = function processKeyWithH3PromptEditor(event) {
        const editor = event?.target?.closest?.(".h3-prompt-editor")
            || document.activeElement?.closest?.(".h3-prompt-editor")
            || activePromptNode?.__h3Editor;
        if (editor) {
            const node = editorPromptNode(editor);
            if (node && isPromptUndoRedoEvent(event)) handlePromptHistoryKeydown(node, event);
            return;
        }
        return original.apply(this, arguments);
    };
}

function hideOriginalPromptWidget(widget) {
    if (!widget) return;
    if (!widget.__h3PromptHidden) {
        widget.__h3PromptHidden = true;
        widget.__h3OriginalType = widget.type;
        widget.__h3OriginalComputeSize = widget.computeSize;
        widget.__h3OriginalHidden = widget.hidden;
        widget.__h3OriginalOptionsHidden = widget.options?.hidden;
        widget.__h3OriginalOptionsCanvasOnly = widget.options?.canvasOnly;
    }
    widget.hidden = true;
    setWidgetOption(widget, "hidden", true);
    setWidgetOption(widget, "canvasOnly", true);
    widget.type = "hidden";
    widget.computeSize = () => [0, -4];
}

function restoreOriginalPromptWidget(widget) {
    if (!widget?.__h3PromptHidden) return;
    widget.type = widget.__h3OriginalType || "customtext";
    widget.computeSize = widget.__h3OriginalComputeSize || (() => [220, 120]);
    widget.hidden = widget.__h3OriginalHidden ?? false;
    setWidgetOption(widget, "hidden", widget.__h3OriginalOptionsHidden);
    setWidgetOption(widget, "canvasOnly", widget.__h3OriginalOptionsCanvasOnly);
    widget.__h3PromptHidden = false;
}

function hideDomEditorWidget(widget) {
    if (!widget) return;
    if (!widget.__h3EditorHidden) {
        widget.__h3EditorHidden = true;
        widget.__h3EditorType = widget.type;
        widget.__h3EditorComputeSize = widget.computeSize;
    }
    widget.hidden = true;
    setWidgetOption(widget, "hidden", true);
    widget.type = "hidden";
    widget.computeSize = () => [0, -4];
}

function showDomEditorWidget(widget) {
    if (!widget?.__h3EditorHidden) return;
    widget.type = widget.__h3EditorType || "h3_prompt_mentions";
    widget.computeSize = widget.__h3EditorComputeSize || (() => [220, 96]);
    widget.hidden = false;
    setWidgetOption(widget, "hidden", false);
    widget.__h3EditorHidden = false;
}

function refreshVueNodeWidgets(node) {
    if (!Array.isArray(node?.widgets)) return;
    const widgets = [...node.widgets];
    try {
        if (isVueNodesMode()) node.widgets = [];
        node.widgets = widgets;
    } catch { /* Some frontends expose widgets as a read-only field. */ }
}

function getConditionalWidgetHeight(node, widget) {
    if (!widget) return Number(globalThis.LiteGraph?.NODE_WIDGET_HEIGHT) || 20;
    const storedHeight = Number(widget.__h3ConditionalRowHeight);
    if (Number.isFinite(storedHeight) && storedHeight > 0) return storedHeight;
    const measure = widget.__h3ConditionalOrigComputeSize || widget.computeSize;
    try {
        const measured = measure?.call(widget, Math.max(80, Number(node?.size?.[0]) || 220));
        const height = Number(measured?.[1]);
        if (Number.isFinite(height) && height > 0) {
            widget.__h3ConditionalRowHeight = height;
            return height;
        }
    } catch { /* Use the standard row height when a widget cannot be measured. */ }
    const height = Number(widget.computedHeight) > 0
        ? Number(widget.computedHeight)
        : Number(globalThis.LiteGraph?.NODE_WIDGET_HEIGHT) || 20;
    widget.__h3ConditionalRowHeight = height;
    return height;
}

function adjustNodeHeight(node, delta) {
    if (!node?.size || !Number.isFinite(delta) || !delta) return;
    const width = Number(node.size[0]) || 0;
    const beforeHeight = Number(node.size[1]) || 0;
    const nextHeight = Math.max(0, beforeHeight + delta);
    const nextSize = [width, nextHeight];
    node.setSize?.(nextSize);
    if (node.size) {
        node.size[0] = width;
        node.size[1] = nextHeight;
    } else {
        node.size = nextSize;
    }
    node._widgetSlotsDirty = true;
    node.setDirtyCanvas?.(true, true);
    node.graph?.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
}

function setNodeSizeExact(node, size) {
    if (!node || !Array.isArray(size) || size.length < 2) return false;
    const width = Number(size[0]);
    const height = Number(size[1]);
    if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return false;
    const nextSize = [width, height];
    node.setSize?.(nextSize);
    if (Array.isArray(node.size)) {
        node.size[0] = width;
        node.size[1] = height;
    } else {
        node.size = nextSize;
    }
    node._widgetSlotsDirty = true;
    node.setDirtyCanvas?.(true, true);
    node.graph?.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    return true;
}

function restorePromptEditorStableSize(node) {
    const stableSize = Array.isArray(node?.__h3EditorStableSize) ? [...node.__h3EditorStableSize] : null;
    if (!stableSize || stableSize.length < 2) return false;
    const restored = setNodeSizeExact(node, stableSize);
    if (restored) node.__h3EditorStableSize = null;
    return restored;
}

function hideConditionalWidget(widget) {
    if (!widget) return false;
    let compactSize = false;
    try {
        const measured = widget.computeSize?.();
        compactSize = Number(measured?.[0]) === 0 && Number(measured?.[1]) === -4;
    } catch { /* The widget may not expose a measurable size yet. */ }
    const wasVisible = widget.hidden !== true
        || widget.options?.hidden !== true
        || widget.type !== "hidden"
        || !compactSize;
    const originalType = widget.type;
    const originalComputeSize = widget.computeSize;
    const originalHidden = widget.hidden;
    if (widget.type !== "hidden") widget.__h3ConditionalOrigType = widget.type;
    if (!Object.prototype.hasOwnProperty.call(widget, "__h3ConditionalOrigComputeSize")) {
        widget.__h3ConditionalOrigComputeSize = originalComputeSize;
        widget.__h3ConditionalHadComputeSize = Object.prototype.hasOwnProperty.call(widget, "computeSize");
        widget.__h3ConditionalOrigHidden = originalHidden;
        widget.__h3ConditionalOrigOptionsHidden = widget.options?.hidden;
        widget.__h3ConditionalOrigOptionsCanvasOnly = widget.options?.canvasOnly;
        widget.__h3ConditionalOrigComputedHeight = widget.computedHeight;
        widget.__h3ConditionalHadComputedHeight = Object.prototype.hasOwnProperty.call(widget, "computedHeight");
    }
    widget.hidden = true;
    if (widget.inputEl) widget.inputEl.style.display = "none";
    if (widget.element) widget.element.style.display = "none";
    widget.type = "hidden";
    widget.computeSize = () => [0, -4];
    widget.computedHeight = 0;
    setWidgetOption(widget, "hidden", true);
    setWidgetOption(widget, "canvasOnly", true);
    if (widget._state) {
        widget._state.hidden = true;
        widget._state.type = "hidden";
        widget._state.computedHeight = 0;
    }
    return wasVisible;
}

function showConditionalWidget(widget, node = null) {
    if (!widget) return false;
    const wasHidden = widget.type === "hidden"
        || widget.hidden === true
        || widget.options?.hidden === true
        || widget._state?.type === "hidden"
        || widget._state?.hidden === true
        || widget._state?.options?.hidden === true;
    if (!wasHidden) return false;
    widget.hidden = widget.__h3ConditionalOrigHidden ?? false;
    if (widget.inputEl) widget.inputEl.style.display = "";
    if (widget.element) widget.element.style.display = "";
    if (widget.type === "hidden") widget.type = widget.__h3ConditionalOrigType || "combo";
    if (widget.__h3ConditionalHadComputeSize) widget.computeSize = widget.__h3ConditionalOrigComputeSize;
    else delete widget.computeSize;
    if (widget.__h3ConditionalHadComputedHeight) widget.computedHeight = widget.__h3ConditionalOrigComputedHeight;
    else delete widget.computedHeight;
    setWidgetOption(widget, "hidden", false);
    setWidgetOption(widget, "canvasOnly", false);
    if (widget._state) {
        widget._state.hidden = widget.hidden;
        widget._state.type = widget.type;
        if (widget.__h3ConditionalHadComputedHeight) widget._state.computedHeight = widget.computedHeight;
        else delete widget._state.computedHeight;
        widget._state.options ||= {};
        if (widget.options?.hidden === undefined) delete widget._state.options.hidden;
        else widget._state.options.hidden = widget.options.hidden;
        if (widget.options?.canvasOnly === undefined) delete widget._state.options.canvasOnly;
        else widget._state.options.canvasOnly = widget.options.canvasOnly;
    }
    localizeComboWidget(widget, node);
    return wasHidden;
}

function setConditionalWidgetVisible(node, widget, visible, { adjustHeight = true } = {}) {
    if (!widget) return false;
    node.__h3ConditionalVisibility ||= new Map();
    const key = String(widget.name || widget.label || node.widgets?.indexOf(widget) || "widget");
    const previousTarget = node.__h3ConditionalVisibility.get(key);
    const rowHeight = getConditionalWidgetHeight(node, widget);
    // A hidden ComfyUI widget still contributes -4 px through computeSize().
    // Showing a row therefore needs rowHeight + 4 px, not just rowHeight;
    // otherwise the flexible prompt editor is compressed a little for every
    // expanded setting row instead of the node extending downward.
    const layoutDelta = rowHeight + 4;
    const changed = visible ? showConditionalWidget(widget, node) : hideConditionalWidget(widget);
    node.__h3ConditionalVisibility.set(key, Boolean(visible));
    if (!changed) return false;
    // Change height only when the desired state actually changed. ComfyUI may
    // reconstruct widget visibility while switching workflow tabs; that is a
    // visual reset, not a user-requested row insertion/removal, and must not
    // grow the node again.
    if (adjustHeight && (previousTarget === undefined || previousTarget !== Boolean(visible))) {
        adjustNodeHeight(node, visible ? layoutDelta : -layoutDelta);
    }
    refreshVueNodeWidgets(node);
    node._widgetSlotsDirty = true;
    return true;
}

function syncSegmentSummary(node) {
    if (!isSegmentMode(node)) return false;
    const secondsSpec = String(getWidgetValue(node, "segment_seconds", "") || "");
    const parts = secondsSpec.replace(/\uff0c/g, ",").split(",").map((item) => item.trim()).filter(Boolean);
    const total = parts.reduce((sum, item) => {
        const value = Number.parseFloat(item);
        return Number.isFinite(value) ? sum + value : sum;
    }, 0);
    const seconds = getWidget(node, "seconds");
    if (seconds && total > 0) {
        seconds.value = Math.round(total * 10) / 10;
        if (seconds._state) seconds._state.value = seconds.value;
    }
    const segmentSeconds = getWidget(node, "segment_seconds");
    if (segmentSeconds) segmentSeconds.label = TEXT.segmentSecondsHint && parts.length ? TEXT.segmentSeconds : TEXT.segmentSeconds;
    return true;
}

function promptTextForOptimizer(node) {
    const doc = node?.properties?.[PROMPT_DOC_PROP];
    if (Array.isArray(doc?.parts)) {
        return promptDocTextFromParts(doc.parts);
    }
    return String(getWidget(node, "prompt")?.value || "");
}

function contextFrameGrid(node) {
    const mode = canonicalOption("continuity_mode", getWidgetValue(node, "continuity_mode", CONTINUITY_LATENT));
    return AV_CONTINUITY_MODES.has(mode) ? AV_CONTEXT_FRAME_GRID : GUIDE_CONTEXT_FRAME_GRID;
}

function syncContextLengthWidget(node) {
    const widget = getWidget(node, "context_length");
    if (!widget || (!isSegmentMode(node) && !isSelectedVideoContextSegmented(node))) return false;
    const grid = contextFrameGrid(node);
    widget.options ||= {};
    widget.options.min = grid[0];
    widget.options.max = grid[grid.length - 1];
    widget.options.step = grid.length > 1 ? grid[1] - grid[0] : 1;
    const current = Number(widget.value);
    const value = Number.isFinite(current)
        ? grid.reduce((best, candidate) => Math.abs(candidate - current) < Math.abs(best - current) ? candidate : best, grid[0])
        : grid[0];
    const changed = current !== value;
    if (changed) {
        widget.value = value;
        if (widget._state) widget._state.value = value;
    }
    return changed;
}

function syncModeWidgets(node, { adjustHeight = true } = {}) {
    const advanced = isAdvancedEnabled(node);
    const optimizerEnabled = asBoolean(getWidgetValue(node, "prompt_optimizer", false));
    const contextOptimizerMode = canonicalOption(
        "context_prompt_optimizer_mode",
        getWidgetValue(node, "context_prompt_optimizer_mode", "whole_sequence"),
    );
    const contextNode = isContextSegmentsNode(node);
    const selectedVideoContext = isSelectedVideoContextNode(node);
    const selectedSegmentMode = canonicalOption(
        "selected_video_segment_mode",
        getWidgetValue(node, "segment_mode", SELECTED_VIDEO_SEGMENT_WHOLE),
    );
    const selectedVideoSegmented = selectedVideoContext && selectedSegmentMode !== SELECTED_VIDEO_SEGMENT_WHOLE;
    const segmentContextNode = contextNode || selectedVideoSegmented;
    const changed = [
        syncContextLengthWidget(node),
        setConditionalWidgetVisible(node, getWidget(node, "mode"), !contextNode, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "audio_mode"), contextNode, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "fps"), advanced && !segmentContextNode, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "keyframe_role"), advanced && !isReferenceMode(node) && !segmentContextNode, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "ref_image_size"), advanced, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "reference_mention_mode"), advanced && isReferenceMode(node), { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "aspect_ratio"), !isCustomResolution(node), { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "width"), isCustomResolution(node), { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "height"), isCustomResolution(node), { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "prompt_optimizer"), advanced, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "prompt_optimizer_api_format"), advanced && optimizerEnabled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "prompt_optimizer_api_url"), advanced && optimizerEnabled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "prompt_optimizer_api_key"), advanced && optimizerEnabled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "prompt_optimizer_model"), advanced && optimizerEnabled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "prompt_optimizer_scene_guide"), advanced && optimizerEnabled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "prompt_optimizer_read_media"), advanced && optimizerEnabled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "prompt_optimizer_optimize_on_run"), advanced && optimizerEnabled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "context_prompt_optimizer_mode"), segmentContextNode && advanced && optimizerEnabled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "context_prompt_optimizer_concurrency"), segmentContextNode && advanced && optimizerEnabled && contextOptimizerMode === "per_segment", { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "segment_seconds"), isSegmentMode(node), { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "context_length"), segmentContextNode, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "continuity_mode"), segmentContextNode, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "segment_mode"), selectedVideoContext, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "segment_cuts"), selectedVideoContext && selectedSegmentMode !== SELECTED_VIDEO_SEGMENT_WHOLE, { adjustHeight }),
    ].some(Boolean);
    if (!isSegmentMode(node)) {
        const segmentSeconds = getWidget(node, "segment_seconds");
        if (segmentSeconds) segmentSeconds.label = TEXT.segmentSeconds;
    } else {
        syncSegmentSummary(node);
    }
    const cuts = getWidget(node, "segment_cuts");
    if (cuts && selectedVideoContext) {
        cuts.label = selectedSegmentMode === SELECTED_VIDEO_SEGMENT_FRAME_CUTS
            ? TEXT.selectedVideoFrameCuts
            : TEXT.selectedVideoTimeCuts;
    }
    if (changed) {
        refreshVueNodeWidgets(node);
        node._widgetSlotsDirty = true;
        node.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
    }
    return changed;
}

function syncSegmentRefineWidgets(node, { adjustHeight = true } = {}) {
    if (!isSegmentRefineNode(node)) return false;
    // Combo widgets expose their localized display label as .value. Convert
    // it back to the stable enum before deciding which parameter rows to show.
    const refineMode = canonicalOption("refine_mode", getWidgetValue(node, "refine_mode", "pixel_resize"));
    const refineExecution = canonicalOption("refine_execution", getWidgetValue(node, "refine_execution", "whole_segment"));
    const tiled = refineExecution === "tiled_low_vram";
    const changed = [
        setConditionalWidgetVisible(node, getWidget(node, "target_width"), refineMode === "pixel_resize", { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "target_height"), refineMode === "pixel_resize", { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "latent_upscale_model"), refineMode === "latent_upscale", { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "latent_upscale_scale"), refineMode === "latent_upscale", { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "latent_upscale_device"), refineMode === "latent_upscale", { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "latent_upscale_precision"), refineMode === "latent_upscale", { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "tile_width"), tiled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "tile_height"), tiled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "tile_overlap"), tiled, { adjustHeight }),
        setConditionalWidgetVisible(node, getWidget(node, "tile_fade"), tiled, { adjustHeight }),
    ].some(Boolean);
    if (changed) {
        refreshVueNodeWidgets(node);
        node._widgetSlotsDirty = true;
        node.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
    }
    return changed;
}

function repairNodeLayout(node) {
    if (!node) return;
    const run = () => {
        refreshVueNodeWidgets(node);
        node._widgetSlotsDirty = true;
        node.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
    };
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(run);
    else setTimeout(run, 0);
}

function syncPromptViewButton(node) {
    const button = node?.__h3PromptViewButton;
    if (!button) return;
    const raw = isRawPromptMode(node);
    const label = raw ? TEXT.showStructuredPrompt : TEXT.showRawPrompt;
    button.textContent = raw ? "@" : "</>";
    button.title = label;
    button.setAttribute("aria-label", label);
    button.setAttribute("aria-pressed", raw ? "true" : "false");
    // The icon already communicates the current view. Keep the button's
    // visual treatment identical in both modes instead of adding a colored
    // active border in raw-prompt mode.
    button.classList.remove("is-active");
}

function togglePromptView(node) {
    const editor = node?.__h3Editor;
    if (!editor) return;
    const raw = isRawPromptMode(node);
    if (!raw) syncPromptFromEditor(node, false);
    else if (node.__h3RawPromptNeedsSync) syncPromptFromEditor(node, false);
    setPromptViewMode(node, raw ? PROMPT_VIEW_STRUCTURED : PROMPT_VIEW_RAW);
    node.__h3RawPromptNeedsSync = false;
    renderEditorFromNode(node, true);
    syncEditorMode(node);
    editor.focus({ preventScroll: true });
    setEditorCaretAtEnd(editor);
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
}

function promptOptimizerState(node) {
    node.properties ||= {};
    const saved = node.properties[PROMPT_OPTIMIZER_PROP];
    const state = saved && typeof saved === "object" ? saved : {};
    const widgetValue = (name, fallback) => getWidgetValue(node, name, fallback);
    const requestedFormat = canonicalOption("prompt_optimizer_api_format", widgetValue("prompt_optimizer_api_format", state.api_format || "openai"));
    const normalized = {
        enabled: asBoolean(widgetValue("prompt_optimizer", state.enabled), false),
        api_format: ["openai", "responses", "gemini"].includes(requestedFormat) ? requestedFormat : "openai",
        api_url: String(widgetValue("prompt_optimizer_api_url", state.api_url || "") || ""),
        api_key: String(widgetValue("prompt_optimizer_api_key", "") || ""),
        model: String(widgetValue("prompt_optimizer_model", state.model || "") || ""),
        scene_guide: canonicalPromptGuide(widgetValue("prompt_optimizer_scene_guide", state.scene_guide || "none")),
        read_media: asBoolean(widgetValue("prompt_optimizer_read_media", state.read_media), false),
        optimize_on_run: asBoolean(widgetValue("prompt_optimizer_optimize_on_run", state.optimize_on_run), false),
    };
    node.properties[PROMPT_OPTIMIZER_PROP] = {
        enabled: normalized.enabled,
        api_format: normalized.api_format,
        api_url: normalized.api_url,
        model: normalized.model,
        scene_guide: normalized.scene_guide,
        read_media: normalized.read_media,
        optimize_on_run: normalized.optimize_on_run,
    };
    return normalized;
}

function promptOptimizerApiKeyRequired(apiFormat) {
    return String(apiFormat || "openai").trim().toLowerCase() === "gemini";
}

function promptOptimizerConfigured(state) {
    return Boolean(
        state?.api_url?.trim()
        && state?.model?.trim()
        && (state?.api_key?.trim() || !promptOptimizerApiKeyRequired(state?.api_format))
    );
}

function splitContextPromptSegments(value) {
    const normalized = String(value || "")
        .replace(/\r\n?/g, "\n")
        .replace(/[\u2028\u2029]/g, "\n")
        .replace(/[\ufeff\u200b\u200c\u200d\u2060]/g, "");
    return normalized
        .split(/^\s*\\?\s*-{3,}\s*\\?\s*$/m)
        .map((part) => part.trim())
        .filter(Boolean);
}

function contextSegmentDurations(node, count) {
    const raw = String(getWidgetValue(node, "segment_seconds", "") || "")
        .replace(/\uff0c/g, ",");
    const values = raw.split(",")
        .map((item) => Number.parseFloat(item.trim()))
        .filter((item) => Number.isFinite(item) && item > 0);
    if (values.length === count) return values;
    const fallback = Number(getWidgetValue(node, "seconds", 5)) || 5;
    return Array.from({ length: count }, () => fallback);
}

async function requestPromptOptimization(payload, signal) {
    const response = await api.fetchApi("/minimax_h3_easy/prompt_optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal,
        body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data?.ok) throw new Error(data?.error || `HTTP ${response.status}`);
    return data;
}

async function optimizeContextSegmentsIndividually({ node, sourcePrompt, commonPayload, concurrency, signal, requestId }) {
    const segments = splitContextPromptSegments(sourcePrompt);
    if (segments.length < 2) return null;
    const durations = contextSegmentDurations(node, segments.length);
    const results = Array.from({ length: segments.length }, () => "");
    let nextIndex = 0;
    let completed = 0;
    const workerCount = Math.max(1, Math.min(20, Number(concurrency) || 3, segments.length));
    setPromptOptimizerStatus(node, "loading", { completed: 0, total: segments.length });

    const worker = async () => {
        while (true) {
            if (signal.aborted || node.__h3OptimizerRequestId !== requestId) return;
            const index = nextIndex++;
            if (index >= segments.length) return;
            const data = await requestPromptOptimization({
                ...commonPayload,
                prompt: segments[index],
                seconds: durations[index],
                segment_index: index,
                segment_count: segments.length,
                previous_prompts: segments.slice(0, index),
                optimizer_mode: "per_segment",
            }, signal);
            results[index] = String(data.prompt || "").trim();
            completed += 1;
            setPromptOptimizerStatus(node, "loading", { completed, total: segments.length });
        }
    };
    await Promise.all(Array.from({ length: workerCount }, () => worker()));
    if (results.some((part) => !part)) throw new Error("One or more context segments returned an empty result");
    return results.join("\n\n---\n\n");
}

function notifyPromptOptimizer(message, severity = "error") {
    const detail = String(message || "");
    const toast = app.extensionManager?.toast;
    if (toast?.add) {
        toast.add({ severity, summary: severity === "error" ? TEXT.optimizerFailed : TEXT.optimizerSettings, detail, life: 6000 });
        return;
    }
    globalThis.alert?.(detail);
}

function syncPromptExternalConnectionState(node) {
    const connected = promptInputIsConnected(node);
    node.__h3PromptExternalConnected = connected;
    const editor = node?.__h3Editor;
    const wrap = node?.__h3EditorWrap;
    if (editor) {
        editor.contentEditable = connected ? "false" : "true";
        editor.setAttribute("aria-readonly", connected ? "true" : "false");
        editor.title = connected ? TEXT.promptExternalConnected : "";
        editor.classList.toggle("is-external", connected);
        editor.tabIndex = connected ? -1 : 0;
        if (connected) {
            closeMentionMenu(node);
            if (document.activeElement === editor) editor.blur();
        }
    }
    wrap?.classList?.toggle("is-external", connected);
    syncPromptOptimizerButton(node);
}

function clearPromptOptimizerStatusTimers(node) {
    if (!node) return;
    if (node.__h3OptimizerStatusTimer) clearInterval(node.__h3OptimizerStatusTimer);
    if (node.__h3OptimizerStatusHideTimer) clearTimeout(node.__h3OptimizerStatusHideTimer);
    node.__h3OptimizerStatusTimer = null;
    node.__h3OptimizerStatusHideTimer = null;
}

function cancelPromptOptimization(node) {
    if (!node?.__h3OptimizerPending) return;
    node.__h3OptimizerRequestId = null;
    node.__h3OptimizerAbortController?.abort?.();
    node.__h3OptimizerAbortController = null;
    node.__h3OptimizerPending = false;
    setPromptOptimizerStatus(node, "idle");
    syncPromptOptimizerButton(node);
}

function setPromptOptimizerStatus(node, state = "idle", progress = null) {
    if (!node) return;
    clearPromptOptimizerStatusTimers(node);
    node.__h3OptimizerStatus = state;
    if (state !== "loading" || progress == null) node.__h3OptimizerProgress = null;
    const status = node.__h3PromptOptimizerStatus;
    const label = node.__h3PromptOptimizerStatusText;
    if (!status || !label) return;
    const loading = state === "loading";
    status.hidden = !loading;
    status.className = `h3-prompt-editor-status${loading ? " is-loading" : ""}`;
    if (!loading) {
        label.textContent = "";
        return;
    }
    const startedAt = Number(node.__h3OptimizerStartedAt) || (globalThis.performance?.now?.() || Date.now());
    node.__h3OptimizerStartedAt = startedAt;
    if (progress && Number.isFinite(Number(progress.total))) {
        node.__h3OptimizerProgress = {
            completed: Math.max(0, Math.min(Number(progress.total), Number(progress.completed) || 0)),
            total: Math.max(1, Number(progress.total)),
        };
    }
    const update = () => {
        const elapsed = Math.max(0, Math.floor(((globalThis.performance?.now?.() || Date.now()) - startedAt) / 1000));
        const current = node.__h3OptimizerProgress;
        const progressText = current ? ` ${current.completed}/${current.total}` : "";
        label.textContent = elapsed > 1
            ? `${TEXT.optimizerRunning}${progressText} \u00b7 ${elapsed}s`
            : `${TEXT.optimizerRunning}${progressText}...`;
    };
    update();
    node.__h3OptimizerStatusTimer = setInterval(update, 1000);
}

function syncPromptOptimizerButton(node) {
    const button = node?.__h3PromptOptimizeButton;
    if (!button) return;
    const state = promptOptimizerState(node);
    const configured = promptOptimizerConfigured(state);
    const external = promptInputIsConnected(node);
    const pending = Boolean(node.__h3OptimizerPending);
    const locked = external || pending;
    button.title = external ? TEXT.promptExternalConnected : TEXT.optimizePrompt;
    button.setAttribute("aria-label", button.title);
    button.classList.toggle("is-configured", configured);
    button.classList.toggle("is-loading", pending);
    button.classList.toggle("is-external", external);
    button.setAttribute("aria-disabled", external ? "true" : "false");
    button.disabled = pending || external;
    const editor = node?.__h3Editor;
    const wrap = node?.__h3EditorWrap;
    if (editor) {
        editor.contentEditable = locked ? "false" : "true";
        editor.setAttribute("aria-readonly", locked ? "true" : "false");
        editor.setAttribute("aria-busy", pending ? "true" : "false");
        editor.tabIndex = locked ? -1 : 0;
        editor.title = external ? TEXT.promptExternalConnected : pending ? TEXT.optimizerRunning : "";
        editor.classList.toggle("is-loading", pending);
    }
    wrap?.classList?.toggle("is-loading", pending);
    if (pending) closeMentionMenu(node);
}

function sourceAssetDescriptor(node, mediaType) {
    if (!node) return null;
    const preferred = {
        image: ["image", "filename", "file"],
        video: ["video", "file", "filename", "video_file", "videofile"],
        audio: ["audio", "file", "filename", "audio_file", "audiofile"],
    }[mediaType] || ["file", "filename"];
    const preferredSet = new Set(preferred);
    const widgets = Array.isArray(node.widgets) ? node.widgets : [];
    const ordered = [...widgets.filter((widget) => preferredSet.has(String(widget?.name || "").toLowerCase())), ...widgets];
    for (const widget of ordered) {
        const value = widget?.value;
        const filename = typeof value === "object" ? String(value?.filename || value?.name || "") : String(value || "");
        if (!filename || /^data:|^blob:|^https?:/i.test(filename)) continue;
        if (!preferredSet.has(String(widget?.name || "").toLowerCase()) && !/\.(png|jpe?g|webp|gif|bmp|mp4|webm|mov|mkv|avi|m4v|mp3|wav|flac|ogg|m4a|aac)$/i.test(filename)) continue;
        return {
            filename,
            subfolder: typeof value === "object" ? String(value?.subfolder || "") : "",
            storage: typeof value === "object" ? String(value?.type || "input") : "input",
        };
    }
    return null;
}

function promptOptimizerResources(node) {
    const native = getNativeMediaBridgeLink(node);
    const loader = native ? app.graph?.getNodeById?.(Number(native.source_id)) : null;
    if (loader && isMediaLoader(loader)) {
        return mediaLoaderMentionOptions(loader, node).map((option) => ({
            type: option.type,
            tag: option.tag,
            name: option.filename,
            asset: { filename: option.filename, subfolder: "", storage: "input" },
        }));
    }
    const counts = { image: 0, video: 0, audio: 0 };
    return normalizeLinks(node).map((link) => {
        const type = String(link.media_type || "image").toLowerCase();
        counts[type] = (counts[type] || 0) + 1;
        const ordinal = counts[type];
        const source = app.graph?.getNodeById?.(Number(link.source_id));
        return {
            type,
            tag: promptMentionTag(type, ordinal),
            name: sourceFilename(source, type) || sourceLabel(source),
            asset: sourceAssetDescriptor(source, type),
        };
    });
}

function clearAutomaticPromptMarker(node) {
    if (!node?.properties || !Object.prototype.hasOwnProperty.call(node.properties, PROMPT_AUTO_MARKER_PROP)) return false;
    delete node.properties[PROMPT_AUTO_MARKER_PROP];
    return true;
}

function setPromptFromOptimizedText(node, value, { preserveAutoMarker = false, notifyGraphChange = true } = {}) {
    const text = String(value || "").replace(/^```(?:text)?\s*/i, "").replace(/\s*```$/, "").trim();
    const doc = { version: 1, text, parts: promptPartsFromText(node, text) };
    const widget = getWidget(node, "prompt");
    node.properties ||= {};
    if (!preserveAutoMarker) clearAutomaticPromptMarker(node);
    node.properties[PROMPT_DOC_PROP] = doc;
    if (widget) {
        widget.value = doc.text;
        if (widget._state) widget._state.value = doc.text;
    }
    node.__h3RawPromptNeedsSync = false;
    renderEditorFromNode(node, true);
    syncPromptFromEditor(node, false);
    pushPromptHistory(node);
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    if (notifyGraphChange) app.graph?.change?.();
}

function promptOptimizerUiValue(message, name) {
    const output = message?.output && typeof message.output === "object" ? message.output : message;
    const value = output?.[name];
    return Array.isArray(value) ? value[0] : value;
}

function applyRuntimePromptOptimization(node, message) {
    if (!node || promptInputIsConnected(node)) return;
    const prompt = String(promptOptimizerUiValue(message, "auto_optimized_prompt") || "").trim();
    const markerValue = promptOptimizerUiValue(message, "auto_optimization_marker");
    if (!prompt || markerValue == null) return;

    let marker;
    try {
        marker = typeof markerValue === "string" ? JSON.parse(markerValue) : markerValue;
    } catch {
        return;
    }
    if (!marker || typeof marker !== "object") return;

    const currentPrompt = promptTextForOptimizer(node);
    const currentMarker = node.properties?.[PROMPT_AUTO_MARKER_PROP];
    if (currentPrompt === prompt && JSON.stringify(currentMarker || {}) === JSON.stringify(marker)) return;

    if (node.__h3Editor) syncPromptFromEditor(node, false);
    pushPromptHistory(node);
    setPromptFromOptimizedText(node, prompt, { preserveAutoMarker: true, notifyGraphChange: false });
    node.properties ||= {};
    node.properties[PROMPT_AUTO_MARKER_PROP] = marker;
    node.__h3OptimizerSourcePrompt = null;
    node.__h3OptimizerLastResult = null;
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
}

async function optimizePromptFromEditor(node) {
    if (!node || node.__h3OptimizerPending || promptInputIsConnected(node)) return;
    syncPromptFromEditor(node, false);
    pushPromptHistory(node);
    const state = promptOptimizerState(node);
    if (!promptOptimizerConfigured(state)) {
        notifyPromptOptimizer(TEXT.optimizerMissing);
        return;
    }
    const currentPrompt = promptTextForOptimizer(node);
    const sourcePrompt = node.__h3OptimizerLastResult === currentPrompt && node.__h3OptimizerSourcePrompt != null
        ? node.__h3OptimizerSourcePrompt
        : currentPrompt;
    if (!sourcePrompt.trim()) return;
    const resources = promptOptimizerResources(node);
    const mediaCounts = { image: 0, video: 0, audio: 0 };
    resources.forEach((item) => { mediaCounts[item.type] = (mediaCounts[item.type] || 0) + 1; });
    const requestMode = canonicalOption("mode", getWidgetValue(node, "mode", MODE_IMAGE));
    const segmentMode = requestMode === MODE_SEGMENTS;
    const requestId = Symbol("h3-prompt-optimizer");
    const abortController = new AbortController();
    node.__h3OptimizerRequestId = requestId;
    node.__h3OptimizerAbortController = abortController;
    node.__h3OptimizerPending = true;
    node.__h3OptimizerStartedAt = globalThis.performance?.now?.() || Date.now();
    setPromptOptimizerStatus(node, "loading");
    syncPromptOptimizerButton(node);
    try {
        const optimizerMode = segmentMode
            ? canonicalOption("context_prompt_optimizer_mode", getWidgetValue(node, "context_prompt_optimizer_mode", "whole_sequence"))
            : "whole_sequence";
        const commonPayload = {
            prompt: sourcePrompt,
            api_format: state.api_format,
            api_url: state.api_url,
            api_key: state.api_key,
            model: state.model,
            scene_guide: state.scene_guide,
            read_media: state.read_media,
            mode: requestMode,
            audio_mode: segmentMode
                ? canonicalOption("audio_mode", getWidgetValue(node, "audio_mode", CONTEXT_AUDIO_GENERATED))
                : "",
            seconds: segmentMode
                ? Number(getWidgetValue(node, "seconds", 5)) || 5
                : Math.min(MAX_SECONDS, Math.max(MIN_SECONDS, Number(getWidgetValue(node, "seconds", 5)) || 5)),
            segment_seconds: segmentMode ? String(getWidgetValue(node, "segment_seconds", "") || "") : "",
            media_counts: mediaCounts,
            resources,
            optimizer_mode: optimizerMode,
        };
        let optimizedPrompt = "";
        const sourceSegments = segmentMode ? splitContextPromptSegments(sourcePrompt) : [];
        if (segmentMode && optimizerMode === "per_segment" && sourceSegments.length >= 2) {
            optimizedPrompt = await optimizeContextSegmentsIndividually({
                node,
                sourcePrompt,
                commonPayload,
                concurrency: getWidgetValue(node, "context_prompt_optimizer_concurrency", 3),
                signal: abortController.signal,
                requestId,
            });
        } else {
            const data = await requestPromptOptimization(commonPayload, abortController.signal);
            optimizedPrompt = String(data.prompt || "");
        }
        if (node.__h3OptimizerRequestId !== requestId) return;
        node.__h3OptimizerSourcePrompt = sourcePrompt;
        node.__h3OptimizerLastResult = optimizedPrompt;
        setPromptFromOptimizedText(node, node.__h3OptimizerLastResult);
        setPromptOptimizerStatus(node, "success");
    } catch (error) {
        if (abortController.signal.aborted || node.__h3OptimizerRequestId !== requestId || error?.name === "AbortError") return;
        setPromptOptimizerStatus(node, "error");
        notifyPromptOptimizer(error?.message || error);
    } finally {
        if (node.__h3OptimizerRequestId === requestId) {
            node.__h3OptimizerRequestId = null;
            node.__h3OptimizerAbortController = null;
            node.__h3OptimizerPending = false;
            syncPromptOptimizerButton(node);
        }
    }
}

function syncEditorMode(node) {
    syncModeWidgets(node, { adjustHeight: false });
    const widget = getWidget(node, "prompt");
    const editor = node.__h3Editor;
    const wrap = node.__h3EditorWrap;
    const domWidget = node.__h3DomWidget;
    if (!widget || !editor || !wrap || !domWidget) return;
    syncPromptExternalConnectionState(node);
    const mediaMentions = canUseMediaMentions(node);
    const raw = isRawPromptMode(node);
    hideOriginalPromptWidget(widget);
    setWidgetOption(domWidget, "canvasOnly", false);
    showDomEditorWidget(domWidget);
    editor.style.display = "block";
    wrap.style.display = "block";
    editor.dataset.placeholder = raw ? TEXT.rawPromptPlaceholder : mediaMentions ? TEXT.referencePromptPlaceholder : TEXT.promptPlaceholder;
    editor.classList.toggle("is-raw", raw);
    wrap.classList.toggle("is-raw", raw);
    syncPromptViewButton(node);
    applyNativeEditorTheme(wrap);
    if (!mediaMentions || raw) closeMentionMenu(node);
}

function handleMentionMenuKeydown(node, event) {
    const state = node?.__h3MentionMenu;
    if (!state) return false;
    if (event.key === "Escape") {
        closeMentionMenu(node);
        return true;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        if (state.options.length) {
            const delta = event.key === "ArrowDown" ? 1 : -1;
            state.activeIndex = (state.activeIndex + delta + state.options.length) % state.options.length;
            renderMentionMenu(node);
            state.element.querySelector(".is-active")?.scrollIntoView?.({ block: "nearest" });
        }
        return true;
    }
    if (event.key === "Enter" || event.key === "Tab") {
        const option = state.options[state.activeIndex];
        if (option) chooseMention(node, option);
        return Boolean(option);
    }
    return false;
}

function stripCaretSentinels(value) {
    return String(value ?? "").replaceAll(CARET_SENTINEL, "");
}

function makeCaretSentinel() {
    return document.createTextNode(CARET_SENTINEL);
}

function isCaretSentinelText(node) {
    return node?.nodeType === Node.TEXT_NODE && String(node.textContent || "").includes(CARET_SENTINEL);
}

function isOnlyCaretSentinelText(node) {
    return node?.nodeType === Node.TEXT_NODE && stripCaretSentinels(node.textContent) === "";
}

function isIgnorableTextNode(node) {
    return node?.nodeType === Node.TEXT_NODE && stripCaretSentinels(node.textContent).trim() === "";
}

function isMentionChip(node) {
    return node?.nodeType === Node.ELEMENT_NODE && node.classList?.contains("h3-mention-chip");
}

function deepestLeaf(node, direction) {
    let current = node;
    if (isMentionChip(current) || isDialogueBlock(current)) return current;
    while (current?.childNodes?.length) {
        if (isMentionChip(current) || isDialogueBlock(current) || current.contentEditable === "false") return current;
        current = direction === "backward"
            ? current.childNodes[current.childNodes.length - 1]
            : current.childNodes[0];
    }
    return current;
}

function adjacentLeaf(node, root, direction) {
    if (!node || node === root) return null;
    let current = node;
    while (current && current !== root) {
        const sibling = direction === "backward" ? current.previousSibling : current.nextSibling;
        if (sibling) return deepestLeaf(sibling, direction);
        current = current.parentNode;
    }
    return null;
}

function getAdjacentLeafFromCaret(range, root, direction) {
    const container = range.startContainer;
    const offset = range.startOffset;
    if (container.nodeType === Node.TEXT_NODE) {
        if (direction === "backward" && offset > 0) return null;
        if (direction === "forward" && offset < container.textContent.length) return null;
        return adjacentLeaf(container, root, direction);
    }
    if (container.nodeType === Node.ELEMENT_NODE) {
        if (direction === "backward") {
            if (offset > 0) return deepestLeaf(container.childNodes[offset - 1], "backward");
            return adjacentLeaf(container, root, "backward");
        }
        if (offset < container.childNodes.length) return deepestLeaf(container.childNodes[offset], "forward");
        return adjacentLeaf(container, root, "forward");
    }
    return null;
}

function findChipAcrossWhitespace(start, root, direction) {
    let current = start;
    const skipped = [];
    while (current) {
        if (isMentionChip(current)) return { chip: current, skipped };
        if (isIgnorableTextNode(current)) {
            skipped.push(current);
            current = adjacentLeaf(current, root, direction);
            continue;
        }
        if (current.nodeType === Node.ELEMENT_NODE && current.tagName === "BR") return null;
        return null;
    }
    return null;
}

function findLineBreakAcrossWhitespace(start, root, direction) {
    let current = start;
    const skipped = [];
    while (current) {
        if (current.nodeType === Node.ELEMENT_NODE && current.tagName === "BR") {
            return { breakNode: current, skipped };
        }
        if (isIgnorableTextNode(current)) {
            skipped.push(current);
            current = adjacentLeaf(current, root, direction);
            continue;
        }
        return null;
    }
    return null;
}

function setCaretAtNode(node, offset = 0) {
    const selection = window.getSelection?.();
    if (!selection || !node) return;
    const range = document.createRange();
    range.setStart(node, offset);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
}

function getDeletionScanStart(range, editor, direction) {
    let spacer = null;
    let start = null;
    const container = range.startContainer;
    const offset = range.startOffset;
    if (container.nodeType === Node.TEXT_NODE) {
        const text = container.textContent || "";
        if (direction === "backward") {
            const before = text.slice(0, offset);
            if (before && stripCaretSentinels(before).trim() !== "") return null;
            spacer = before ? container : null;
            start = before ? adjacentLeaf(container, editor, "backward") : getAdjacentLeafFromCaret(range, editor, "backward");
        } else {
            const after = text.slice(offset);
            if (after && stripCaretSentinels(after).trim() !== "") return null;
            spacer = after ? container : null;
            start = after ? adjacentLeaf(container, editor, "forward") : getAdjacentLeafFromCaret(range, editor, "forward");
        }
    } else {
        start = getAdjacentLeafFromCaret(range, editor, direction);
    }
    return { start, spacer, container, offset };
}

function removeSpacerText(spacer, offset, direction) {
    if (spacer?.nodeType !== Node.TEXT_NODE) return;
    if (direction === "backward") spacer.deleteData(0, offset);
    else spacer.deleteData(offset, spacer.textContent.length - offset);
    if (!spacer.textContent) spacer.remove();
}

function deleteLastVisibleChar(textNode) {
    const text = String(textNode?.textContent || "");
    let cursor = 0;
    let last = null;
    for (const char of Array.from(text)) {
        const length = char.length;
        if (char !== CARET_SENTINEL) last = { index: cursor, length };
        cursor += length;
    }
    if (!last) return false;
    textNode.deleteData(last.index, last.length);
    if (!textNode.textContent) textNode.remove();
    return true;
}

function deletePreviousVisibleCharBeforeOffset(textNode, offset) {
    if (textNode?.nodeType !== Node.TEXT_NODE) return false;
    const text = String(textNode.textContent || "");
    const limit = Math.max(0, Math.min(Number(offset) || 0, text.length));
    let cursor = 0;
    let target = null;
    for (const char of Array.from(text)) {
        const length = char.length;
        const next = cursor + length;
        if (next > limit) break;
        if (char !== CARET_SENTINEL) target = { index: cursor, length };
        cursor = next;
    }
    if (!target) return false;
    textNode.deleteData(target.index, target.length);
    setCaretAtNode(textNode, target.index);
    return true;
}

function getOrInsertCaretSentinel(chip, side) {
    if (!chip?.parentNode) return null;
    const sibling = side === "before" ? chip.previousSibling : chip.nextSibling;
    if (isCaretSentinelText(sibling)) return sibling;
    const marker = makeCaretSentinel();
    chip.parentNode.insertBefore(marker, side === "before" ? chip : chip.nextSibling);
    return marker;
}

function removeMentionChip(chip, direction = "backward") {
    if (!chip?.parentNode) return null;
    const marker = makeCaretSentinel();
    chip.parentNode.insertBefore(marker, direction === "backward" ? chip : chip.nextSibling);
    chip.remove();
    return marker;
}

function findPreviousContentFromSentinel(marker, editor) {
    let current = adjacentLeaf(marker, editor, "backward");
    const skipped = [];
    while (current) {
        if (isOnlyCaretSentinelText(current)) {
            skipped.push(current);
            current = adjacentLeaf(current, editor, "backward");
            continue;
        }
        return { node: current, skipped };
    }
    return { node: null, skipped };
}

function removeEmptyCaretMarker(marker) {
    if (isOnlyCaretSentinelText(marker)) marker.remove?.();
}

function placeCaretAfterPreviousContent(marker, editor) {
    const previous = findPreviousContentFromSentinel(marker, editor);
    if (previous.node?.nodeType === Node.TEXT_NODE) {
        setCaretAtNode(previous.node, previous.node.textContent.length);
        removeEmptyCaretMarker(marker);
        return true;
    }
    if (isMentionChip(previous.node)) {
        const afterMarker = getOrInsertCaretSentinel(previous.node, "after");
        setCaretAtNode(afterMarker, afterMarker.textContent.length);
        if (afterMarker !== marker) removeEmptyCaretMarker(marker);
        return true;
    }
    setCaretAtNode(marker, marker.textContent.length);
    return false;
}

function isSentinelBeforeChip(marker, editor) {
    const next = adjacentLeaf(marker, editor, "forward");
    return Boolean(findChipAcrossWhitespace(next, editor, "forward")?.chip);
}

function backspaceBeforeChip(editor, node) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !selection.isCollapsed) return false;
    const range = selection.getRangeAt(0);
    const marker = range.startContainer;
    if (!editor.contains(marker) || !isCaretSentinelText(marker) || !isSentinelBeforeChip(marker, editor)) return false;
    if (deletePreviousVisibleCharBeforeOffset(marker, range.startOffset)) return true;
    const previous = findPreviousContentFromSentinel(marker, editor);
    if (!previous.node) {
        if (isSentinelBeforeChip(marker, editor)) setCaretAtNode(marker, marker.textContent.length);
        else if (marker.textContent === CARET_SENTINEL) marker.remove();
        closeMentionMenu(node);
        return true;
    }
    if (previous.node.nodeType === Node.TEXT_NODE) deleteLastVisibleChar(previous.node);
    else if (isMentionChip(previous.node)) previous.node.remove();
    else if (previous.node.nodeType === Node.ELEMENT_NODE && previous.node.tagName === "BR") previous.node.remove();
    else return false;
    for (const item of previous.skipped) item.remove?.();
    setCaretAtNode(marker, marker.textContent.length);
    closeMentionMenu(node);
    return true;
}

function backspaceAtLooseSentinel(editor, node) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !selection.isCollapsed) return false;
    const range = selection.getRangeAt(0);
    const marker = range.startContainer;
    if (!editor.contains(marker) || !isCaretSentinelText(marker) || isSentinelBeforeChip(marker, editor)) return false;
    if (deletePreviousVisibleCharBeforeOffset(marker, range.startOffset)) return true;
    const previous = findPreviousContentFromSentinel(marker, editor);
    if (!previous.node || (previous.node.nodeType === Node.ELEMENT_NODE && previous.node.tagName === "BR")) return false;
    if (previous.node.nodeType === Node.TEXT_NODE) deleteLastVisibleChar(previous.node);
    else if (isMentionChip(previous.node)) previous.node.remove();
    else return false;
    for (const item of previous.skipped) item.remove?.();
    setCaretAtNode(marker, marker.textContent.length);
    closeMentionMenu(node);
    return true;
}

function deleteLineBreakNearCaret(editor, node, direction) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !selection.isCollapsed) return false;
    const range = selection.getRangeAt(0);
    if (!editor.contains(range.startContainer)) return false;
    const scan = getDeletionScanStart(range, editor, direction);
    if (!scan) return false;
    const found = findLineBreakAcrossWhitespace(scan.start, editor, direction);
    if (!found?.breakNode) return false;
    const marker = makeCaretSentinel();
    found.breakNode.parentNode?.insertBefore(marker, found.breakNode);
    found.breakNode.remove();
    for (const item of found.skipped) item.remove?.();
    removeSpacerText(scan.spacer, scan.offset, direction);
    placeCaretAfterPreviousContent(marker, editor);
    closeMentionMenu(node);
    return true;
}

function blockNativeSentinelDeletion(editor) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !selection.isCollapsed) return false;
    const range = selection.getRangeAt(0);
    const marker = range.startContainer;
    if (!editor.contains(marker) || !isCaretSentinelText(marker)) return false;
    if (stripCaretSentinels(marker.textContent || "") !== "") return false;
    const previous = adjacentLeaf(marker, editor, "backward");
    const next = adjacentLeaf(marker, editor, "forward");
    return Boolean(
        findChipAcrossWhitespace(previous, editor, "backward")?.chip
        || findChipAcrossWhitespace(next, editor, "forward")?.chip
    );
}

function deleteChipNearCaret(editor, node, direction) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !selection.isCollapsed) return false;
    const range = selection.getRangeAt(0);
    const editorNode = range.startContainer;
    if (!editor.contains(editorNode)) return false;
    const directChip = editorNode.nodeType === Node.ELEMENT_NODE
        ? editorNode.closest?.(".h3-mention-chip")
        : editorNode.parentElement?.closest?.(".h3-mention-chip");
    if (directChip && editor.contains(directChip)) {
        const marker = removeMentionChip(directChip, direction);
        setCaretAtNode(marker, marker.textContent.length);
        closeMentionMenu(node);
        return true;
    }
    const scan = getDeletionScanStart(range, editor, direction);
    if (!scan) return false;
    const found = findChipAcrossWhitespace(scan.start, editor, direction);
    if (!found?.chip) return false;
    const marker = removeMentionChip(found.chip, direction);
    for (const item of found.skipped) item.remove?.();
    removeSpacerText(scan.spacer, scan.offset, direction);
    setCaretAtNode(marker, marker.textContent.length);
    closeMentionMenu(node);
    return true;
}

function insertEditorLineBreak(editor) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount) return false;
    const range = selection.getRangeAt(0);
    if (!editor.contains(range.commonAncestorContainer)) return false;
    range.deleteContents();
    const br = document.createElement("br");
    const marker = document.createTextNode("\u200B");
    const fragment = document.createDocumentFragment();
    fragment.append(br, marker);
    range.insertNode(fragment);
    const caret = document.createRange();
    caret.setStart(marker, marker.textContent.length);
    caret.collapse(true);
    selection.removeAllRanges();
    selection.addRange(caret);
    return true;
}

function insertPlainText(editor, text) {
    if (document.execCommand?.("insertText", false, text)) return;
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    range.deleteContents();
    const node = document.createTextNode(text);
    range.insertNode(node);
    range.setStartAfter(node);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
}

function pastedMentionCandidates(node) {
    if (!canUseMediaMentions(node)) return [];
    const labels = {
        image: ["\u56fe\u7247", "Image", "image", "Picture", "picture"],
        video: ["\u89c6\u9891", "Video", "video"],
        audio: ["\u97f3\u9891", "Audio", "audio"],
    };
    const candidates = [];
    const seen = new Set();
    for (const option of mentionOptions(node)) {
        const aliases = new Set();
        if (option.fullLabel) aliases.add(`@${option.fullLabel}`);
        if (option.token) aliases.add(option.token);
        for (const prefix of labels[option.type] || []) {
            aliases.add(`@${prefix}${option.ordinal}`);
            aliases.add(`@${prefix} ${option.ordinal}`);
        }
        for (const raw of aliases) {
            const value = String(raw || "");
            const key = value.toLocaleLowerCase();
            if (!value || seen.has(key)) continue;
            seen.add(key);
            candidates.push({ raw: value, option });
        }
    }
    return candidates.sort((left, right) => right.raw.length - left.raw.length);
}

function pastedOfficialMediaTagMatch(node, value, cursor) {
    if (!canUseMediaMentions(node)) return null;
    const match = String(value || "").slice(cursor).match(/^<\s*(picture|video|audio)\s*(\d+)\s*>/i);
    if (!match) return null;
    const type = match[1].toLowerCase() === "picture" ? "image" : match[1].toLowerCase();
    const ordinal = Number(match[2]);
    if (!Number.isFinite(ordinal) || ordinal <= 0) return null;
    const live = mentionOptions(node);
    const resolved = live.find((option) => option.type === type && Number(option.ordinal) === ordinal);
    const tag = type === "image" ? `<Picture ${ordinal}>` : type === "video" ? `<Video ${ordinal}>` : `<Audio ${ordinal}>`;
    const fallbackLabel = `${LABELS[type] || type}${ordinal}`;
    return {
        raw: match[0],
        option: resolved || {
            type,
            tag,
            token: `@${fallbackLabel}`,
            label: fallbackLabel,
            fullLabel: fallbackLabel,
            ordinal,
            referenceMode: referenceMentionMode(node),
            sourceId: null,
            sourceSlot: 0,
            previewUrl: "",
            unresolved: true,
            pending: true,
        },
    };
}

function appendPastedText(fragment, text) {
    let last = null;
    String(text || "").split("\n").forEach((part, index) => {
        if (index) {
            last = document.createElement("br");
            fragment.append(last);
        }
        if (part) {
            last = document.createTextNode(part);
            fragment.append(last);
        }
    });
    return last;
}

function insertTextWithMentionChips(node, editor, text) {
    const selection = window.getSelection?.();
    if (!selection || !selection.rangeCount || !editor.contains(selection.anchorNode)) return false;
    const range = selection.getRangeAt(0);
    const value = String(text || "");
    if (!value) return false;
    const candidates = pastedMentionCandidates(node);
    range.deleteContents();
    const fragment = document.createDocumentFragment();
    let plainStart = 0;
    let cursor = 0;
    while (cursor < value.length) {
        const match = pastedOfficialMediaTagMatch(node, value, cursor)
            || candidates.find((candidate) => value.slice(cursor, cursor + candidate.raw.length).toLocaleLowerCase() === candidate.raw.toLocaleLowerCase());
        if (!match) {
            cursor += 1;
            continue;
        }
        if (plainStart < cursor) appendPastedText(fragment, value.slice(plainStart, cursor));
        fragment.append(document.createTextNode(CARET_SENTINEL));
        fragment.append(makeMentionChip(match.option));
        fragment.append(document.createTextNode(CARET_SENTINEL));
        cursor += match.raw.length;
        plainStart = cursor;
    }
    if (plainStart < value.length) appendPastedText(fragment, value.slice(plainStart));
    const caretMarker = document.createTextNode(CARET_SENTINEL);
    fragment.append(caretMarker);
    range.insertNode(fragment);
    const caret = document.createRange();
    caret.setStart(caretMarker, caretMarker.textContent.length);
    caret.collapse(true);
    selection.removeAllRanges();
    selection.addRange(caret);
    return true;
}

function ensurePromptEditor(node) {
    if (node.__h3Editor) {
        preparePromptEditorForUndo(node.__h3Editor);
        return;
    }
    if (typeof document === "undefined" || typeof node.addDOMWidget !== "function") return;
    // A workflow tab can deactivate and reactivate the same node instance.
    // `onRemoved` clears the DOM editor, but older builds left its DOM widget
    // in `node.widgets`. Adding another one on every activation makes ComfyUI
    // allocate the editor row repeatedly and the node grows on each tab switch.
    removePromptEditorWidgets(node);
    ensurePromptUndoRedoShield();
    patchLiteGraphPromptProcessKey();
    const widget = getWidget(node, "prompt");
    if (!widget) return;
    hideOriginalPromptWidget(widget);
    const wrap = document.createElement("div");
    wrap.className = "h3-prompt-editor-wrap";
    wrap.style.minHeight = "0px";
    applyNativeEditorTheme(wrap);
    const editor = document.createElement("div");
    editor.className = "comfy-multiline-input h3-prompt-editor";
    editor.contentEditable = "true";
    preparePromptEditorForUndo(editor);
    editor.__h3PromptNode = node;
    editor.tabIndex = 0;
    editor.setAttribute("role", "textbox");
    editor.setAttribute("aria-label", "prompt");
    editor.dataset.placeholder = canUseMediaMentions(node) ? TEXT.referencePromptPlaceholder : TEXT.promptPlaceholder;
    editor.spellcheck = false;
    const editorTools = document.createElement("div");
    editorTools.className = "h3-prompt-editor-tools";
    const optimizerStatus = document.createElement("div");
    optimizerStatus.className = "h3-prompt-editor-status";
    optimizerStatus.hidden = true;
    optimizerStatus.setAttribute("role", "status");
    optimizerStatus.setAttribute("aria-live", "polite");
    const optimizerStatusSpinner = document.createElement("span");
    optimizerStatusSpinner.className = "h3-prompt-editor-status-spinner";
    const optimizerStatusText = document.createElement("span");
    optimizerStatusText.className = "h3-prompt-editor-status-text";
    const optimizerCancelButton = document.createElement("button");
    optimizerCancelButton.type = "button";
    optimizerCancelButton.className = "h3-prompt-editor-status-cancel";
    optimizerCancelButton.textContent = "\u25a0";
    optimizerCancelButton.title = TEXT.optimizerCancel;
    optimizerCancelButton.setAttribute("aria-label", TEXT.optimizerCancel);
    optimizerCancelButton.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        event.stopPropagation();
    });
    optimizerCancelButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        cancelPromptOptimization(node);
    });
    optimizerStatus.append(optimizerStatusSpinner, optimizerStatusText, optimizerCancelButton);
    const viewButton = document.createElement("button");
    viewButton.type = "button";
    viewButton.className = "h3-prompt-editor-tool h3-prompt-editor-view-toggle";
    viewButton.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        event.stopPropagation();
    });
    viewButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        togglePromptView(node);
    });
    const optimizeButton = document.createElement("button");
    optimizeButton.type = "button";
    optimizeButton.className = "h3-prompt-editor-tool h3-prompt-editor-optimize";
    optimizeButton.textContent = "\u2726";
    optimizeButton.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        event.stopPropagation();
    });
    optimizeButton.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        optimizePromptFromEditor(node);
    });
    editorTools.append(optimizeButton, viewButton);
    editor.addEventListener("beforeinput", (event) => {
        if (isRawPromptMode(node)) {
            node.__h3DialogueHashHandled = false;
            return;
        }
        if (node.__h3DialogueHashHandled) {
            node.__h3DialogueHashHandled = false;
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation?.();
            return;
        }
        if (event.inputType === "insertText" && event.data === "#" && insertDialogueBlockAtSelection(node, editor)) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation?.();
            syncPromptFromEditor(node);
            pushPromptHistory(node);
            return;
        }
        if (event.inputType === "insertText" && event.data === "~" && insertSegmentDividerAtSelection(node, editor)) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation?.();
            syncPromptFromEditor(node);
            pushPromptHistory(node);
            return;
        }
        if (canUseMediaMentions(node) && event.data === "@") setTimeout(() => syncMentionMenuToCaret(node, editor), 0);
    });
    editor.addEventListener("input", (event) => {
        const raw = isRawPromptMode(node);
        if (raw) node.__h3RawPromptNeedsSync = true;
        syncPromptFromEditor(node);
        if (event?.isComposing || event?.inputType === "insertCompositionText" || node.__h3PromptComposing) {
            if (!raw) syncMentionMenuToCaret(node, editor);
            return;
        }
        pushPromptHistory(node);
        if (raw) {
            closeMentionMenu(node);
            return;
        }
        syncMentionMenuToCaret(node, editor);
    });
    editor.addEventListener("compositionstart", () => {
        node.__h3PromptComposing = true;
    });
    editor.addEventListener("compositionend", () => {
        node.__h3PromptComposing = false;
        if (isRawPromptMode(node)) node.__h3RawPromptNeedsSync = true;
        syncPromptFromEditor(node);
        pushPromptHistory(node);
    });
    editor.addEventListener("focus", () => {
        activePromptNode = node;
        applyNativeEditorTheme(wrap);
        // Focusing the editor must not open the picker by itself. It should only
        // appear when the caret is actually inside a freshly typed @ query.
        if (isRawPromptMode(node)) closeMentionMenu(node);
        else syncMentionMenuToCaret(node, editor);
    });
    editor.addEventListener("pointerdown", () => {
        activePromptNode = node;
    }, true);
    editor.addEventListener("keyup", (event) => {
        if (isRawPromptMode(node) || !canUseMediaMentions(node) || ["ArrowUp", "ArrowDown", "Enter", "Escape", "Tab"].includes(event.key)) return;
        syncMentionMenuToCaret(node, editor);
        event.stopPropagation();
    });
    editor.addEventListener("keydown", (event) => {
        if (isPromptUndoRedoEvent(event)) {
            handlePromptHistoryKeydown(node, event);
        }
    }, true);
    editor.addEventListener("keydown", (event) => {
        const key = String(event.key || "").toLowerCase();
        if ((event.ctrlKey || event.metaKey) && key === "s") {
            syncPromptFromEditor(node);
            event.preventDefault();
            return;
        }
        const raw = isRawPromptMode(node);
        if (raw) closeMentionMenu(node);
        if (!raw && handleMentionMenuKeydown(node, event)) {
            event.preventDefault();
            event.stopPropagation();
            return;
        }
        if (!raw && event.key === "#" && !event.ctrlKey && !event.metaKey && !event.altKey && insertDialogueBlockAtSelection(node, editor)) {
            event.preventDefault();
            event.stopPropagation();
            node.__h3DialogueHashHandled = true;
            setTimeout(() => { node.__h3DialogueHashHandled = false; }, 0);
            syncPromptFromEditor(node);
            pushPromptHistory(node);
            return;
        }
        if (!raw && event.key === "~" && !event.ctrlKey && !event.metaKey && !event.altKey && insertSegmentDividerAtSelection(node, editor)) {
            event.preventDefault();
            event.stopPropagation();
            node.__h3DialogueHashHandled = true;
            setTimeout(() => { node.__h3DialogueHashHandled = false; }, 0);
            syncPromptFromEditor(node);
            pushPromptHistory(node);
            return;
        }
        const dialogue = dialogueBlockAtSelection(editor);
        if (event.key === "Enter" && dialogue && !event.shiftKey) {
            event.preventDefault();
            event.stopPropagation();
            exitDialogueBlock(node, editor, dialogue);
            syncPromptFromEditor(node);
            pushPromptHistory(node);
            return;
        }
        if (event.key === "Enter" && dialogue && event.shiftKey && insertEditorLineBreak(editor)) {
            event.preventDefault();
            event.stopPropagation();
            syncPromptFromEditor(node);
            pushPromptHistory(node);
            return;
        }
        if (event.key === "Backspace" && (
            backspaceDialogueBoundary(editor, node)
            || deleteLineBreakNearCaret(editor, node, "backward")
            || deleteChipNearCaret(editor, node, "backward")
            || backspaceBeforeChip(editor, node)
            || backspaceAtLooseSentinel(editor, node)
            || blockNativeSentinelDeletion(editor)
        )) {
            event.preventDefault();
            syncPromptFromEditor(node);
            pushPromptHistory(node);
        } else if (event.key === "Delete" && deleteChipNearCaret(editor, node, "forward")) {
            event.preventDefault();
            syncPromptFromEditor(node);
            pushPromptHistory(node);
        } else if (event.key === "Enter" && insertEditorLineBreak(editor)) {
            event.preventDefault();
            closeMentionMenu(node);
            syncPromptFromEditor(node);
            pushPromptHistory(node);
        } else if (event.key === "Escape") {
            closeMentionMenu(node);
        }
        event.stopPropagation();
    });
    editor.addEventListener("paste", (event) => {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation?.();
        const text = event.clipboardData?.getData("text/plain") || "";
        if (isRawPromptMode(node)) {
            insertPlainText(editor, text);
            node.__h3RawPromptNeedsSync = true;
            syncPromptFromEditor(node);
            pushPromptHistory(node);
            return;
        }
        insertTextWithMentionChips(node, editor, text);
        syncPromptFromEditor(node);
        pushPromptHistory(node);
        syncMentionMenuToCaret(node, editor);
    });
    editor.addEventListener("blur", () => {
        syncPromptFromEditor(node);
        setTimeout(() => {
            if (!node.__h3MentionMenu?.element?.matches?.(":hover")) closeMentionMenu(node);
        }, 160);
    });
    wrap.addEventListener("pointerdown", (event) => {
        event.stopPropagation();
        if (!event.target?.closest?.(".h3-mention-chip")) closeMentionMenu(node);
    });
    const wheelHandler = (event) => {
        const editorFocused = document.activeElement === editor;
        const horizontal = Math.abs(event.deltaX || 0) > Math.abs(event.deltaY || 0);
        const maxScrollTop = Math.max(0, editor.scrollHeight - editor.clientHeight);
        const lineHeight = parseFloat(getComputedStyle(editor).lineHeight) || 16;
        const deltaY = event.deltaMode === 1
            ? event.deltaY * lineHeight
            : event.deltaMode === 2
                ? event.deltaY * editor.clientHeight
                : event.deltaY;
        if (!editorFocused) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation?.();
            app.canvas?.processMouseWheel?.(event);
            return;
        }
        if (!event.ctrlKey && !horizontal && maxScrollTop > 0 && deltaY) {
            const next = Math.max(0, Math.min(maxScrollTop, editor.scrollTop + deltaY));
            if (next !== editor.scrollTop) {
                editor.scrollTop = next;
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation?.();
                return;
            }
        }
        if (!event.ctrlKey && !horizontal && maxScrollTop > 0) {
            event.stopPropagation();
            event.stopImmediatePropagation?.();
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation?.();
        app.canvas?.processMouseWheel?.(event);
    };
    editor.addEventListener("wheel", wheelHandler, { passive: false, capture: true });
    wrap.addEventListener("wheel", wheelHandler, { passive: false });
    wrap.append(editor, optimizerStatus, editorTools);
    node.__h3Editor = editor;
    node.__h3EditorWrap = wrap;
    node.__h3PromptEditorTools = editorTools;
    node.__h3PromptViewButton = viewButton;
    node.__h3PromptOptimizeButton = optimizeButton;
    node.__h3PromptOptimizerStatus = optimizerStatus;
    node.__h3PromptOptimizerStatusText = optimizerStatusText;
    syncPromptExternalConnectionState(node);
    renderEditorFromNode(node);
    syncPromptOptimizerButton(node);
    resetPromptHistory(node);
    const domWidget = node.addDOMWidget("h3_prompt_mentions", "h3_prompt_mentions", wrap, {
        getValue: () => String(getWidget(node, "prompt")?.value || ""),
        setValue: (value) => {
            const promptWidget = getWidget(node, "prompt");
            if (promptWidget) promptWidget.value = String(value || "");
            renderEditorFromNode(node);
        },
        margin: 10,
        serialize: false,
        getMinHeight: () => 50,
        afterResize: () => {
            applyNativeEditorTheme(wrap);
            node._widgetSlotsDirty = true;
            node.setDirtyCanvas?.(true, true);
        },
        onDraw: () => applyNativeEditorTheme(wrap),
    });
    if (!domWidget) {
        restoreOriginalPromptWidget(widget);
        wrap.remove();
        node.__h3Editor = null;
        node.__h3EditorWrap = null;
        node.__h3PromptEditorTools = null;
        node.__h3PromptViewButton = null;
        node.__h3PromptOptimizeButton = null;
        return;
    }
    node.__h3DomWidget = domWidget;
    domWidget.serialize = false;
    setWidgetOption(domWidget, "serialize", false);
    setWidgetOption(domWidget, "canvasOnly", false);
    domWidget.__h3EditorType = domWidget.type;
    domWidget.__h3EditorComputeSize = domWidget.computeSize;
    const domIndex = node.widgets?.indexOf(domWidget) ?? -1;
    const promptIndex = node.widgets?.indexOf(widget) ?? -1;
    if (domIndex >= 0 && promptIndex >= 0 && domIndex !== promptIndex + 1) {
        node.widgets.splice(domIndex, 1);
        const nextPromptIndex = node.widgets.indexOf(widget);
        node.widgets.splice(nextPromptIndex + 1, 0, domWidget);
    }
    syncEditorMode(node);
    repairNodeLayout(node);
}

function installPromptEditorSoon(node) {
    if (!node || node.__h3PromptInstallPending || node.__h3PromptInstallRetry || node.__h3Editor) return;
    const now = typeof performance !== "undefined" ? performance.now() : Date.now();
    if (now < (Number(node.__h3PromptInstallNextAt) || 0)) return;
    node.__h3PromptInstallPending = true;
    const run = () => {
        node.__h3PromptInstallPending = false;
        ensurePromptEditor(node);
        if (node.__h3Editor) {
            if (restorePromptEditorStableSize(node)) repairNodeLayout(node);
            node.__h3PromptInstallAttempts = 0;
            node.__h3PromptInstallNextAt = 0;
            return;
        }
        const attempts = Math.min(8, (Number(node.__h3PromptInstallAttempts) || 0) + 1);
        const delay = Math.min(2000, 120 * (2 ** Math.min(attempts - 1, 4)));
        node.__h3PromptInstallAttempts = attempts;
        node.__h3PromptInstallNextAt = (typeof performance !== "undefined" ? performance.now() : Date.now()) + delay;
        node.__h3PromptInstallRetry = setTimeout(() => {
            node.__h3PromptInstallRetry = null;
            installPromptEditorSoon(node);
        }, delay);
    };
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(run);
    else setTimeout(run, 0);
}

function removePromptEditorWidgets(node) {
    if (!Array.isArray(node?.widgets)) return false;
    const stale = node.widgets.filter((widget) =>
        widget === node.__h3DomWidget || String(widget?.name || "") === "h3_prompt_mentions"
    );
    if (!stale.length) return false;
    for (const widget of stale) {
        try { widget.element?.remove?.(); } catch { /* Already detached. */ }
    }
    const next = node.widgets.filter((widget) => !stale.includes(widget));
    node.widgets = next;
    if (Array.isArray(node._widgets)) node._widgets = next;
    node.__h3DomWidget = null;
    node._widgetSlotsDirty = true;
    refreshVueNodeWidgets(node);
    return true;
}

function updatePromptEditor(node) {
    if (!node.__h3Editor) {
        installPromptEditorSoon(node);
        return;
    }
    const editor = node.__h3Editor;
    if (!editor) return;
    preparePromptEditorForUndo(editor);
    syncEditorMode(node);
}

function isTransportInputName(name) {
    const value = String(name || "");
    return /^media_[0-9]+$/i.test(value)
        || /^media_type_[0-9]+$/i.test(value)
        || value === "prompt_optimizer_resources"
        || value === "prompt_optimizer_marker"
        || value === "prompt_optimizer_prompt_connected";
}

function removeInputSlot(node, index) {
    const input = node?.inputs?.[index];
    if (!input) return false;
    if (input.link != null) {
        try {
            node.disconnectInput?.(index);
        } catch {
            // Ignore and fall through to hard removal.
        }
        if (input.link != null) {
            try {
                node.graph?.removeLink?.(input.link);
            } catch {
                // Ignore - the slot is going away either way.
            }
            input.link = null;
        }
    }
    if (typeof node.removeInput === "function") node.removeInput(index);
    else node.inputs.splice(index, 1);
    return true;
}

function pruneTransportInputs(nodeData) {
    const sections = [nodeData?.input?.required, nodeData?.input?.optional];
    let changed = false;
    for (const section of sections) {
        if (!section || typeof section !== "object") continue;
        for (const name of Object.keys(section)) {
            if (!isTransportInputName(name)) continue;
            delete section[name];
            changed = true;
        }
    }
    if (Array.isArray(nodeData?.inputs)) {
        const nextInputs = nodeData.inputs.filter((input) => !isTransportInputName(input?.name));
        if (nextInputs.length !== nodeData.inputs.length) {
            nodeData.inputs = nextInputs;
            changed = true;
        }
    }
    return changed;
}

function pruneTransportInputsFromNode(node, { requestLayout = true, force = false } = {}) {
    if (!node || (!force && !isTarget(node))) return false;
    let changed = false;
    if (Array.isArray(node.inputs)) {
        for (let index = node.inputs.length - 1; index >= 0; index -= 1) {
            const input = node.inputs[index];
            const name = String(input?.name || "");
            if (!isTransportInputName(name)) continue;
            if (/^media_\d+$/i.test(name) && input.link != null) {
                convertNativeMediaConnection(node, index);
            }
            removeInputSlot(node, index);
            changed = true;
        }
    }
    if (Array.isArray(node.widgets)) {
        const stale = node.widgets.filter((widget) => /^media_type_\d+$/i.test(String(widget?.name || "")));
        if (stale.length) {
            for (const widget of stale) {
                try { widget.element?.remove?.(); } catch { /* Already detached. */ }
            }
            node.widgets = node.widgets.filter((widget) => !stale.includes(widget));
            if (Array.isArray(node._widgets)) {
                node._widgets = node._widgets.filter((widget) => !stale.includes(widget));
            }
            refreshVueNodeWidgets(node);
            changed = true;
        }
    }
    if (changed) {
        node._widgetSlotsDirty = true;
        app.graph?.change?.();
        node.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
        if (requestLayout) repairNodeLayout(node);
    }
    return changed;
}

function setConfiguredWidgetValue(node, name, value) {
    const widget = getWidget(node, name);
    if (!widget || value === undefined) return;
    widget.value = value;
    if (widget._state) widget._state.value = value;
}

function bindPromptOptimizerWidgetCallbacks(node) {
    const names = [
        "prompt_optimizer",
        "prompt_optimizer_api_format",
        "prompt_optimizer_api_url",
        "prompt_optimizer_api_key",
        "prompt_optimizer_model",
        "prompt_optimizer_scene_guide",
        "prompt_optimizer_read_media",
        "prompt_optimizer_optimize_on_run",
        "context_prompt_optimizer_mode",
        "context_prompt_optimizer_concurrency",
    ];
    for (const name of names) {
        const widget = getWidget(node, name);
        if (!widget || widget.__h3PromptOptimizerCallbackBound) continue;
        widget.__h3PromptOptimizerCallbackBound = true;
        const original = widget.callback;
        widget.callback = (value) => {
            original?.call(widget, value);
            if (name === "prompt_optimizer_scene_guide") widget.value = ZH_BROWSER
                ? (PROMPT_GUIDES.find((item) => item.value === canonicalPromptGuide(value))?.zh || value)
                : (PROMPT_GUIDES.find((item) => item.value === canonicalPromptGuide(value))?.en || value);
            if (name === "context_prompt_optimizer_mode") {
                widget.value = OPTION_DEFS.context_prompt_optimizer_mode[
                    canonicalOption("context_prompt_optimizer_mode", value)
                ] || widget.value;
            }
            promptOptimizerState(node);
            if (name === "prompt_optimizer" || name === "context_prompt_optimizer_mode") {
                syncModeWidgets(node);
                repairNodeLayout(node);
            }
            syncPromptOptimizerButton(node);
            node.setDirtyCanvas?.(true, true);
            app.graph?.change?.();
        };
    }
}

function repairConfiguredWidgetValues(node, info) {
    const raw = Array.isArray(info?.widgets_values) ? [...info.widgets_values] : [];
    if (!raw.length) return;

    // Selected-video context has its own prefix and keeps the API optimizer
    // fields inline with the rest of the node. Normalize it before the
    // generic Easy/context parser below so switching workflows cannot shift
    // the segment controls into the wrong rows.
    if (isSelectedVideoContextNode(node)) {
        const named = info?.widgets_values_named && typeof info.widgets_values_named === "object"
            ? info.widgets_values_named
            : {};
        const values = [...raw];
        const segmentModeIsValid = (value) => Object.prototype.hasOwnProperty.call(
            OPTION_DEFS.selected_video_segment_mode,
            canonicalOption("selected_video_segment_mode", value),
        );
        if (values.length > 3 && (values[2] == null || String(values[2]).trim() === "") && segmentModeIsValid(values[3])) {
            values.splice(2, 1);
        }
        const namedValue = (name) => named[name];
        const optionValue = (name, optionName, positional, fallback) => {
            const positionalValue = canonicalOption(optionName, positional);
            if (Object.prototype.hasOwnProperty.call(OPTION_DEFS[optionName], positionalValue)) return positionalValue;
            const namedValueNormalized = canonicalOption(optionName, namedValue(name));
            if (Object.prototype.hasOwnProperty.call(OPTION_DEFS[optionName], namedValueNormalized)) return namedValueNormalized;
            return fallback;
        };
        const stringValue = (name, positional, fallback) =>
            typeof positional === "string" ? positional : (typeof namedValue(name) === "string" ? namedValue(name) : fallback);
        const boolValue = (name, positional, fallback) => {
            if (typeof positional === "boolean") return positional;
            if (typeof positional === "number" && Number.isFinite(positional)) return positional !== 0;
            const text = String(positional ?? "").trim().toLowerCase();
            if (["1", "true", "on", "yes"].includes(text)) return true;
            if (["0", "false", "off", "no", ""].includes(text)) {
                const namedText = String(namedValue(name) ?? "").trim().toLowerCase();
                if (["1", "true", "on", "yes"].includes(namedText)) return true;
                return fallback;
            }
            return fallback;
        };
        const numberValue = (name, positional, fallback) => {
            const value = Number(positional);
            if (Number.isFinite(value)) return value;
            const namedNumber = Number(namedValue(name));
            return Number.isFinite(namedNumber) ? namedNumber : fallback;
        };
        const defaults = {
            mode: MODE_IMAGE,
            prompt: "",
            segment_mode: SELECTED_VIDEO_SEGMENT_WHOLE,
            segment_cuts: "",
            context_length: GUIDE_CONTEXT_FRAME_GRID[0],
            continuity_mode: CONTINUITY_LATENT,
            advanced: false,
            keyframe_role: KEYFRAME_FIRST,
            ref_image_size: REF_IMAGE_1K,
            reference_mention_mode: "index",
            prompt_optimizer: false,
            prompt_optimizer_api_format: "openai",
            prompt_optimizer_api_url: "",
            prompt_optimizer_api_key: "",
            prompt_optimizer_model: "",
            prompt_optimizer_scene_guide: "none",
            prompt_optimizer_read_media: false,
            prompt_optimizer_optimize_on_run: false,
            context_prompt_optimizer_mode: "whole_sequence",
            context_prompt_optimizer_concurrency: 3,
        };
        let suffix = values.slice(10);
        let contextOptimizerMode = defaults.context_prompt_optimizer_mode;
        let contextOptimizerConcurrency = defaults.context_prompt_optimizer_concurrency;
        if (suffix.length >= 2) {
            const candidate = canonicalOption("context_prompt_optimizer_mode", suffix[suffix.length - 2]);
            const concurrency = Number(suffix[suffix.length - 1]);
            if (Object.prototype.hasOwnProperty.call(OPTION_DEFS.context_prompt_optimizer_mode, candidate) && Number.isFinite(concurrency)) {
                contextOptimizerMode = candidate;
                contextOptimizerConcurrency = Math.max(1, Math.min(20, concurrency || 3));
                suffix = suffix.slice(0, -2);
            }
        }
        const apiFormat = canonicalOption("prompt_optimizer_api_format", suffix[1]);
        const optimizer = {
            prompt_optimizer: defaults.prompt_optimizer,
            prompt_optimizer_api_format: defaults.prompt_optimizer_api_format,
            prompt_optimizer_api_url: defaults.prompt_optimizer_api_url,
            prompt_optimizer_api_key: defaults.prompt_optimizer_api_key,
            prompt_optimizer_model: defaults.prompt_optimizer_model,
            prompt_optimizer_scene_guide: defaults.prompt_optimizer_scene_guide,
            prompt_optimizer_read_media: defaults.prompt_optimizer_read_media,
            prompt_optimizer_optimize_on_run: defaults.prompt_optimizer_optimize_on_run,
        };
        if (suffix.length >= 8 && ["openai", "responses", "gemini"].includes(apiFormat)) {
            optimizer.prompt_optimizer = boolValue("prompt_optimizer", suffix[0], false);
            optimizer.prompt_optimizer_api_format = apiFormat;
            optimizer.prompt_optimizer_api_url = String(suffix[2] ?? "");
            optimizer.prompt_optimizer_api_key = String(suffix[3] ?? "");
            optimizer.prompt_optimizer_model = String(suffix[4] ?? "");
            optimizer.prompt_optimizer_scene_guide = canonicalPromptGuide(suffix[5] || "none");
            optimizer.prompt_optimizer_read_media = boolValue("prompt_optimizer_read_media", suffix[6], false);
            optimizer.prompt_optimizer_optimize_on_run = boolValue("prompt_optimizer_optimize_on_run", suffix[7], false);
        } else if (suffix.length >= 2) {
            // Read the old temporary-settings layout only to preserve its
            // selected guide; the branch itself always writes inline API rows.
            optimizer.prompt_optimizer_scene_guide = canonicalPromptGuide(suffix[1] || "none");
        }
        const continuityMode = optionValue("continuity_mode", "continuity_mode", values[5], defaults.continuity_mode);
        const normalizedContinuityMode = Object.prototype.hasOwnProperty.call(OPTION_DEFS.continuity_mode, continuityMode)
            ? continuityMode : defaults.continuity_mode;
        const grid = AV_CONTINUITY_MODES.has(normalizedContinuityMode) ? AV_CONTEXT_FRAME_GRID : GUIDE_CONTEXT_FRAME_GRID;
        const rawContextLength = numberValue("context_length", values[4], defaults.context_length);
        const contextLength = grid.reduce((best, candidate) => Math.abs(candidate - rawContextLength) < Math.abs(best - rawContextLength) ? candidate : best, grid[0]);
        const normalized = {
            mode: optionValue("mode", "mode", values[0], defaults.mode),
            prompt: stringValue("prompt", values[1], defaults.prompt),
            segment_mode: optionValue("segment_mode", "selected_video_segment_mode", values[2], defaults.segment_mode),
            segment_cuts: stringValue("segment_cuts", values[3], defaults.segment_cuts),
            context_length: contextLength,
            continuity_mode: normalizedContinuityMode,
            advanced: boolValue("advanced", values[6], defaults.advanced),
            keyframe_role: optionValue("keyframe_role", "keyframe_role", values[7], defaults.keyframe_role),
            ref_image_size: optionValue("ref_image_size", "ref_image_size", values[8], defaults.ref_image_size),
            reference_mention_mode: optionValue("reference_mention_mode", "reference_mention_mode", values[9], defaults.reference_mention_mode),
            ...optimizer,
            context_prompt_optimizer_mode: contextOptimizerMode,
            context_prompt_optimizer_concurrency: contextOptimizerConcurrency,
        };
        if (normalized.segment_mode === SELECTED_VIDEO_SEGMENT_WHOLE || segmentModeIsValid(normalized.segment_cuts)) {
            normalized.segment_cuts = defaults.segment_cuts;
        }
        for (const name of Object.keys(normalized)) setConfiguredWidgetValue(node, name, normalized[name]);
        info.widgets_values = [
            normalized.mode, normalized.prompt, normalized.segment_mode, normalized.segment_cuts,
            normalized.context_length, normalized.continuity_mode, normalized.advanced,
            normalized.keyframe_role, normalized.ref_image_size, normalized.reference_mention_mode,
            normalized.prompt_optimizer, normalized.prompt_optimizer_api_format,
            normalized.prompt_optimizer_api_url, normalized.prompt_optimizer_api_key,
            normalized.prompt_optimizer_model, normalized.prompt_optimizer_scene_guide,
            normalized.prompt_optimizer_read_media, normalized.prompt_optimizer_optimize_on_run,
            normalized.context_prompt_optimizer_mode, normalized.context_prompt_optimizer_concurrency,
        ];
        info.widgets_values_named = {
            ...(info.widgets_values_named && typeof info.widgets_values_named === "object" ? info.widgets_values_named : {}),
            ...normalized,
        };
        return;
    }

    const contextSegments = isContextSegmentsNode(node);
    const values = raw;
    if (contextSegments && !Object.prototype.hasOwnProperty.call(OPTION_DEFS.audio_mode, canonicalOption("audio_mode", values[1]))) {
        values.splice(1, 0, CONTEXT_AUDIO_GENERATED);
    }

    const promptIndex = contextSegments ? 2 : 1;
    const resolutionIndexBeforeRepair = promptIndex + 1;
    const resolutionAt = canonicalOption("resolution", values[resolutionIndexBeforeRepair]);
    const nextResolution = canonicalOption("resolution", values[resolutionIndexBeforeRepair + 1]);
    if (
        !Object.prototype.hasOwnProperty.call(OPTION_DEFS.resolution, resolutionAt)
        && Object.prototype.hasOwnProperty.call(OPTION_DEFS.resolution, nextResolution)
    ) {
        values.splice(resolutionIndexBeforeRepair, 1);
    }

    const defaults = {
        mode: contextSegments ? MODE_SEGMENTS : MODE_IMAGE,
        audio_mode: CONTEXT_AUDIO_GENERATED,
        prompt: "",
        resolution: "480P",
        aspect_ratio: "16:9",
        width: 1344,
        height: 768,
        seconds: 5,
        segment_seconds: "",
        context_length: GUIDE_CONTEXT_FRAME_GRID[0],
        continuity_mode: CONTINUITY_LATENT,
        advanced: contextSegments,
        fps: 24,
        keyframe_role: KEYFRAME_FIRST,
        ref_image_size: REF_IMAGE_1K,
        reference_mention_mode: "index",
        prompt_optimizer: false,
        prompt_optimizer_api_format: "openai",
        prompt_optimizer_api_url: "",
        prompt_optimizer_api_key: "",
        prompt_optimizer_model: "",
        prompt_optimizer_scene_guide: "none",
        prompt_optimizer_read_media: false,
        prompt_optimizer_optimize_on_run: false,
        context_prompt_optimizer_mode: "whole_sequence",
        context_prompt_optimizer_concurrency: 3,
    };
    const index = contextSegments
        ? {
            mode: 0, audio_mode: 1, prompt: 2, resolution: 3, aspect_ratio: 4,
            width: 5, height: 6, seconds: 7, segment_seconds: 8, context_length: 9,
            continuity_mode: 10, advanced: 11, fps: 12, keyframe_role: 13,
            ref_image_size: 14, reference_mention_mode: 15,
        }
        : {
            mode: 0, prompt: 1, resolution: 2, aspect_ratio: 3, width: 4,
            height: 5, seconds: 6, advanced: 7, fps: 8, keyframe_role: 9,
            ref_image_size: 10, reference_mention_mode: 11,
        };
    const prefixLength = contextSegments ? 16 : 12;
    let suffix = values.slice(prefixLength);
    let contextOptimizerMode = defaults.context_prompt_optimizer_mode;
    let contextOptimizerConcurrency = defaults.context_prompt_optimizer_concurrency;
    if (contextSegments && suffix.length >= 2) {
        const modeCandidate = canonicalOption("context_prompt_optimizer_mode", suffix[suffix.length - 2]);
        const concurrencyCandidate = Number(suffix[suffix.length - 1]);
        if (
            Object.prototype.hasOwnProperty.call(OPTION_DEFS.context_prompt_optimizer_mode, modeCandidate)
            && Number.isFinite(concurrencyCandidate)
        ) {
            contextOptimizerMode = modeCandidate;
            contextOptimizerConcurrency = Math.max(1, Math.min(20, concurrencyCandidate || 3));
            suffix = suffix.slice(0, -2);
        }
/*
    const names = Object.keys(defaults);
    const contextSegments = isContextSegmentsNode(node);
    if (isSelectedVideoContextNode(node)) {
        const selectedDefaults = {
            mode: MODE_IMAGE,
            prompt: "",
            advanced: false,
            keyframe_role: KEYFRAME_FIRST,
            ref_image_size: REF_IMAGE_1K,
            reference_mention_mode: "index",
            prompt_optimizer_settings: false,
            prompt_optimizer_scene_guide: "none",
            segment_mode: SELECTED_VIDEO_SEGMENT_WHOLE,
            segment_cuts: "",
            context_length: GUIDE_CONTEXT_FRAME_GRID[0],
            continuity_mode: CONTINUITY_LATENT,
            context_prompt_optimizer_mode: "whole_sequence",
            context_prompt_optimizer_concurrency: 3,
        };

        // Current selected-video schema is:
        // mode, prompt, segment_mode, segment_cuts, context_length,
        // continuity_mode, advanced, then the advanced controls.
        //
        // Some ComfyUI workflow snapshots contain an extra null placeholder
        // after the prompt, producing:
        // mode, prompt, null, segment_mode, segment_cuts, ...
        // The generic Easy/context migration handles this case, but the
        // selected-video node used to read raw positions directly. That made
        // every field after the placeholder shift, with segment_mode falling
        // back to whole_video and the stale mode label landing in segment_cuts.
        const values = [...raw];
        if (values.length < 14) return;

        const named = info?.widgets_values_named && typeof info.widgets_values_named === "object"
            ? info.widgets_values_named
            : {};

        const isSelectedSegmentMode = (value) => Object.prototype.hasOwnProperty.call(
            OPTION_DEFS.selected_video_segment_mode,
            canonicalOption("selected_video_segment_mode", value),
        );
        const placeholderAfterPrompt = values.length > 3
            && (values[2] == null || String(values[2]).trim() === "")
            && isSelectedSegmentMode(values[3]);
        if (placeholderAfterPrompt) values.splice(2, 1);

        const namedValue = (name) => named[name];
        const optionValue = (widgetName, optionName, positional, fallback) => {
            const normalize = (value) => canonicalOption(optionName, value);
            const positionalValue = normalize(positional);
            if (Object.prototype.hasOwnProperty.call(OPTION_DEFS[optionName], positionalValue)) {
                return positionalValue;
            }
            const namedNormalized = normalize(namedValue(widgetName));
            if (Object.prototype.hasOwnProperty.call(OPTION_DEFS[optionName], namedNormalized)) {
                return namedNormalized;
            }
            return fallback;
        };
        const stringValue = (name, positional, fallback) => {
            if (typeof positional === "string") return positional;
            return typeof namedValue(name) === "string" ? namedValue(name) : fallback;
        };
        const strictBoolean = (value) => {
            if (typeof value === "boolean") return value;
            if (typeof value === "number" && Number.isFinite(value)) return value !== 0;
            if (typeof value !== "string") return null;
            const normalized = value.trim().toLowerCase();
            if (["1", "true", "on", "yes"].includes(normalized)) return true;
            if (["0", "false", "off", "no", ""].includes(normalized)) return false;
            return null;
        };
        const booleanValue = (name, positional, fallback) => {
            const parsed = strictBoolean(positional);
            if (parsed !== null) return parsed;
            const namedParsed = strictBoolean(namedValue(name));
            return namedParsed === null ? fallback : namedParsed;
        };
        const numberValue = (name, positional, fallback) => {
            const parsed = Number(positional);
            if (Number.isFinite(parsed)) return parsed;
            const namedParsed = Number(namedValue(name));
            return Number.isFinite(namedParsed) ? namedParsed : fallback;
        };

        const selectedMode = optionValue("mode", "mode", values[0], selectedDefaults.mode);
        const selectedSegmentMode = optionValue(
            "segment_mode",
            "selected_video_segment_mode",
            values[2],
            selectedDefaults.segment_mode,
        );
        const selectedContinuityMode = optionValue(
            "continuity_mode",
            "continuity_mode",
            values[5],
            selectedDefaults.continuity_mode,
        );
        const normalizedContinuityMode = Object.prototype.hasOwnProperty.call(OPTION_DEFS.continuity_mode, selectedContinuityMode)
            ? selectedContinuityMode
            : selectedDefaults.continuity_mode;
        const selectedContextGrid = AV_CONTINUITY_MODES.has(normalizedContinuityMode)
            ? AV_CONTEXT_FRAME_GRID
            : GUIDE_CONTEXT_FRAME_GRID;
        const rawContextLength = numberValue("context_length", values[4], selectedDefaults.context_length);
        const normalizedContextLength = Number.isFinite(rawContextLength)
            ? selectedContextGrid.reduce(
                (best, candidate) => Math.abs(candidate - rawContextLength) < Math.abs(best - rawContextLength) ? candidate : best,
                selectedContextGrid[0],
            )
            : selectedContextGrid[0];
        const selectedValues = {
            mode: Object.prototype.hasOwnProperty.call(OPTION_DEFS.mode, selectedMode)
                ? selectedMode : selectedDefaults.mode,
            prompt: stringValue("prompt", values[1], selectedDefaults.prompt),
            keyframe_role: optionValue("keyframe_role", "keyframe_role", values[7], selectedDefaults.keyframe_role),
            ref_image_size: optionValue("ref_image_size", "ref_image_size", values[8], selectedDefaults.ref_image_size),
            reference_mention_mode: optionValue("reference_mention_mode", "reference_mention_mode", values[9], selectedDefaults.reference_mention_mode),
            prompt_optimizer_settings: false,
            prompt_optimizer_scene_guide: canonicalPromptGuide(
                stringValue("prompt_optimizer_scene_guide", values[11], selectedDefaults.prompt_optimizer_scene_guide),
            ),
            segment_mode: selectedSegmentMode,
            segment_cuts: stringValue("segment_cuts", values[3], selectedDefaults.segment_cuts),
            context_length: normalizedContextLength,
            continuity_mode: normalizedContinuityMode,
            context_prompt_optimizer_mode: optionValue(
                "context_prompt_optimizer_mode",
                "context_prompt_optimizer_mode",
                values[12],
                selectedDefaults.context_prompt_optimizer_mode,
            ),
            context_prompt_optimizer_concurrency: Math.max(
                1,
                Math.min(20, numberValue(
                    "context_prompt_optimizer_concurrency",
                    values[13],
                    selectedDefaults.context_prompt_optimizer_concurrency,
                )),
            ),
            advanced: booleanValue("advanced", values[6], selectedDefaults.advanced),
        };
        // A whole-video snapshot can carry the old localized mode label in
        // the cut-point slot. It is not a valid cut list and must not reappear
        // when the user later switches to time/frame splitting.
        if (selectedValues.segment_mode === SELECTED_VIDEO_SEGMENT_WHOLE
            || isSelectedSegmentMode(selectedValues.segment_cuts)) {
            selectedValues.segment_cuts = selectedDefaults.segment_cuts;
        }
        for (const name of Object.keys(selectedDefaults)) setConfiguredWidgetValue(node, name, selectedValues[name]);
        info.widgets_values = [
            selectedValues.mode,
            selectedValues.prompt,
            selectedValues.segment_mode,
            selectedValues.segment_cuts,
            selectedValues.context_length,
            selectedValues.continuity_mode,
            selectedValues.advanced,
            selectedValues.keyframe_role,
            selectedValues.ref_image_size,
            selectedValues.reference_mention_mode,
            selectedValues.prompt_optimizer_settings,
            selectedValues.prompt_optimizer_scene_guide,
            selectedValues.context_prompt_optimizer_mode,
            selectedValues.context_prompt_optimizer_concurrency,
        ];
        info.widgets_values_named = {
            ...(info.widgets_values_named && typeof info.widgets_values_named === "object" ? info.widgets_values_named : {}),
            ...selectedValues,
        };
        return;
    }
    const values = raw;
    // Context workflows saved before the audio-mode row existed have the
    // prompt directly after mode. Normalize that in-memory before restoring
    // the named widgets so the current workflow files remain usable.
    if (contextSegments && !Object.prototype.hasOwnProperty.call(OPTION_DEFS.audio_mode, canonicalOption("audio_mode", values[1]))) {
        values.splice(1, 0, CONTEXT_AUDIO_GENERATED);
*/
    }

    const optimizer = {
        prompt_optimizer: defaults.prompt_optimizer,
        prompt_optimizer_api_format: defaults.prompt_optimizer_api_format,
        prompt_optimizer_api_url: defaults.prompt_optimizer_api_url,
        prompt_optimizer_api_key: defaults.prompt_optimizer_api_key,
        prompt_optimizer_model: defaults.prompt_optimizer_model,
        prompt_optimizer_scene_guide: defaults.prompt_optimizer_scene_guide,
        prompt_optimizer_read_media: defaults.prompt_optimizer_read_media,
        prompt_optimizer_optimize_on_run: defaults.prompt_optimizer_optimize_on_run,
    };
    const apiFormat = canonicalOption("prompt_optimizer_api_format", suffix[1]);
    if (suffix.length >= 8 && ["openai", "responses", "gemini"].includes(apiFormat)) {
        optimizer.prompt_optimizer = asBoolean(suffix[0], false);
        optimizer.prompt_optimizer_api_format = apiFormat;
        optimizer.prompt_optimizer_api_url = String(suffix[2] ?? "");
        optimizer.prompt_optimizer_api_key = String(suffix[3] ?? "");
        optimizer.prompt_optimizer_model = String(suffix[4] ?? "");
        optimizer.prompt_optimizer_scene_guide = canonicalPromptGuide(suffix[5] || "none");
        optimizer.prompt_optimizer_read_media = asBoolean(suffix[6], false);
        optimizer.prompt_optimizer_optimize_on_run = asBoolean(suffix[7], false);
    } else if (suffix.length >= 2) {
        // Main-branch workflows used a temporary settings button followed by
        // Prompt Guide. Keep the selected guide while initializing inline API fields.
        optimizer.prompt_optimizer_scene_guide = canonicalPromptGuide(suffix[1] || "none");
    }

    const normalized = {
        mode: Object.prototype.hasOwnProperty.call(OPTION_DEFS.mode, canonicalOption("mode", values[index.mode]))
            ? canonicalOption("mode", values[index.mode]) : defaults.mode,
        audio_mode: contextSegments && Object.prototype.hasOwnProperty.call(OPTION_DEFS.audio_mode, canonicalOption("audio_mode", values[index.audio_mode]))
            ? canonicalOption("audio_mode", values[index.audio_mode]) : defaults.audio_mode,
        prompt: typeof values[index.prompt] === "string" ? values[index.prompt] : defaults.prompt,
        resolution: Object.prototype.hasOwnProperty.call(OPTION_DEFS.resolution, canonicalOption("resolution", values[index.resolution]))
            ? canonicalOption("resolution", values[index.resolution]) : defaults.resolution,
        aspect_ratio: Object.prototype.hasOwnProperty.call(OPTION_DEFS.aspect_ratio, canonicalOption("aspect_ratio", values[index.aspect_ratio]))
            ? canonicalOption("aspect_ratio", values[index.aspect_ratio]) : defaults.aspect_ratio,
        width: Number.isFinite(Number(values[index.width])) ? Number(values[index.width]) : defaults.width,
        height: Number.isFinite(Number(values[index.height])) ? Number(values[index.height]) : defaults.height,
        seconds: Number.isFinite(Number(values[index.seconds]))
            ? Math.min(contextSegments ? MAX_SECONDS * SEGMENT_MAX_COUNT : MAX_SECONDS, Math.max(MIN_SECONDS, Number(values[index.seconds])))
            : defaults.seconds,
        advanced: asBoolean(values[index.advanced], defaults.advanced),
        fps: Number.isFinite(Number(values[index.fps])) ? Number(values[index.fps]) : defaults.fps,
        keyframe_role: Object.prototype.hasOwnProperty.call(OPTION_DEFS.keyframe_role, canonicalOption("keyframe_role", values[index.keyframe_role]))
            ? canonicalOption("keyframe_role", values[index.keyframe_role]) : defaults.keyframe_role,
        ref_image_size: Object.prototype.hasOwnProperty.call(OPTION_DEFS.ref_image_size, canonicalOption("ref_image_size", values[index.ref_image_size]))
            ? canonicalOption("ref_image_size", values[index.ref_image_size]) : defaults.ref_image_size,
        reference_mention_mode: Object.prototype.hasOwnProperty.call(OPTION_DEFS.reference_mention_mode, canonicalOption("reference_mention_mode", values[index.reference_mention_mode]))
            ? canonicalOption("reference_mention_mode", values[index.reference_mention_mode]) : defaults.reference_mention_mode,
        continuity_mode: contextSegments && Object.prototype.hasOwnProperty.call(OPTION_DEFS.continuity_mode, canonicalOption("continuity_mode", values[index.continuity_mode]))
            ? canonicalOption("continuity_mode", values[index.continuity_mode]) : defaults.continuity_mode,
        ...optimizer,
        context_prompt_optimizer_mode: contextOptimizerMode,
        context_prompt_optimizer_concurrency: contextOptimizerConcurrency,
    };
    const segmentSeconds = contextSegments && typeof values[index.segment_seconds] === "string"
        ? values[index.segment_seconds] : defaults.segment_seconds;
    const contextGrid = contextSegments && AV_CONTINUITY_MODES.has(normalized.continuity_mode)
        ? AV_CONTEXT_FRAME_GRID : GUIDE_CONTEXT_FRAME_GRID;
    const requestedContextLength = Number(values[index.context_length]);
    const contextLength = contextSegments && Number.isFinite(requestedContextLength)
        ? contextGrid.reduce((best, candidate) => Math.abs(candidate - requestedContextLength) < Math.abs(best - requestedContextLength) ? candidate : best, contextGrid[0])
        : contextGrid[0];

    const commonNames = [
        "mode", "prompt", "resolution", "aspect_ratio", "width", "height", "seconds",
        "advanced", "fps", "keyframe_role", "ref_image_size", "reference_mention_mode",
        "prompt_optimizer", "prompt_optimizer_api_format", "prompt_optimizer_api_url",
        "prompt_optimizer_api_key", "prompt_optimizer_model", "prompt_optimizer_scene_guide",
        "prompt_optimizer_read_media", "prompt_optimizer_optimize_on_run",
    ];
    for (const name of commonNames) setConfiguredWidgetValue(node, name, normalized[name]);
    if (contextSegments) {
        setConfiguredWidgetValue(node, "audio_mode", normalized.audio_mode);
        setConfiguredWidgetValue(node, "segment_seconds", segmentSeconds);
        setConfiguredWidgetValue(node, "context_length", contextLength);
        setConfiguredWidgetValue(node, "continuity_mode", normalized.continuity_mode);
        setConfiguredWidgetValue(node, "context_prompt_optimizer_mode", normalized.context_prompt_optimizer_mode);
        setConfiguredWidgetValue(node, "context_prompt_optimizer_concurrency", normalized.context_prompt_optimizer_concurrency);
        info.widgets_values = [
            normalized.mode, normalized.audio_mode, normalized.prompt, normalized.resolution,
            normalized.aspect_ratio, normalized.width, normalized.height, normalized.seconds,
            segmentSeconds, contextLength, normalized.continuity_mode, normalized.advanced,
            normalized.fps, normalized.keyframe_role, normalized.ref_image_size,
            normalized.reference_mention_mode, normalized.prompt_optimizer,
            normalized.prompt_optimizer_api_format, normalized.prompt_optimizer_api_url,
            normalized.prompt_optimizer_api_key, normalized.prompt_optimizer_model,
            normalized.prompt_optimizer_scene_guide, normalized.prompt_optimizer_read_media,
            normalized.prompt_optimizer_optimize_on_run, normalized.context_prompt_optimizer_mode,
            normalized.context_prompt_optimizer_concurrency,
        ];
    } else {
        info.widgets_values = commonNames.map((name) => normalized[name]);
    }
}
function installNode(nodeType, nodeData) {
    if (![NODE_CLASS, CONTEXT_SEGMENTS_CLASS, SELECTED_VIDEO_CONTEXT_CLASS].includes(nodeData?.name)) return;
    // Strip the virtual-wire transport fields from every frontend definition
    // before a node instance can be constructed. Execution still receives
    // them through the prompt patch and the Python INPUT_TYPES declaration.
    pruneTransportInputs(nodeData);
    if (nodeType?.nodeData && nodeType.nodeData !== nodeData) pruneTransportInputs(nodeType.nodeData);
    if (nodeType?.prototype?.constructor?.nodeData && nodeType.prototype.constructor.nodeData !== nodeData) {
        pruneTransportInputs(nodeType.prototype.constructor.nodeData);
    }
    const installedMarker = nodeData?.name === CONTEXT_SEGMENTS_CLASS
        ? "__h3ContextSegmentsNodeInstalled"
        : nodeData?.name === SELECTED_VIDEO_CONTEXT_CLASS
            ? "__h3SelectedVideoContextNodeInstalled"
            : "__h3EasyNodeInstalled";
    if (nodeType.prototype[installedMarker]) return;
    nodeType.prototype[installedMarker] = true;
    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3Easy() {
        const result = originalCreated?.apply(this, arguments);
        this.properties ||= {};
        ensureLinks(this);
        normalizeLinks(this);
        pruneTransportInputsFromNode(this, { force: true });
        normalizeLinks(this);
        localizeNodeInstance(this);
        bindPromptOptimizerWidgetCallbacks(this);
        syncModeWidgets(this);
        patchCanvas();
        installQuickCreateCapture(app.canvas);
        installPromptEditorSoon(this);
        const modeWidget = getWidget(this, "mode");
        if (modeWidget) {
            const originalCallback = modeWidget.callback;
            modeWidget.callback = (value) => {
                originalCallback?.call(modeWidget, value);
                pruneLinksForMode(this);
                syncModeWidgets(this);
                syncEditorMode(this);
                renderEditorFromNode(this);
                requestMentionPreviewRefresh();
                repairNodeLayout(this);
                this.setDirtyCanvas?.(true, true);
            };
        }
        const audioModeWidget = getWidget(this, "audio_mode");
        if (audioModeWidget && !audioModeWidget.__h3ConditionalCallbackBound) {
            audioModeWidget.__h3ConditionalCallbackBound = true;
            const originalCallback = audioModeWidget.callback;
            audioModeWidget.callback = (value) => {
                originalCallback?.call(audioModeWidget, value);
                syncModeWidgets(this);
                this.setDirtyCanvas?.(true, true);
            };
        }
        const continuityWidget = getWidget(this, "continuity_mode");
        if (continuityWidget && !continuityWidget.__h3ConditionalCallbackBound) {
            continuityWidget.__h3ConditionalCallbackBound = true;
            const originalCallback = continuityWidget.callback;
            continuityWidget.callback = (value) => {
                originalCallback?.call(continuityWidget, value);
                syncModeWidgets(this);
                repairNodeLayout(this);
                this.setDirtyCanvas?.(true, true);
            };
        }
        const selectedSegmentModeWidget = getWidget(this, "segment_mode");
        if (selectedSegmentModeWidget && !selectedSegmentModeWidget.__h3ConditionalCallbackBound) {
            selectedSegmentModeWidget.__h3ConditionalCallbackBound = true;
            const originalCallback = selectedSegmentModeWidget.callback;
            selectedSegmentModeWidget.callback = (value) => {
                originalCallback?.call(selectedSegmentModeWidget, value);
                syncModeWidgets(this);
                repairNodeLayout(this);
                this.setDirtyCanvas?.(true, true);
                app.graph?.change?.();
            };
        }
        const resolutionWidget = getWidget(this, "resolution");
        if (resolutionWidget && !resolutionWidget.__h3ConditionalCallbackBound) {
            resolutionWidget.__h3ConditionalCallbackBound = true;
            const originalCallback = resolutionWidget.callback;
            resolutionWidget.callback = (value) => {
                originalCallback?.call(resolutionWidget, value);
                syncModeWidgets(this);
                repairNodeLayout(this);
                this.setDirtyCanvas?.(true, true);
            };
        }
        const advancedWidget = getWidget(this, "advanced");
        if (advancedWidget && !advancedWidget.__h3ConditionalCallbackBound) {
            advancedWidget.__h3ConditionalCallbackBound = true;
            const originalCallback = advancedWidget.callback;
            advancedWidget.callback = (value) => {
                originalCallback?.call(advancedWidget, value);
                syncModeWidgets(this);
                repairNodeLayout(this);
                this.setDirtyCanvas?.(true, true);
            };
        }
        const referenceMentionWidget = getWidget(this, "reference_mention_mode");
        if (referenceMentionWidget && !referenceMentionWidget.__h3ConditionalCallbackBound) {
            referenceMentionWidget.__h3ConditionalCallbackBound = true;
            const originalCallback = referenceMentionWidget.callback;
            referenceMentionWidget.callback = (value) => {
                originalCallback?.call(referenceMentionWidget, value);
                syncModeWidgets(this);
                renderEditorFromNode(this);
                requestMentionPreviewRefresh();
                repairNodeLayout(this);
                this.setDirtyCanvas?.(true, true);
            };
        }
        return result;
    };

    const originalConnectInput = nodeType.prototype.onConnectInput;
    nodeType.prototype.onConnectInput = function onConnectInputH3Easy(inputIndex, type, output, originNode, originSlot) {
        if (rejectsMixedMediaConnection(this, inputIndex, output, originNode, originSlot)) return false;
        return originalConnectInput?.apply(this, arguments);
    };

    const originalExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function onExecutedH3Easy(message) {
        const result = originalExecuted?.apply(this, arguments);
        applyRuntimePromptOptimization(this, message);
        return result;
    };

    const originalAdded = nodeType.prototype.onAdded;
    nodeType.prototype.onAdded = function onAddedH3Easy(graph) {
        const result = originalAdded?.apply(this, arguments);
        this.properties ||= {};
        ensureLinks(this);
        normalizeLinks(this);
        pruneTransportInputsFromNode(this, { force: true });
        normalizeLinks(this);
        localizeNodeInstance(this);
        bindPromptOptimizerWidgetCallbacks(this);
        // A workflow-tab activation is a restore operation. Its serialized or
        // previously stable size is already authoritative, so reapplying the
        // same widget visibility must not add/subtract rows again.
        syncModeWidgets(this, { adjustHeight: false });
        repairNodeLayout(this);
        return result;
    };

    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3Easy(info) {
        const configuredSize = Array.isArray(info?.size) && info.size.length >= 2
            ? [Number(info.size[0]), Number(info.size[1])]
            : null;
        const result = originalConfigure?.apply(this, arguments);
        if (configuredSize && configuredSize.every(Number.isFinite)) {
            // Adding/replacing the DOM prompt editor may make ComfyUI expand
            // the node to its calculated minimum. Restore the exact workflow
            // size after the editor is mounted instead of accumulating that
            // minimum every time the workflow tab is activated.
            this.__h3EditorStableSize = configuredSize;
        }
        if (info?.properties?.[PROMPT_DOC_PROP]) {
            this.properties ||= {};
            this.properties[PROMPT_DOC_PROP] = info.properties[PROMPT_DOC_PROP];
        }
        if (info?.properties?.[PROMPT_VIEW_PROP]) {
            this.properties ||= {};
            this.properties[PROMPT_VIEW_PROP] = info.properties[PROMPT_VIEW_PROP];
        }
        if (info?.properties?.[PROMPT_AUTO_MARKER_PROP]) {
            this.properties ||= {};
            this.properties[PROMPT_AUTO_MARKER_PROP] = info.properties[PROMPT_AUTO_MARKER_PROP];
        }
        if (info?.properties?.[PROMPT_OPTIMIZER_PROP]) {
            this.properties ||= {};
            const savedOptimizer = info.properties[PROMPT_OPTIMIZER_PROP];
            this.properties[PROMPT_OPTIMIZER_PROP] = {
                enabled: savedOptimizer.enabled,
                api_format: savedOptimizer.api_format,
                api_url: savedOptimizer.api_url,
                model: savedOptimizer.model,
                scene_guide: savedOptimizer.scene_guide,
                read_media: savedOptimizer.read_media,
                optimize_on_run: savedOptimizer.optimize_on_run,
            };
        }
        repairConfiguredWidgetValues(this, info);
        normalizeLinks(this);
        pruneTransportInputsFromNode(this, { force: true });
        normalizeLinks(this);
        localizeNodeInstance(this);
        bindPromptOptimizerWidgetCallbacks(this);
        syncModeWidgets(this, { adjustHeight: false });
        renderEditorFromNode(this);
        resetPromptHistory(this);
        syncEditorMode(this);
        requestMentionPreviewRefresh();
        installPromptEditorSoon(this);
        if (this.__h3Editor && restorePromptEditorStableSize(this)) repairNodeLayout(this);
        repairNodeLayout(this);
        const mediaInputIndex = getMediaInputIndex(this);
        if (mediaInputIndex >= 0 && this.inputs?.[mediaInputIndex]?.link != null) {
            enforceMediaInputExclusivity(this);
            scheduleNativeMediaConnectionConversion(this, mediaInputIndex);
        }
        return result;
    };

    const originalConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function onConnectionsChangeH3Easy(type, index, connected, linkInfo) {
        const result = originalConnectionsChange?.apply(this, arguments);
        const inputIndex = Number(index);
        const input = this.inputs?.[Number.isFinite(inputIndex) ? inputIndex : -1];
        if (String(input?.name || "") === "prompt") {
            syncPromptExternalConnectionState(this);
            globalThis.requestAnimationFrame?.(() => syncPromptExternalConnectionState(this));
        }
        if (connected && !this.__h3VirtualWireClearing && /^media(?:_\d+)?$/i.test(String(input?.name || ""))) {
            enforceMediaInputExclusivity(this);
            scheduleNativeMediaConnectionConversion(this, inputIndex, linkInfo);
        }
        return result;
    };

    const originalSerialize = nodeType.prototype.onSerialize;
    nodeType.prototype.onSerialize = function onSerializeH3Easy(info) {
        if (this.__h3Editor) syncPromptFromEditor(this, false);
        promptOptimizerState(this);
        const result = originalSerialize?.apply(this, arguments);
        if (info && this.properties?.[PROMPT_DOC_PROP]) {
            info.properties ||= {};
            info.properties[PROMPT_DOC_PROP] = this.properties[PROMPT_DOC_PROP];
        }
        if (info && this.properties?.[PROMPT_VIEW_PROP]) {
            info.properties ||= {};
            info.properties[PROMPT_VIEW_PROP] = this.properties[PROMPT_VIEW_PROP];
        }
        if (info && this.properties?.[PROMPT_AUTO_MARKER_PROP]) {
            info.properties ||= {};
            info.properties[PROMPT_AUTO_MARKER_PROP] = this.properties[PROMPT_AUTO_MARKER_PROP];
        }
        if (info && this.properties?.[PROMPT_OPTIMIZER_PROP]) {
            info.properties ||= {};
            info.properties[PROMPT_OPTIMIZER_PROP] = this.properties[PROMPT_OPTIMIZER_PROP];
        }
        return result;
    };

    const originalDraw = nodeType.prototype.onDrawForeground;
    nodeType.prototype.onDrawForeground = function onDrawForegroundH3Easy(ctx) {
        const result = originalDraw?.apply(this, arguments);
        if (!this.__h3Editor && !this.__h3PromptInstallPending && !this.__h3PromptInstallRetry) installPromptEditorSoon(this);
        return result;
    };

    const originalRemoved = nodeType.prototype.onRemoved;
    nodeType.prototype.onRemoved = function onRemovedH3Easy() {
        if (Array.isArray(this.size) && this.size.length >= 2) this.__h3EditorStableSize = [...this.size];
        cancelPromptOptimization(this);
        clearPromptOptimizerStatusTimers(this);
        closeMentionMenu(this);
        if (this.__h3PromptInstallRetry) clearTimeout(this.__h3PromptInstallRetry);
        this.__h3PromptInstallRetry = null;
        this.__h3PromptInstallPending = false;
        this.__h3PromptInstallAttempts = 0;
        this.__h3PromptInstallNextAt = 0;
        this.__h3EditorWrap?.remove?.();
        this.__h3Editor = null;
        this.__h3EditorWrap = null;
        this.__h3PromptEditorTools = null;
        this.__h3PromptViewButton = null;
        this.__h3RawPromptNeedsSync = false;
        this.__h3PromptOptimizerStatus = null;
        this.__h3PromptOptimizerStatusText = null;
        removePromptEditorWidgets(this);
        this.__h3DomWidget = null;
        return originalRemoved?.apply(this, arguments);
    };
}

function installLoaderNode(nodeType, nodeData) {
    if (nodeData?.name !== LOADER_CLASS) return;
    if (nodeType.prototype.__h3EasyLoaderInstalled) return;
    nodeType.prototype.__h3EasyLoaderInstalled = true;
    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3Loader() {
        const result = originalCreated?.apply(this, arguments);
        localizeNodeInstance(this);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3Loader(info) {
        const result = originalConfigure?.apply(this, arguments);
        localizeNodeInstance(this);
        return result;
    };
}

function installAdapterNode(nodeType, nodeData) {
    if (nodeData?.name !== ADAPTER_CLASS) return;
    if (nodeType.prototype.__h3EasyAdapterInstalled) return;
    nodeType.prototype.__h3EasyAdapterInstalled = true;
    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3Adapter() {
        const result = originalCreated?.apply(this, arguments);
        localizeNodeInstance(this);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3Adapter(info) {
        const result = originalConfigure?.apply(this, arguments);
        localizeNodeInstance(this);
        return result;
    };
}

function installOutputNode(nodeType, nodeData) {
    if (nodeData?.name !== OUTPUT_CLASS) return;
    if (nodeType.prototype.__h3EasyOutputInstalled) return;
    nodeType.prototype.__h3EasyOutputInstalled = true;
    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3Output() {
        const result = originalCreated?.apply(this, arguments);
        localizeNodeInstance(this);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3Output(info) {
        const result = originalConfigure?.apply(this, arguments);
        localizeNodeInstance(this);
        return result;
    };
}

function installSegmentRefineNode(nodeType, nodeData) {
    if (nodeData?.name !== SEGMENT_REFINE_CLASS) return;
    const installedMarker = "__h3SegmentRefineInstalled";
    if (nodeType.prototype[installedMarker]) return;
    nodeType.prototype[installedMarker] = true;

    const setup = (node, adjustHeight = true) => {
        if (!node) return;
        localizeNodeInstance(node);
        const mode = getWidget(node, "refine_mode");
        if (mode && !mode.__h3RefineModeBound) {
            mode.__h3RefineModeBound = true;
            const originalCallback = mode.callback;
            mode.callback = (value) => {
                originalCallback?.call(mode, value);
                syncSegmentRefineWidgets(node);
                node.setDirtyCanvas?.(true, true);
            };
        }
        const execution = getWidget(node, "refine_execution");
        if (execution && !execution.__h3RefineExecutionBound) {
            execution.__h3RefineExecutionBound = true;
            const originalCallback = execution.callback;
            execution.callback = (value) => {
                originalCallback?.call(execution, value);
                syncSegmentRefineWidgets(node);
                node.setDirtyCanvas?.(true, true);
            };
        }
        syncSegmentRefineWidgets(node, { adjustHeight });
    };

    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3SegmentRefine() {
        const result = originalCreated?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalAdded = nodeType.prototype.onAdded;
    nodeType.prototype.onAdded = function onAddedH3SegmentRefine(graph) {
        const result = originalAdded?.apply(this, arguments);
        setup(this, false);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3SegmentRefine(info) {
        const result = originalConfigure?.apply(this, arguments);
        setup(this, false);
        return result;
    };
}

function installSegmentStepNode(nodeType, nodeData) {
    if (nodeData?.name !== SEGMENT_STEP_CLASS) return;
    const installedMarker = "__h3SegmentStepInstalled";
    if (nodeType.prototype[installedMarker]) return;
    nodeType.prototype[installedMarker] = true;

    const setup = (node) => {
        if (!node) return;
        localizeNodeInstance(node);
    };

    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3SegmentStep() {
        const result = originalCreated?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalAdded = nodeType.prototype.onAdded;
    nodeType.prototype.onAdded = function onAddedH3SegmentStep(graph) {
        const result = originalAdded?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3SegmentStep(info) {
        const result = originalConfigure?.apply(this, arguments);
        setup(this);
        return result;
    };
}

function installSegmentSampleSetupNode(nodeType, nodeData) {
    if (nodeData?.name !== SEGMENT_SAMPLE_SETUP_CLASS) return;
    const installedMarker = "__h3SegmentSampleSetupInstalled";
    if (nodeType.prototype[installedMarker]) return;
    nodeType.prototype[installedMarker] = true;
    const setup = (node) => {
        if (!node) return;
        localizeNodeInstance(node);
    };
    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3SegmentSampleSetup() {
        const result = originalCreated?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalAdded = nodeType.prototype.onAdded;
    nodeType.prototype.onAdded = function onAddedH3SegmentSampleSetup(graph) {
        const result = originalAdded?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3SegmentSampleSetup(info) {
        const result = originalConfigure?.apply(this, arguments);
        setup(this);
        return result;
    };
}

function installSegmentCollectNode(nodeType, nodeData) {
    if (nodeData?.name !== SEGMENT_COLLECT_CLASS) return;
    const installedMarker = "__h3SegmentCollectInstalled";
    if (nodeType.prototype[installedMarker]) return;
    nodeType.prototype[installedMarker] = true;

    const setup = (node) => {
        if (!node) return;
        localizeNodeInstance(node);
    };
    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3SegmentCollect() {
        const result = originalCreated?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalAdded = nodeType.prototype.onAdded;
    nodeType.prototype.onAdded = function onAddedH3SegmentCollect(graph) {
        const result = originalAdded?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3SegmentCollect(info) {
        const result = originalConfigure?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function onConnectionsChangeH3SegmentCollect() {
        const result = originalConnectionsChange?.apply(this, arguments);
        localizeNodeInstance(this);
        return result;
    };
}

function mediaLoaderReadState(node) {
    const state = mediaLoaderState(node);
    return {
        images: [...state.images],
        audios: [...state.audios],
        videos: [...state.videos],
    };
}

function mediaLoaderWriteState(node, state) {
    const unique = (values) => [...new Set((Array.isArray(values) ? values : []).map((value) => String(value || "").trim()).filter(Boolean))];
    const value = JSON.stringify({
        images: unique(state.images).map((filename) => ({ filename })),
        audios: unique(state.audios).map((filename) => ({ filename })),
        videos: unique(state.videos).map((filename) => ({ filename })),
    });
    const widget = getWidget(node, "media_state");
    if (!widget) return;
    widget.value = value;
    if (widget._state) widget._state.value = value;
    node.properties ||= {};
    node.properties.media_loader_state = value;
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
    app.graph?.change?.();
    requestMentionPreviewRefresh();
}

function mediaLoaderHideStateWidget(widget) {
    if (!widget) return;
    if (!widget.__h3MediaLoaderHidden) {
        widget.__h3MediaLoaderHidden = true;
        widget.__h3MediaLoaderType = widget.type;
        widget.__h3MediaLoaderComputeSize = widget.computeSize;
    }
    widget.hidden = true;
    widget.type = "hidden";
    widget.computeSize = () => [0, -4];
    setWidgetOption(widget, "hidden", true);
    setWidgetOption(widget, "canvasOnly", true);
}

function formatMediaDuration(seconds) {
    const value = Number(seconds);
    if (!Number.isFinite(value) || value < 0) return "";
    const total = Math.max(0, Math.round(value));
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const remainder = total % 60;
    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
    }
    return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function mediaLoaderItemPreview(filename, type) {
    const thumb = document.createElement("div");
    thumb.className = `h3-media-loader-thumb is-${type}`;
    thumb.setAttribute("aria-hidden", "true");
    if (type === "audio") {
        const wave = document.createElement("span");
        wave.className = "h3-media-loader-audio-wave";
        for (const height of [38, 68, 100, 68, 38]) {
            const bar = document.createElement("i");
            bar.style.setProperty("--h3-audio-bar-height", `${height}%`);
            wave.append(bar);
        }
        thumb.append(wave);
        return thumb;
    }

    const previewUrl = mediaLoaderEntryUrl(filename, type);

    const media = document.createElement(type === "video" ? "video" : "img");
    media.alt = "";
    media.draggable = false;
    media.src = previewUrl;
    if (type === "video") {
        media.muted = true;
        media.playsInline = true;
        media.preload = "metadata";

        const duration = document.createElement("span");
        duration.className = "h3-media-loader-duration";
        duration.setAttribute("aria-hidden", "true");
        duration.hidden = true;
        media.addEventListener("loadedmetadata", () => {
            const label = formatMediaDuration(media.duration);
            if (!label) return;
            duration.textContent = label;
            duration.hidden = false;
        }, { once: true });
        thumb.append(duration);
    }
    media.addEventListener("error", () => {
        thumb.replaceChildren();
        const fallback = document.createElement("span");
        fallback.className = "h3-media-loader-preview-fallback";
        fallback.textContent = type === "video" ? "Video" : "Image";
        thumb.append(fallback);
    }, { once: true });
    thumb.append(media);
    return thumb;
}

function mediaLoaderFilenameFromUpload(response) {
    const name = String(response?.name || response?.filename || "").trim();
    if (!name) return "";
    const subfolder = String(response?.subfolder || "").replaceAll("\\", "/").replace(/^\/+|\/+$/g, "");
    return subfolder ? `${subfolder}/${name}` : name;
}

function mediaLoaderTypeForFile(file) {
    const mime = String(file?.type || "").toLowerCase();
    if (mime.startsWith("image/")) return "image";
    if (mime.startsWith("audio/")) return "audio";
    if (mime.startsWith("video/")) return "video";
    const filename = String(file?.name || "").toLowerCase();
    const extension = filename.includes(".") ? filename.slice(filename.lastIndexOf(".") + 1) : "";
    if (["png", "jpg", "jpeg", "webp", "gif", "bmp", "tif", "tiff", "avif", "heic"].includes(extension)) return "image";
    if (["mp3", "wav", "flac", "ogg", "oga", "m4a", "aac", "opus", "wma"].includes(extension)) return "audio";
    if (["mp4", "webm", "mov", "mkv", "avi", "m4v", "mpeg", "mpg", "wmv", "flv"].includes(extension)) return "video";
    return "";
}

async function mediaLoaderUploadOne(file) {
    if (!file) return "";
    const form = new FormData();
    const mime = String(file.type || "").toLowerCase();
    const fallbackExtension = mime.includes("/") ? mime.split("/").pop().replace(/[^a-z0-9]+/g, "") : "";
    const fallbackId = globalThis.crypto?.randomUUID?.().slice(0, 8) || Math.random().toString(36).slice(2, 10);
    const fallbackName = `pasted-media-${Date.now()}-${fallbackId}${fallbackExtension ? `.${fallbackExtension}` : ""}`;
    form.append("image", file, String(file.name || "").trim() || fallbackName);
    form.append("type", "input");
    const response = await api.fetchApi("/upload/image", { method: "POST", body: form });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.error || ("HTTP " + response.status));
    const filename = mediaLoaderFilenameFromUpload(data);
    if (!filename) throw new Error("Upload returned no filename");
    return filename;
}

async function mediaLoaderUploadFilesNow(node, fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    const state = mediaLoaderReadState(node);
    const pending = new Map(MEDIA_LOADER_GROUPS.map((group) => [group.type, state[group.key].length]));
    const errors = [];
    let unsupported = 0;
    let skippedFull = 0;
    let changed = false;
    for (const file of files) {
        const type = mediaLoaderTypeForFile(file);
        if (!type) {
            unsupported += 1;
            continue;
        }
        const group = MEDIA_LOADER_GROUPS.find((entry) => entry.type === type);
        if (!group) {
            unsupported += 1;
            continue;
        }
        if (Number.isFinite(group.max) && (pending.get(type) || 0) >= group.max) {
            skippedFull += 1;
            continue;
        }
        try {
            const filename = await mediaLoaderUploadOne(file);
            if (!state[group.key].includes(filename)) {
                state[group.key].push(filename);
                pending.set(type, (pending.get(type) || 0) + 1);
                changed = true;
            }
        } catch (error) {
            errors.push(String(file.name || type) + ": " + (error?.message || error));
        }
    }
    if (changed) {
        mediaLoaderWriteState(node, state);
        mediaLoaderRender(node);
    }
    const notices = [];
    if (unsupported) notices.push(TEXT.mediaLoaderUnsupported + " (" + unsupported + ")");
    if (skippedFull) notices.push(TEXT.mediaLoaderLimit + " (" + skippedFull + ")");
    if (errors.length) notices.push(TEXT.mediaLoaderUpload + ": " + errors.join("; "));
    if (notices.length) globalThis.alert?.(notices.join("\n"));
}

function mediaLoaderUploadFiles(node, fileList) {
    const files = Array.from(fileList || []);
    if (!node || !files.length) return Promise.resolve();
    // Clipboard, file-picker, and drag/drop uploads may arrive almost together.
    // Serialize them per node so a later batch cannot overwrite an earlier
    // batch's media_state snapshot while the files are still uploading.
    const previous = node.__h3MediaLoaderUploadQueue || Promise.resolve();
    const queued = Promise.resolve(previous)
        .catch(() => {})
        .then(() => mediaLoaderUploadFilesNow(node, files));
    node.__h3MediaLoaderUploadQueue = queued;
    const clear = () => {
        if (node.__h3MediaLoaderUploadQueue === queued) delete node.__h3MediaLoaderUploadQueue;
    };
    queued.then(clear, clear);
    return queued;
}

async function mediaLoaderUpload(node, input) {
    try {
        await mediaLoaderUploadFiles(node, input?.files || []);
    } finally {
        if (input) input.value = "";
    }
}

function mediaLoaderDataTransferHasFiles(dataTransfer) {
    if (!dataTransfer) return false;
    if (Array.from(dataTransfer.types || []).some((type) => String(type).toLowerCase() === "files")) return true;
    if (Array.from(dataTransfer.items || []).some((item) => item?.kind === "file")) return true;
    return Boolean(dataTransfer.files?.length);
}

function mediaLoaderFilesFromDataTransfer(dataTransfer) {
    const direct = Array.from(dataTransfer?.files || []).filter(Boolean);
    if (direct.length) return direct;
    return Array.from(dataTransfer?.items || [])
        .filter((item) => item?.kind === "file")
        .map((item) => item.getAsFile?.())
        .filter(Boolean);
}

function mediaLoaderClipboardMediaFiles(dataTransfer) {
    return mediaLoaderFilesFromDataTransfer(dataTransfer)
        .filter((file) => Boolean(mediaLoaderTypeForFile(file)));
}

function isStrictMediaLoaderNode(node) {
    if (!node) return false;
    if (node.constructor?.prototype?.__h3EasyMediaLoaderInstalled === true) return true;
    const candidates = [
        node.comfyClass,
        node.type,
        node.constructor?.comfyClass,
        node.constructor?.type,
        node.constructor?.nodeData?.name,
    ];
    return candidates.some((value) => value != null && String(value) === MEDIA_LOADER_CLASS);
}

function mediaLoaderSelectedNode() {
    const canvas = app.canvas;
    const graph = canvas?.graph || app.graph;
    const selected = (graph?._nodes || []).filter((node) => Boolean(
        node?.selected === true
        || node?.is_selected === true
        || canvas?.selectedItems?.has?.(node)
        || canvas?.selected_nodes?.[node?.id]
    ));
    const current = canvas?.current_node;
    if (!selected.length && current?.is_selected) selected.push(current);
    if (selected.length !== 1 || !isStrictMediaLoaderNode(selected[0])) return null;
    return selected[0];
}

function mediaLoaderPasteTargetsEditor(event) {
    const path = typeof event?.composedPath === "function" ? event.composedPath() : [event?.target];
    return path.some((target) => {
        if (!(target instanceof Element)) return false;
        if (target.matches?.("input, textarea, select, [contenteditable], [role='textbox']")) return true;
        return Boolean(target.closest?.("input, textarea, select, [contenteditable], [role='textbox']"));
    });
}

function mediaLoaderOwnsPasteFocus(node, event) {
    const panel = node?.__h3MediaLoaderPanel;
    const canvas = app.canvas?.canvas;
    const owns = (target) => Boolean(
        !target
        || target === document
        || target === document.body
        || target === document.documentElement
        || target === canvas
        || (target instanceof Node && panel?.contains?.(target))
    );
    return owns(event?.target) && owns(document.activeElement);
}

function installMediaLoaderClipboardPaste() {
    if (document.__h3MediaLoaderClipboardPasteInstalled) return;
    document.__h3MediaLoaderClipboardPasteInstalled = true;
    document.addEventListener("paste", (event) => {
        if (event.defaultPrevented || event.shiftKey || mediaLoaderPasteTargetsEditor(event)) return;
        const selectedText = String(globalThis.getSelection?.()?.toString?.() || "").trim();
        if (selectedText) return;
        const node = mediaLoaderSelectedNode();
        if (!node || !mediaLoaderOwnsPasteFocus(node, event)) return;
        const files = mediaLoaderClipboardMediaFiles(event.clipboardData);
        if (!files.length) return;
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation?.();
        mediaLoaderUploadFiles(node, files).catch((error) => console.error("Media Loader clipboard paste failed", error));
    }, true);
}

function installMediaLoaderFileDrop(node, panel) {
    const stopExternalFileEvent = (event) => {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation?.();
        if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
    };
    panel.addEventListener("dragenter", (event) => {
        if (!mediaLoaderDataTransferHasFiles(event.dataTransfer)) return;
        mediaLoaderInternalDrag = null;
        stopExternalFileEvent(event);
        panel.classList.add("is-file-drop-target");
    });
    panel.addEventListener("dragover", (event) => {
        if (!mediaLoaderDataTransferHasFiles(event.dataTransfer)) return;
        stopExternalFileEvent(event);
        panel.classList.add("is-file-drop-target");
    });
    panel.addEventListener("dragleave", (event) => {
        if (!panel.classList.contains("is-file-drop-target")) return;
        const related = event.relatedTarget;
        if (related instanceof Node && panel.contains(related)) return;
        panel.classList.remove("is-file-drop-target");
    });
    panel.addEventListener("drop", (event) => {
        if (!mediaLoaderDataTransferHasFiles(event.dataTransfer)) return;
        stopExternalFileEvent(event);
        panel.classList.remove("is-file-drop-target");
        const files = mediaLoaderFilesFromDataTransfer(event.dataTransfer);
        mediaLoaderUploadFiles(node, files).catch((error) => console.error("Media Loader file drop failed", error));
    });
}

function mediaLoaderUpdateCard(card, group, filename, index) {
    card.dataset.index = String(index);
    card.dataset.filename = filename;
    card.dataset.mediaType = group.type;
    card.title = filename;
    card.querySelector(".h3-media-loader-tag").textContent = String(index + 1);
    const label = card.querySelector(".h3-media-loader-label");
    label.textContent = filename.split(/[\\/]/).pop() || filename;
    label.title = filename;
}

function mediaLoaderCreateCard(node, group, filename) {
    const card = document.createElement("div");
    card.className = `h3-media-loader-card is-${group.type}`;
    card.draggable = true;
    card.tabIndex = 0;
    card.append(mediaLoaderItemPreview(filename, group.type));

    const tag = document.createElement("span");
    tag.className = "h3-media-loader-tag";
    const label = document.createElement("span");
    label.className = "h3-media-loader-label";
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "h3-media-loader-remove";
    remove.textContent = "\u00d7";
    remove.title = TEXT.mediaLoaderRemove;
    remove.setAttribute("aria-label", TEXT.mediaLoaderRemove);
    remove.addEventListener("pointerdown", (event) => event.stopPropagation());
    remove.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const index = Number(card.dataset.index);
        if (!Number.isInteger(index)) return;
        const next = mediaLoaderReadState(node);
        next[group.key].splice(index, 1);
        mediaLoaderWriteState(node, next);
        mediaLoaderSyncGroup(node, group, next);
        mediaLoaderResize(node);
    });
    card.append(tag, label, remove);

    card.addEventListener("dragstart", (event) => {
        mediaLoaderInternalDrag = { node, groupType: group.type, card };
        event.dataTransfer?.setData(MEDIA_LOADER_INTERNAL_DRAG_TYPE, group.type);
        event.dataTransfer?.setData("text/plain", String(card.dataset.index));
        if (event.dataTransfer) event.dataTransfer.effectAllowed = "move";
        card.classList.add("is-dragging");
    });
    card.addEventListener("dragend", () => {
        if (mediaLoaderInternalDrag?.card === card) mediaLoaderInternalDrag = null;
        card.classList.remove("is-dragging");
        card.parentElement?.querySelectorAll(".is-drop-target").forEach((item) => item.classList.remove("is-drop-target"));
    });
    card.addEventListener("dragover", (event) => {
        if (mediaLoaderDataTransferHasFiles(event.dataTransfer)) return;
        const drag = mediaLoaderInternalDrag;
        if (!drag || drag.node !== node || drag.groupType !== group.type) return;
        event.preventDefault();
        event.stopPropagation();
        if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
        card.classList.add("is-drop-target");
    });
    card.addEventListener("dragleave", () => card.classList.remove("is-drop-target"));
    card.addEventListener("drop", (event) => {
        if (mediaLoaderDataTransferHasFiles(event.dataTransfer)) return;
        const drag = mediaLoaderInternalDrag;
        if (!drag || drag.node !== node || drag.groupType !== group.type) return;
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation?.();
        card.classList.remove("is-drop-target");
        const from = Number(drag.card?.dataset?.index);
        const index = Number(card.dataset.index);
        mediaLoaderInternalDrag = null;
        if (!Number.isInteger(from) || !Number.isInteger(index) || from === index) return;
        const next = mediaLoaderReadState(node);
        // The entire target card is the hit area. Swap cards directly instead
        // of requiring the pointer to land on a particular half of the tile.
        [next[group.key][from], next[group.key][index]] = [
            next[group.key][index],
            next[group.key][from],
        ];
        mediaLoaderWriteState(node, next);
        mediaLoaderSyncGroup(node, group, next);
    });
    return card;
}

function mediaLoaderSyncGroup(node, group, state = mediaLoaderReadState(node)) {
    const panel = node?.__h3MediaLoaderPanel;
    const list = panel?.querySelector?.(`[data-media-loader-section="${group.type}"] .h3-media-loader-list`);
    if (!list) return;
    const entries = state[group.key] || [];
    const cards = new Map([...list.querySelectorAll(".h3-media-loader-card")]
        .map((card) => [card.dataset.filename, card]));
    list.querySelectorAll(".h3-media-loader-empty").forEach((empty) => empty.remove());

    for (const [filename, card] of cards) {
        if (!entries.includes(filename)) card.remove();
    }
    if (!entries.length) {
        const empty = document.createElement("div");
        empty.className = "h3-media-loader-empty";
        empty.textContent = TEXT.mediaLoaderEmpty;
        list.append(empty);
        return;
    }
    entries.forEach((filename, index) => {
        const card = cards.get(filename) || mediaLoaderCreateCard(node, group, filename);
        mediaLoaderUpdateCard(card, group, filename, index);
        // Appending an existing card only moves it. Its image/video element stays
        // alive, so reordering another group cannot reload or flash previews.
        list.append(card);
    });
}

function mediaLoaderRender(node) {
    const panel = node?.__h3MediaLoaderPanel;
    if (!panel) return;
    const state = mediaLoaderReadState(node);
    const total = MEDIA_LOADER_GROUPS.reduce((sum, group) => sum + (state[group.key]?.length || 0), 0);
    const capacities = MEDIA_LOADER_GROUPS.map((group) => Number(group.max));
    const finiteCapacity = capacities.every((capacity) => Number.isFinite(capacity));
    if (node.__h3MediaLoaderCount) node.__h3MediaLoaderCount.textContent = finiteCapacity
        ? String(total) + "/" + String(capacities.reduce((sum, capacity) => sum + capacity, 0))
        : String(total);
    for (const group of MEDIA_LOADER_GROUPS) mediaLoaderSyncGroup(node, group, state);
    mediaLoaderResize(node);
}

function mediaLoaderResize(node) {
    const panel = node?.__h3MediaLoaderPanel;
    const domWidget = node?.__h3MediaLoaderWidget;
    if (!panel || !domWidget) return;
    const measure = () => {
        // Measure the natural content while the panel is not filling a previously
        // stretched DOM slot. The measured value is only the minimum, never a cap.
        panel.style.height = "auto";
        panel.style.minHeight = "0px";
        panel.style.maxHeight = "none";
        panel.style.flex = "0 0 auto";
        const contentHeight = Math.max(1, Math.ceil(panel.scrollHeight || panel.getBoundingClientRect?.().height || 0));
        const widgetHeight = Math.max(1, contentHeight + 8);
        node.__h3MediaLoaderMinWidgetHeight = widgetHeight;

        // Restore the fill layout after measuring. LiteGraph gives a DOM widget
        // its extra height through computedHeight when the user resizes the node.
        panel.style.height = "100%";
        panel.style.minHeight = `${contentHeight}px`;
        panel.style.maxHeight = "100%";
        panel.style.flex = "1 1 auto";
        domWidget.options ||= {};
        const getWidgetHeight = () => Math.max(1, Number(node.__h3MediaLoaderMinWidgetHeight) || widgetHeight);
        // No fixed computeSize or maxHeight here. This is the same growable DOM
        // widget contract used by the batch text-card node: extra node height is
        // allocated to the panel instead of becoming an empty node background.
        try {
            delete domWidget.computeSize;
        } catch {
            domWidget.computeSize = undefined;
        }
        domWidget.computeLayoutSize = () => {
            const height = getWidgetHeight();
            return { minHeight: height, maxHeight: undefined, minWidth: 0 };
        };
        domWidget.options.getMinHeight = getWidgetHeight;
        delete domWidget.options.getMaxHeight;
        delete domWidget.options.getHeight;
        const currentWidth = Number(node.size?.[0]) || 300;
        // Compute the fixed node chrome independently. Only grow a too-small
        // node to its content minimum; never shrink a user-resized node.
        const wasHidden = domWidget.hidden;
        const wasType = domWidget.type;
        let fixedSize = null;
        try {
            domWidget.hidden = true;
            domWidget.type = "hidden";
            fixedSize = node.computeSize?.();
        } finally {
            domWidget.hidden = wasHidden;
            domWidget.type = wasType;
        }
        if (Array.isArray(fixedSize) && typeof node.setSize === "function") {
            const width = Math.max(currentWidth, 320);
            const minimumHeight = Math.max(1, Math.ceil((fixedSize[1] || 0) + widgetHeight + 4));
            const currentHeight = Number(node.size?.[1]) || 0;
            if (currentHeight + 1 < minimumHeight) {
                node.setSize([width, minimumHeight]);
                if (Array.isArray(node.size)) {
                    node.size[0] = width;
                    node.size[1] = minimumHeight;
                }
            }
        }
        node._widgetSlotsDirty = true;
        node.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
    };
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(measure);
    else setTimeout(measure, 0);
}

function installMediaLoaderStyles() {
    let style = document.getElementById("h3-media-loader-styles");
    if (!style) {
        style = document.createElement("style");
        style.id = "h3-media-loader-styles";
        document.head.append(style);
    }
    style.textContent = `
      .h3-media-loader-panel { position:relative; display:flex; flex-direction:column; gap:8px; width:100%; height:100%; min-height:0; max-height:100%; flex:1 1 auto; align-self:stretch; box-sizing:border-box; padding:8px; border:1px solid #111; border-radius:6px; background:#222; color:var(--h3-native-widget-text,#ddd); font-size:12px; overflow:hidden; transition:border-color .14s ease, box-shadow .14s ease; }
      .h3-media-loader-panel.is-file-drop-target { border-color:#718ca6; box-shadow:inset 0 0 0 1px rgba(113,140,166,.34); }
      .h3-media-loader-panel.is-file-drop-target::after { content:attr(data-drop-label); position:absolute; inset:8px; z-index:20; display:flex; align-items:center; justify-content:center; box-sizing:border-box; border:1px dashed rgba(146,177,207,.62); border-radius:5px; background:rgba(25,28,32,.9); color:#d7e2ec; font-size:12px; font-weight:600; letter-spacing:.01em; pointer-events:none; }
      .h3-media-loader-toolbar { display:flex; align-items:center; justify-content:space-between; gap:8px; min-height:28px; padding-bottom:1px; }
      .h3-media-loader-heading { display:flex; align-items:baseline; gap:7px; min-width:0; }
      .h3-media-loader-title { font-weight:650; color:#eee; }
      .h3-media-loader-count { color:#888; font-size:10px; font-variant-numeric:tabular-nums; }
      .h3-media-loader-upload { border:1px solid #444; border-radius:4px; background:#2a2a2a; color:#ddd; padding:4px 8px; cursor:pointer; font-size:11px; line-height:1.35; }
      .h3-media-loader-upload:hover { background:#333; border-color:#666; color:#fff; }
      .h3-media-loader-groups { display:flex; flex:1 1 auto; flex-direction:column; gap:8px; min-width:0; min-height:0; }
      .h3-media-loader-section { min-width:0; border-top:1px solid #353535; padding-top:7px; }
      .h3-media-loader-header { display:flex; align-items:center; justify-content:space-between; gap:6px; margin:0 0 5px; color:#bdbdbd; font-size:10px; font-weight:650; line-height:1.2; }
      .h3-media-loader-list { display:grid; grid-template-columns:repeat(auto-fill,76px); gap:8px; min-height:26px; }
      .h3-media-loader-empty { display:flex; grid-column:1 / -1; align-items:center; min-height:26px; padding:0 5px; border:1px dashed #3c3c3c; border-radius:4px; color:#6f6f6f; font-size:10px; }
      .h3-media-loader-card { position:relative; display:block; min-width:0; aspect-ratio:1; overflow:visible; border:1px solid #393939; border-radius:5px; background:#161616; cursor:grab; outline:none; transition:border-color .14s ease, background .14s ease, transform .14s ease; }
      .h3-media-loader-card:hover, .h3-media-loader-card:focus-visible { border-color:#6b829b; background:#1a1d20; }
      .h3-media-loader-card:active { cursor:grabbing; }
      .h3-media-loader-card.is-dragging { opacity:.4; transform:scale(.96); }
      .h3-media-loader-card.is-drop-target { border-color:#7ea6cb; box-shadow:0 0 0 1px rgba(126,166,203,.45); }
      .h3-media-loader-thumb { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; overflow:hidden; border-radius:4px; background:#101010; }
      .h3-media-loader-thumb.is-audio { background:#10201d; }
      .h3-media-loader-thumb.is-audio::before { content:""; position:absolute; inset:7px; border:1px solid rgba(70,206,182,.18); border-radius:3px; pointer-events:none; }
      .h3-media-loader-thumb > img, .h3-media-loader-thumb > video { position:relative; z-index:1; width:100%; height:100%; display:block; object-fit:contain; object-position:center; }
      .h3-media-loader-audio-wave { position:relative; z-index:1; display:flex; align-items:center; justify-content:center; gap:4px; width:48%; height:42%; }
      .h3-media-loader-audio-wave i { display:block; width:4px; height:var(--h3-audio-bar-height); border-radius:3px; background:#35cdb9; box-shadow:0 0 0 1px rgba(0,0,0,.08); }
      .h3-media-loader-preview-fallback { color:#777; font-size:10px; }
      .h3-media-loader-card.is-audio::after { content:""; position:absolute; inset:48% 0 0; border-radius:0 0 4px 4px; pointer-events:none; background:linear-gradient(180deg,transparent,rgba(0,0,0,.86)); }
      .h3-media-loader-tag { position:absolute; bottom:4px; left:4px; z-index:2; min-width:12px; padding:2px 4px; border-radius:3px; background:rgba(8,8,8,.7); color:#e7e7e7; font-size:9px; line-height:1.15; text-align:center; font-variant-numeric:tabular-nums; pointer-events:none; }
      .h3-media-loader-duration { position:absolute; right:4px; bottom:4px; z-index:2; padding:2px 4px; border-radius:3px; background:rgba(8,8,8,.35); color:#f1f1f1; font-size:9px; line-height:1.15; font-variant-numeric:tabular-nums; text-shadow:0 1px 2px rgba(0,0,0,.45); pointer-events:none; }
      .h3-media-loader-label { position:absolute; right:4px; bottom:4px; left:25px; z-index:1; overflow:hidden; color:#eee; font-size:9px; line-height:1.2; text-overflow:ellipsis; white-space:nowrap; pointer-events:none; }
      .h3-media-loader-card.is-image .h3-media-loader-label, .h3-media-loader-card.is-video .h3-media-loader-label { display:none; }
      .h3-media-loader-remove { position:absolute; top:-7px; right:-7px; z-index:3; width:17px; height:17px; padding:0; border:2px solid #222; border-radius:50%; background:#3b434a; color:#f1f1f1; cursor:pointer; display:flex; align-items:center; justify-content:center; font-family:Arial,sans-serif; font-size:15px; font-weight:400; line-height:1; opacity:0; visibility:hidden; transform:scale(.82); transition:opacity .15s ease, visibility .15s ease, transform .15s ease, background .15s ease; }
      .h3-media-loader-card:hover .h3-media-loader-remove, .h3-media-loader-card:focus-within .h3-media-loader-remove { opacity:1; visibility:visible; transform:scale(1); }
      .h3-media-loader-remove:hover { background:#8b4242; color:#fff; }
    `;
}

function installMediaLoaderNode(nodeType, nodeData) {
    if (nodeData?.name !== MEDIA_LOADER_CLASS) return;
    if (nodeType.prototype.__h3EasyMediaLoaderInstalled) return;
    nodeType.prototype.__h3EasyMediaLoaderInstalled = true;
    installMediaLoaderStyles();
    const originalPasteFiles = nodeType.prototype.pasteFiles;
    nodeType.prototype.pasteFiles = function pasteFilesH3MediaLoader(files) {
        const list = Array.from(files || []);
        if (!list.length && typeof originalPasteFiles === "function") return originalPasteFiles.apply(this, arguments);
        return mediaLoaderUploadFiles(this, list);
    };
    const setup = (node) => {
        if (!node || node.__h3MediaLoaderSetup || typeof node.addDOMWidget !== "function") return;
        node.__h3MediaLoaderSetup = true;
        localizeNodeInstance(node);
        const stateWidget = getWidget(node, "media_state");
        mediaLoaderHideStateWidget(stateWidget);
        const panel = document.createElement("div");
        panel.className = "h3-media-loader-panel";
        panel.dataset.dropLabel = TEXT.mediaLoaderDrop;
        installMediaLoaderFileDrop(node, panel);
        panel.addEventListener("pointerdown", (event) => event.stopPropagation());
        panel.addEventListener("wheel", (event) => {
            // This node has no wheel-scrolling surface. Forward every wheel event
            // to LiteGraph so the canvas keeps its normal zoom behavior.
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation?.();
            app.canvas?.processMouseWheel?.(event);
        }, { passive: false, capture: true });
        const toolbar = document.createElement("div");
        toolbar.className = "h3-media-loader-toolbar";
        const heading = document.createElement("div");
        heading.className = "h3-media-loader-heading";
        const title = document.createElement("span");
        title.className = "h3-media-loader-title";
        title.textContent = TEXT.mediaLoaderAll;
        const count = document.createElement("span");
        count.className = "h3-media-loader-count";
        heading.append(title, count);
        const upload = document.createElement("button");
        upload.type = "button";
        upload.className = "h3-media-loader-upload";
        upload.textContent = TEXT.mediaLoaderUpload;
        upload.title = TEXT.mediaLoaderUpload;
        upload.addEventListener("click", () => {
            const input = document.createElement("input");
            input.type = "file";
            input.accept = "image/*,audio/*,video/*";
            input.multiple = true;
            input.addEventListener("change", () => {
                mediaLoaderUpload(node, input).catch((error) => console.error("Media Loader upload failed", error));
            }, { once: true });
            input.click();
        });
        toolbar.append(heading, upload);
        const groups = document.createElement("div");
        groups.className = "h3-media-loader-groups";
        panel.append(toolbar, groups);
        node.__h3MediaLoaderCount = count;
        for (const group of MEDIA_LOADER_GROUPS) {
            const section = document.createElement("section");
            section.className = "h3-media-loader-section";
            section.dataset.mediaLoaderSection = group.type;
            const header = document.createElement("div");
            header.className = "h3-media-loader-header";
            const sectionTitle = document.createElement("span");
            sectionTitle.textContent = group.type === "image" ? TEXT.mediaLoaderImages : group.type === "audio" ? TEXT.mediaLoaderAudio : TEXT.mediaLoaderVideos;
            header.append(sectionTitle);
            const list = document.createElement("div");
            list.className = "h3-media-loader-list";
            section.append(header, list);
            groups.append(section);
        }
        node.__h3MediaLoaderPanel = panel;
        const domWidget = node.addDOMWidget("h3_media_loader", "h3_media_loader", panel, {
            getValue: () => String(getWidget(node, "media_state")?.value || ""),
            setValue: (value) => { const widget = getWidget(node, "media_state"); if (widget) widget.value = String(value || ""); mediaLoaderRender(node); },
            serialize: false,
            getMinHeight: () => Math.max(1, Number(node.__h3MediaLoaderMinWidgetHeight) || 48),
            afterResize: () => mediaLoaderResize(node),
        });
        if (!domWidget) return;
        domWidget.serialize = false;
        setWidgetOption(domWidget, "serialize", false);
        node.__h3MediaLoaderWidget = domWidget;
        mediaLoaderRender(node);
        mediaLoaderResize(node);
        repairNodeLayout(node);
    };
    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3MediaLoader() { const result = originalCreated?.apply(this, arguments); setup(this); return result; };
    const originalAdded = nodeType.prototype.onAdded;
    nodeType.prototype.onAdded = function onAddedH3MediaLoader(graph) { const result = originalAdded?.apply(this, arguments); setup(this); mediaLoaderRender(this); return result; };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3MediaLoader(info) { const result = originalConfigure?.apply(this, arguments); setup(this); mediaLoaderRender(this); return result; };
    const originalResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function onResizeH3MediaLoader(size) {
        const result = originalResize?.apply(this, arguments);
        if (this.__h3MediaLoaderSetup) mediaLoaderResize(this);
        return result;
    };
}

function installMediaBridgeNode(nodeType, nodeData) {
    if (nodeData?.name !== MEDIA_BRIDGE_CLASS) return;
    trimMediaBridgeNodeDataInputs(nodeData);
    if (nodeType?.nodeData && nodeType.nodeData !== nodeData) trimMediaBridgeNodeDataInputs(nodeType.nodeData);
    if (nodeType?.prototype?.constructor?.nodeData && nodeType.prototype.constructor.nodeData !== nodeData) {
        trimMediaBridgeNodeDataInputs(nodeType.prototype.constructor.nodeData);
    }
    if (nodeType.prototype.__h3EasyMediaBridgeInstalled) return;
    nodeType.prototype.__h3EasyMediaBridgeInstalled = true;

    const setup = (node) => {
        if (!node || node.__h3MediaBridgeSetup) return;
        node.__h3MediaBridgeSetup = true;
        localizeNodeInstance(node);
        for (const group of MEDIA_BRIDGE_GROUPS) {
            const widget = getWidget(node, group.count);
            if (!widget) continue;
            clampMediaBridgeWidgetValue(widget, group, widget.value);
            const original = widget.callback;
            widget.callback = function onMediaBridgeCountChanged(value) {
                original?.apply(this, arguments);
                clampMediaBridgeWidgetValue(widget, group, value);
                updateMediaBridgeWidgets(node);
            };
        }
        updateMediaBridgeWidgets(node, { force: true });
    };

    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3EasyMediaBridge() {
        const result = originalCreated?.apply(this, arguments);
        setup(this);
        return result;
    };

    const originalAdded = nodeType.prototype.onAdded;
    nodeType.prototype.onAdded = function onAddedH3EasyMediaBridge(graph) {
        const result = originalAdded?.apply(this, arguments);
        setup(this);
        updateMediaBridgeWidgets(this);
        return result;
    };

    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3EasyMediaBridge(info) {
        const result = originalConfigure?.apply(this, arguments);
        setup(this);
        updateMediaBridgeWidgets(this, { force: true });
        return result;
    };
}

function installMediaSplitterNode(nodeType, nodeData) {
    if (nodeData?.name !== MEDIA_SPLITTER_CLASS) return;
    trimMediaSplitterNodeDataOutputs(nodeData);
    if (nodeType?.nodeData && nodeType.nodeData !== nodeData) trimMediaSplitterNodeDataOutputs(nodeType.nodeData);
    if (nodeType?.prototype?.constructor?.nodeData && nodeType.prototype.constructor.nodeData !== nodeData) {
        trimMediaSplitterNodeDataOutputs(nodeType.prototype.constructor.nodeData);
    }
    if (nodeType.prototype.__h3EasyMediaSplitterInstalled) return;
    nodeType.prototype.__h3EasyMediaSplitterInstalled = true;

    const setup = (node) => {
        if (!node || node.__h3MediaSplitterSetup) return;
        node.__h3MediaSplitterSetup = true;
        localizeNodeInstance(node);
        for (const group of MEDIA_SPLITTER_GROUPS) {
            const widget = getWidget(node, group.count);
            if (!widget) continue;
            clampMediaSplitterWidgetValue(widget, group, widget.value);
            const original = widget.callback;
            widget.callback = function onMediaSplitterCountChanged(value) {
                original?.apply(this, arguments);
                clampMediaSplitterWidgetValue(widget, group, value);
                updateMediaSplitterWidgets(node);
            };
        }
        updateMediaSplitterWidgets(node, { force: true });
    };

    const originalCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function onNodeCreatedH3EasyMediaSplitter() {
        const result = originalCreated?.apply(this, arguments);
        setup(this);
        return result;
    };
    const originalAdded = nodeType.prototype.onAdded;
    nodeType.prototype.onAdded = function onAddedH3EasyMediaSplitter(graph) {
        const result = originalAdded?.apply(this, arguments);
        setup(this);
        updateMediaSplitterWidgets(this);
        return result;
    };
    const originalConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function onConfigureH3EasyMediaSplitter(info) {
        const result = originalConfigure?.apply(this, arguments);
        setup(this);
        updateMediaSplitterWidgets(this, { force: true });
        return result;
    };
}

function install() {
    if (installed) return;
    installed = true;
    patchCanvas();
    patchGraphToPrompt();
    patchEditorKeyHandling();
    installNativeThemeWatcher();
    installMediaLoaderClipboardPaste();
    for (const delay of [0, 100, 500, 1200]) setTimeout(() => patchCanvas(), delay);
    setTimeout(() => installQuickCreateCapture(app.canvas), 0);
    setTimeout(() => installQuickCreateCapture(app.canvas), 250);
    document.addEventListener("pointerdown", (event) => {
        for (const node of app.graph?._nodes || []) {
            const state = node?.__h3MentionMenu;
            if (!state) continue;
            if (state.element?.contains?.(event.target) || node.__h3EditorWrap?.contains?.(event.target)) continue;
            closeMentionMenu(node);
        }
    }, true);
    const style = document.createElement("style");
    style.textContent = `
      .h3-prompt-editor-wrap {
        position: relative; display: block; width: 100%; height: 100%; min-width: 0; min-height: 0; max-height: 100%;
        box-sizing: border-box; padding: 0; border-radius: var(--h3-native-widget-radius, 0); overflow: hidden; contain: size layout paint;
      }
      .h3-prompt-editor {
        --h3-prompt-text-size: var(--h3-native-widget-text-size, var(--comfy-textarea-font-size, 12px));
        display: block; width: 100%; height: 100%; min-width: 0; min-height: 0; max-height: 100%; box-sizing: border-box;
        padding: var(--h3-native-widget-padding, 2px);
        padding-bottom: calc(var(--h3-native-widget-padding, 2px) + 24px); overflow-y: auto; overflow-x: hidden; overscroll-behavior: contain;
        white-space: pre-wrap; overflow-wrap: anywhere; border: 0; border-radius: var(--h3-native-widget-radius, 0); outline: none;
        resize: none; background-color: var(--h3-native-widget-bg, var(--comfy-input-bg, #222));
        color: var(--h3-native-widget-text, var(--input-text, #ddd)); caret-color: var(--h3-native-widget-text, var(--input-text, #ddd));
        font-family: Consolas, "Courier New", monospace; font-size: var(--h3-prompt-text-size); font-weight: 400;
        font-style: normal; line-height: var(--h3-native-widget-line-height, normal); letter-spacing: 0;
      }
      .h3-prompt-editor :not(.h3-mention-chip):not(.h3-mention-chip *):not(.h3-dialogue-block):not(.h3-dialogue-block *) {
        font-family: Consolas, "Courier New", monospace !important; font-size: var(--h3-prompt-text-size) !important;
        font-weight: 400 !important; font-style: normal !important; line-height: var(--h3-native-widget-line-height, normal) !important; letter-spacing: 0 !important;
      }
      .h3-prompt-editor-wrap.h3-native-vue-nodes .h3-prompt-editor:focus {
        box-shadow: 0 0 0 1px var(--h3-native-widget-focus, var(--h3-native-widget-outline, rgba(255,255,255,.18)));
      }
      .h3-prompt-editor-wrap.is-external .h3-prompt-editor {
        color: var(--h3-native-widget-muted, rgba(255,255,255,.42)); caret-color: transparent; cursor: not-allowed; opacity: .72;
      }
      .h3-prompt-editor-wrap.is-external .h3-prompt-editor:focus { box-shadow: none; }
      .h3-prompt-editor-wrap.is-loading .h3-prompt-editor { cursor: wait; opacity: .72; }
      .h3-prompt-editor:empty::before { content: attr(data-placeholder); color: var(--h3-native-widget-muted, rgba(255,255,255,.38)); pointer-events: none; }
      .h3-prompt-editor-status {
        position: absolute; left: 12px; bottom: 4px; z-index: 3; display: inline-flex; align-items: center; gap: 5px; max-width: calc(100% - 92px);
        overflow: hidden; color: var(--h3-native-widget-text, rgba(255,255,255,.78)); pointer-events: auto; user-select: none;
        font: 600 9px/18px Consolas, "Courier New", monospace; letter-spacing: 0; white-space: nowrap; text-overflow: ellipsis;
      }
      .h3-prompt-editor-status[hidden] { display: none !important; }
      .h3-prompt-editor-status-spinner {
        display: inline-block; width: 8px; height: 8px; flex: 0 0 8px; box-sizing: border-box; border: 1px solid currentColor; border-radius: 50%; opacity: .56;
      }
      .h3-prompt-editor-status-text { min-width: 0; overflow: hidden; text-overflow: ellipsis; opacity: .56; }
      .h3-prompt-editor-status.is-loading .h3-prompt-editor-status-spinner { border-right-color: transparent; animation: h3-prompt-status-spin .72s linear infinite; }
      .h3-prompt-editor-status-cancel {
        appearance: none; display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; flex: 0 0 16px; padding: 0;
        border: 1px solid transparent; border-radius: 3px; outline: none; background: transparent; color: inherit; opacity: .5; cursor: pointer;
        font: 600 7px/1 Consolas, "Courier New", monospace; letter-spacing: 0; transition: opacity .12s ease, background-color .12s ease, border-color .12s ease;
      }
      .h3-prompt-editor-status-cancel:hover, .h3-prompt-editor-status-cancel:focus-visible {
        opacity: .82; background: rgba(255,255,255,.045); border-color: rgba(255,255,255,.1);
      }
      @keyframes h3-prompt-status-spin { to { transform: rotate(360deg); } }
      .h3-prompt-editor-tools {
        position: absolute; right: 14px; bottom: 4px; z-index: 3; display: flex; align-items: center; gap: 3px; pointer-events: auto;
      }
      .h3-prompt-editor-tool {
        appearance: none; display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 18px; padding: 0;
        border: 1px solid transparent; border-radius: 4px; outline: none; background: transparent; box-shadow: none;
        color: var(--h3-native-widget-text, rgba(255,255,255,.78)); opacity: .34; cursor: pointer; user-select: none;
        font: 600 9px/1 Consolas, "Courier New", monospace; letter-spacing: -.4px; transition: opacity .12s ease, background-color .12s ease, border-color .12s ease, color .12s ease;
      }
      .h3-prompt-editor-tool:hover, .h3-prompt-editor-tool:focus-visible {
        opacity: .62; background: rgba(255,255,255,.045); border-color: rgba(255,255,255,.1);
      }
      .h3-prompt-editor-tool.is-active {
        opacity: .5; color: rgba(190,255,244,.88); background: rgba(0,226,187,.04); border-color: rgba(0,226,187,.12);
      }
      .h3-prompt-editor-tool.is-configured { opacity: .46; }
      .h3-prompt-editor-tool.is-loading { opacity: .64; animation: h3-prompt-tool-pulse .8s ease-in-out infinite alternate; }
      .h3-prompt-editor-tool:disabled, .h3-prompt-editor-tool.is-external { opacity: .16; cursor: not-allowed; pointer-events: none; }
      @keyframes h3-prompt-tool-pulse { from { transform: scale(.88); } to { transform: scale(1.06); } }
      .h3-mention-chip {
        display: inline; max-width: 150px; margin: 0 1px; padding: 0; vertical-align: baseline; border: 0; border-radius: 0;
        background: transparent; color: rgba(0,226,187,.98); font-family: inherit; font-size: var(--h3-prompt-text-size, 12px);
        font-weight: 400; line-height: inherit; letter-spacing: 0; user-select: text; cursor: text;
      }
      .h3-mention-chip.is-unresolved { color: #ff9b9b; text-decoration: underline wavy rgba(255,110,110,.86); text-decoration-thickness: 1px; }
      .h3-mention-chip-label { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: baseline; }
      .h3-dialogue-block {
        display: inline; margin: 0 1px; padding: 2px 4px; vertical-align: 1px; border: 0; border-radius: 4px;
        background: rgba(0,226,187,.14); color: rgba(190,255,244,.98); font-family: Consolas, "Courier New", monospace; font-size: var(--h3-prompt-text-size, 12px);
        box-shadow: inset 0 0 0 1px rgba(0,226,187,.16); font-weight: 400; line-height: calc(1em + 6px); letter-spacing: 0; white-space: pre-wrap;
        -webkit-box-decoration-break: clone; box-decoration-break: clone; user-select: text; cursor: text; outline: none;
      }
      .h3-dialogue-block:focus { background: rgba(0,226,187,.19); box-shadow: inset 0 0 0 1px rgba(0,226,187,.26); }
      .h3-mention-chip-thumb { display: inline-block; width: 16px; height: 16px; margin-right: 2px; object-fit: cover; border-radius: 3px; vertical-align: -2px; background: rgba(255,255,255,.12); user-select: none; }
      .h3-mention-chip-thumb.is-image, .h3-mention-menu-thumb.is-image { background: #5aa9f0; }
      .h3-mention-chip-thumb.is-video, .h3-mention-menu-thumb.is-video { position: relative; background: linear-gradient(135deg, #1557b8, #49b6ff); }
      .h3-mention-chip-thumb.is-video::after {
        content: ""; position: absolute; left: 6px; top: 4px; border-left: 6px solid rgba(255,255,255,.9); border-top: 4px solid transparent; border-bottom: 4px solid transparent;
      }
      .h3-mention-menu-thumb.is-video::after {
        content: ""; position: absolute; left: 13px; top: 10px; border-left: 10px solid rgba(255,255,255,.9); border-top: 7px solid transparent; border-bottom: 7px solid transparent;
      }
      .h3-mention-menu {
        position: fixed; z-index: 10080; width: 198px; min-width: 198px; max-width: 198px; max-height: 360px; overflow: auto; padding: 5px;
        border: 1px solid var(--h3-native-widget-outline, rgba(255,255,255,.16)); border-radius: 8px;
        background: var(--h3-native-menu-bg, rgba(28,28,28,.98)); box-shadow: 0 16px 38px rgba(0,0,0,.42);
        color: var(--h3-native-widget-text, rgba(255,255,255,.94)); font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      .h3-mention-menu-title { padding: 6px 8px 7px; color: var(--h3-native-widget-muted, rgba(255,255,255,.62)); font-size: 12px; }
      .h3-mention-menu-empty { padding: 9px 10px; color: var(--h3-native-widget-muted, rgba(255,255,255,.62)); font-size: 12px; }
      .h3-mention-menu-item { display: grid; grid-template-columns: 38px minmax(0,1fr); gap: 8px; align-items: center; min-height: 42px; padding: 4px 7px; border-radius: 6px; cursor: pointer; }
      .h3-mention-menu-item.is-active, .h3-mention-menu-item:hover { background: rgba(160,255,178,.15); }
      .h3-mention-menu-thumb { display: block; width: 36px; height: 36px; object-fit: cover; border-radius: 5px; background: rgba(255,255,255,.1); }
      .h3-mention-menu-main { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; font-weight: 700; }
      .h3-mention-menu-detail { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 2px; color: var(--h3-native-widget-muted, rgba(255,255,255,.55)); font-size: 11px; }
    `;
    document.head.append(style);
}

app.registerExtension({
    name: "MiniMaxH3Easy",
    setup() {
        install();
    },
    beforeRegisterNodeDef(nodeType, nodeData) {
        localizeNodeDefinition(nodeData);
        installMediaSourceNode(nodeType, nodeData);
        installLoaderNode(nodeType, nodeData);
        installAdapterNode(nodeType, nodeData);
        installMediaLoaderNode(nodeType, nodeData);
        installMediaBridgeNode(nodeType, nodeData);
        installMediaSplitterNode(nodeType, nodeData);
        installOutputNode(nodeType, nodeData);
        installSegmentRefineNode(nodeType, nodeData);
        installSegmentSampleSetupNode(nodeType, nodeData);
        installSegmentStepNode(nodeType, nodeData);
        installSegmentCollectNode(nodeType, nodeData);
        installNode(nodeType, nodeData);
    },
});
