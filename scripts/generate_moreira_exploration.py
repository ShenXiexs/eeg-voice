#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns


REPO_ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = REPO_ROOT / "events_information"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "exploration_outputs"
OPENNEURO_GRAPHQL_URL = "https://openneuro.org/crn/graphql"
OPENNEURO_DATASET_ID = "ds006104"
OPENNEURO_TAG = "1.0.1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a lightweight exploration package for the Moreira speech decoding dataset."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where manifests, figures, and validation summaries will be written.",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Skip OpenNeuro API queries and remote sample validation.",
    )
    return parser.parse_args()


@dataclass
class OutputPaths:
    root: Path
    figures: Path
    tables: Path
    validation: Path


def ensure_output_dirs(base: Path) -> OutputPaths:
    figures = base / "figures"
    tables = base / "tables"
    validation = base / "validation"
    for path in (base, figures, tables, validation):
        path.mkdir(parents=True, exist_ok=True)
    return OutputPaths(root=base, figures=figures, tables=tables, validation=validation)


def snake_case(name: str) -> str:
    return (
        name.replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .strip("_")
        .lower()
    )


def standardize_local_events(events_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    frames: list[pd.DataFrame] = []
    source_rows: list[dict[str, Any]] = []

    for csv_path in sorted(events_dir.glob("*_Tab.csv")):
        subject_id = csv_path.stem.replace("_Tab", "")
        raw = pd.read_csv(csv_path)
        original_columns = raw.columns.tolist()

        normalized = raw.rename(columns={"Correct_key": "Correct_Key"}).copy()
        normalized.columns = [snake_case(col) for col in normalized.columns]
        normalized["subject_id"] = subject_id
        normalized["study_year"] = 2019 if subject_id.startswith("P") else 2021
        normalized["session_id"] = "01" if subject_id.startswith("P") else "02"
        normalized["source_file"] = csv_path.name

        frames.append(normalized)
        source_rows.append(
            {
                "subject_id": subject_id,
                "source_file": csv_path.name,
                "n_rows": len(raw),
                "original_columns": "|".join(original_columns),
                "normalized_columns": "|".join(normalized.columns.tolist()),
                "used_correct_key_variant": "Correct_Key"
                if "Correct_Key" in raw.columns
                else "Correct_key"
                if "Correct_key" in raw.columns
                else "missing",
                "has_order": int("Order" in raw.columns),
                "has_p3_tsidx": int("P3_TSidx" in raw.columns),
            }
        )

    manifest = pd.concat(frames, ignore_index=True).sort_values(
        ["study_year", "subject_id", "task", "trialn"], na_position="last"
    )
    manifest.reset_index(drop=True, inplace=True)

    summary = {
        "subject_count": int(manifest["subject_id"].nunique()),
        "row_count": int(len(manifest)),
        "task_counts": {
            str(k): int(v)
            for k, v in manifest["task"].fillna("missing").value_counts().sort_index().items()
        },
        "study_year_counts": {
            str(k): int(v)
            for k, v in manifest["study_year"].value_counts().sort_index().items()
        },
        "field_inconsistencies": source_rows,
    }
    return manifest, summary


def save_local_tables(manifest: pd.DataFrame, summary: dict[str, Any], paths: OutputPaths) -> None:
    manifest.to_csv(paths.tables / "local_events_manifest.csv", index=False)
    pd.DataFrame(summary["field_inconsistencies"]).to_csv(
        paths.tables / "field_inconsistency_by_subject.csv", index=False
    )

    missingness = (
        manifest.isna()
        .sum()
        .rename("missing_count")
        .rename_axis("field")
        .reset_index()
        .sort_values(["missing_count", "field"], ascending=[False, True])
    )
    missingness["missing_ratio"] = missingness["missing_count"] / len(manifest)
    missingness.to_csv(paths.tables / "field_missingness.csv", index=False)

    with (paths.tables / "local_summary.json").open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)


def make_subject_trial_count_figure(manifest: pd.DataFrame, figure_path: Path) -> None:
    counts = manifest.groupby(["study_year", "subject_id"]).size().reset_index(name="trial_count")
    counts = counts.sort_values(["study_year", "subject_id"])

    plt.figure(figsize=(12, 5))
    ax = sns.barplot(data=counts, x="subject_id", y="trial_count", hue="study_year", palette="deep")
    ax.set_title("Trial count per subject")
    ax.set_xlabel("Subject")
    ax.set_ylabel("Trials")
    ax.legend(title="Study year")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.savefig(figure_path, dpi=220)
    plt.close()


