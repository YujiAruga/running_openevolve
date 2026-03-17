import subprocess
import os
import glob
import tempfile

from openevolve.evaluation_result import EvaluationResult


class Evaluator:
    def __init__(self, data_path=None):
        self.language = "cpp"
        if data_path is None:
            data_path = "examples/graph_coloring/data"

        self.cpp_file = "temp_algo.cpp"
        self.exe_file = "./temp_algo.out"
        self.instances = self._load_instances(data_path)
        self.history = "examples/graph_coloring/openevolve_output/fitness_history.csv"

        if not self.instances:
            print(
                f"WARNING: No data files found in {data_path}. Please download .col files."
            )

    def _load_instances(self, data_path):
        """Parses DIMACS .col files."""
        instances = []
        for filepath in glob.glob(os.path.join(data_path, "*.col")):
            with open(filepath, "r") as f:
                raw_text = f.read()

            v_count, e_count = 0, 0
            edges = []

            for line in raw_text.splitlines():
                parts = line.split()
                if not parts:
                    continue
                if parts[0] == "p" and parts[1] == "edge":
                    v_count = int(parts[2])
                    e_count = int(parts[3])
                elif parts[0] == "e":
                    u, v = int(parts[1]), int(parts[2])
                    edges.append((u, v))

            if v_count > 0:
                instances.append(
                    {
                        "name": os.path.basename(filepath),
                        "V": v_count,
                        "E": e_count,
                        "edges": edges,
                        "raw_text": raw_text,
                    }
                )
        return instances

    def _extract_cpp_code(self, code_string):
        """Extracts C++ code if the LLM wraps it in markdown."""
        if "```cpp" in code_string:
            return code_string.split("```cpp")[1].split("```")[0].strip()
        if "```c++" in code_string:
            return code_string.split("```c++")[1].split("```")[0].strip()
        if "```" in code_string:
            return code_string.split("```")[1].split("```")[0].strip()
        return code_string.strip()

    def _evaluate_single(self, code_string):
        if not self.instances:
            return EvaluationResult(
                metrics={"score": 0.0, "valid": 0.0},
                artifacts={"error": "No data instances found."},
            )

        clean_code = self._extract_cpp_code(code_string)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cpp", delete=False) as f:
            f.write(clean_code)
            cpp_file = f.name

        exe_file = cpp_file + ".out"

        compile_process = subprocess.run(
            ["g++", "-O3", "-std=c++17", cpp_file, "-o", exe_file],
            capture_output=True,
            text=True,
        )

        if compile_process.returncode != 0:
            os.remove(cpp_file)
            err_msg = (
                compile_process.stderr.strip().splitlines()[-1]
                if compile_process.stderr
                else "Unknown Compilation Error"
            )
            return EvaluationResult(
                metrics={"score": 0.0, "valid": 0.0},
                artifacts={"error": f"[Compilation Failed] {err_msg}"},
            )

        total_colors_used = 0
        valid_count = 0
        full_feedback = ""
        sum_of_num_of_optimal_colors_of_all_instances = 579

        for idx, instance in enumerate(self.instances, 1):
            full_feedback += f"---------- Instance {idx} ----------\n"
            full_feedback += f"{instance['name']} has {instance['V']} vertices and {instance['E']} edges.\n"
            try:
                run_process = subprocess.run(
                    [exe_file],
                    input=instance["raw_text"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                output = run_process.stdout
                if run_process.returncode != 0:
                    full_feedback += f"[Crash] Runtime Error.\n"
                    continue

                colors = []
                in_result = False
                for line in output.split("\n"):
                    line = line.strip()
                    if line == "RESULT_START":
                        in_result = True
                        continue
                    if line == "RESULT_END":
                        break
                    if in_result and line:
                        try:
                            colors.extend([int(x) for x in line.split()])
                        except ValueError:
                            pass

                V = instance["V"]
                if len(colors) != V:
                    full_feedback += f"[Fail] Returned {len(colors)} colors, expected {V} vertices.\n"
                    continue

                is_valid = True
                for u, v in instance["edges"]:
                    if colors[u - 1] == colors[v - 1]:
                        full_feedback += f"[Conflict] Vertices {u} and {v} both have color {colors[u - 1]}.\n"
                        is_valid = False
                        break

                if not is_valid:
                    continue

                num_colors = len(set(colors))
                total_colors_used += num_colors
                full_feedback += f"Valid! Colors used: {num_colors}\n"
                valid_count += 1

            except subprocess.TimeoutExpired:
                full_feedback += f"[Timeout] Algorithm exceeded 5s.\n"
            except Exception as e:
                full_feedback += f"[System Error] {str(e)}\n"

        if os.path.exists(cpp_file):
            os.remove(cpp_file)
        if os.path.exists(exe_file):
            os.remove(exe_file)

        if valid_count < len(self.instances):
            if valid_count == 0:
                return EvaluationResult(
                    metrics={"score": 0.0, "valid": 0.0},
                    artifacts={"feedback": f"Failed all instances.\n{full_feedback}"},
                )
            return EvaluationResult(
                metrics={"score": 0.0, "valid": 0.0},
                artifacts={"feedback": f"Failed on some instances.\n{full_feedback}"},
            )

        full_feedback += f"The sum of the number of optimal colors of all instances is {sum_of_num_of_optimal_colors_of_all_instances} and the algorithm used {total_colors_used}.\n"
        fitness_score = (
            sum_of_num_of_optimal_colors_of_all_instances / total_colors_used
        ) * 100


        return EvaluationResult(
            metrics={
                "score": fitness_score,
                "valid": 1.0,
                "colors_used": total_colors_used,
            },
            artifacts={"feedback": full_feedback},
        )


_evaluator = None


def evaluate(program_path: str) -> EvaluationResult:
    """OpenEvolve evaluator function."""
    global _evaluator
    if _evaluator is None:
        _evaluator = Evaluator()

    with open(program_path, "r") as f:
        code = f.read()

    return _evaluator._evaluate_single(code)

def log_fitness(score, filepath="examples/graph_coloring/openevolve_output/fitness_history.csv"):
    # Ensure the directory exists so the code doesn't crash
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # 'a' stands for append mode
    with open(filepath, "a") as f:
        f.write(f"{score}\n")
