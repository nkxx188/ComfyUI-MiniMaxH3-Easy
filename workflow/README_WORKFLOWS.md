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

### 上下文分段模式

节点 `MiniMax H3 Easy Context Segments` 用于多分段连续创作：在提示词中用单独一行 `---`（或输入 `~`）划分分段，在“分段秒数”中按 `10,8,5` 的形式填写每段时长，素材仍连接该节点的 Media 口，各段通过显式媒体标签声明自己使用的素材。Latent/RGB 引导使用 `5、22、39、56、73`；柔性/硬性 AV 前缀使用独立的 `39、90、141` 网格，不能混用。RGB 引导会把上一段尾部作为一个连续多帧 Guide 块，并在编码前对上下文加入渐进式刷新噪声，以减轻长链画质劣化。上下文条件通过 ComfyUI 原生 Guide 数据结构传递；每段自己的参考媒体仍独立进入该段的 `minimax_refs`。柔性 AV 保持画面重叠前缀，只对音频前缀末端渐进释放；硬性 AV 同时严格保持视频和音频重叠前缀。`音频模式` 默认为生成音频；切换为 `数字人` 并连接且只连接一条音频时，该音频按累计时间轴切片并锁定到每段 AV latent，最终预览和视频也使用这条完整音轨；若未提供音频，则自动回退到普通生成音频/参考生视频流程，不会报错。图片/视频参考仍按分段独立生效。需要逐段控制和局部重跑时，把 `H3 Context`、`Model`、`SAMPLER`、`SIGMAS` 接入 `MiniMax H3 Easy Sample Setup`，再把它接到第一个 `MiniMax H3 Easy Segment Step`。后续 Step 只串联 `Previous segment`，不再重复连接这些公共输入；分段顺序由串联关系自动确定。最后一个 Step 接到 `MiniMax H3 Easy Segment Collect`，再接 `MiniMax H3 Easy Segment Decode`。常规整链仍可直接使用 `MiniMax H3 Easy Segment Sample`。需要二采时，将第一采 `Segments`、同一个 `H3 Context`、SAMPLER/SIGMAS 接到 `MiniMax H3 Easy Segment Refine`；`latent_upscale` 模式复用一采的 H3 模型，只额外加载 3D latent upscaler，不再加载 W4A8 二采模型。像素放大或需要独立二采模型时，才接入另一套模型。该节点会逐段重建各自的提示词和参考媒体条件，并把上一段二采尾部传给下一段。再将二采节点的输出接到第二个 `MiniMax H3 Easy Segment Decode`，保存其 `Preview`。这样不会把整条片段先合成成一个全局 latent，也不会把不同分段的参考媒体混在一起；二采后的音频默认沿用第一采音频，数字人模式则沿用 Media 驱动音频时间线。

`Segment Refine` 的“二采执行方式”默认是“常规模式”。显存不足而需要更高分辨率时，选择“Low VRAM Tile”：它仍以用户的上下文分段为时间单位，只把当前分段的空间 latent 切成有重叠的 tile 二采。每个 tile 使用从同一整段噪声场裁切的坐标噪声，接缝区域先冻结再渐变融合；提示词、每段 `@` 媒体、上下文尾帧和音频模式都不会混入其他分段。Tile 越小显存越低，但二采次数和耗时越高；默认 `512 / 512 / 128 / 32` 分别是宽、高、重叠和接缝渐变（像素）。

`7.MiniMax_H3_Easy_Context_Segments_Control.json` 是逐段控制示例：先用一个 `MiniMax H3 Easy Sample Setup` 接收公共的 Context、Model、SAMPLER、SIGMAS，再接 3 个 `MiniMax H3 Easy Segment Step`。第一次运行仍会完整生成；需要时再利用 ComfyUI 原生缓存进行局部重跑。第一个 Step 接 Setup，后两个只按 `1 → 2 → 3` 串联 `Previous segment`；最后一个 Step 单独接 `Segment Collect` 和 `Segment Decode`。每个 Step 的 Seed 独立可改，分段顺序不需要手填；只改第 N 段时，前面的段可以命中缓存，第 N 段及其后续段才会重新采样。常规整链的 `Segment Sample` 和 `Segment Refine` 中，`Segment seeds` 默认填 `default`，表示所有分段沿用主 Seed；如需独立控制，可填写数字 Seed 列表，列表少于分段数时，末尾剩余分段自动沿用主 Seed，不能把 `default` 和数字混在一起。需要临时改某一段提示词时，可选接入一个外部 STRING 到该段的 `Prompt override`，不接则继续使用上下文节点中的分段提示词和 `@` 参考素材。这个节点只负责单个分段的处理，二采仍使用现有的 `Segment Refine` 或已选视频二采节点，避免把工作流混成一团。

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

