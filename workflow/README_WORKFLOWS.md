# MiniMax H3 Easy 工作流说明

## 中文

使用本文件夹中的工作流前，请先更新 ComfyUI，并安装所需的自定义节点和模型。

### 可能需要安装的插件

所有工作流均需要：

- [ComfyUI-MiniMaxH3-Easy](https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy)

通过 ComfyUI Manager 安装本节点时，请选择 **Nightly** 版本，以获得最新的节点和工作流支持。

根据导入的工作流，还可能需要：

- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
- [Comfyui-Memory_Cleanup](https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup)
- [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)
- [rgthree-comfy](https://github.com/rgthree/rgthree-comfy)

可以在 ComfyUI Manager 中搜索以上名称安装。安装或更新后，请重启 ComfyUI。

### 模型与资源

模型和相关资源：

<https://pan.quark.cn/s/8be70c7581e6?pwd=6LmC>

工作流可能涉及以下模型类别：

- MiniMax H3 生成模型（FL2VA / Ref2VA）
- MiniMax H3 文本编码器
- MiniMax H3 视频 VAE 和音频 VAE
- 可选的加速 LoRA
- 可选的二采模型、3D Latent 放大模型或预览模型

MiniMax H3 存在多种精度、量化方式和模型变体，工作流不限定必须使用某一个版本。请根据自己的显存、速度和画质需求，在对应加载器中选择兼容模型；LoRA 和二采相关模型也可以自行搭配。

如果加载器中没有出现已经下载的模型，请检查文件是否放入了正确的 `ComfyUI/models` 子目录，然后刷新模型列表或重启 ComfyUI。

---

# MiniMax H3 Easy Workflow Guide

## English

Before using the workflows in this folder, update ComfyUI and install the required custom nodes and models.

### Custom nodes you may need

Required by every workflow:

- [ComfyUI-MiniMaxH3-Easy](https://github.com/nkxx188/ComfyUI-MiniMaxH3-Easy)

When installing this node through ComfyUI Manager, select the **Nightly** version to get the latest nodes and workflow support.

Depending on the imported workflow, you may also need:

- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)
- [Comfyui-Memory_Cleanup](https://github.com/LAOGOU-666/Comfyui-Memory_Cleanup)
- [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use)
- [rgthree-comfy](https://github.com/rgthree/rgthree-comfy)

Search for these names in ComfyUI Manager. Restart ComfyUI after installing or updating custom nodes.

### Models and resources

Models and related resources:

<https://pan.quark.cn/s/8be70c7581e6?pwd=6LmC>

The workflows may use the following model categories:

- MiniMax H3 generation models (FL2VA / Ref2VA)
- MiniMax H3 text encoder
- MiniMax H3 video VAE and audio VAE
- Optional acceleration LoRAs
- Optional second-pass models, 3D latent upscalers, or preview models

MiniMax H3 is available in multiple precisions, quantizations, and model variants. The workflows do not require one specific version. Choose compatible models in the corresponding loaders according to your VRAM, speed, and quality requirements; LoRAs and second-pass models can also be selected independently.

If a downloaded model does not appear in a loader, verify that it is stored in the correct `ComfyUI/models` subdirectory, then refresh the model list or restart ComfyUI.
