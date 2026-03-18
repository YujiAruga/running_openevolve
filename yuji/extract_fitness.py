import re
import csv
import os

def parse_openevolve_logs(log_file_path, output_csv):
    # Regex patterns
    iter_pattern = re.compile(r"Iteration (\d+):")
    metrics_pattern = re.compile(r"Metrics:.*sum_radii=([\d.]+)")
    initial_pattern = re.compile(r"Evaluated program .* sum_radii=([\d.]+)")

    data_points = []
    best_score = float('-inf')
    last_iter_num = None

    if not os.path.exists(log_file_path):
        print(f"Error: File {log_file_path} not found.")
        return

    with open(log_file_path, 'r') as f:
        initial_found = False
        
        for line in f:
            # 1. Handle Initial Program (Iteration 0)
            if not initial_found:
                initial_match = initial_pattern.search(line)
                if initial_match:
                    score = float(initial_match.group(1))
                    best_score = max(best_score, score)
                    data_points.append({'Generation': 0, 'Current_Fitness': score, 'Best_Fitness': best_score})
                    initial_found = True
                    continue

            # 2. Capture Iteration Number
            iter_match = iter_pattern.search(line)
            if iter_match:
                last_iter_num = int(iter_match.group(1))
                continue

            # 3. Capture Metrics (linked to the last seen Iteration Number)
            metrics_match = metrics_pattern.search(line)
            if metrics_match and last_iter_num is not None:
                score = float(metrics_match.group(1))
                best_score = max(best_score, score)
                data_points.append({
                    'Generation': last_iter_num, 
                    'Current_Fitness': score, 
                    'Best_Fitness': best_score
                })
                # Reset so we don't accidentally attribute the same score to different lines
                last_iter_num = None 

    # Sort data points by Generation just in case logs are out of order due to parallel processing
    data_points.sort(key=lambda x: x['Generation'])

    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['Generation', 'Current_Fitness', 'Best_Fitness']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_points)

    print(f"Successfully extracted {len(data_points)} data points to {output_csv}")

# Updated path based on your latest log snippet
log_path = "examples/circle_packing/openevolve_output/checkpoints/checkpoint_100/openevolve_output/logs/openevolve_20260312_161659.log"
output_path = "examples/circle_packing/openevolve_output/fitness_history.csv"
parse_openevolve_logs(log_path, output_path)