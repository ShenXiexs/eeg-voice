#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "exploration_outputs" / "tables" / "local_events_manifest.csv"
VALIDATION_PATH = REPO_ROOT / "exploration_outputs" / "validation" / "openneuro_validation.json"
OUTPUT_ROOT = REPO_ROOT / "exploration_outputs" / "data_priority"


@dataclass
class OutputPaths:
    root: Path
    figures: Path
    tables: Path


def ensure_dirs(root: Path) -> OutputPaths:
    figures = root / "figures"
    tables = root / "tables"
    for path in (root, figures, tables):
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(root=root, figures=figures, tables=tables)


def load_manifest(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing manifest: {path}")
    df = pd.read_csv(path)
    df["stimulus_base"] = df["stimulus"].astype(str).str.replace(r"_(angry|happy)\d+$", "", regex=True)
    return df


def load_validation(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing validation summary: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def balance_note(counts: pd.Series) -> str:
    counts = counts[counts > 0]
    if counts.empty:
        return "N/A"
    ratio = counts.max() / counts.min()
    if ratio <= 1.05:
        return "完全均衡"
    if ratio <= 1.25:
        return "较均衡"
    return "不均衡"


def summarize_tasks(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["study_year", "task"])
        .agg(
            subjects=("subject_id", "nunique"),
            trials=("stimulus", "size"),
            unique_stimuli=("stimulus", "nunique"),
            unique_stimulus_bases=("stimulus_base", "nunique"),
        )
        .reset_index()
        .sort_values(["study_year", "task"])
    )
    return summary


def candidate_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    single = df[(df["study_year"] == 2021) & (df["task"] == "single-phoneme")].copy()
    words = df[(df["study_year"] == 2021) & (df["task"] == "Words")].copy()
    phonemes_control = df[
        (df["task"] == "phonemes") & (df["tmstarget"].astype(str).str.startswith("control"))
    ].copy()

    base2019 = set(phonemes_control[phonemes_control["study_year"] == 2019]["stimulus_base"].dropna())
    base2021 = set(phonemes_control[phonemes_control["study_year"] == 2021]["stimulus_base"].dropna())
    shared_bases = sorted(base2019 & base2021)
    phonemes_shared = phonemes_control[phonemes_control["stimulus_base"].isin(shared_bases)].copy()

    rows = [
        {
            "priority": 1,
            "subset_name": "2021 single-phoneme",
            "subset_definition": "study_year=2021, task=single-phoneme",
            "recommended_unit": "phoneme1",
            "subjects": int(single["subject_id"].nunique()),
            "trials": int(len(single)),
            "class_count": int(single["phoneme1"].nunique()),
            "class_balance": balance_note(single["phoneme1"].value_counts()),
            "control_only_version": "是，且全部 trial 均为 control* 条件",
            "cross_year_alignment": "否，2019 无 single-phoneme 任务",
            "why_useful": "最干净的离散 speech-unit 数据，适合先看 EEG token 是否可分",
        },
        {
            "priority": 2,
            "subset_name": "2021 Words",
            "subset_definition": "study_year=2021, task=Words",
            "recommended_unit": "category (real/nonce)，另有 20 个 lexical bases",
            "subjects": int(words["subject_id"].nunique()),
            "trials": int(len(words)),
            "class_count": int(words["category"].nunique()),
            "class_balance": balance_note(words["category"].value_counts()),
            "control_only_version": "是，存在 control_BA06 / control_BA44 子集",
            "cross_year_alignment": "否，2019 无 Words 任务",
            "why_useful": "最接近高层 speech unit，可先做粗粒度 lexical token 准备",
        },
        {
            "priority": 3,
            "subset_name": "control-only phonemes",
            "subset_definition": "task=phonemes, tmstarget startswith control",
            "recommended_unit": "20 shared phoneme bases（跨年）或 articulation labels",
            "subjects": int(phonemes_control["subject_id"].nunique()),
            "trials": int(len(phonemes_control)),
            "class_count": int(len(shared_bases)),
            "class_balance": balance_note(phonemes_shared["stimulus_base"].value_counts()),
            "control_only_version": "是，当前子集即 control-only",
            "cross_year_alignment": "是，但只有 20 个 shared bases",
            "why_useful": "唯一具备跨 2019/2021 对齐基础的离散 phoneme 子集",
        },
    ]
    return rows


def build_core_field_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    fields = [
        ("stimulus", "trial 标识"),
        ("phoneme1", "speech unit 标签"),
        ("phoneme2", "speech unit 标签"),
        ("phoneme3", "speech unit 标签"),
        ("category", "粗粒度类别"),
        ("place", "articulatory 标签"),
        ("manner", "articulatory 标签"),
        ("voicing", "articulatory 标签"),
        ("tmstarget", "条件标签"),
        ("p1_tsidx", "主事件时间点"),
        ("p2_tsidx", "附加时间点"),
        ("p3_tsidx", "附加时间点"),
        ("order", "CV/VC 顺序"),
        ("correct_key", "行为标签"),
    ]
    for field, role in fields:
        if field not in df.columns:
            continue
        overall_ratio = 1 - df[field].isna().mean()
        present_2019 = (1 - df[df["study_year"] == 2019][field].isna().mean()) > 0
        present_2021 = (1 - df[df["study_year"] == 2021][field].isna().mean()) > 0
        non_null_tasks = sorted(df.loc[df[field].notna(), "task"].dropna().unique().tolist())
        rows.append(
            {
                "field": field,
                "role": role,
                "overall_non_null_ratio": round(float(overall_ratio), 4),
                "present_in_2019": "是" if present_2019 else "否",
                "present_in_2021": "是" if present_2021 else "否",
                "tasks_with_values": ", ".join(non_null_tasks),
            }
        )
    return pd.DataFrame(rows)


def build_supervision_signal_table(df: pd.DataFrame, validation: dict[str, Any]) -> pd.DataFrame:
    raw_ext = validation["bids_summary"].get("raw_file_extensions", {})
    has_public_audio = any(ext in raw_ext for ext in [".wav", ".mp3", ".flac", ".ogg", ".m4a"])
    rows = [
        {
            "signal": "stimulus onset",
            "status": "已有",
            "evidence": "BIDS events.tsv 含 onset；本地 manifest 含 p1_tsidx",
            "why_it_matters": "支持 trial-level 窗口切片",
        },
        {
            "signal": "discrete phoneme labels",
            "status": "已有",
            "evidence": "phoneme1/2/3 在 local manifest 与 BIDS events 中均可见",
            "why_it_matters": "支持 unit-level speech token 准备",
        },
        {
            "signal": "articulatory labels",
            "status": "已有",
            "evidence": "place / manner / voicing 在 phoneme 条件下可用",
            "why_it_matters": "适合构建粗粒度 EEG token",
        },
        {
            "signal": "lexical labels",
            "status": "已有",
            "evidence": "Words 任务含 real / nonce 和 20 个 lexical bases",
            "why_it_matters": "支持高层 speech unit 对齐准备",
        },
        {
            "signal": "TMS / condition labels",
            "status": "已有",
            "evidence": "tmstarget 与 tms 标记完整",
            "why_it_matters": "支持 domain / condition 分析",
        },
        {
            "signal": "public stimulus audio",
            "status": "缺失" if not has_public_audio else "已有",
            "evidence": f"raw file extensions={raw_ext}",
            "why_it_matters": "没有公开语音波形就无法直接做 EEG-to-audio 监督",
        },
        {
            "signal": "subject-produced speech audio",
            "status": "缺失",
            "evidence": "任务描述是 listened to audio clips and responded with button presses",
            "why_it_matters": "不支持 spoken EEG 到用户自身语音的直接配对",
        },
        {
            "signal": "phoneme boundaries / durations",
            "status": "缺失",
            "evidence": "events.tsv 只有 trial-level onset，没有逐音素声学边界",
            "why_it_matters": "不支持 frame-level speech alignment",
        },
        {
            "signal": "mel / vocoder target",
            "status": "缺失",
            "evidence": "公开数据中未提供 mel-spectrogram 或 waveform targets",
            "why_it_matters": "不能直接作为 Lee 2023 式重建监督",
        },
        {
            "signal": "imagined speech EEG",
            "status": "缺失",
            "evidence": "Moreira 是 auditory discrimination，不是 imagined speech",
            "why_it_matters": "不能单独承担 imagined EEG 到 voice 主线",
        },
    ]
    return pd.DataFrame(rows)


def build_granularity_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "granularity": "trial-level",
                "status": "可用",
                "available_supervision": "stimulus onset, phoneme1-3, category, tmstarget",
                "missing_supervision": "无额外缺口",
                "takeaway": "可以直接做 trial/unit 级数据观察和切窗准备",
            },
            {
                "granularity": "unit-level",
                "status": "部分可用",
                "available_supervision": "single phoneme, phoneme pair, CVC base, articulation labels",
                "missing_supervision": "公开音频、音素时长、speech-side tokenizer 输出",
                "takeaway": "适合离散 speech-unit 级 EEG token 准备",
            },
            {
                "granularity": "frame-level",
                "status": "不可用",
                "available_supervision": "无",
                "missing_supervision": "waveform, mel target, forced alignment, phoneme boundaries",
                "takeaway": "当前不能直接支持 EEG-to-voice 重建监督",
            },
        ]
    )


