# 中文配音与流程可视化：证据、成本和启用门槛

本文件记录截至 **2026-10-24** 的候选判断。这里的“免费”只指某项明确的代码/权重授权或已提供的免费用法，**不代表算力、网络、部署和商业服务都免费**。任何模型的“自然”“真诚”“有老者阅历”均不得凭宣传语判为通过，必须对实际中文讲稿盲听。

## 声音候选：按状态选，不按热度选

| 候选 | 查证到的范围 | 现在决定 | 仍需确认 |
| --- | --- | --- | --- |
| **Dessa / Block**（用户截图） | 官方发布的是纯语音训练、实时双向对话的研究预览；官网有体验片段与候补/研究访问入口，尚未公开可用于本项目的下载、API、价格或中文能力说明。**成本 UNKNOWN，中文亲切度 UNKNOWN**。 | **WATCHLIST**；不要填写“免费”，不要接入生产配音；它主要是会话模型，不等同于可控逐字旁白 TTS。 | 是否有可获取的模型/API、价格/条款、中文样本、可重复的批量朗读和时间戳。 |
| **Qwen3-TTS CustomVoice** | 上游明确支持中文、文本控制语气；官方 `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` 模型页标注 **Apache-2.0**，可下载权重本地运行。官方列出中文 `Uncle_Fu`（低沉成熟男声）和 `Serena`（温柔女声）。 | **OPTIONAL_LOCAL_TRIAL**；先用 `scripts/zh_voice_sample.py` 生成两种试听 WAV，再由真人选择。**不改变默认 Edge 引擎**。 | GPU/内存、下载到手时的权重版本与许可、真实普通话发音与情绪、音量和断句、与 Papermorph `[[mark]]` 字词时间戳的对齐方案。 |
| **Qwen3-TTS VoiceDesign** | 官方模型页 `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` 标明 Apache-2.0、约 4.52 GB 文件总量，官方代码支持中文自然语言描述音色。 | **OPTIONAL_LOCAL_TRIAL**；适合设计独特原创声音，前提是声明合成且不模仿真人。 | 本地可运行与人工试听，稳定性与后期对齐。 |
| **Edge TTS / 中文神经音色** | PaperMorph 当前 `tts.py` 支持，按项目现有方式调用线上服务；并非本仓库自有的商业授权或离线模型。 | **BASELINE_PENDING**：原样留作基准，当前环境连不上服务端，尚无有效 WAV 和字幕同步验证。 | 可用网络、服务条件、最终授权用途、试听通过。 |
| **CosyVoice** | 官方仓库提供中文、多语种能力；开源代码与具体模型权重的条款应逐版本核对。 | **BACKUP_EVALUATE_LATER**；与 Qwen3 做过中文试听对比后再决定要不要增加依赖。 | 指定模型、权重条款、部署成本、时间戳对接与盲听效果。 |

一手资料（复核时记录访问日期和下载版本）：[Dessa 官方](https://block.xyz/dessa)、[Qwen3-TTS 官方仓库](https://github.com/QwenLM/Qwen3-TTS)、[Qwen3-TTS CustomVoice 模型](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)、[Qwen3-TTS VoiceDesign 模型](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign)、[CosyVoice 官方仓库](https://github.com/QwenAudio/CosyVoice)。

### 最低成本试听流程

1. 使用同一段经事实审查的约 45—90 秒中文讲稿；**绝不**把模型宣传样本当作本作品验证。
2. 先记录 Edge 方案的状态；如果网络不可用，明确 `FAILED_NETWORK`，不要填入假样本。
3. 若有可用的本地 GPU 和足够内存，再决定是否下载 Qwen3-TTS。模型权重、软件本身可免费获取，并不免除算力/下载成本。命令示例：

   ```bash
   python3 .claude/skills/papermorph/scripts/zh_voice_sample.py \
     --text-file .claude/skills/papermorph/assets/templates/zh-humanist/narration.zh.json \
     --speaker Uncle_Fu --output /tmp/papermorph-uncle-fu.wav --dry-run
   ```

   上面的 `--dry-run` **只核对配置，不生成音频**。执行实际生成时去掉该参数，并在隔离环境里安装官方 `qwen-tts`、`torch`、`soundfile` 以及满足需求的硬件环境；默认不能自动在主发布管道启用。
4. 用相同讲稿盲听比较：发音/多音字、停顿、节奏、长句呼吸、情绪是否克制、像不像真的对一个人说话。记录每项具体问题，特别记录是否用朗读腔冒充阅历。必要时宁可真人录音。
5. 试听 WAV **还不是成片配音**：Papermorph 的 `tts.py` 需要字词边界和 `[[mark]]` 时间，必须先做可追溯的对齐验证，才能作为新 TTS 引擎接入。不得用均分时长猜时间戳并宣称同步通过。

## 工作流：只在能把一件事讲清楚时才加工具

统一制作链：**问题与目标受众 → 来源/修订版/适用范围核对 → 中文大纲与场景 → 人工读稿 → 候选声音试听 → 画面与节奏设计 → 语音与标记精准同步 → 手机/电脑复核 → 人工审片 → 发布**。

| 情境 | 合适工具 | 授权/成本判断 | 取舍 |
| --- | --- | --- | --- |
| 普通机制解释、一步步观察变化 | **PaperMorph 自带 timed beats + SVG/动画** | 已在本 fork；不新增运行依赖 | **DEFAULT**，给画面留空间。 |
| 编排因果流程、脚本分镜、工艺次序 | **Mermaid** 作为创作阶段的流程草图 | 开源工具；具体模板/外链服务另核 | **USE_IN_AUTHORING**；成片优先改造成原生 SVG，而非加载第三方在线图。 |
| 品质数据、Pareto、SPC、趋势、散点与分布 | **Apache ECharts** | Apache-2.0，开源；数据和中文字体仍需自查 | **ON_DEMAND**；真正涉及多组数据才用，静态成片可导出 SVG/图像。 |
| 观众点击选择分支、故障树、知识地图 | **React Flow (`@xyflow/react`)** | MIT 开源；Pro 示例/服务可能收费 | **ON_DEMAND**；只用于互动阅读页，不为普通视频增加 React 构建链。 |
| 每日资料收集、审稿通知、批量任务转移 | **n8n 自托管 Community** | 可免费自托管，但 Sustainable Use License **并非无条件开源/商用授权**；硬件与托管另计 | **DEFER**；等确实出现重复任务和运行维护需求，逐案例审查授权。 |
| 特效视频、复杂三维动画 | 现有 PaperMorph 不能表达时再评估专业渲染 | 成本/部署复杂度另评估 | **DEFER**，不堆工具。 |

一手资料：[Apache ECharts](https://echarts.apache.org/en/index.html)、[React Flow](https://reactflow.dev/)、[Mermaid](https://mermaid.js.org/)、[n8n 授权问答](https://support.n8n.io/article/can-i-use-your-license-for-my-use-case)。

## 每个片段的展示原则

- **一句话/一个机制/一个主要视觉焦点**。图表需要读数时暂停运动。不要同屏塞满语录、数字、流程和角色。
- 颜色不替代文字；中文字号、对比、行间距和图表标签必须在手机上检查。
- 事实图与比喻图分开；图中的数值、单位、材料或因果箭头必须能回到证据，不许为了美观改写。
- 能用老人的一种朴素说法说清楚的，不要再配四种过场特效；真挚来自正确的观察与克制。
- 所有 `OPTIONAL_LOCAL_TRIAL`、`ON_DEMAND`、`DEFER` 都是**已纳入候选库**，不是已安装、已生成或已验收。

