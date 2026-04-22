# EEG 数据说明

## 1. 项目定位与当前状态

### 1.1 项目在做什么

本项目围绕 `Moreira et al., 2025` 公开的 EEG speech decoding 数据集展开，界定下面几件事：

1. 公开数据结构是什么
2. 标签和任务层级是什么
3. 当前数据能支持到哪一层 speech alignment
4. 哪些子集更适合作为后续 `EEG token / speech token` 研究起点

### 1.2 当前已经完成到哪一步

目前已经完成：

- 本地事件表整理与标准化
- OpenNeuro `ds006104` BIDS 结构验证
- 事件级数据分析与图表
- 原始 `EDF` 批量基础分析
- 原始 `EDF` 批量完整导出为 HDF5

当前还没有正式进入：

- stimulus-locked epoch 批量切片
- trial-level 数据集构建
- EEG token 学习
- speech token 对齐训练

### 1.3 最值得先记住的结论

1. 数据公开主源是 `OpenNeuro ds006104`，对应 Moreira 2025。
2. 任务是 `听刺激 + 按键辨别`，不是 imagined speech。
3. 当前公开结构支持 `trial-level` 和部分 `unit-level` 研究。
4. 当前公开结构不支持 `frame-level` 语音监督，也不支持直接 `EEG -> mel / waveform`。
5. 优先关注的子集包括：
   - `2021 single-phoneme`
   - `2021 Words`
   - `control-only phonemes`

## 2. 两张总图

### 2.1 数据说明导图

![EEG 数据说明导图](../exploration_outputs/figures/eeg_data_overview_map.svg)

这张图对应的问题包括：

1. 数据总体从哪里来
2. 任务怎么分层
3. 当前能做什么、不能做什么
4. 后续工作路径如何展开

### 2.2 数据结构说明图

![EEG 数据结构说明图](../exploration_outputs/figures/eeg_data_structure_map.svg)

这张图对应的问题包括：

1. 单个记录目录里有哪些文件
2. 每个文件分别代表什么
3. 哪些是原始定义
4. 哪些只是描述性结果
5. 哪些才是后面真正能拿去切 epoch 和训练的完整数据

这两张图最重要的含义可以压缩成三句：

1. `EDF + sidecars` 是原始定义层。
2. `summary / PSD / overview` 属于描述性摘要层。
3. `*_full_eeg.h5` 才是当前项目里真正的完整 EEG 数据本体。

## 3. 数据来源与目录关系

当前项目里的数据来源最好分成 4 层来看。

### 3.1 OpenNeuro 主数据源

公开主数据源是：

- `OpenNeuro ds006104`

当前本地下载目录是：

- `openneuro_downloads/ds006104-download/`

这层提供：

- 原始 `EDF`
- `events.tsv/json`
- `channels.tsv`
- `eeg.json`
- `coordsystem.json`

这是后续正式分析最标准、最可复现的入口。

### 3.2 本地事件表层

目录：

- `ref_github/speech_decoding/events_information/`

这层提供：

- 仓库原带的本地事件表 CSV

这层的价值主要在于：

- 快速汇总和做描述性统计
- 和 BIDS `events.tsv` 互相校对
- 在 `Words` 任务里补充词级信息，尤其是 `phoneme3 / p3_tsidx`

### 3.3 分析与导出结果层

目录：

- `ref_github/speech_decoding/exploration_outputs/`

这层提供：

- 表格
- 图表
- 事件级分析结果
- EDF 描述性分析结果
- 完整 EEG 导出结果

这是当前项目中最直接可用的工作层。

### 3.4 代码与说明层

目录：

- `ref_github/speech_decoding/scripts/`
- `ref_github/speech_decoding/reports/`

作用：

- 记录当前项目如何读数据、分析数据、导出数据、规划后续研究

## 4. Moreira 论文背景与核心概念

### 4.1 这篇论文到底是什么

`作者公开了一套更系统的 EEG speech decoding 数据集，让研究者可以从简单语音单位逐步走向更复杂语音单位。`

### 4.2 这篇论文为什么重要

它重要的地方在于：

