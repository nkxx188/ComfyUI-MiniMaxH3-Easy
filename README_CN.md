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
参考模式中的所有 `@` 素材引用。这两个完整的提示词常量位于 `prompt_optimizer.py`。

首次使用前，在 ComfyUI 设置面板的 **MiniMaxH3Easy → PromptOptimizer** 中配置实例级参数：

- `Base URL`：例如 `https://api.openai.com/v1`；
- `Model`：服务商提供的模型 ID；
- `API Key`：可留空以支持不需要鉴权的本地兼容服务；
- 视频传输：`Auto` / `Native` / `Sampled frames`；
- 音频传输：`Auto` / `input_audio` / `Video wrapper`。

后端将配置保存到 `user/__minimax_h3_easy/`。API Key 输入框始终空白，设置页只显示
“已配置”状态并提供清除操作，GET 路由绝不返回密钥。也可使用
`MINIMAX_H3_OPTIMIZER_BASE_URL`、`MINIMAX_H3_OPTIMIZER_MODEL` 和
`MINIMAX_H3_OPTIMIZER_API_KEY` 环境变量，且环境变量优先。这些配置不会进入
`/prompt` 或队列历史。配置由同一 ComfyUI 实例的所有工作流和用户共享，应仅由可信管理员管理。

原生视频会在内存中编码为 H.264/AAC MP4，保留帧率和同步音轨，最长边缩放到 720；
抽帧模式附加三帧。音频可使用 `input_audio`，也可封装成带 512×512 静态波形画面的 MP4。
`Auto` 首次使用原生视频和 `input_audio`；仅当 400/415/422 明确说明 `video_url` 或
`input_audio` 不受支持时回退一次，显式模式和模糊错误不重试。

单项二进制限制为 24 MiB，Base64 总负载限制为 4000 万字符。响应优先使用 SSE 流，也兼容
非流式 JSON。进度由累计 UTF-8 字节数÷4 与最大输出 Tokens 估算，读取时最高 95%，
正常结束后 100%。短/中/长分别发送 1024/4096/8192 `max_tokens`，自定义范围为
256–32768，非法值回退到 4096。

## 节点和连接方式

### MiniMax H3 Easy Loader

一体化加载器分别选择：

- FL2VA 主模型；
- Ref2VA 主模型；
- Qwen3-VL 文本编码器；
- 视频 VAE；
- 音频 VAE。

官方和常见社区模型命名都可以识别，包括 BF16、FP8、INT8、INT4、NVFP4、NF4 和 GGUF等版本。

如果只想使用一种主模型，将另一种模型设置为“无”即可。节点会自动使用剩下的模型完成文生视频、
图生或首尾帧、参考生视频等多种任务。同时安装两种模型时，文生视频、图生或首尾帧优先使用
FL2VA，参考生视频优先使用 Ref2VA。两种主模型不能同时设置为“无”。

### MiniMax H3 Easy

这是整套节点的主要操作入口。原有前两个输出索引保持不变，末尾追加两个文本输出：

- `Model`：可以直接连接采样器，也可以先连接模型专用 LoRA、Sage Attention 或其他模型补丁；
- `H3 Context`：连接到 **MiniMax H3 Easy Output**。
- `Optimized prompt`：实际优化结果；关闭优化时输出原提示词；
- `Reasoning content`：聚合 `reasoning_content`、`reasoning` 或 `reasoning_details`，没有时为空。

优化失败会直接报错，不返回半成品。旧 API 工作流缺少 `optimize_prompt` 时仍可执行，默认为关闭。

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
