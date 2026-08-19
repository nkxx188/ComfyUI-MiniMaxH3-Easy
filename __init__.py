from .nodes import MiniMaxH3Easy, MiniMaxH3EasyAspectRatio, MiniMaxH3EasyLoader, MiniMaxH3EasyMediaBridge, MiniMaxH3EasyModelAdapter, MiniMaxH3EasyOutput, MiniMaxH3EasySecondPassConditioning

NODE_CLASS_MAPPINGS = {
    "MiniMaxH3EasyLoader": MiniMaxH3EasyLoader,
    "MiniMaxH3EasyModelAdapter": MiniMaxH3EasyModelAdapter,
    "MiniMaxH3EasyMediaBridge": MiniMaxH3EasyMediaBridge,
    "MiniMaxH3Easy": MiniMaxH3Easy,
    "MiniMaxH3EasyOutput": MiniMaxH3EasyOutput,
    "MiniMaxH3EasyAspectRatio": MiniMaxH3EasyAspectRatio,
    "MiniMaxH3EasySecondPassConditioning": MiniMaxH3EasySecondPassConditioning,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxH3EasyLoader": "MiniMax H3 Easy Loader",
    "MiniMaxH3EasyModelAdapter": "MiniMax H3 Easy Model Adapter",
    "MiniMaxH3EasyMediaBridge": "MiniMax H3 Easy Media Bridge",
    "MiniMaxH3Easy": "MiniMax H3 Easy",
    "MiniMaxH3EasyOutput": "MiniMax H3 Easy Output",
    "MiniMaxH3EasyAspectRatio": "MiniMax H3 Easy Aspect Ratio",
    "MiniMaxH3EasySecondPassConditioning": "MiniMax H3 Easy Second Pass Conditioning",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
