#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a full EDF recording and export lightweight descriptive analysis outputs."
    )
    parser.add_argument("edf_path", type=Path, help="Path to a hydrated EDF file.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exploration_outputs/edf_full_analysis"),
        help="Directory for tables, plots, and JSON summary.",
    )
    parser.add_argument(
        "--resample",
        type=float,
        default=250.0,
        help="Target sampling frequency for analysis. Set 0 to keep original.",
    )
    parser.add_argument(
        "--overview-channels",
        type=int,
        default=8,
        help="Number of EEG channels to include in the overview trace plot.",
    )
    parser.add_argument(
        "--psd-channels",
        type=int,
        default=8,
        help="Number of EEG channels to include in PSD plots.",
    )
    return parser.parse_args()


def ensure_readable_file(path: Path) -> None:
    if path.is_symlink() and not path.exists():
        raise FileNotFoundError(
            f"{path} 还是一个 broken git-annex symlink。请改用已经真正下载好的 EDF 文件。"
        )
    if not path.exists():
        raise FileNotFoundError(f"EDF file not found: {path}")


def log_step(message: str, start_time: float | None = None) -> None:
    if start_time is None:
        print(f"[read_edf_full_analysis] {message}", flush=True)
    else:
        elapsed = time.time() - start_time
        print(f"[read_edf_full_analysis] {message} ({elapsed:.1f}s)", flush=True)


def make_overview_plot(data: np.ndarray, times: np.ndarray, names: list[str], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 7))
    spacing = max(float(np.nanstd(data)) * 8, 100.0)
    offset = 0.0
    ticks = []
    labels = []
    for idx, name in enumerate(names):
        ax.plot(times, data[idx] + offset, linewidth=0.7)
        ticks.append(offset)
        labels.append(name)
        offset += spacing

    ax.set_title("Full Recording Overview")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Channel")
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def make_channel_std_barplot(stats_df: pd.DataFrame, path: Path) -> None:
    top = stats_df.sort_values("std_uV", ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.bar(top["channel"], top["std_uV"], color="#4c78a8")
    ax.set_title("Top 20 EEG Channels by Standard Deviation")
    ax.set_xlabel("Channel")
    ax.set_ylabel("Std (uV)")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def make_psd_plot(raw, picks: list[int], names: list[str], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    spectrum = raw.compute_psd(
        method="welch",
        picks=picks,
        fmin=1.0,
        fmax=45.0,
        verbose="ERROR",
    )
    psd, freqs = spectrum.get_data(return_freqs=True)
    for idx, name in enumerate(names):
        ax.plot(freqs, 10 * np.log10(psd[idx]), linewidth=1.0, label=name)
    ax.set_title("Power Spectral Density (1-45 Hz)")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (dB)")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def analyze_edf(
    edf_path: Path,
    output: Path,
    resample: float = 250.0,
    overview_channels: int = 8,
    psd_channels: int = 8,
) -> dict[str, Any]:
    overall_start = time.time()
    ensure_readable_file(edf_path)
    file_output = output / edf_path.stem
    file_output.mkdir(parents=True, exist_ok=True)

    try:
        import mne
    except ImportError as exc:
        raise SystemExit(
            "当前环境没有安装 mne。先运行 `python3 -m pip install mne`，再执行这个脚本。"
        ) from exc

    load_start = time.time()
    log_step("Loading full EDF into memory")
    raw = mne.io.read_raw_edf(edf_path, preload=True, verbose="ERROR")
    log_step("Full EDF loaded", load_start)

    original_sfreq = float(raw.info["sfreq"])
    if resample and resample > 0 and resample < original_sfreq:
        resample_start = time.time()
        log_step(f"Resampling from {original_sfreq:.1f} Hz to {resample:.1f} Hz")
        raw.resample(resample, npad="auto", verbose="ERROR")
        log_step("Resampling finished", resample_start)

    sfreq = float(raw.info["sfreq"])
    eeg_picks = mne.pick_types(raw.info, eeg=True, exclude=[])
    channel_names = [raw.ch_names[idx] for idx in eeg_picks]

    data_start = time.time()
    log_step("Extracting EEG matrix")
    data = raw.get_data(picks=eeg_picks)
    log_step("EEG matrix extracted", data_start)

    times = np.arange(data.shape[1]) / sfreq
    duration_sec = data.shape[1] / sfreq

    print(f"EDF: {edf_path}")
    print(f"Original sampling frequency: {original_sfreq} Hz")
    print(f"Analysis sampling frequency: {sfreq} Hz")
    print(f"EEG channels: {len(channel_names)}")
    print(f"Samples per channel: {data.shape[1]}")
    print(f"Duration: {duration_sec / 60:.2f} minutes")
    print(f"Matrix shape: {data.shape}")

    stats_rows = []
    for idx, name in enumerate(channel_names):
        trace = data[idx]
        stats_rows.append(
            {
                "channel": name,
                "mean_uV": float(np.mean(trace)),
                "std_uV": float(np.std(trace)),
                "min_uV": float(np.min(trace)),
                "max_uV": float(np.max(trace)),
                "ptp_uV": float(np.ptp(trace)),
            }
        )
    stats_df = pd.DataFrame(stats_rows).sort_values("channel")

    summary = {
        "edf_path": str(edf_path),
        "original_sampling_frequency_hz": original_sfreq,
        "analysis_sampling_frequency_hz": sfreq,
        "eeg_channel_count": len(channel_names),
        "samples_per_channel": int(data.shape[1]),
        "duration_seconds": float(duration_sec),
        "duration_minutes": float(duration_sec / 60),
        "matrix_shape": [int(data.shape[0]), int(data.shape[1])],
        "global_mean_uV": float(np.mean(data)),
        "global_std_uV": float(np.std(data)),
        "global_min_uV": float(np.min(data)),
        "global_max_uV": float(np.max(data)),
    }

    stats_df.to_csv(file_output / f"{edf_path.stem}_channel_stats.csv", index=False)
    with (file_output / f"{edf_path.stem}_summary.json").open("w", encoding="utf-8") as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)

    plot_start = time.time()
    overview_count = max(1, min(overview_channels, len(eeg_picks)))
    make_overview_plot(
        data[:overview_count],
        times,
        channel_names[:overview_count],
        file_output / f"{edf_path.stem}_full_overview.png",
    )
    make_channel_std_barplot(
        stats_df,
        file_output / f"{edf_path.stem}_channel_std_top20.png",
    )
    psd_count = max(1, min(psd_channels, len(eeg_picks)))
    make_psd_plot(
        raw,
        eeg_picks[:psd_count],
        channel_names[:psd_count],
        file_output / f"{edf_path.stem}_psd.png",
    )
    log_step("Plots and tables saved", plot_start)
    log_step("All done", overall_start)
    summary["output_dir"] = str(file_output)
    return summary


def main() -> None:
    args = parse_args()
    analyze_edf(
        edf_path=args.edf_path,
        output=args.output,
        resample=args.resample,
        overview_channels=args.overview_channels,
        psd_channels=args.psd_channels,
    )


if __name__ == "__main__":
    main()
