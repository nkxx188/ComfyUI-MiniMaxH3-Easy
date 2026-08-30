# MiniMax H3 Easy 工作流说明

## 中文说明

使用本文件夹中的工作流前，请先安装所需插件，并下载对应模型。

### 可能需要安装的插件

- [ComfyUI-MiniMaxH3-Easy](https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
- [Comfyui-Memory_Cleanup](https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup)
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)
- [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)

也可以在 ComfyUI Manager 中搜索插件名称安装。安装或更新后请重启 ComfyUI。

### 模型与资源

工作流需要的插件、模型和相关资源：

<https://pan.quark.cn/s/8be70c7581e6?pwd=6LmC>

- [LightX2V MiniMax H3 Turbo（正式版 8-step LoRA）](https://huggingface.co/lightx2v/Minimax-h3-Turbo)
- [MiniMax H3 FL2VA 剪枝 W4A8（minimax_h3_fl2va_pruned_w4a8_mixed.safetensors）](https://huggingface.co/Kijai/MiniMax-H3-experimental)

不同工作流需要的模型可能不同，请按照工作流中的加载器选择对应文件。如果列表中找不到模型，请检查模型是否放入了正确的 `ComfyUI/models` 子目录，然后刷新或重启 ComfyUI。

部分工作流还需要额外的 LoRA 或其他自定义节点，具体以工作流中的节点为准。

---

# MiniMax H3 Easy Workflow Guide

## English

Before using any workflow in this folder, install the required custom nodes and download the models used by that workflow.

### Required custom nodes

- [ComfyUI-MiniMaxH3-Easy](https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
- [Comfyui-Memory_Cleanup](https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup)
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)
- [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)

You can also install them by searching for their names in ComfyUI Manager. Restart ComfyUI after installing or updating custom nodes.

### Models and assets

The plugins, models, and related assets used by the workflows are available here:

- [LightX2V MiniMax H3 Turbo (official 8-step LoRA)](https://huggingface.co/lightx2v/Minimax-h3-Turbo)
- [MiniMax H3 FL2VA pruned W4A8 (minimax_h3_fl2va_pruned_w4a8_mixed.safetensors)](https://huggingface.co/Kijai/MiniMax-H3-experimental)

Model requirements may differ between workflows. Select the matching files in each workflow's loader node. If a model is not listed, place it in the correct `ComfyUI/models` subdirectory, then refresh or restart ComfyUI.

Some workflows may also require additional LoRAs or custom nodes. Please check the nodes included in the workflow.