1. 公开了两批相关 EEG 数据：`2019` 和 `2021`
2. 任务从 `single phoneme -> phoneme pairs -> words/pseudowords` 逐步增加复杂度
3. 加入了 `TMS` 条件来观察构音相关脑区和语言相关脑区的影响
4. 数据以 `BIDS` 方式组织，方便复现

### 4.3 这套实验本质上在做什么

按当前可直接利用的数据结构来看，这套实验更接近：

- 听语音刺激
- EEG 记录脑反应
- 被试做辨别 / 按键响应
- 结合语音标签和 TMS 条件做分析

不是：

- imagined speech paired audio
- 被试自己说话的配对语音重建数据

### 4.4 基本概念

#### [EEG]()

头皮脑电。优点是非侵入、时间分辨率高；缺点是噪声大、空间定位弱。

#### [Speech decoding]()

不是传统麦克风语音识别，而是：

`从脑信号里推断被试正在处理什么语音单位。`

#### [Phoneme]()

音位。可近似理解成语言里最小的可区分语音单位。

#### CV / VC / CVC

- `C`: consonant, 辅音
- `V`: vowel, 元音

所以：

- `CV` = 辅音 + 元音，例如 `ba`
- `VC` = 元音 + 辅音，例如 `ab`
- `CVC` = 辅音 + 元音 + 辅音，例如 `bad`

#### Real / nonce

- `real`: 真词
- `nonce` / `pseudoword`: 假词

#### Articulation / coarticulation

- `articulation`: 发音动作
- `coarticulation`: 前后音相互影响的协同构音

#### Place / manner / voicing

- `place`: 发音部位，例如 `bilabial`、`alveolar`
- `manner`: 发音方式，例如 `stop`、`fricative`
- `voicing`: 是否带声，例如 `voiced`、`unvoiced`

#### TMS

经颅磁刺激。这里主要作为实验条件变量，而不是预测目标本身。

## 5. 研究对象：两批数据与三类任务

### 5.1 两批数据

#### Study 1

- 年份：`2019`
- 被试：`P01-P08`
- 核心任务：`phoneme pairs`
- 重点结构：`CV / VC`

#### Study 2

- 年份：`2021`
- 被试：`S01-S16`
- 任务扩展为：
  - `single-phoneme`
  - `phonemes`
  - `Words`

即：

- `2019`: 较早、较小、较基础
- `2021`: 更完整、更适合开发模型

### 5.2 三类任务分别是什么

#### `single-phoneme`

含义：

- 单个语音单位
- 离散 speech-unit 结构最清晰的任务

真实示例：

- [sub-S01_ses-02_task-singlephoneme_events.tsv](/Users/samxie/Research/EEG-Voice/openneuro_downloads/ds006104-download/sub-S01/ses-02/eeg/sub-S01_ses-02_task-singlephoneme_events.tsv)

示例片段：

```text
336.489  stimulus  phoneme1=a  tms_target=control_
338.426  stimulus  phoneme1=i  tms_target=control_
346.4365 stimulus  phoneme1=s  tms_target=control_
```

如何理解：

- 每个刺激就是一个音
- 可用于分类、embedding、token purity、leave-one-subject-out baseline

#### `phonemes`

含义：

- 双音组合任务
- 适合承载小序列和 articulatory 结构分析

真实示例：

- [sub-P01_ses-01_task-phonemes_events.tsv](/Users/samxie/Research/EEG-Voice/openneuro_downloads/ds006104-download/sub-P01/ses-01/eeg/sub-P01_ses-01_task-phonemes_events.tsv)

示例片段：

```text
7.154   TMS       category=alveolar  tms_target=control_lip  trial=1
7.204   stimulus  phoneme1=i phoneme2=t
11.137  TMS       category=bilabial  tms_target=lip         trial=2
11.187  stimulus  phoneme1=b phoneme2=o
```

如何理解：

- 一个完整 trial 里通常至少有 `TMS` 和 `stimulus` 两类事件
- 标签可以从 `phoneme1 + phoneme2`、`place / manner / voicing`、`tmstarget` 三层理解

#### `Words`

含义：

- 词 / 假词任务
- 最高层的 lexical unit

真实示例：

