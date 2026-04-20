# ds006104 本地 BIDS 数据集说明

## 1. 一句话先说清楚

`ds006104/` 不是另外一套新数据，而是 `Moreira et al., 2025` 对应的 `OpenNeuro` 公开主数据源在本地的 `BIDS` 目录。

如果只看作用，它比前面单独整理的 `events_information/` 更正式，也更接近后续真正做可复现分析时应该读取的标准入口。

## 2. 这个目录是干什么的

这个目录的主要作用不是“再提供一份论文摘要”，而是把公开数据按 `BIDS` 规范组织起来，让你知道：

- 有哪些被试
- 每个被试有哪些任务
- 每个任务有哪些事件
- EEG 的采样率、参考电极、通道信息是什么
- TMS 的目标区域和刺激参数是什么

换句话说，`ds006104/` 是“正式数据结构”，而不是“已经整理好的实验表格”。

## 3. 它和前面那些材料是什么关系

可以把几套东西这样区分：

1. `events_information/`
   这是仓库里原来就有的事件表，适合快速汇总和做描述性统计。
2. `ds006104/`
   这是标准 `BIDS` 数据目录，适合后续按官方公开结构做正式读取。
3. `reports/`
   这是对论文、数据和概念的中文解释，不是原始数据本身。
4. `exploration_outputs/`
   这是基于前面材料生成的汇总表、图表和验证结果。

所以，`ds006104/` 的加入，最大的意义不是“又多了一份数据”，而是：

`现在本地已经有了更标准的官方数据组织形式。`

## 4. 本地目录里现在有什么

基于当前工作区，`ds006104/` 里已经能直接看到这些内容：

- 根目录元数据：
  - `dataset_description.json`
  - `README`
  - `participants.tsv`
  - `participants.json`
- 受试者目录：
  - `24` 个受试者
  - `sub-P01` 到 `sub-P08`
  - `sub-S01` 到 `sub-S16`
- 任务文件：
  - `24` 份 `task-phonemes_events.tsv`
  - `16` 份 `task-singlephoneme_events.tsv`
  - `16` 份 `task-Words_events.tsv`
- 每个任务对应的：
  - `events.tsv`
  - `events.json`
  - `channels.tsv`
  - `eeg.json`
- 其他元数据：
  - `coordsystem.json`
  - `sourcedata/tms_metadata/tms_parameters.json`
  - `derivatives/eeglab/dataset_description.json`

## 5. 它说明了什么实验

从 `dataset_description.json` 和 `README` 可以直接确认，这个数据集包含两批相关研究：

### Study 1

- 年份：`2019`
- 被试：`P01-P08`
- session：`ses-01`
- 任务重点：`CV` 和 `VC` phoneme pairs
- TMS 目标：`LipM1`、`TongueM1`

### Study 2

- 年份：`2021`
- 被试：`S01-S16`
- session：`ses-02`
- 任务扩展为：
  - `singlephoneme`
  - `phonemes`
  - `Words`
- 新增 TMS 目标：
  - `BA44`
  - `BA06`

从 `README` 的原文设定看，这些任务都属于：

`听觉刺激 + button-press phoneme discrimination task，并叠加不同 TMS 条件。`

这说明它本质上还是一个语音辨别/解码数据集，不是 imagined speech paired-audio 数据集。

## 6. BIDS 文件应该怎么读

### 6.1 根目录文件

- `dataset_description.json`
  - 说明数据集名称、BIDS 版本、作者、DOI、研究描述
- `participants.tsv`
  - 列出全部参与者，并告诉你哪些人属于 `Study1`、哪些属于 `Study2`
- `participants.json`
  - 对 `participants.tsv` 每一列做字段说明

### 6.2 受试者目录

目录格式是：

```text
ds006104/sub-[subject]/ses-[session]/eeg/
```

例如：

- `sub-P03/ses-01/eeg/`
- `sub-S01/ses-02/eeg/`

### 6.3 `events.tsv`

这是最值得先看的文件。

它不是“每行一个完整 trial 的汇总表”，而更像“实验事件流”。

以 `sub-P03_ses-01_task-phonemes_events.tsv` 为例，可以看到一个很典型的结构：

1. 一行 `trial_type = TMS`
2. 紧接着一行 `trial_type = stimulus`

也就是说，单个 trial 往往包含至少两类事件：

- TMS 事件
- 刺激出现事件

这和之前的本地整理版事件表不完全一样，阅读时要注意。

### 6.4 `events.json`

这个文件解释 `events.tsv` 每一列是什么意思，例如：