def make_task_distribution_figure(manifest: pd.DataFrame, figure_path: Path) -> None:
    counts = manifest.groupby(["study_year", "task"]).size().reset_index(name="trial_count")
    counts["study_year"] = counts["study_year"].astype(str)

    plt.figure(figsize=(10, 5))
    ax = sns.barplot(data=counts, x="task", y="trial_count", hue="study_year", palette="muted")
    ax.set_title("Task distribution by study year")
    ax.set_xlabel("Task")
    ax.set_ylabel("Trials")
    ax.legend(title="Study year")
    plt.tight_layout()
    plt.savefig(figure_path, dpi=220)
    plt.close()


def make_tms_heatmap(manifest: pd.DataFrame, figure_path: Path) -> None:
    table = pd.crosstab(manifest["task"].fillna("missing"), manifest["tmstarget"].fillna("missing"))

    plt.figure(figsize=(11, 4))
    ax = sns.heatmap(table, annot=True, fmt="d", cmap="YlGnBu")
    ax.set_title("Task by TMS target")
    ax.set_xlabel("TMS target")
    ax.set_ylabel("Task")
    plt.tight_layout()
    plt.savefig(figure_path, dpi=220)
    plt.close()


def make_label_taxonomy_figure(figure_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.axis("off")

    boxes = [
        ((0.05, 0.70), 0.25, 0.18, "single phoneme\n2021 only\n/b p d t s z/ + 5 vowels"),
        ((0.37, 0.70), 0.25, 0.18, "phoneme pairs\n2019 + 2021\nCV and VC"),
        ((0.69, 0.70), 0.25, 0.18, "word / pseudoword\n2021 only\nCVC real vs nonce"),
        ((0.17, 0.28), 0.20, 0.16, "articulation labels\nalveolar / bilabial"),
        ((0.42, 0.28), 0.20, 0.16, "speech features\nplace / manner / voicing"),
        ((0.67, 0.28), 0.20, 0.16, "conditions\ncontrol / lip / tongue / BA06 / BA44"),
    ]

    for (x, y), w, h, text in boxes:
        rect = plt.Rectangle((x, y), w, h, fc="#f3f0e8", ec="#4c4c4c", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11)

    arrows = [
        ((0.17, 0.70), (0.27, 0.44)),
        ((0.49, 0.70), (0.52, 0.44)),
        ((0.81, 0.70), (0.77, 0.44)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.5})

    ax.set_title("Label taxonomy used in the Moreira dataset", pad=14)
    plt.tight_layout()
    plt.savefig(figure_path, dpi=220)
    plt.close()


def make_missingness_figure(manifest: pd.DataFrame, figure_path: Path) -> None:
    missingness = (
        manifest.isna()
        .sum()
        .rename("missing_count")
        .rename_axis("field")
        .reset_index()
        .query("missing_count > 0")
        .sort_values("missing_count", ascending=False)
        .head(12)
    )

    plt.figure(figsize=(10, 5))
    ax = sns.barplot(
        data=missingness,
        x="missing_count",
        y="field",
        hue="field",
        dodge=False,
        palette="crest",
        legend=False,
    )
    ax.set_title("Top missing fields in the merged local manifest")
    ax.set_xlabel("Missing values")
    ax.set_ylabel("Field")
    plt.tight_layout()
    plt.savefig(figure_path, dpi=220)
    plt.close()


def make_timeline_figure(figure_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 2.6))
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.set_yticks([])
    ax.set_xlim(-520, 1020)
    ax.set_ylim(-1, 1)
    ax.hlines(0, -500, 1000, color="#333333", linewidth=2)

    points = [
        (-500, "baseline start"),
        (-200, "task onset"),
        (-100, "TMS pulse 1"),
        (-50, "TMS pulse 2"),
        (0, "P1 / first speech sound"),
        (250, "P2 or later segment"),
        (1000, "trial end"),
    ]
    for x, label in points:
        ax.vlines(x, -0.18, 0.18, color="#7a2e2e" if "TMS" in label else "#1f4e79", linewidth=2)
        ax.text(x, 0.28 if x <= 0 else -0.34, label, rotation=0, ha="center", va="center", fontsize=9)

    ax.set_title("Simplified trial timeline used in local MATLAB/event tables")
    ax.set_xlabel("Time relative to first speech segment (ms)")
    plt.tight_layout()
    plt.savefig(figure_path, dpi=220)
    plt.close()