def make_task_size_figure(task_summary: pd.DataFrame, out: Path) -> None:
    labels = [f"{row.study_year}-{row.task}" for row in task_summary.itertuples()]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    sns.barplot(x=labels, y=task_summary["trials"], ax=axes[0], palette="deep", hue=labels, legend=False)
    axes[0].set_title("Trials per task slice")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Trials")
    axes[0].tick_params(axis="x", rotation=35)

    sns.barplot(
        x=labels,
        y=task_summary["unique_stimuli"],
        ax=axes[1],
        palette="muted",
        hue=labels,
        legend=False,
    )
    axes[1].set_title("Unique stimuli per task slice")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Unique stimuli")
    axes[1].tick_params(axis="x", rotation=35)

    plt.tight_layout()
    plt.savefig(out, dpi=220)
    plt.close()


def make_candidate_balance_figure(df: pd.DataFrame, out: Path) -> None:
    single = df[(df["study_year"] == 2021) & (df["task"] == "single-phoneme")]
    words = df[(df["study_year"] == 2021) & (df["task"] == "Words")]
    phonemes_control = df[
        (df["task"] == "phonemes") & (df["tmstarget"].astype(str).str.startswith("control"))
    ].copy()
    base2019 = set(phonemes_control[phonemes_control["study_year"] == 2019]["stimulus_base"].dropna())
    base2021 = set(phonemes_control[phonemes_control["study_year"] == 2021]["stimulus_base"].dropna())
    shared_bases = sorted(base2019 & base2021)
    phonemes_shared = phonemes_control[phonemes_control["stimulus_base"].isin(shared_bases)]
    shared_counts = phonemes_shared.groupby(["stimulus_base", "study_year"]).size().reset_index(name="count")

    fig, axes = plt.subplots(3, 1, figsize=(12, 11))

    sns.barplot(
        data=single.groupby("phoneme1").size().reset_index(name="count"),
        x="phoneme1",
        y="count",
        ax=axes[0],
        hue="phoneme1",
        palette="tab10",
        legend=False,
    )
    axes[0].set_title("2021 single-phoneme: class balance")
    axes[0].set_xlabel("phoneme1")
    axes[0].set_ylabel("Trials")

    sns.barplot(
        data=words.groupby("category").size().reset_index(name="count"),
        x="category",
        y="count",
        ax=axes[1],
        hue="category",
        palette="Set2",
        legend=False,
    )
    axes[1].set_title("2021 Words: real vs nonce balance")
    axes[1].set_xlabel("category")
    axes[1].set_ylabel("Trials")

    sns.barplot(
        data=shared_counts,
        x="stimulus_base",
        y="count",
        hue="study_year",
        ax=axes[2],
        palette="dark",
    )
    axes[2].set_title("Control-only phonemes: shared 20 bases across 2019 and 2021")
    axes[2].set_xlabel("shared phoneme base")
    axes[2].set_ylabel("Trials")
    axes[2].tick_params(axis="x", rotation=45)
    axes[2].legend(title="study_year")

    plt.tight_layout()
    plt.savefig(out, dpi=220)
    plt.close()


