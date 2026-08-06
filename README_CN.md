# ComfyUI-MiniMaxH3-Easy 中文说明

[English README](README.md)

`ComfyUI-MiniMaxH3-Easy` 将 MiniMax H3 的文生视频、图生视频和参考生视频整合到一套
简洁的 ComfyUI 工作流中。交互层经过专门打磨，让媒体输入、参考素材选择和提示词编辑
都更加直观、简单、顺手。

它的目标不是把 ComfyUI 变成黑盒，而是把重复的媒体连线、素材排序和参考引用管理
交给节点处理，让用户把注意力放在提示词和创作本身，同时保留 LoRA、采样器、保存
节点等标准 ComfyUI 组件的自由组合能力。

## 核心卖点

### 多种媒体共用一个 `Media` 输入

主节点只暴露一个可排序的 `Media` 输入。图片、视频、音频都可以接入同一个端点，
不需要为每一种媒体准备一排输入口。

图片、视频、音频仍然各自保持独立的顺序和编号，前端会使用不同颜色的连线、缩略图
和序号帮助区分。

<p align="center">
  <img src="images/mixed-media-input-zh.png" alt="多线输入" width="560">
</p>

从 `Media` 输入端拖线到空白画布，会弹出快速创建菜单，可以直接创建对应的资源节点。
点击虚拟连线中间的序号，会打开只有“删除”选项的小菜单。

<p align="center">
  <img src="images/quick-create-node-zh.png" alt="快速创建媒体节点" width="460">
</p>

### 完整的 `@` 参考素材编辑器

在 **参考生视频** 模式中，在提示词里输入 `@` 即可选择已连接的图片、视频或独立音频。
弹窗按照图片、视频、音频的顺序显示，并提供预览，方便快速辨认素材。

<p align="center">
  <img src="images/mention-popup-zh.png" alt="引用素材弹窗" width="320">
</p>

<p align="center">
  <img src="images/reference-editor-zh.png" alt="参考模式中的整体效果" width="720">
</p>

默认使用**按序号**引用，因为显示更简洁；用户也可以切换为**按文件名**，在文件名
本身更有辨识度时使用。

编辑器中的芯片只是方便用户编辑的显示形式。真正执行工作流时，节点会自动把引用转换成MiniMax 官方推荐的提示词格式，包括 `<Picture N>`、`<Video N>` 和 `<Audio N>`，用户不需要手动书写或维护这些标签。

用户也不需要手动拆分视频音轨。视频自带的同步音轨会自动和对应视频配对；单独接入的音频则作为独立参考处理。

### 简洁的台词块

在提示词编辑器中输入 `#`，即可创建可编辑的台词块。

<p align="center">
  <img src="images/dialogue-block-zh.png" alt="台词块" width="560">
</p>

- `Enter`：结束当前台词块；
- `Shift+Enter`：在台词块内部换行；
- 可以随时点击台词块重新编辑。

台词块在执行时会自动转换成 MiniMax 官方推荐的 `<d>...</d>` 台词格式。台词块之外仍然是普通提示词文本，用户可以自然地描述画面，不需要理解底层标签。

### H3 提示词优化

主节点提供**优化提示词**开关，可通过任意 OpenAI 兼容的
`chat/completions` API，将简短创意扩写为符合 MiniMax H3 结构的视听提示词。
该开关是节点的原生 BOOLEAN 输入；启用后，由 Python 节点在执行 `generate()` 时
优化提示词，再使用优化结果创建 H3 conditioning。
优化器会直接根据主节点的顶层模式选择两套硬编码系统提示词之一：`image`
使用 `IMAGE_SYSTEM_PROMPT`，`reference` 使用 `REFERENCE_SYSTEM_PROMPT`，并保留
参考模式中的所有 `@` 素材引用。这两个提示词常量位于 `prompt_optimizer.py`，默认
留空，便于直接粘贴完整提示词。

首次使用前，在 ComfyUI 设置面板的 **MiniMaxH3Easy → PromptOptimizer** 中填写：

- `Base URL`：例如 `https://api.openai.com/v1`；
- `Model`：服务商提供的模型 ID；
- `API Key`：可留空以支持不需要鉴权的本地兼容服务。

`API Key` 由 ComfyUI 设置系统保存，仅在开关启用时注入本次执行数据，不写入工作流
JSON。优化结果仅供当次节点执行使用，不会改写前端提示词编辑器。

优化请求会直接读取当前节点收到的多模态数据：图片会缩放后附加，视频会抽取三个代表
帧，音频会编码为最长约 6 MB 的 WAV `input_audio`。所选提示词模型必须支持对应的
OpenAI 兼容多模态消息。