- [sub-S01_ses-02_task-Words_events.tsv](/Users/samxie/Research/EEG-Voice/openneuro_downloads/ds006104-download/sub-S01/ses-02/eeg/sub-S01_ses-02_task-Words_events.tsv)

示例片段：

```text
2487.3975 TMS       category=real   tms_target=BA06
2487.4475 stimulus  phoneme1=b phoneme2=o
2490.194  TMS       category=nonce  tms_target=control_BA06
2490.244  stimulus  phoneme1=t phoneme2=u
```

如何理解：

- 当前 BIDS 事件流里 `category` 可直接区分 `real / nonce`
- 但完整 `CVC` 级词结构，不能只靠 BIDS `events.tsv` 恢复

## 6. 当前仓库与目录怎么读

### 6.1 仓库最重要的几个目录

```text
ref_github/speech_decoding/
├── events_information/        # 本地事件表
├── exploration_outputs/       # 表格、图表、EDF 分析与完整导出
├── matlab_code/               # 原作者 MATLAB 技术验证代码
├── reports/                   # 当前只保留本手册
├── scripts/                   # 数据读取、分析、完整导出脚本
└── sensors_layout/            # 电极布局
```

### 6.2 OpenNeuro BIDS 目录怎么读

标准路径格式：

```text
openneuro_downloads/ds006104-download/sub-[subject]/ses-[session]/eeg/
```

例如：

- `sub-P03/ses-01/eeg/`
- `sub-S01/ses-02/eeg/`

根目录最关键的元数据有：

- `dataset_description.json`
- `participants.tsv`
- `participants.json`
- `README`

### 6.3 `ds006104/` 和 `events_information/` 的关系

它们不是两套互相独立的数据。

更准确的理解是：

1. `ds006104` / `openneuro_downloads/ds006104-download`
   是标准公开主数据源
2. `events_information/`
   是本地事件表整理层，更适合快速汇总和补充某些字段

后续做正式可复现分析时，应优先以 BIDS 结构为主；需要补字段时，再回看本地事件表。

## 7. BIDS 文件结构与字段解释

下面按最常用文件类型说明“是什么、从哪里来、有什么含义、怎么用”。

### 7.1 `*_eeg.edf`

来源：

- OpenNeuro 原始 EEG 主文件

含义：

- 连续脑电主文件
- 不是按 trial 切好的样本
- 一个文件通常对应一整场 recording

当前项目示例：

- `openneuro_downloads/ds006104-download/sub-P01/ses-01/eeg/sub-P01_ses-01_task-phonemes_eeg.edf`

后面怎么用：

- 先读取成连续 EEG
- 再结合 `events.tsv` 的 onset 切 epoch

### 7.2 `*_events.tsv`

来源：

- OpenNeuro BIDS sidecar

含义：

- 实验事件流
- 每一行是一个事件，不一定是一整个 trial 汇总

当前最重要的列有：

- `onset`
- `duration`
- `trial_type`
- `phoneme1`
- `phoneme2`
- `phoneme3`
- `category`
- `place`
- `manner`
- `voicing`
- `tms_target`
- `trial`

如何理解：

- `trial_type=TMS` 表示 TMS 事件
- `trial_type=stimulus` 表示刺激真正出现的时刻
- 后续切 `stimulus-locked epoch` 的核心时间基准是这里的 `stimulus onset`

### 7.3 `*_events.json`

来源：

- OpenNeuro BIDS sidecar

含义：

- 对 `events.tsv` 每一列做字段说明

注意：

- 它给的是泛化说明
- 真正分析时必须结合 `events.tsv` 的真实值去理解

例如：

- `category` 在不同任务里含义不完全一样
- 在 `Words` 里常见 `real / nonce`
- 在其他任务里会带不同类型的发音类别信息

### 7.4 `*_channels.tsv`

来源：

- OpenNeuro BIDS sidecar

含义：

- 说明通道名字、类型和单位

真实示例：

- [sub-P01_ses-01_task-phonemes_channels.tsv](/Users/samxie/Research/EEG-Voice/openneuro_downloads/ds006104-download/sub-P01/ses-01/eeg/sub-P01_ses-01_task-phonemes_channels.tsv)

示例片段：

```text
name  type  units
Fp1   EEG   uV
Fpz   EEG   uV
Fp2   EEG   uV
F7    EEG   uV
F3    EEG   uV
```

