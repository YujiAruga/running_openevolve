import re
import csv
import os

def parse_openevolve_logs(log_file_path, output_csv):
    # Regex patterns for the two types of lines we need
    # 1. Initial program evaluation (Iteration 0)
    # 2. Subsequent iterations
    iter_pattern = re.compile(r"Iteration (\d+):.*Metrics: score=([\d.]+)")
    initial_pattern = re.compile(r"Evaluated program .* score=([\d.]+)")

    data_points = []
    best_score = float('-inf')  # Assuming higher is better based on your logs

    if not os.path.exists(log_file_path):
        print(f"Error: File {log_file_path} not found.")
        return

    with open(log_file_path, 'r') as f:
        # We handle the initial program as Iteration 0
        initial_found = False
        
        lines = f.readlines()
        for i, line in enumerate(lines):
            # Check for initial score first
            if not initial_found:
                initial_match = initial_pattern.search(line)
                if initial_match:
                    score = float(initial_match.group(1))
                    best_score = max(best_score, score)
                    data_points.append({'iteration': 0, 'score': score, 'best_so_far': best_score})
                    initial_found = True
                    continue

            # Check for standard iterations
            # In your logs, Iteration and Metrics are often on separate lines.
            # We look for "Iteration X" and then peek at the next line for "Metrics"
            if "Iteration" in line:
                iter_num_match = re.search(r"Iteration (\d+):", line)
                if iter_num_match:
                    iter_num = int(iter_num_match.group(1))
                    
                    # Look at the next line for the score
                    if i + 1 < len(lines) and "Metrics: score=" in lines[i+1]:
                        score_match = re.search(r"score=([\d.]+)", lines[i+1])
                        if score_match:
                            score = float(score_match.group(1))
                            best_score = max(best_score, score)
                            data_points.append({
                                'iteration': iter_num, 
                                'score': score, 
                                'best_so_far': best_score
                            })

    # Write to CSV
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['iteration', 'score', 'best_so_far']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_points)

    print(f"Successfully extracted {len(data_points)} data points to {output_csv}")

# Usage
log_path = "examples/knapsack/openevolve_output/logs/openevolve_20260318_012146.log"
output_path = "examples/knapsack/openevolve_output/fitness_history.csv"
parse_openevolve_logs(log_path, output_path)