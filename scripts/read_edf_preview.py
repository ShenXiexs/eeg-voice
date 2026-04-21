#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import time

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read one EDF file and save a quick EEG preview plot.")
    parser.add_argument("edf_path", type=Path, help="Path to the hydrated EDF file.")
    parser.add_argument(
        "--start",
        type=float,
        default=0.0,
        help="Start time in seconds for the preview window.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Duration in seconds for the preview window.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Read the full recording duration instead of using --duration.",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=8,
        help="Number of EEG channels to include in the preview plot.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exploration_outputs/edf_preview"),
        help="Directory for the preview figure.",
    )
    return parser.parse_args()


def ensure_readable_file(path: Path) -> None:
    if path.is_symlink() and not path.exists():
        raise FileNotFoundError(
            f"{path} 还是一个 broken git-annex symlink。"
            " 请确认你读取的是已经真正下载完成的 EDF 文件，而不是当前仓库里那份未 hydrated 的链接。"
        )
    if not path.exists():
        raise FileNotFoundError(f"EDF file not found: {path}")


def log_step(message: str, start_time: float | None = None) -> None:
    if start_time is None:
        print(f"[read_edf_preview] {message}", flush=True)
    else:
        elapsed = time.time() - start_time
        print(f"[read_edf_preview] {message} ({elapsed:.1f}s)", flush=True)


def main() -> None:
    args = parse_args()
    overall_start = time.time()
    log_step("Checking EDF path")
    ensure_readable_file(args.edf_path)
    log_step("EDF path looks valid", overall_start)

    try:
        import mne
    except ImportError as exc:
        raise SystemExit(
            "当前环境没有安装 mne。先运行 `python3 -m pip install mne`，再执行这个脚本。"
        ) from exc

    open_start = time.time()
    log_step("Opening EDF header with MNE")
    raw = mne.io.read_raw_edf(args.edf_path, preload=False, verbose="ERROR")
    log_step("EDF header loaded", open_start)

    sfreq = float(raw.info["sfreq"])
    n_times = int(raw.n_times)
    duration_sec = n_times / sfreq
    eeg_picks = mne.pick_types(raw.info, eeg=True, exclude=[])
    channel_names = [raw.ch_names[index] for index in eeg_picks]

    print(f"EDF: {args.edf_path}")
    print(f"Sampling frequency: {sfreq} Hz")
    print(f"EEG channels: {len(channel_names)}")
    print(f"Duration: {duration_sec / 60:.2f} minutes")
    print(f"First EEG channels: {channel_names[:10]}")

    start = max(0.0, args.start)
    stop = duration_sec if args.full else min(duration_sec, start + max(0.1, args.duration))
    if stop <= start:
        raise ValueError("Preview window is empty. Check --start and --duration.")

    preview_picks = eeg_picks[: max(1, min(args.channels, len(eeg_picks)))]
    read_start = time.time()
    log_step(
        f"Reading preview window: {start:.1f}s to {stop:.1f}s, {len(preview_picks)} EEG channels"
    )
    data, times = raw.get_data(
        picks=preview_picks,
        start=int(start * sfreq),
        stop=int(stop * sfreq),
        return_times=True,
    )
    log_step("Preview window loaded into memory", read_start)
    times = times + start

    plot_start = time.time()
    log_step("Rendering preview plot")
    fig, ax = plt.subplots(figsize=(12, 6))
    offset = 0.0
    spacing = max(data.std() * 6, 100.0)
    y_ticks = []
    y_labels = []

    for idx, pick in enumerate(preview_picks):
        trace = data[idx]
        ax.plot(times, trace + offset, linewidth=0.8)
        y_ticks.append(offset)
        y_labels.append(raw.ch_names[pick])
        offset += spacing

    ax.set_title(f"EEG preview: {args.edf_path.name}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Channel")
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    args.output.mkdir(parents=True, exist_ok=True)
    output_path = args.output / f"{args.edf_path.stem}_preview.png"
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    log_step("Preview plot rendered and saved", plot_start)
    print(f"Saved preview figure to: {output_path}")
    log_step("All done", overall_start)


if __name__ == "__main__":
    main()
