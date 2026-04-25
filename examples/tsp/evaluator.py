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

        self.instances = self._load_instances(data_path)

        if not self.instances:
            print(
                f"WARNING: No data files found in {data_path}. Please download .tsp files."
            )
        else:
            for inst in self.instances:
                inst["lower_bound"] = self._get_lower_bound(inst["cities"])

    def _load_instances(self, data_path):
        """
        Parses standard TSPLIB format files.
        Test instances comes from National TSP Collection on https://www.math.uwaterloo.ca/tsp/data/index.html
        Using test instances less than 10000.
        There are shortest tour record for each instance, some of them have proved as the shortest tour and the others are open.
        (ar9152, eg7146, ei8246, kz9976, tz6117 are still open instances)
        The fitness score be defined by average of ratio of shortest tour length over tour length returned by the algorithm

        """
        shortest_tour = {
            "ar9152.tsp": 837479,
            "ca4663.tsp": 1290319,
            "dj38.tsp": 6656,
            "eg7146.tsp": 172386,
            "ei8246.tsp": 206171,
            "gr9882.tsp": 300899,
            "ja9847.tsp": 491924,
            "kz9976.tsp": 1061881,
            "lu980.tsp": 11340,
            "mu1979.tsp": 86891,
            "nu3496.tsp": 96132,
            "pm8079.tsp": 114855,
            "qa194.tsp": 9352,
            "rw1621.tsp": 26051,
            "tz6117.tsp": 394718,
            "wi29.tsp": 27603,
            "ym7663.tsp": 238314,
            "zi929.tsp": 95345,
        }
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
                filename = os.path.basename(filepath)
                if filename in shortest_tour:
                    instances.append(
                        {
                            "name": filename,
                            "dimension": dimension,
                            "cities": cities,
                            "shortest_tour": shortest_tour[filename],
                        }
                    )
                else:
                    print(
                        f"Skipping {filename}: No shortest tour record found in dictionary."
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
        min_heap = [(0.0, 0)]
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

    def evaluate(self, code_string):
        if not self.instances:
            return 0.0, "No data instances found."

        # 1. Save and Compile C++ code
        clean_code = self._extract_cpp_code(code_string)

        with tempfile.NamedTemporaryFile(
            suffix=".cpp", mode="w", delete=False
        ) as temp_cpp:
            temp_cpp.write(clean_code)
            cpp_path = temp_cpp.name

        # Create a unique executable path based on the temporary cpp file's name
        exe_path = cpp_path[:-4] + ".out"

        compile_process = subprocess.run(
            ["g++", "-O3", "-std=c++17", cpp_path, "-o", exe_path],
            capture_output=True,
            text=True,
        )

        if compile_process.returncode != 0:
            err_msg = (
                compile_process.stderr.strip().splitlines()[-1]
                if compile_process.stderr
                else "Unknown Compilation Error"
            )
            os.makedirs("outputs/tsp_tour_minimisation", exist_ok=True)
            with open("outputs/tsp_tour_minimisation/crash_debug.cpp", "w") as f:
                f.write(clean_code)

            if os.path.exists(cpp_path):
                os.remove(cpp_path)

            return 0.0, f"[Compilation Failed] {err_msg}"

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
                input_list = [str(instance["dimension"])]
                for x, y in instance["cities"]:
                    input_list.append(f"{x} {y}")
                input_data = "\n".join(input_list) + "\n"

                run_process = subprocess.run(
                    [exe_path],
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

                ratio = instance["shortest_tour"] / tour_dist
                if ratio >= 1.0:
                    save_dir = "outputs/tsp_tour_minimisation/algorithms"
                    os.makedirs(save_dir, exist_ok=True)
                    # Name the file based on the instance it broke the record on
                    save_path = os.path.join(
                        save_dir, f"record_breaker_{instance['name']}.cpp"
                    )
                    with open(save_path, "w") as f:
                        f.write(clean_code)
                    full_feedback += f"[WOW] Found a tour shorter than or equal to the known best! Saved to {save_path}\n"

                fitness += instance["shortest_tour"] / tour_dist
                full_feedback += f"Valid! Tour Distance: {tour_dist:.2f}\n"
                valid_count += 1

            except subprocess.TimeoutExpired:
                full_feedback += f"[Timeout] Algorithm took > 10s.\n"
            except Exception as e:
                full_feedback += f"[System Error] {str(e)}\n"

        # 3. Cleanup binaries
        if os.path.exists(cpp_path):
            os.remove(cpp_path)
        if os.path.exists(exe_path):
            os.remove(exe_path)

        # 4. SCORING
        if valid_count < len(self.instances):
            if valid_count == 0:
                return 0.0, f"Failed all instances.\n{full_feedback}"
            return 0.0, f"Failed on some instances.\n{full_feedback}"

        final_fitness = fitness / valid_count
        return (
            final_fitness,
            f"Perfect run! The average ratio of shortest tour to generated tour distance: {final_fitness:.4f}\n{full_feedback}",
        )


def evaluate(program_path):
    """
    Wrapper function for OpenEvolve integration.
    Reads the program file and delegates to Evaluator class.

    Args:
        program_path: Path to the C++ program file

    Returns:
        EvaluationResult with metrics
    """
    try:
        with open(program_path, "r") as f:
            code_string = f.read()
    except Exception as e:
        return EvaluationResult(
            metrics={
                "fitness": 0.0,
                "combined_score": 0.0,
                "error": f"Failed to read program file: {str(e)}",
            }
        )

    evaluator = Evaluator()
    fitness, feedback = evaluator.evaluate(code_string)

    return EvaluationResult(
        metrics={
            "fitness": fitness,
            "combined_score": fitness,
        },
        artifacts={
            "feedback": feedback,
            "language": "cpp",
        },
    )
