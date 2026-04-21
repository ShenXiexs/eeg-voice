# EEG Speech Token 阅读与检索清单

这份清单不是“列很多论文”，而是帮你节省时间。

目标是回答两个问题：

1. 你应该先读什么，才能把当前项目做成一篇稳的文章。
2. 你在 Google 或 Google Scholar 上应该搜什么，才不会被大量不相关的 imagined speech / invasive speech reconstruction 文章带偏。

## 1. 先给结论

你的阅读顺序最好分成 5 层：

1. 数据集和任务边界
2. 非侵入 EEG speech / speech perception 解码
3. EEG 自监督表征学习
4. speech-side token / SSL speech representation
5. 序列对齐方法

不要一开始扎进：

- 纯 imagined speech 分类综述
- 大量 invasive ECoG-to-speech 重建论文
- 纯 ASR 工程论文

这些要读，但不是第一层。

## 2. 第一优先级：你现在必须读的论文

### 2.1 Moreira et al., 2025

题目：

`An open-access EEG dataset for speech decoding: Exploring the role of articulation and coarticulation`

为什么先读：

- 这是你当前数据的官方主文献
- 你要知道作者原本想让这套数据支持哪些层级任务
- 你后面论文里 dataset section、limitations section 都会引用它

Google / Scholar 建议直接搜：

`Moreira 2025 open-access EEG dataset speech decoding articulation coarticulation`

链接：

- https://www.nature.com/articles/s41597-025-05187-2

你读的时候重点看：

- stimulus 设计
- 任务层级：single / pair / word
- TMS 条件
- 公开数据记录到底提供了什么

### 2.2 Défossez et al., 2023

题目：

`Decoding speech perception from non-invasive brain recordings`

为什么重要：

- 这是非常接近你目标的问题设置
- 它不是 speech production，而是 speech perception
- 它直接把 `pretrained speech representations + contrastive learning + non-invasive EEG/MEG` 连起来了

Google / Scholar 建议搜：

`Decoding speech perception from non-invasive brain recordings EEG wav2vec contrastive`

链接：

- https://www.nature.com/articles/s42256-023-00714-5

你读的时候重点看：

- 为什么他们不用原始 mel 做唯一目标
- 为什么要用 pretrained speech representations
- 为什么 contrastive learning 对 noisy brain data 有帮助
- 多被试联合训练怎么做

### 2.3 Lee et al., 2023

题目：

`Towards Voice Reconstruction from EEG during Imagined Speech`

为什么要读：

- 不是因为你现在要复现它
- 而是因为它能帮你明确“你当前项目和 EEG-to-voice reconstruction 的边界”

Google / Scholar 建议搜：

`Towards Voice Reconstruction from EEG during Imagined Speech AAAI 2023`

链接：

- https://doi.org/10.1609/aaai.v37i5.25745
- https://arxiv.org/abs/2301.07173

你读的时候重点看：

- 它依赖了什么监督
- spoken / imagined 的桥接是怎么做的
- 为什么那条路线和你当前数据不完全同构

### 2.4 BENDR, 2021

题目：

`BENDR: Using Transformers and a Contrastive Self-Supervised Learning Task to Learn From Massive Amounts of EEG Data`

为什么重要：

- 这是 EEG 自监督表征学习非常值得读的一篇
- 它明确讨论了把 speech SSL 思路迁移到 EEG
- 你后面做 EEG encoder 预训练时，很容易借鉴它

Google / Scholar 建议搜：

`BENDR EEG self-supervised learning transformers contrastive`

链接：

- https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2021.653659/full

你读的时候重点看：

- EEG 预训练任务怎么设计
- 为什么他们借鉴 `wav2vec 2.0`
- 跨数据集迁移怎么评估

### 2.5 Graves et al., 2006 / Hannun, 2017

题目：

- `Connectionist temporal classification: Labelling unsegmented sequence data with recurrent neural networks`
- `Sequence Modeling With CTC`

为什么重要：

- 你当前最自然的对齐方法就是 CTC
- 不需要音素边界
- 非常适合 `EEG sequence -> speech token sequence`

