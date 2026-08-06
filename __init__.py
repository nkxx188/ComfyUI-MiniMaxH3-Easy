from .nodes import MiniMaxH3Easy, MiniMaxH3EasyLoader, MiniMaxH3EasyOutput
from .optimizer_config import public_optimizer_config, save_optimizer_config

try:
    from aiohttp import web
    from server import PromptServer

    @PromptServer.instance.routes.get("/minimax_h3_easy/prompt_optimizer/config")
    async def get_prompt_optimizer_config(_request):
        return web.json_response(public_optimizer_config())

    @PromptServer.instance.routes.post("/minimax_h3_easy/prompt_optimizer/config")
    async def set_prompt_optimizer_config(request):
        try:
            values = await request.json()
            return web.json_response(save_optimizer_config(values))
        except (ValueError, TypeError) as error:
            return web.json_response({"error": str(error)}, status=400)
except (ImportError, AttributeError):
    # Allows documentation tooling to import the package outside ComfyUI.
    pass

NODE_CLASS_MAPPINGS = {
    "MiniMaxH3EasyLoader": MiniMaxH3EasyLoader,
    "MiniMaxH3Easy": MiniMaxH3Easy,
    "MiniMaxH3EasyOutput": MiniMaxH3EasyOutput,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxH3EasyLoader": "MiniMax H3 Easy Loader",
    "MiniMaxH3Easy": "MiniMax H3 Easy",
    "MiniMaxH3EasyOutput": "MiniMax H3 Easy Output",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