对应信息包括：

- 标准 EEG 通道有哪些
- 后面提取数据时哪些是 EEG、哪些不是

### 7.5 `*_eeg.json`

来源：

- OpenNeuro BIDS sidecar

含义：

- 采样率、参考电极、地电极、电源频率、硬件滤波、帽子型号等元数据

真实示例：

- [sub-P01_ses-01_task-phonemes_eeg.json](/Users/samxie/Research/EEG-Voice/openneuro_downloads/ds006104-download/sub-P01/ses-01/eeg/sub-P01_ses-01_task-phonemes_eeg.json)

示例片段：

```json
{
  "TaskName": "phonemes",
  "TaskDescription": "Listening to consonant-vowel and vowel-consonant phoneme pairs.",
  "Instructions": "Participants listened to audio clips immersed in white noise and responded with button presses.",
  "EEGReference": "CPz",
  "EEGGround": "AFz",
  "SamplingFrequency": 2000
}
```

对应信息包括：

- 当前任务是 `phonemes`
- 任务本质是听刺激并按键反应
- 原始采样率是 `2000 Hz`
- 参考电极是 `CPz`

### 7.6 `*_coordsystem.json`

来源：

- OpenNeuro BIDS sidecar

含义：

- 电极坐标系统说明

作用：

- 后续如果要画头皮拓扑图或解释电极布局，会用到这一层

### 7.7 `participants.tsv`

来源：

- OpenNeuro 根目录元数据

含义：

- 列出参与者
- 哪些人属于 `Study 1`
- 哪些人属于 `Study 2`

### 7.8 本地事件表里的额外字段

来自：

- `events_information/*_Tab.csv`
- 标准化结果见 [local_events_manifest.csv](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/exploration_outputs/tables/local_events_manifest.csv)

这些字段在后面很重要：

- `stimulus`
- `phoneme1 / phoneme2 / phoneme3`
- `p1_tsidx / p2_tsidx / p3_tsidx`
- `tmstarget`
- `order`
- `study_year`

特别要注意：

- `2019` 有 `order`，但没有 `phoneme3 / p3_tsidx`
- `2021` 有 `phoneme3 / p3_tsidx`，但大多没有 `order`

## 8. 当前本地数据状态与 EDF 完整导出

### 8.1 当前本地数据状态

当前工作区已经不只是 sidecar 了。

从当前结果看：

- 原始 EDF 已经成功 hydrated
- 描述性 EDF 分析已经完成
- 完整 HDF5 导出已经完成

其中当前记录是：

- `56` 个 EDF 条目
- `56` 个完成导出
- `0` 个失败

### 8.2 描述性分析结果是什么

单个记录目录下已有的描述性结果包括：

- `*_summary.json`
- `*_channel_stats.csv`
- `*_full_overview.png`
- `*_psd.png`
- `*_channel_std_top20.png`

这些结果的作用是：

- 检查 EDF 是否正常
- 看全程波形大概形态
- 看通道统计和频谱概览

但它们不是后面训练时真正的数据本体。

### 8.3 当前完整导出结果是什么

单个记录目录下当前包含：

- `*_full_eeg.h5`
- `*_full_export_manifest.json`

例如：

- [sub-P01_ses-01_task-phonemes_eeg_full_eeg.h5](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/exploration_outputs/edf_full_analysis/sub-P01_ses-01_task-phonemes_eeg/sub-P01_ses-01_task-phonemes_eeg_full_eeg.h5)
- [sub-P01_ses-01_task-phonemes_eeg_full_export_manifest.json](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/exploration_outputs/edf_full_analysis/sub-P01_ses-01_task-phonemes_eeg/sub-P01_ses-01_task-phonemes_eeg_full_export_manifest.json)

manifest 关键信息示例：

```json
{
  "sampling_frequency_hz": 2000.0,
  "sample_count": 6574000,
  "total_channel_count": 62,
  "eeg_channel_count": 61,
  "non_eeg_channel_names": ["Status"],
  "data_unit": "uV"
}
```

解释：