- `onset`
- `duration`
- `trial_type`
- `phoneme1/phoneme2/phoneme3`
- `place`
- `manner`
- `voicing`
- `category`
- `tms_target`
- `tms_intensity`
- `trial`

但这里也要注意一个实际问题：

`events.json` 的字段描述比较泛，而真实列值会随任务变化。

例如：

- 在 `phonemes` 任务里，`category` 更像 articulatory 类别的一部分
- 在 `Words` 任务里，`category` 实际上出现了 `real / nonce`
- 在 `singlephoneme` 任务里，`category` 还会出现 `vowels`

所以后续分析不能只照抄 `events.json` 的一句说明，而要结合真实 `events.tsv` 一起理解。

### 6.5 `eeg.json`

这个文件说明原始 EEG 采集参数。

例如 `sub-S01_ses-02_task-phonemes_eeg.json` 里已经可以直接看到：

- `TaskName = phonemes`
- `SamplingFrequency = 2000`
- `EEGReference = CPz`
- `EEGGround = AFz`
- `PowerLineFrequency = 60`
- 硬件滤波约为 `0.1-350 Hz`
- 采集系统为 `ANT Neuro WaveGuard 64-channel cap + eego mylab system`

这类信息对于后面做正式预处理是必要的。

### 6.6 `channels.tsv`

这个文件给出通道名称、类型和单位。

当前样本里可以直接看到标准 `extended 10-20 system` 下的 EEG 通道，例如：

- `Fp1`
- `Fz`
- `Cz`
- `Pz`
- `O1`

单位是 `uV`。

### 6.7 `coordsystem.json`

这个文件告诉你电极坐标系统使用的是：

- `extended 10-20 system`
- 坐标单位是 `mm`

这对后面画 topography 或对接电极布局文件时有帮助。

### 6.8 `sourcedata/tms_metadata/tms_parameters.json`

这个文件补充了 TMS 的实验参数，例如：

- 刺激设备：`Magstim Super Rapid Plus1`
- 线圈：`figure-of-eight`
- 强度：`110% resting motor threshold`
- 方式：`paired-pulse`
- 脉冲间隔：`50 ms`
- 目标脑区的 `MNI` 坐标

这部分是论文方法细节的重要来源。

## 7. 当前本地状态要注意什么

虽然 `ds006104/` 的目录结构已经在本地，但当前工作区里还没有看到真正下载下来的原始 `.edf` 文件。

当前本地检查结果是：

- `24` 个受试者目录在
- 各任务的 `events/channels/eeg/coordsystem` sidecars 在
- `sourcedata` 和 `derivatives` 元数据在
- 原始 `.edf` 当前未见本地文件
- 预处理 `.set/.fdt` 当前也未见本地文件

这通常说明当前目录更像是：

`一个已克隆但尚未把大文件 fully downloaded 到本地的 OpenNeuro/DataLad 数据仓库。`

所以现在可以做的事情主要是：

- 看清数据结构
- 看清标签和条件
- 明确任务边界
- 为后续正式读取代码做准备

但现在还不能直接在这个本地目录上做完整原始 EEG 波形分析。

## 8. 这个目录现在最有价值的地方

对当前阶段来说，`ds006104/` 最有价值的不是“给出更多结果”，而是让很多问题有了标准答案：

1. 官方数据的任务名到底怎么写
   - `phonemes`
   - `singlephoneme`
   - `Words`
2. 官方数据的事件字段到底叫什么
3. 采样率、参考电极、地电极、通道单位是什么
4. TMS 参数和目标脑区坐标是什么
5. Study 1 和 Study 2 在 BIDS 中如何区分

这些信息会直接影响后续：

- 数据读取脚本怎么写
- manifest 怎么和 BIDS 对齐
- 哪些标签是任务专有的，哪些能跨任务复用

## 9. 对当前研究的实际意义

把 `ds006104/` 放进工作区之后，当前项目的材料层级已经更完整了：

1. `论文`
2. `本地事件表`
3. `官方 BIDS 目录`
4. `中文解释和汇总结果`

这意味着后续如果要继续往前走，优先顺序应该是：

1. 继续以 `ds006104/` 核对官方字段和任务边界
2. 保持 `events_information/` 作为快速汇总入口
3. 真要进入信号分析时，再决定是否把 `.edf` 或衍生大文件完整拉到本地

## 10. 当前最简结论

`ds006104/` 是 Moreira 2025 对应的官方公开 BIDS 数据目录。

它现在最重要的价值是：

- 补足了标准元数据
- 让任务结构和事件语义更清楚
- 为后续正式的数据读取和可复现分析提供入口

它现在还不是“已经能直接开跑完整 EEG 分析”的状态，因为当前本地尚未看到原始 `.edf` 文件。