### Context Segment mode

The `MiniMax H3 Easy Context Segments` node covers multi-shot creation. Split the prompt into shots with a standalone `---` line (or type `~`), fill "Segment seconds" as `10,8,5`, keep media linked to the node's Media port, and declare per-shot media with explicit tags. The shared context media library accepts up to 45 resources (27 images, 9 videos, 9 audio clips), while each segment still sends only its own referenced subset and keeps the normal per-segment H3 budget. Latent/RGB guide modes use `5, 22, 39, 56, 73`; Soft/Hard AV prefix modes use a separate `39, 90, 141` grid. RGB continuation uses ComfyUI's native Guide data structure as one continuous multi-frame block, and each segment's references remain in its own `minimax_refs` payload. Soft AV keeps the picture prefix exact and releases only the tail of the carried audio prefix; Hard AV holds both streams strictly. `Audio mode` defaults to generated audio; in `Digital Human`, connect exactly one audio resource through Media to drive the sequence. It is sliced on the cumulative timeline, locked into each segment AV latent, and used as the final soundtrack, while visual references remain segment-local. When no audio is connected, the node automatically falls back to its normal generated-audio/reference path. For per-segment control and local reruns, connect `H3 Context`, `Model`, `SAMPLER`, and `SIGMAS` to **MiniMax H3 Easy Sample Setup**, then connect its output to the first **MiniMax H3 Easy Segment Step**. Chain only `Previous segment` on later Steps; their order is inferred automatically from the chain. Connect the final Step to **MiniMax H3 Easy Segment Collect**, then to **MiniMax H3 Easy Segment Decode**. The regular one-node chain remains available as **MiniMax H3 Easy Segment Sample**. For a second pass, connect the first-pass `Segments`, the same `H3 Context`, and SAMPLER/SIGMAS to **MiniMax H3 Easy Segment Refine**. In `latent_upscale` mode, reuse the first-pass H3 model and load only the 3D latent upscaler; do not add a separate W4A8 second-pass model. Pixel resize or an intentionally separate second model remains available as another mode. The refine node rebuilds each segment's prompt and reference-media conditioning independently and passes the previous refined tail into the next segment. Connect the refine output to a second **MiniMax H3 Easy Segment Decode** and save that `Preview`. This avoids a global latent second pass and prevents references from different segments from being mixed; second-pass audio follows the first-pass timeline, or the Media driving timeline in Digital Human mode.

`Segment Refine` defaults to `Standard mode`. Select `Low VRAM Tile` when a higher-resolution second pass does not fit in VRAM. User context segments remain the temporal units; only the current segment's spatial latent is sampled as overlapping tiles. Tiles crop one shared full-segment noise field by coordinate, freeze then fade their seams, and retain the segment's own prompt, `@` media, carried context tail, and selected audio mode. Smaller tiles reduce VRAM but increase the number and duration of sampling runs. The default `512 / 512 / 128 / 32` values are tile width, height, overlap, and seam fade in pixels.

`7.MiniMax_H3_Easy_Context_Segments_Control.json` demonstrates per-segment control with one `MiniMax H3 Easy Sample Setup` for the shared Context, Model, SAMPLER, and SIGMAS, followed by three `MiniMax H3 Easy Segment Step` nodes. The first run still generates the complete video; selective reruns are optional. The first Step receives Setup; the later Steps only chain `Previous segment` as `1 → 2 → 3`; the final Step alone connects to `Segment Collect` and `Segment Decode`. Each Step has its own seed and the segment order is inferred, not entered manually. If only segment N changes, earlier steps can hit ComfyUI's native cache while segment N and its dependent later steps resample. In the regular `Segment Sample` and `Segment Refine` nodes, `Segment seeds` defaults to `default`, meaning every segment uses the main seed. For independent control, enter a numeric comma-separated list; if it is shorter than the segment count, remaining trailing segments automatically use the main seed. Do not mix `default` with numbers. To temporarily replace one segment's prompt, optionally connect a STRING node to that Step's `Prompt override`; without it, the Context node's segment prompt and `@` media remain in use. This node handles one segment at a time. Use the existing `Segment Refine` or selected-video refine workflow for second-pass upscaling, keeping the graph readable.