- EDF 总共有 `62` 个通道
- 其中 `61` 个是真正 EEG
- 非 EEG 通道是 `Status`
- HDF5 里保存的是完整 EEG 矩阵，单位已统一成 `uV`

### 8.4 `*_summary.json` 和 `*_full_eeg.h5` 的区别

#### `*_summary.json`

是轻量级摘要，例如：

- 原始采样率
- 分析时使用的重采样率
- 通道数
- 时长
- 全局统计量

示例文件名：

- `sub-P01_ses-01_task-phonemes_eeg_summary.json`

#### `*_full_eeg.h5`

是完整 EEG 数据本体，后面切 epoch、构造 trial dataset、训练模型都要从它开始。

一句话区分：

- `summary.json` 属于摘要层
- `full_eeg.h5` 属于完整矩阵层

### 8.5 当前目录中各类文件分别是什么

以 [sub-P01_ses-01_task-phonemes_eeg](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/exploration_outputs/edf_full_analysis/sub-P01_ses-01_task-phonemes_eeg) 为例：

#### 原始定义复制件

- `sub-P01_ses-01_task-phonemes_events.tsv/json`
- `sub-P01_ses-01_task-phonemes_channels.tsv`
- `sub-P01_ses-01_task-phonemes_eeg.json`
- `sub-P01_ses-01_coordsystem.json`

#### 描述性分析结果

- `sub-P01_ses-01_task-phonemes_eeg_summary.json`
- `sub-P01_ses-01_task-phonemes_eeg_channel_stats.csv`
- `sub-P01_ses-01_task-phonemes_eeg_full_overview.png`
- `sub-P01_ses-01_task-phonemes_eeg_psd.png`
- `sub-P01_ses-01_task-phonemes_eeg_channel_std_top20.png`

#### 完整导出结果

- `sub-P01_ses-01_task-phonemes_eeg_full_eeg.h5`
- `sub-P01_ses-01_task-phonemes_eeg_full_export_manifest.json`

## 9. 数据结构与标签的主要分析结论

### 9.1 受试者与任务规模

基于事件级整理结果，可以把当前数据整体规模概括为：

- 总 trial 数：`14630`
- `2019 phonemes = 3742`
- `2021 phonemes = 3840`
- `2021 single-phoneme = 3355`
- `2021 Words = 3693`

相关图表：

- [subject_trial_counts.png](../exploration_outputs/figures/subject_trial_counts.png)
- [subject_task_trial_counts.png](../exploration_outputs/ds006104_bids_analysis/figures/subject_task_trial_counts.png)

### 9.2 任务与 TMS 条件绑定得很紧

关键结论：

1. `phonemes` 只和 `lip / tongue / control_lip / control_tongue` 紧密绑定
2. `Words` 只和 `BA06 / BA44 / control_BA06 / control_BA44` 紧密绑定
3. `single-phoneme` 全部是 `control` 条件，没有 active TMS

图表：

- [tms_target_by_task_heatmap.png](../exploration_outputs/figures/tms_target_by_task_heatmap.png)
- [task_tms_heatmap.png](../exploration_outputs/data_priority/figures/task_tms_heatmap.png)

含义：

- 不同任务不能简单混成统一条件空间
- 模型与分析需要按任务拆开解释

### 9.3 `single-phoneme` 是结构最清晰的起点

关键结论：

- `16` 名被试
- `3355` trials
- `11` 个音
- 每类约 `305` 条
- 全部是 `control*` 条件

这使它成为：

- 适合作为离散 speech-unit 的起点子集
- 适合用于验证 EEG token 的可分性

### 9.4 `Words` 对应较高层 lexical unit

关键结论：

- `real / nonce` 基本完全均衡
- 适合做 coarse lexical token
- 但完整 `CVC` 结构不能只依赖 BIDS `events.tsv`

### 9.5 跨年份比较只能落在 shared `20` 个 CV units

关键结论：

- `2019 phonemes` 有 `40` 个 units
- `2021 phonemes` 有 `20` 个 units
- 真正跨年份稳妥共享的是 `20` 个 `CV` units
- `2019` 额外多的是 `VC` units

图表：

- [phoneme_overlap_2019_2021.png](../exploration_outputs/ds006104_bids_analysis/figures/phoneme_overlap_2019_2021.png)
- [phoneme_base_overlap.png](../exploration_outputs/data_priority/figures/phoneme_base_overlap.png)

