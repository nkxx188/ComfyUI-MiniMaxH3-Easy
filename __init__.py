from .nodes import (
    MiniMaxH3Easy,
    MiniMaxH3EasyContextSegments,
    MiniMaxH3EasyAspectRatio,
    MiniMaxH3EasyLoader,
    MiniMaxH3EasyMediaLoader,
    MiniMaxH3EasyMediaBridge,
    MiniMaxH3EasyMediaSplitter,
    MiniMaxH3EasyModelAdapter,
    MiniMaxH3EasyOutput,
    MiniMaxH3EasySecondPassConditioning,
    MiniMaxH3EasySegmentDecode,
    MiniMaxH3EasySegmentRefine,
    MiniMaxH3EasySegmentRender,
    MiniMaxH3EasySegmentSampleSetup,
    MiniMaxH3EasySegmentStep,
    MiniMaxH3EasySegmentCollect,
    MiniMaxH3EasySelectedVideoContext,
)
from .h3_latent_upscaler import MiniMaxH3EasyLatentUpscaler3D

NODE_CLASS_MAPPINGS = {
    "MiniMaxH3EasyLoader": MiniMaxH3EasyLoader,
    "MiniMaxH3EasyModelAdapter": MiniMaxH3EasyModelAdapter,
    "MiniMaxH3EasyMediaLoader": MiniMaxH3EasyMediaLoader,
    "MiniMaxH3EasyMediaBridge": MiniMaxH3EasyMediaBridge,
    "MiniMaxH3EasyMediaSplitter": MiniMaxH3EasyMediaSplitter,
    "MiniMaxH3Easy": MiniMaxH3Easy,
    "MiniMaxH3EasyContextSegments": MiniMaxH3EasyContextSegments,
    "MiniMaxH3EasyOutput": MiniMaxH3EasyOutput,
    "MiniMaxH3EasySegmentRender": MiniMaxH3EasySegmentRender,
    "MiniMaxH3EasySegmentSampleSetup": MiniMaxH3EasySegmentSampleSetup,
    "MiniMaxH3EasySegmentStep": MiniMaxH3EasySegmentStep,
    "MiniMaxH3EasySegmentCollect": MiniMaxH3EasySegmentCollect,
    "MiniMaxH3EasySegmentRefine": MiniMaxH3EasySegmentRefine,
    "MiniMaxH3EasySegmentDecode": MiniMaxH3EasySegmentDecode,
    "MiniMaxH3EasySelectedVideoContext": MiniMaxH3EasySelectedVideoContext,
    "MiniMaxH3EasyAspectRatio": MiniMaxH3EasyAspectRatio,
    "MiniMaxH3EasySecondPassConditioning": MiniMaxH3EasySecondPassConditioning,
    "MiniMaxH3EasyLatentUpscaler3D": MiniMaxH3EasyLatentUpscaler3D,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxH3EasyLoader": "MiniMax H3 Easy Loader",
    "MiniMaxH3EasyModelAdapter": "MiniMax H3 Easy Model Adapter",
    "MiniMaxH3EasyMediaLoader": "MiniMax H3 Easy Media Loader",
    "MiniMaxH3EasyMediaBridge": "MiniMax H3 Easy Media Bridge",
    "MiniMaxH3EasyMediaSplitter": "MiniMax H3 Easy Media Splitter",
    "MiniMaxH3Easy": "MiniMax H3 Easy",
    "MiniMaxH3EasyContextSegments": "MiniMax H3 Easy Context Segments",
    "MiniMaxH3EasyOutput": "MiniMax H3 Easy Output",
    "MiniMaxH3EasySegmentRender": "MiniMax H3 Easy Segment Sample",
    "MiniMaxH3EasySegmentSampleSetup": "MiniMax H3 Easy Sample Setup",
    "MiniMaxH3EasySegmentStep": "MiniMax H3 Easy Segment Step",
    "MiniMaxH3EasySegmentCollect": "MiniMax H3 Easy Segment Collect",
    "MiniMaxH3EasySegmentRefine": "MiniMax H3 Easy Segment Refine",
    "MiniMaxH3EasySegmentDecode": "MiniMax H3 Easy Segment Decode",
    "MiniMaxH3EasySelectedVideoContext": "MiniMax H3 Easy Selected Video Context",
    "MiniMaxH3EasyAspectRatio": "MiniMax H3 Easy Aspect Ratio",
    "MiniMaxH3EasySecondPassConditioning": "MiniMax H3 Easy Second Pass Conditioning",
    "MiniMaxH3EasyLatentUpscaler3D": "MiniMax H3 Easy 3D Latent Upscale (Built-in)",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