def make_task_tms_heatmap(df: pd.DataFrame, out: Path) -> None:
    table = pd.crosstab(df["task"], df["tmstarget"])
    plt.figure(figsize=(11, 4))
    ax = sns.heatmap(table, annot=True, fmt="d", cmap="YlGnBu")
    ax.set_title("Task by TMS target")
    ax.set_xlabel("TMS target")
    ax.set_ylabel("Task")
    plt.tight_layout()
    plt.savefig(out, dpi=220)
    plt.close()


def make_overlap_figure(df: pd.DataFrame, out: Path) -> None:
    phonemes = df[df["task"] == "phonemes"].copy()
    presence = (
        phonemes.assign(present=1)
        .drop_duplicates(subset=["study_year", "stimulus_base"])
        .pivot_table(
            index="stimulus_base",
            columns="study_year",
            values="present",
            fill_value=0,
            aggfunc="max",
        )
        .astype(int)
    )
    presence = presence.reindex(sorted(presence.index), axis=0)
    presence["sort_key"] = presence.sum(axis=1)
    presence = presence.sort_values(
        ["sort_key", 2019, 2021, "stimulus_base"], ascending=[False, False, False, True]
    )
    presence = presence.drop(columns=["sort_key"])

    plt.figure(figsize=(5.5, 8.5))
    ax = sns.heatmap(presence, annot=True, fmt="d", cmap=["#f1efe8", "#1f4e79"], cbar=False)
    ax.set_title("Phoneme-base overlap between 2019 and 2021")
    ax.set_xlabel("study_year")
    ax.set_ylabel("stimulus_base")
    plt.tight_layout()
    plt.savefig(out, dpi=220)
    plt.close()