### 9.6 事件时间结构不完全一致

关键结论：

- `Words`: `TMS -> stimulus` 间隔固定 `50 ms`
- `phonemes`: 也固定 `50 ms`
- `single-phoneme`: 不是固定值，约在 `70.0-427.5 ms` 之间变化，中位数 `89.5 ms`

含义：

- `single-phoneme` 任务不宜用固定偏移替代真实 onset
- 后续 epoch 仍需使用真实 recorded onset

图表：

- [tms_to_stim_interval_by_task.png](../exploration_outputs/ds006104_bids_analysis/figures/tms_to_stim_interval_by_task.png)

### 9.7 字段并不完全统一

当前最值得注意的字段问题：

1. `2019` 使用 `Correct_Key`，`2021` 使用 `Correct_key`
2. `2019` 有 `order`，没有 `phoneme3 / p3_tsidx`
3. `2021` 有 `phoneme3 / p3_tsidx`，但大多没有 `order`
4. `Words` 任务里，BIDS 事件流的 `phoneme3` 恢复不完整

相关图表：

- [field_missingness.png](../exploration_outputs/figures/field_missingness.png)
- [field_coverage_bids_vs_local.png](../exploration_outputs/ds006104_bids_analysis/figures/field_coverage_bids_vs_local.png)

含义：

- 字段“缺失”很多时候不是脏数据，而是任务设计差异
- 分析前必须先做标准化和任务分层

## 10. 数据边界：能做什么、不能做什么

当前最重要的边界判断见：

- [alignment_granularity.csv](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/exploration_outputs/data_priority/tables/alignment_granularity.csv)
- [supervision_signal_matrix.csv](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/exploration_outputs/data_priority/tables/supervision_signal_matrix.csv)

### 10.1 当前能做的

- `trial-level` 数据观察和分析
- `stimulus onset` 驱动的切窗准备
- 单音、双音、词级离散 speech-unit 研究
- articulatory feature 分析
- EEG token 学习
- EEG sequence 到 speech token sequence 的弱监督对齐

### 10.2 当前不能直接做的

- frame-level speech alignment
- 基于公开数据直接做 `EEG -> mel`
- 基于公开数据直接做 `EEG -> waveform`
- 被试自己语音的配对监督

### 10.3 为什么现在不能直接做 `EEG -> voice`

因为当前公开数据缺：

- 公开 stimulus audio 波形
- phoneme boundaries / durations
- mel / vocoder target
- 被试自己发声的 paired audio

所以 Moreira 更适合：

`speech-unit EEG token 准备`

而不是：

`Lee 2023 式 EEG-to-voice reconstruction`

## 11. 子集优先级与研究顺序

优先级表：

- [candidate_subset_priority.csv](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/exploration_outputs/data_priority/tables/candidate_subset_priority.csv)

按当前数据质量和标签结构，可按以下顺序展开。

### 11.1 第一优先级：`2021 single-phoneme`

原因：

- 结构最清晰
- 类别最均衡
- 全部为 control 条件
- 适合首先检验 EEG token 的可分性

### 11.2 第二优先级：`2021 Words`

原因：

- `real / nonce` 分布较均衡
- 更接近高层 lexical unit

限制：

- 完整词级 `CVC` 不能只靠 BIDS events 恢复

### 11.3 第三优先级：`control-only phonemes`

原因：

- 唯一具备明确跨 `2019/2021` 对齐基础的离散 phoneme 子集

限制：

- 跨年份只能稳定落在 shared `20` 个 `CV` units 上

## 12. 当前项目里这些结果文件分别是干什么的

### 12.1 最重要的表格

- [local_events_manifest.csv](../exploration_outputs/tables/local_events_manifest.csv)
  标准化本地事件总表
- [candidate_subset_priority.csv](../exploration_outputs/data_priority/tables/candidate_subset_priority.csv)
  最值得先看的子集排序
- [supervision_signal_matrix.csv](../exploration_outputs/data_priority/tables/supervision_signal_matrix.csv)
  当前已有/缺失的监督类型
