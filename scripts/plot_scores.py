import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import json


def plot_scores(output_dir, save_path=None):
    history_file = os.path.join(output_dir, "fitness_history.csv")
    metadata_file = os.path.join(output_dir, "metadata.json")

    if not os.path.exists(history_file):
        print(f"Error: Could not find {history_file}. Have you run the agent yet?")
        return

    df = pd.read_csv(history_file)

    model_name = "Unknown Model"
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
            model_name = metadata.get("model", "Unknown Model")

    plt.figure(figsize=(10, 6))

    plt.plot(
        df["Generation"],
        df["Best_Fitness"],
        label="Best Fitness so far",
        color="green",
        linewidth=2.5,
    )

    plt.plot(
        df["Generation"],
        df["Current_Fitness"],
        label="Current Generation Fitness",
        color="orange",
        alpha=0.6,
        linestyle="--",
    )

    running_max = df["Best_Fitness"].cummax()
    is_new_high = (df["Best_Fitness"] == running_max) & (
        df["Best_Fitness"] > df["Best_Fitness"].shift(1).fillna(-np.inf)
    )
    x_highs = df.loc[is_new_high, "Generation"]
    y_highs = df.loc[is_new_high, "Best_Fitness"]
    plt.scatter(x_highs, y_highs, color="red", label="New Record High", zorder=3, s=40)

    task_name = os.path.basename(output_dir.rstrip("/"))
    plt.title(
        f"Evolutionary Optimization Progress: {task_name}\nModel: {model_name}",
        fontsize=14,
        pad=15,
    )
    plt.xlabel("Generation")
    plt.ylabel("Fitness Score")
    plt.legend(bbox_to_anchor=(0.5, -0.15), loc="upper center", ncol=2)
    plt.tight_layout()
    plt.grid(True, linestyle=":", alpha=0.7)

    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"Graph successfully saved to: {save_path}")
    else:
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize Evolution History")
    parser.add_argument(
        "--path",
        type=str,
        default="examples/graph_coloring/openevolve_output",
        help="Path to the openevolve output directory",
    )
    parser.add_argument("--save", type=str, default=None, help="Save plot to file")
    args = parser.parse_args()

    plot_scores(args.path, args.save)
