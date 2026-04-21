#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from read_edf_full_analysis import analyze_edf


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET_ROOT = Path("/Users/samxie/Research/EEG-Voice/openneuro_downloads/ds006104-download")
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "exploration_outputs" / "edf_full_analysis_batch"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch download and analyze all EDF files from ds006104 with visible progress."
    )
    parser.add_argument(
        "--mode",
        choices=["download", "analyze", "all"],
        default="all",
        help="Run download only, analysis only, or both in sequence.",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=DEFAULT_DATASET_ROOT,
        help="Path to the OpenNeuro dataset clone/download directory.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory for batch analysis outputs and logs.",
    )
    parser.add_argument(
        "--subjects",
        nargs="*",
        default=None,
        help="Optional subject filter, e.g. P03 S01 S02.",
    )
    parser.add_argument(
        "--resample",
        type=float,
        default=250.0,
        help="Target sampling frequency for EDF analysis. Set 0 to keep original.",
    )
    parser.add_argument(
        "--overview-channels",
        type=int,
        default=8,
        help="Number of EEG channels in overview plots.",
    )
    parser.add_argument(
        "--psd-channels",
        type=int,
        default=8,
        help="Number of EEG channels in PSD plots.",
    )
    parser.add_argument(
        "--skip-existing-analysis",
        action="store_true",
        help="Skip analysis if the summary JSON for a file already exists.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing remaining EDF files after one failure.",
    )
    return parser.parse_args()


def log(message: str) -> None:
    print(f"[batch_ds006104] {message}", flush=True)