- [alignment_granularity.csv](../exploration_outputs/data_priority/tables/alignment_granularity.csv)
  当前最多支持到哪一层对齐
- [bids_trial_manifest.csv](../exploration_outputs/ds006104_bids_analysis/tables/bids_trial_manifest.csv)
  从 BIDS 事件流还原的 trial 级 manifest

### 12.2 最重要的图

- [label_taxonomy.png](../exploration_outputs/figures/label_taxonomy.png)
  标签体系总图
- [tms_target_by_task_heatmap.png](../exploration_outputs/figures/tms_target_by_task_heatmap.png)
  任务和 TMS 条件的关系
- [alignment_granularity.png](../exploration_outputs/data_priority/figures/alignment_granularity.png)
  对齐粒度总览
- [candidate_subset_balance.png](../exploration_outputs/data_priority/figures/candidate_subset_balance.png)
  子集平衡性
- [task_size_and_unique_stimuli.png](../exploration_outputs/data_priority/figures/task_size_and_unique_stimuli.png)
  任务规模和 unique stimuli

### 12.3 最重要的脚本

- [generate_moreira_exploration.py](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/scripts/generate_moreira_exploration.py)
  生成数据探索结果
- [generate_moreira_data_priority.py](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/scripts/generate_moreira_data_priority.py)
  生成优先级、监督矩阵、对齐粒度结果
- [analyze_ds006104_bids.py](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/scripts/analyze_ds006104_bids.py)
  BIDS 事件级分析
- [read_edf_full_analysis.py](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/scripts/read_edf_full_analysis.py)
  EDF 描述性分析
- [export_edf_full_data.py](/Users/samxie/Research/EEG-Voice/ref_github/speech_decoding/scripts/export_edf_full_data.py)
  EDF 完整 HDF5 导出

## 13. EEG token / speech token 研究路径

### 13.1 研究目标

当前更稳妥的目标不是：

- `EEG -> mel`
- `EEG -> waveform`

而是：

`弱监督 speech-unit EEG token 学习`

### 13.2 核心研究问题

研究问题可压缩为 3 个方面：

1. EEG 里能不能学出稳定的 speech-unit token
2. 这些 token 能不能和 speech-side token 对齐
3. 这些 token 能不能跨被试、跨年份泛化

### 13.3 实现顺序

#### 第一阶段：统一 epoch 数据集

从：

- `*_full_eeg.h5`
- `*_events.tsv`

构建：

- stimulus-locked epoch
- trial-level label dataset

#### 第二阶段：连续 EEG embedding

首版可先学习连续表征，离散量化放在后一步处理。

#### 第三阶段：EEG token 化

首版可采用：

- encoder 提 embedding
- 训练集上做 `k-means`
- 得到离散 `EEG token`

#### 第四阶段：speech-side token 定义

当前阶段更适合使用符号 token，而不是音频 tokenizer：

- `single-phoneme`: `phoneme1`
- `phonemes`: `[phoneme1, phoneme2]`
- `Words`: `[phoneme1, phoneme2, phoneme3]` 或 `real/nonce`

#### 第五阶段：弱监督对齐

与当前数据结构更匹配的方法是：

- `CTC`

原因在于当前数据结构具有以下特点：

- 输入：长度较长的 EEG sequence
- 输出：长度较短的 speech token sequence
- 对齐未知但单调

### 13.4 训练范式

#### 阶段 A：表征预训练

可以考虑：

- masked reconstruction
- contrastive learning
- temporal prediction

#### 阶段 B：speech-unit 监督学习

先做：

- single-phoneme classification
- articulatory feature classification
- `real / nonce` classification

#### 阶段 C：序列对齐训练

正式模型采用：

- EEG encoder
- sequence output
- `CTC + classification + contrastive` 组合损失

### 13.5 baseline

1. bandpower + SVM
2. EEGNet / shallow convnet
3. continuous embedding + linear probe
4. encoder + CTC

### 13.6 评估指标

- accuracy
- macro-F1
- balanced accuracy
- token purity / NMI / ARI
- token error rate / edit distance
- EEG-to-token retrieval
- leave-one-subject-out
- cross-year transfer

### 13.7 实验顺序