def make_granularity_figure(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.axis("off")
    specs = [
        (0.05, "#d9ead3", "trial-level\navailable\nonset + labels + condition"),
        (0.37, "#fff2cc", "unit-level\npartially available\nspeech-unit labels but no public audio"),
        (0.69, "#f4cccc", "frame-level\nnot available\nno waveform / no boundaries / no mel target"),
    ]
    for x, color, text in specs:
        rect = plt.Rectangle((x, 0.25), 0.24, 0.45, fc=color, ec="#444444", linewidth=1.3)
        ax.add_patch(rect)
        ax.text(x + 0.12, 0.475, text, ha="center", va="center", fontsize=11)
    ax.annotate("", xy=(0.37, 0.48), xytext=(0.29, 0.48), arrowprops={"arrowstyle": "->", "lw": 1.5})
    ax.annotate("", xy=(0.69, 0.48), xytext=(0.61, 0.48), arrowprops={"arrowstyle": "->", "lw": 1.5})
    ax.set_title("Current alignment granularity supported by Moreira", pad=10)
    plt.tight_layout()
    plt.savefig(out, dpi=220)
    plt.close()


def main() -> None:
    paths = ensure_dirs(OUTPUT_ROOT)
    sns.set_theme(style="whitegrid")

    manifest = load_manifest(MANIFEST_PATH)
    validation = load_validation(VALIDATION_PATH)

    task_summary = summarize_tasks(manifest)
    candidate_table = pd.DataFrame(candidate_rows(manifest)).sort_values("priority")
    field_table = build_core_field_table(manifest)
    supervision_table = build_supervision_signal_table(manifest, validation)
    granularity_table = build_granularity_table()

    task_summary.to_csv(paths.tables / "task_size_summary.csv", index=False)
    candidate_table.to_csv(paths.tables / "candidate_subset_priority.csv", index=False)
    field_table.to_csv(paths.tables / "core_field_availability.csv", index=False)
    supervision_table.to_csv(paths.tables / "supervision_signal_matrix.csv", index=False)
    granularity_table.to_csv(paths.tables / "alignment_granularity.csv", index=False)

    make_task_size_figure(task_summary, paths.figures / "task_size_and_unique_stimuli.png")
    make_candidate_balance_figure(manifest, paths.figures / "candidate_subset_balance.png")
    make_task_tms_heatmap(manifest, paths.figures / "task_tms_heatmap.png")
    make_overlap_figure(manifest, paths.figures / "phoneme_base_overlap.png")
    make_granularity_figure(paths.figures / "alignment_granularity.png")

    summary = {
        "task_summary_rows": len(task_summary),
        "candidate_subset_rows": len(candidate_table),
        "figure_files": sorted(path.name for path in paths.figures.glob("*.png")),
        "table_files": sorted(path.name for path in paths.tables.glob("*.csv")),
    }
    (paths.root / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote data-priority outputs to: {paths.root}")
    print(f"Figures: {len(summary['figure_files'])}")
    print(f"Tables: {len(summary['table_files'])}")


if __name__ == "__main__":
    main()