Google / Scholar 建议搜：

- `CTC labelling unsegmented sequence data speech recognition Graves 2006`
- `Sequence Modeling with CTC Distill`

链接：

- https://doi.org/10.1145/1143844.1143891
- https://distill.pub/2017/ctc/

你读的时候重点看：

- 为什么 CTC 适合未知对齐
- 它要求什么样的单调 many-to-one 结构
- 为什么它比强制 frame 对齐更适合你当前数据

## 3. 第二优先级：你真正需要借鉴的方法论文

### 3.1 vq-wav2vec, 2019

题目：

`vq-wav2vec: Self-Supervised Learning of Discrete Speech Representations`

为什么重要：

- 这是“连续表征 -> 离散 token”最直接的参考之一
- 你做 EEG token 时，可以借它的思想，但不是照搬音频模型

Google / Scholar 建议搜：

`vq-wav2vec discrete speech representations`

链接：

- https://arxiv.org/abs/1910.05453

你读的时候重点看：

- 为什么先学连续表征再量化
- 为什么离散 token 对序列建模有利
- `k-means / quantization` 的角色是什么

### 3.2 wav2vec 2.0, 2020

题目：

`wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations`

为什么重要：

- 这是 speech SSL 的基础设施论文
- EEG 侧的很多对比学习、自监督策略都可以从这里借结构直觉

Google / Scholar 建议搜：

`wav2vec 2.0 self-supervised speech representations`

链接：

- https://arxiv.org/abs/2006.11477

你读的时候重点看：

- masking
- contrastive objective
- latent quantization

### 3.3 HuBERT, 2021

题目：

`HuBERT: Self-Supervised Speech Representation Learning by Masked Prediction of Hidden Units`

为什么重要：

- 它更接近“先聚类，再做 masked prediction”
- 这和你未来的 `EEG token` 设计逻辑非常接近

Google / Scholar 建议搜：

`HuBERT hidden unit BERT masked prediction hidden units`

链接：

- https://arxiv.org/abs/2106.07447

你读的时候重点看：

- offline clustering teacher
- hidden unit prediction
- 为什么 cluster labels 不必完美也能有用

### 3.4 Bollens et al., 2025

题目：

`Contrastive representation learning with transformers for robust auditory EEG decoding`

为什么重要：

- 这是很接近 auditory EEG 的近期工作
- 它把 `contrastive learning + transformer + auditory EEG` 直接串起来了

Google / Scholar 建议搜：

`contrastive representation learning transformers auditory EEG decoding`

链接：

- https://www.nature.com/articles/s41598-025-13646-4

你读的时候重点看：

- EEG preprocessing 粒度
- speech representation 选型
- downstream task 和 latent reuse 的关系

## 4. 第三优先级：你可以拿来做 EEG encoder 预训练参考的论文

### 4.1 Large Brain Model, 2024

题目：

`Large Brain Model for Learning Generic Representations with Tremendous EEG Data in BCI`

Google / Scholar 建议搜：

`Large Brain Model EEG generic representations BCI`

链接：

- https://arxiv.org/abs/2405.18765

为什么读：

- 看大规模 EEG 预训练的思路
- 看“generic representation”怎么写

### 4.2 EEG MAE, 2024

题目：

`Enhancing Representation Learning of EEG Data with Masked Autoencoders`

Google / Scholar 建议搜：

`EEG masked autoencoder representation learning`

链接：

- https://arxiv.org/abs/2408.05375

为什么读：

- 如果你想做 masked EEG pretraining，这篇很直接

## 5. 第四优先级：只读思路，不要照着复现的论文

### 5.1 Chen et al., 2024

题目：

`A neural speech decoding framework leveraging deep learning and speech synthesis`

链接：

- https://www.nature.com/articles/s42256-024-00824-8

为什么读：

- 它展示了“中间 speech representation + speech synthesizer”的非常强版本
- 但这是 invasive `ECoG`，不是你当前数据条件

你要借鉴的是：

- 中间表征设计
- 多阶段训练
- “先建一个好 latent，再接 speech output”