1. `2021 single-phoneme`
2. `control-only phonemes`
3. `2021 Words`

## 14. 阅读清单与搜索词

### 14.1 优先阅读的论文

1. Moreira et al., 2025
   `An open-access EEG dataset for speech decoding: Exploring the role of articulation and coarticulation`
   https://www.nature.com/articles/s41597-025-05187-2
2. Défossez et al., 2023
   `Decoding speech perception from non-invasive brain recordings`
   https://www.nature.com/articles/s42256-023-00714-5
3. Lee et al., 2023
   `Towards Voice Reconstruction from EEG during Imagined Speech`
   https://doi.org/10.1609/aaai.v37i5.25745
4. BENDR, 2021
   `BENDR: Using Transformers and a Contrastive Self-Supervised Learning Task to Learn From Massive Amounts of EEG Data`
   https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2021.653659/full
5. Graves et al., 2006 / Distill 2017
   `Connectionist temporal classification`
   https://doi.org/10.1145/1143844.1143891
   https://distill.pub/2017/ctc/

### 14.2 第二优先级方法论文

1. `vq-wav2vec`
   https://arxiv.org/abs/1910.05453
2. `wav2vec 2.0`
   https://arxiv.org/abs/2006.11477
3. `HuBERT`
   https://arxiv.org/abs/2106.07447
4. Bollens et al., 2025
   `Contrastive representation learning with transformers for robust auditory EEG decoding`
   https://www.nature.com/articles/s41598-025-13646-4

### 14.3 检索词

#### 数据与任务边界

```text
Moreira 2025 open-access EEG dataset speech decoding articulation coarticulation
ds006104 speech decoding EEG OpenNeuro
non-invasive speech perception EEG decoding phoneme word
```

#### 非侵入 speech perception / auditory EEG

```text
Decoding speech perception from non-invasive brain recordings EEG wav2vec contrastive
auditory EEG decoding contrastive learning transformer
continuous speech EEG decoding wav2vec
speech perception EEG self-supervised representations
```

#### EEG 自监督表征学习

```text
BENDR EEG self-supervised learning transformers
EEG masked autoencoder representation learning
Large Brain Model EEG generic representations
contrastive learning EEG representation learning
```

#### speech token / speech SSL

```text
vq-wav2vec discrete speech representations
wav2vec 2.0 self-supervised speech representations
HuBERT hidden units speech representations
discrete speech units self-supervised speech
```

#### 序列对齐

```text
connectionist temporal classification speech recognition Graves 2006
CTC weakly supervised alignment token sequence
CTC phoneme alignment without boundaries
```

### 14.4 暂不优先的检索词

```text
EEG to voice reconstruction
imagined speech EEG classification accuracy
brain to speech waveform
```

原因是：

- 检索结果容易偏向 imagined speech 或 invasive ECoG 主线
- 与当前数据条件不完全匹配

## 15. 关键风险、误区与边界提醒

### 15.1 最容易误解的地方

1. 误解成 imagined speech 数据
2. 误解成有 EEG 就能直接做语音重建
3. 误解成所有任务共享同一套标签与条件空间
4. 误解成 `category` 在所有任务里都表示同一件事
5. 误解成 `summary / PSD` 已经等于完整 EEG 分析

### 15.2 当前最大工程风险

1. 忽视 trial 切片，直接在连续 recording 上做不清晰分析
2. 忽视 `single-phoneme` 的真实 onset 差异
3. 把不同任务强行混训
4. 把旧报告里某些过时状态当成当前状态

### 15.3 对“完整内容”的界定

完整内容不是：

- 多几张全程概览图
- 多几个通道统计表

更接近完整实验链条的是：

`full_eeg.h5 + events.tsv -> stimulus-locked epoch -> trial dataset -> baseline -> EEG token -> speech token 对齐`

## 16. 工作顺序概括

按当前数据条件，后续工作顺序可概括为：

1. 基于 `*_full_eeg.h5` 和 `*_events.tsv` 构建 stimulus-locked epoch
2. 在 `2021 single-phoneme` 上完成第一版 baseline
3. 将 `phonemes` 和 `Words` 纳入序列建模与对齐

这对应于当前项目从“看懂数据”走向“可训练实验”的主线。