def progress_bar(current: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "[no items]"
    filled = int(width * current / total)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {current}/{total}"


def discover_edf_paths(dataset_root: Path, subjects: list[str] | None) -> list[Path]:
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset root not found: {dataset_root}")

    edf_paths = sorted(dataset_root.rglob("*_eeg.edf"))
    if subjects:
        subject_set = {subject.replace("sub-", "") for subject in subjects}
        edf_paths = [path for path in edf_paths if path.parts[-4].replace("sub-", "") in subject_set]
    return edf_paths


def ensure_git_annex() -> None:
    if shutil.which("git-annex") is None:
        raise SystemExit(
            "当前环境没有 git-annex。先安装后再跑批量下载，例如 `brew install git-annex`。"
        )


def run_git_annex_get(dataset_root: Path, rel_path: Path) -> None:
    cmd = ["git-annex", "get", str(rel_path)]
    subprocess.run(cmd, cwd=dataset_root, check=True)


def download_edfs(
    dataset_root: Path,
    edf_paths: list[Path],
    continue_on_error: bool,
) -> tuple[list[str], list[dict[str, str]]]:
    ensure_git_annex()
    hydrated: list[str] = []
    failures: list[dict[str, str]] = []

    for index, path in enumerate(edf_paths, start=1):
        rel_path = path.relative_to(dataset_root)
        log(f"{progress_bar(index, len(edf_paths))} Downloading {rel_path}")
        if path.exists():
            hydrated.append(str(rel_path))
            log("Already hydrated locally, skipping download.")
            continue
        try:
            run_git_annex_get(dataset_root, rel_path)
        except subprocess.CalledProcessError as exc:
            failures.append({"edf": str(rel_path), "stage": "download", "error": str(exc)})
            log(f"Download failed: {rel_path}")
            if not continue_on_error:
                raise
            continue

        if path.exists():
            hydrated.append(str(rel_path))
            log("Download finished.")
        else:
            failures.append(
                {
                    "edf": str(rel_path),
                    "stage": "download",
                    "error": "git-annex reported success but file is still not hydrated",
                }
            )
            log(f"Download finished but file is still not hydrated: {rel_path}")
            if not continue_on_error:
                raise RuntimeError(f"Hydration check failed for {rel_path}")

    return hydrated, failures


def analyze_edfs(
    dataset_root: Path,
    output_root: Path,
    edf_paths: list[Path],
    resample: float,
    overview_channels: int,
    psd_channels: int,
    skip_existing_analysis: bool,
    continue_on_error: bool,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    output_root.mkdir(parents=True, exist_ok=True)
    completed: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for index, path in enumerate(edf_paths, start=1):
        rel_path = path.relative_to(dataset_root)
        if not path.exists():
            failures.append(
                {"edf": str(rel_path), "stage": "analyze", "error": "EDF is not hydrated locally"}
            )
            log(f"{progress_bar(index, len(edf_paths))} Skipping missing EDF: {rel_path}")
            if not continue_on_error:
                raise FileNotFoundError(f"EDF is not hydrated locally: {path}")
            continue

        summary_path = output_root / path.stem / f"{path.stem}_summary.json"
        if skip_existing_analysis and summary_path.exists():
            completed.append({"edf": str(rel_path), "summary_json": str(summary_path)})
            log(f"{progress_bar(index, len(edf_paths))} Analysis already exists, skipping {rel_path}")
            continue

        log(f"{progress_bar(index, len(edf_paths))} Analyzing {rel_path}")
        try:
            summary = analyze_edf(
                edf_path=path,
                output=output_root,
                resample=resample,
                overview_channels=overview_channels,
                psd_channels=psd_channels,
            )
            completed.append({"edf": str(rel_path), "summary_json": str(summary_path), "duration_minutes": str(round(summary["duration_minutes"], 2))})
        except Exception as exc:  # noqa: BLE001
            failures.append({"edf": str(rel_path), "stage": "analyze", "error": str(exc)})
            log(f"Analysis failed: {rel_path}")
            if not continue_on_error:
                raise

    return completed, failures


def main() -> None:
    args = parse_args()
    started = time.time()
    log(f"Dataset root: {args.dataset_root}")
    log(f"Mode: {args.mode}")

    edf_paths = discover_edf_paths(args.dataset_root, args.subjects)
    if not edf_paths:
        raise SystemExit("No EDF files found for the given dataset root / subject filter.")

    log(f"Discovered {len(edf_paths)} EDF entries.")
    hydrated_before = sum(path.exists() for path in edf_paths)
    log(f"Hydrated locally before run: {hydrated_before}/{len(edf_paths)}")

    all_failures: list[dict[str, str]] = []
    downloaded: list[str] = []
    analyzed: list[dict[str, str]] = []

    if args.mode in {"download", "all"}:
        downloaded, failures = download_edfs(
            dataset_root=args.dataset_root,
            edf_paths=edf_paths,
            continue_on_error=args.continue_on_error,
        )
        all_failures.extend(failures)
        log(f"Hydrated after download step: {sum(path.exists() for path in edf_paths)}/{len(edf_paths)}")

    if args.mode in {"analyze", "all"}:
        analyzed, failures = analyze_edfs(
            dataset_root=args.dataset_root,
            output_root=args.output_root,
            edf_paths=edf_paths,
            resample=args.resample,
            overview_channels=args.overview_channels,
            psd_channels=args.psd_channels,
            skip_existing_analysis=args.skip_existing_analysis,
            continue_on_error=args.continue_on_error,
        )
        all_failures.extend(failures)

    summary = {
        "mode": args.mode,
        "dataset_root": str(args.dataset_root),
        "output_root": str(args.output_root),
        "subjects": args.subjects or [],
        "edf_entries": len(edf_paths),
        "hydrated_before": hydrated_before,
        "hydrated_after": sum(path.exists() for path in edf_paths),
        "downloaded_count": len(downloaded),
        "analyzed_count": len(analyzed),
        "failure_count": len(all_failures),
        "failures": all_failures,
        "elapsed_seconds": round(time.time() - started, 2),
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_root / "batch_run_summary.json"
    with summary_path.open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    log(f"Batch summary saved to: {summary_path}")
    log(
        f"Done. downloaded={summary['downloaded_count']}, analyzed={summary['analyzed_count']}, failures={summary['failure_count']}"
    )


if __name__ == "__main__":
    main()
