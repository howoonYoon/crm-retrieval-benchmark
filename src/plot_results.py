from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METRICS = ROOT / "results" / "metrics.csv"
DEFAULT_OUT = ROOT / "results" / "metrics_plot.png"


def plot_metrics(metrics_path: Path, out_path: Path) -> None:
    metrics = pd.read_csv(metrics_path)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    metrics.plot(
        x="config",
        y=["recall_at_5", "mrr"],
        kind="bar",
        ax=axes[0],
        ylim=(0, 1),
        rot=0,
    )
    axes[0].set_title("Retrieval quality")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("score")
    axes[0].legend(loc="lower right")

    metrics.plot(
        x="config",
        y="p95_latency_ms",
        kind="bar",
        ax=axes[1],
        legend=False,
        rot=0,
        color="#4C78A8",
    )
    axes[1].axhline(1000, color="#D62728", linestyle="--", linewidth=1)
    axes[1].set_title("p95 latency")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("milliseconds")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot benchmark metrics.")
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    plot_metrics(args.metrics, args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