不是直接拿它当你的实验目标。

## 6. 综述该怎么读

### 6.1 Frontiers 2022 imagined speech review

题目：

`A State-of-the-Art Review of EEG-Based Imagined Speech Decoding`

链接：

- https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.867281/full

为什么读：

- 快速知道 imagined speech 文献地图
- 知道哪些任务、哪些数据集常见

但要注意：

- 这不是你当前论文的主文献
- 你现在做的是 `speech perception + stimulus-locked EEG token learning`
- 不是典型 imagined speech classification

## 7. 推荐的检索词

下面这些词建议直接复制到 Google Scholar。

### 7.1 数据与任务边界

```text
Moreira 2025 open-access EEG dataset speech decoding articulation coarticulation
ds006104 speech decoding EEG OpenNeuro
non-invasive speech perception EEG decoding phoneme word
```

### 7.2 非侵入 speech perception / auditory EEG

```text
Decoding speech perception from non-invasive brain recordings wav2vec EEG
auditory EEG decoding contrastive learning transformer
continuous speech EEG decoding wav2vec
speech perception EEG self-supervised representations
```

### 7.3 EEG 自监督表征学习

```text
BENDR EEG self-supervised learning transformers
EEG masked autoencoder representation learning
Large Brain Model EEG generic representations
contrastive learning EEG representation learning
```

### 7.4 speech token / speech SSL

```text
vq-wav2vec discrete speech representations
wav2vec 2.0 self-supervised speech representations
HuBERT hidden units speech representations
discrete speech units self-supervised speech
```

### 7.5 序列对齐

```text
connectionist temporal classification speech recognition Graves 2006
CTC weakly supervised alignment token sequence
CTC phoneme alignment without boundaries
```

### 7.6 迁移和泛化

```text
subject independent EEG speech decoding
cross-subject EEG decoding speech
cross-session EEG speech decoding
transfer learning EEG speech decoding
```

## 8. 不建议你现在优先搜的词

下面这些很容易把你带偏。

### 8.1

`EEG to voice reconstruction`

问题：

- 会把你带到 paired audio / imagined speech / very small bespoke datasets

### 8.2

`imagined speech EEG classification accuracy`

问题：

- 很多文章只是在几个词或几个元音上做小规模分类
- 对你当前 perception dataset 的帮助有限

### 8.3

`brain to speech waveform`

问题：

- 大部分高质量结果来自 invasive ECoG

## 9. 一个实际可执行的阅读顺序

如果你这周只读 6 篇，就按这个顺序。

1. Moreira et al., 2025
2. Défossez et al., 2023
3. BENDR, 2021
4. HuBERT, 2021
5. vq-wav2vec, 2019
6. CTC: Graves 2006 + Distill 2017

如果你再多读 3 篇：

7. Bollens et al., 2025
8. Lee et al., 2023
9. Chen et al., 2024

## 10. 每篇文章你应该带着什么问题去读

### 读数据集文章时

问：

- 我到底拥有什么监督
- 缺什么监督
- 可做哪一层对齐

### 读 EEG representation 文章时

问：

- encoder 输入粒度是什么
- 预训练任务是什么
- 跨被试怎么做

### 读 speech SSL 文章时

问：

- token 是怎么定义的
- 连续表征和离散 token 如何衔接
- masking / clustering 在这里各起什么作用

### 读 alignment 文章时

问：

- 为什么不需要 frame-level 边界
- 模型对单调对齐有哪些假设

## 11. 你最后应该形成的文献结构

你的 related work 不应该写成一锅粥。

建议分成 4 段：

1. EEG speech decoding datasets and non-invasive speech perception
2. EEG representation learning and cross-subject generalization
3. Self-supervised speech representations and discrete speech units
4. Weakly supervised sequence alignment between EEG and speech units

这样结构最清楚，也最适合你后面的文章主线。

## 12. 一句话版搜索策略

先搜：

`dataset + non-invasive perception + EEG SSL + speech SSL + CTC`

不要先搜：

`EEG to voice reconstruction`
