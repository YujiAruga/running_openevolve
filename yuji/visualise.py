import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import json

def plot_fitness(task_name):
    # 1. Define the path to the history file
    history_file = f"examples/{task_name}/openevolve_output/fitness_history.csv"
    metadata_file = f"examples/{task_name}/metadata.json"

    if not os.path.exists(history_file):
        print(f"Error: Could not find {history_file}. Have you run the agent yet?")
        return

    # 2. Road the data
    df = pd.read_csv(history_file)

    model_name = "Unknown Model"
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
            model_name = metadata.get("model", "Unknown Model")

    # 3. Create the plot
    plt.plot(df['Generation'], df['Best_Fitness'],
             label="Best Fitness so far", color="green", linewidth=2.5)

    plt.plot(df["Generation"], df["Current_Fitness"],
    label="Current Generation Fitness", color="orange", alpha=0.6, linestyle="--")


    running_max = df["Best_Fitness"].cummax()
    is_new_high = (df["Best_Fitness"] == running_max) & (df["Best_Fitness"] > df["Best_Fitness"].shift(1).fillna(-np.inf))
    x_highs = df.loc[is_new_high, "Generation"]
    y_highs = df.loc[is_new_high, "Best_Fitness"]
    plt.scatter(x_highs, y_highs, color='red', label='New Record High', zorder=3, s=40)

    for i in range(len(y_highs)):
        plt.annotate(
            f"{y_highs.iloc[i]:.2f}",           # Format to 2 decimal places
            (x_highs.iloc[i], y_highs.iloc[i]), # Access coordinates by position
            textcoords="offset points", 
            xytext=(0, 7), 
            ha='center', 
            fontsize=8, 
            color='black'
        )

    # 4. Format the graph
    plt.title(f"Evolutionary Optimization Progress: {task_name}\nModel: {model_name}", fontsize=14, pad=15)
    plt.xlabel("Generation")
    plt.ylabel("Fitness Score")
    plt.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=2)
    plt.tight_layout()
    plt.grid(True, linestyle=':', alpha=0.7)


    # 5. Save and show
    output_image = f"examples/{task_name}/openevolve_output/fitness_plot.png"
    plt.savefig(output_image, dpi=300)
    print(f"Graph successfully saved to: {output_image}")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize Evolution History")
    parser.add_argument("--task", type=str, required=True, help="Name of the task (e.g., circle_packing)")
    args = parser.parse_args()

    plot_fitness(args.task)