## 节点和连接方式

### MiniMax H3 Easy Loader

四合一加载器，分别选择：

- FL2VA 主模型；
- Ref2VA 主模型；
- Qwen3-VL 文本编码器；
- 视频 VAE；
- 音频 VAE。

官方和常见社区模型命名都可以识别，包括 BF16、FP8、INT8、INT4、NVFP4、NF4 和 GGUF等版本。

### MiniMax H3 Easy

这是整套节点的主要操作入口，输出两个端口：

- `Model`：可以直接连接采样器，也可以先连接模型专用 LoRA、Sage Attention 或其他模型补丁；
- `H3 Context`：连接到 **MiniMax H3 Easy Output**。

### MiniMax H3 Easy Output

把 `H3 Context` 展开成标准 ComfyUI 工作流需要的：

- Conditioning；
- Latent；
- Video VAE；
- Audio VAE；
- FPS。

采样器、加速节点、视频/音频处理和保存节点仍然放在外部，方便继续使用 ComfyUI 生态中的其他节点。

## 模式

### 图生或首尾帧

- 不连接媒体：文生视频；
- 连接一张图片：图生视频；
- 连接两张图片：首尾帧生成；
- 此模式不接受视频和音频输入。

### 参考生视频

- 最多九张参考图片、三条参考视频和三条独立音频；
- 启用 `@` 编辑器；
- 引用顺序和提示词中的素材对应关系自动维护。

## 参数设计逻辑

### 分辨率和宽高比

分辨率预设采用 MiniMax H3/ComfyUI 的 megapixel 预算逻辑：

`360P`、`416P`、`480P`、`540P`、`640P`、`720P`、`768P`、`832P`、`928P`、`1024P`、
`1080P` 和 `Custom`。

选择预设时，节点根据宽高比计算画布尺寸，并自动对齐到 32 的倍数。可选比例包括：
`1:1`、`2:3`、`3:2`、`3:4`、`4:3`、`9:16`、`16:9` 和 `21:9`。

选择 `Custom` 后才显示宽高输入，同时隐藏宽高比选项。自定义宽高必须是 32 的倍数。

### 秒数

时长使用秒数表示，范围为 **4～20 秒**。

### 高级选项

高级选项默认关闭。开启后显示：

- 图生或首尾帧模式下的首尾帧设置；
- 参考生视频模式下的参考图尺寸；
- 参考生视频模式下 `@` 的按文件名/按序号显示方式。

参考图尺寸使用短边上限：

- **短边最大 1K 像素**；
- **短边最大 2K 像素**。

图片小于上限时保留原始分辨率；超过上限时保持原比例缩小，不会为了生成 480P 视频就把参考图也压到 480P。

首尾帧设置只在图生或首尾帧模式显示：

- **首帧优先**：一张图作为首帧；两张图按首帧、尾帧顺序处理；
- **尾帧优先**：一张图作为尾帧；两张图按尾帧、首帧顺序处理。

## 安装和模型

将本节点放入：

```text
ComfyUI/custom_nodes/ComfyUI-MiniMaxH3-Easy
```

模型放入：

```text
ComfyUI/models/diffusion_models/
ComfyUI/models/text_encoders/
ComfyUI/models/vae/
```

加载器会识别官方和常见社区命名，包括大小写、短横线/下划线、`FL2VA`/`FL2V`、
`Ref2VA`/`Ref2V`、Qwen3-VL 变体，以及常见量化版本。

如果使用 `.gguf` 主模型或文本编码器，请额外安装[ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) 并重启 ComfyUI。普通 safetensors无需额外后端。

## 开源协议和署名

本项目采用 [MIT 协议](LICENSE) 发布。

如果参考、复用或改写本项目的较大部分代码，需在项目文档中注明原作者和
`ComfyUI-MiniMaxH3-Easy` 项目。

请不要将本项目的多媒体单输入设计、`@` 参考编辑器、台词块转换机制或相关实现完整描述为你自己的原创工作。

## 注意事项

- 图生或首尾帧模式最多连接两张图片；
- 参考生视频模式最多九张图片、三条视频和三条独立音频；
- 视频自带同步音轨会自动和视频配对，不占用独立音频数量；
- 图片、视频、音频的序号分别独立；
- 模型专用 LoRA 和注意力/加速补丁连接在主节点的 `Model` 输出之后；
- 同时兼容 ComfyUI 旧画布和 Nodes 2.0；
- 中文浏览器显示中文参数标签，非中文浏览器显示英文参数标签。