def generate_local_figures(manifest: pd.DataFrame, paths: OutputPaths) -> None:
    sns.set_theme(style="whitegrid")
    make_subject_trial_count_figure(manifest, paths.figures / "subject_trial_counts.png")
    make_task_distribution_figure(manifest, paths.figures / "task_distribution.png")
    make_tms_heatmap(manifest, paths.figures / "tms_target_by_task_heatmap.png")
    make_label_taxonomy_figure(paths.figures / "label_taxonomy.png")
    make_missingness_figure(manifest, paths.figures / "field_missingness.png")
    make_timeline_figure(paths.figures / "experiment_timeline.png")


def openneuro_graphql(query: str) -> dict[str, Any]:
    response = requests.post(
        OPENNEURO_GRAPHQL_URL,
        json={"query": query},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(json.dumps(payload["errors"], ensure_ascii=False))
    return payload["data"]


def parse_edf_header(header_bytes: bytes) -> dict[str, Any]:
    def text(start: int, end: int) -> str:
        return header_bytes[start:end].decode("ascii", errors="ignore").strip()

    header_length = int(text(184, 192))
    num_data_records_raw = text(236, 244)
    duration_raw = text(244, 252)
    num_signals = int(text(252, 256))

    labels_start = 256
    labels_end = labels_start + 16 * num_signals
    raw_labels = header_bytes[labels_start:labels_end]
    labels = [
        raw_labels[idx : idx + 16].decode("ascii", errors="ignore").strip()
        for idx in range(0, len(raw_labels), 16)
    ]

    return {
        "format": "EDF",
        "version": text(0, 8),
        "patient_id": text(8, 88),
        "recording_id": text(88, 168),
        "start_date": text(168, 176),
        "start_time": text(176, 184),
        "header_bytes": header_length,
        "num_data_records": num_data_records_raw,
        "data_record_duration_seconds": duration_raw,
        "num_signals": num_signals,
        "signal_labels_preview": labels[:10],
    }


def fetch_sample_file(url: str, dest: Path) -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    dest.write_bytes(response.content)


def fetch_edf_header(url: str, byte_count: int = 20000) -> bytes:
    response = requests.get(
        url,
        headers={"Range": f"bytes=0-{byte_count - 1}"},
        timeout=60,
        stream=True,
    )
    response.raise_for_status()
    chunks: list[bytes] = []
    remaining = byte_count
    for chunk in response.iter_content(chunk_size=8192):
        if not chunk:
            continue
        if len(chunk) >= remaining:
            chunks.append(chunk[:remaining])
            break
        chunks.append(chunk)
        remaining -= len(chunk)
        if remaining <= 0:
            break
    response.close()
    return b"".join(chunks)


def build_openneuro_validation(paths: OutputPaths) -> dict[str, Any]:
    top_level = openneuro_graphql(
        f"""
        query {{
          snapshot(datasetId: "{OPENNEURO_DATASET_ID}", tag: "{OPENNEURO_TAG}") {{
            files {{
              filename
              directory
              annexed
              size
            }}
          }}
        }}
        """
    )["snapshot"]["files"]

    all_files = openneuro_graphql(
        f"""
        query {{
          snapshot(datasetId: "{OPENNEURO_DATASET_ID}", tag: "{OPENNEURO_TAG}") {{
            files(recursive: true) {{
              filename
              directory
              annexed
              size
              urls
            }}
          }}
        }}
        """
    )["snapshot"]["files"]

    file_records = pd.DataFrame(all_files)
    file_records = file_records[~file_records["directory"]].copy()
    file_records["filename"] = file_records["filename"].astype(str)

    bids_summary = {
        "dataset_id": OPENNEURO_DATASET_ID,
        "snapshot_tag": OPENNEURO_TAG,
        "top_level_entries": [item["filename"] for item in top_level],
        "subject_directories": sorted(
            {
                path.split("/")[0]
                for path in file_records["filename"]
                if path.startswith("sub-")
            }
        ),
        "raw_file_extensions": (
            file_records[file_records["filename"].str.contains(r"/eeg/")]["filename"]
            .map(lambda value: Path(value).suffix)
            .value_counts()
            .sort_index()
            .to_dict()
        ),
        "annexed_file_count": int(file_records["annexed"].fillna(False).sum()),
        "non_annexed_file_count": int((~file_records["annexed"].fillna(False)).sum()),
    }

    sample_specs = [
        ("sub-P01/ses-01/eeg/sub-P01_ses-01_task-phonemes", "2019 phoneme pair sample"),
        ("sub-S01/ses-02/eeg/sub-S01_ses-02_task-phonemes", "2021 phoneme pair sample"),
    ]

    sample_results: list[dict[str, Any]] = []
    for prefix, note in sample_specs:
        sample_dir = paths.validation / prefix.replace("/", "_")
        sample_dir.mkdir(parents=True, exist_ok=True)

        related = file_records[file_records["filename"].str.startswith(prefix)]
        related_records = related.to_dict("records")

        eeg_json_record = next(row for row in related_records if row["filename"].endswith("_eeg.json"))
        events_record = next(row for row in related_records if row["filename"].endswith("_events.tsv"))
        channels_record = next(row for row in related_records if row["filename"].endswith("_channels.tsv"))
        edf_record = next(row for row in related_records if row["filename"].endswith(".edf"))

        eeg_json_path = sample_dir / Path(eeg_json_record["filename"]).name
        events_path = sample_dir / Path(events_record["filename"]).name
        channels_path = sample_dir / Path(channels_record["filename"]).name

        fetch_sample_file(eeg_json_record["urls"][0], eeg_json_path)
        fetch_sample_file(events_record["urls"][0], events_path)
        fetch_sample_file(channels_record["urls"][0], channels_path)
        edf_header = fetch_edf_header(edf_record["urls"][0])
        edf_header_info = parse_edf_header(edf_header)

        events_df = pd.read_csv(events_path, sep="\t")
        channels_df = pd.read_csv(channels_path, sep="\t")
        eeg_json = json.loads(eeg_json_path.read_text(encoding="utf-8"))
        event_preview = (
            events_df.head(3).astype(object).where(pd.notna(events_df.head(3)), None).to_dict(orient="records")
        )

        sample_results.append(
            {
                "sample_note": note,
                "prefix": prefix,
                "edf_size_bytes": int(edf_record["size"]),
                "edf_header": edf_header_info,
                "sampling_frequency": eeg_json.get("SamplingFrequency"),
                "task_name": eeg_json.get("TaskName"),
                "channel_count": int(len(channels_df)),
                "channel_type_counts": channels_df["type"].fillna("missing").value_counts().to_dict(),
                "event_count": int(len(events_df)),
                "event_columns": events_df.columns.tolist(),
                "event_preview": event_preview,
            }
        )

    tree_lines = []
    for prefix in [
        "sub-P01/ses-01/eeg/",
        "sub-S01/ses-02/eeg/",
        "derivatives/eeglab/sub-P01/ses-01/",
        "derivatives/eeglab/sub-S01/ses-02/",
    ]:
        tree_lines.append(f"[{prefix}]")
        for path in sorted(file_records[file_records["filename"].str.startswith(prefix)]["filename"].tolist()):
            tree_lines.append(path)
        tree_lines.append("")
    (paths.validation / "openneuro_tree_excerpt.txt").write_text("\n".join(tree_lines), encoding="utf-8")

    result = {
        "bids_summary": bids_summary,
        "sample_validation": sample_results,
    }
    with (paths.validation / "openneuro_validation.json").open("w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)
    return result


def main() -> None:
    args = parse_args()
    paths = ensure_output_dirs(args.output_dir)

    manifest, local_summary = standardize_local_events(EVENTS_DIR)
    save_local_tables(manifest, local_summary, paths)
    generate_local_figures(manifest, paths)

    remote_summary: dict[str, Any] | None = None
    if not args.skip_network:
        remote_summary = build_openneuro_validation(paths)

    final_summary = {
        "local_summary": local_summary,
        "generated_figures": sorted(path.name for path in paths.figures.glob("*.png")),
        "remote_validation_written": remote_summary is not None,
    }
    with (paths.root / "run_summary.json").open("w", encoding="utf-8") as fp:
        json.dump(final_summary, fp, ensure_ascii=False, indent=2)

    print(f"Wrote outputs to: {paths.root}")
    print(f"Manifest rows: {len(manifest)}")
    print(f"Generated figures: {len(list(paths.figures.glob('*.png')))}")
    print(f"Remote validation: {'yes' if remote_summary else 'no'}")


if __name__ == "__main__":
    main()
