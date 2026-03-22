import subprocess
import os
import glob
import math
import heapq
import tempfile

from openevolve.evaluation_result import EvaluationResult


class Evaluator:
    def __init__(self, data_path=None):
        self.language = "cpp"
        if data_path is None:
            data_path = "examples/tsp/data"
        self.history = "examples/tsp/openevolve_output/fitness_history.csv"

        self.cpp_file = "temp_algo.cpp"
        self.exe_file = "./temp_algo.out"
        self.instances = self._load_instances(data_path)

        if not self.instances:
            print(
                f"WARNING: No data files found in {data_path}. Please download .tsp files."
            )
        else:
            # Pre-calculate MST for each instance to use as a baseline
            for inst in self.instances:
                inst["lower_bound"] = self._get_lower_bound(inst["cities"])

    def _load_instances(self, data_path):
        """Parses standard TSPLIB format files."""
        instances = []
        for filepath in glob.glob(os.path.join(data_path, "*.tsp")):
            with open(filepath, "r") as f:
                lines = f.readlines()

            dimension = 0
            cities = []
            in_node_section = False

            for line in lines:
                line = line.strip()
                if not line or line == "EOF":
                    continue

                if line.startswith("DIMENSION"):
                    dimension = int(line.replace(":", "").split()[-1])
                elif line.startswith("NODE_COORD_SECTION"):
                    in_node_section = True
                    continue
                elif in_node_section:
                    parts = line.split()
                    if len(parts) >= 3:
                        cities.append((float(parts[1]), float(parts[2])))

            if dimension > 0 and len(cities) == dimension:
                instances.append(
                    {
                        "name": os.path.basename(filepath),
                        "dimension": dimension,
                        "cities": cities,
                    }
                )
        return instances

    def _extract_cpp_code(self, code_string):
        if "```cpp" in code_string:
            return code_string.split("```cpp")[1].split("```")[0].strip()
        if "```c++" in code_string:
            return code_string.split("```c++")[1].split("```")[0].strip()
        if "```" in code_string:
            return code_string.split("```")[1].split("```")[0].strip()
        return code_string.strip()

    def _calculate_mst(self, cities):
        """Calculates the weight of the Minimum Spanning Tree using Prim's Algorithm."""
        n = len(cities)
        if n == 0:
            return 0

        mst_weight = 0.0
        visited = [False] * n
        min_heap = [(0.0, 0)]  # (cost, node)
        count = 0

        while min_heap and count < n:
            cost, u = heapq.heappop(min_heap)
            if visited[u]:
                continue

            visited[u] = True
            mst_weight += cost
            count += 1

            for v in range(n):
                if not visited[v]:
                    c1, c2 = cities[u], cities[v]
                    dist = math.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)
                    heapq.heappush(min_heap, (dist, v))
        return mst_weight

    def _get_lower_bound(self, cities):
        x_coords = [c[0] for c in cities]
        y_coords = [c[1] for c in cities]
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        return math.sqrt(width**2 + height**2)

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

        fitness = 0.0
        full_feedback = ""
        valid_count = 0

        # 2. Run compiled binary against instances
        for idx, instance in enumerate(self.instances, 1):
            full_feedback += f"---------- Instance {idx} ----------\n"
            full_feedback += (
                f" {instance['name']} has {instance['dimension']} cities.\n "
            )
            try:
                # Prepare clean data for C++ stdin
                # Format:
                # N
                # x0 y0
                # x1 y1 ...
                input_list = [str(instance["dimension"])]
                for x, y in instance["cities"]:
                    input_list.append(f"{x} {y}")
                input_data = "\n".join(input_list) + "\n"

                run_process = subprocess.run(
                    [exe_file],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                output = run_process.stdout
                if run_process.returncode != 0:
                    err_msg = (
                        run_process.stderr.strip().splitlines()[-1]
                        if run_process.stderr
                        else "Runtime Error"
                    )
                    full_feedback += f"[Crash] {err_msg}\n"
                    continue

                # Parse the C++ output
                tour = []
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
                            # Parse space-separated or comma-separated output
                            cleaned_line = line.replace(",", " ")
                            tour.extend([int(x) for x in cleaned_line.split()])
                        except ValueError:
                            pass

                # --- VALIDATION ---
                N = instance["dimension"]
                if len(tour) != N:
                    full_feedback += (
                        f"[Fail] Returned {len(tour)} cities, expected exactly {N}.\n"
                    )
                    continue

                if len(set(tour)) != N or min(tour) < 0 or max(tour) >= N:
                    full_feedback += f"[Fail] Tour must contain exactly one of each integer from 0 to {N - 1}.\n"
                    continue

                # --- DISTANCE CALCULATION ---
                cities = instance["cities"]
                tour_dist = 0.0
                for i in range(N):
                    c1 = cities[tour[i]]
                    c2 = cities[tour[(i + 1) % N]]

                    # Exact Euclidean distance
                    dx = c1[0] - c2[0]
                    dy = c1[1] - c2[1]
                    tour_dist += math.sqrt(dx * dx + dy * dy)

                fitness += instance["lower_bound"] / tour_dist
                full_feedback += f"Valid! Tour Distance: {tour_dist:.2f}\n"
                valid_count += 1

            except subprocess.TimeoutExpired:
                full_feedback += f"[Timeout] Algorithm took > 5s.\n"
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

        final_fitness = fitness / valid_count
        return EvaluationResult(
            metrics={"score": final_fitness, "valid": 1.0},
            artifacts={
                "feedback": f"Perfect run! The average of weight of MST divided by tour distance: {final_fitness:.4f}\n{full_feedback}"
            },
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


def log_fitness(score, filepath="examples/tsp/openevolve_output/fitness_history.csv"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "a") as f:
        f.write(f"{score}\n")
