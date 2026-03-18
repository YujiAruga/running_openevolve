import subprocess
import os
import textwrap
import glob

from openevolve.evaluation_result import EvaluationResult


class Evaluator:
    def __init__(self, data_path=None):
        self.language = "python"
        if data_path is None:
            data_path = "examples/knapsack/data"
        self.temp_file = "temp_packing.py"
        self.instances = self._load_instances(data_path)

        if not self.instances:
            print(
                f"WARNING: No data files found in {data_path}. Ensure .2kp or .3kp files are present."
            )

    def _load_instances(self, data_path):
        instances = []
        files = glob.glob(os.path.join(data_path, "*.2kp")) + glob.glob(
            os.path.join(data_path, "*.3kp")
        )

        for filepath in files:
            with open(filepath, "r") as f:
                lines = [line.strip() for line in f if line.strip()]
                if not lines:
                    continue

                try:
                    header = [x.strip() for x in lines[0].split(",")]
                    vals = [float(x) for x in header if x.lower() != "dim"]

                    dim = len(vals)
                    container_dims = tuple(vals)

                    items = []
                    for line in lines[1:]:
                        parts = [x.strip() for x in line.split(",")]
                        data = [x for x in parts if x.lower() != "rect"]
                        data = data[1:]

                        if dim == 2:
                            items.append(
                                {
                                    "id": int(parts[1]),
                                    "w": float(data[0]),
                                    "h": float(data[1]),
                                    "p": float(data[2]),
                                    "count": int(data[3]),
                                }
                            )
                        else:
                            items.append(
                                {
                                    "id": int(parts[1]),
                                    "w": float(data[0]),
                                    "h": float(data[1]),
                                    "d": float(data[2]),
                                    "p": float(data[3]),
                                    "count": int(data[4]),
                                }
                            )

                    instances.append(
                        {
                            "name": os.path.basename(filepath),
                            "dim": dim,
                            "container": container_dims,
                            "items": items,
                            "total_possible_profit": sum(
                                it["p"] * it["count"] for it in items
                            ),
                        }
                    )
                except Exception as e:
                    print(f"Skipping {filepath} due to parsing error: {e}")
        return instances

    def _prepare_script(self, code_string, container, items):
        template = textwrap.dedent("""
        import math
        import sys

        # --- CANDIDATE CODE START ---
        <INJECT_CODE>
        # --- CANDIDATE CODE END ---

        if __name__ == "__main__":
            try:
                container = <INJECT_CONTAINER>
                items = <INJECT_ITEMS>
                
                result = solve_packing(container, items)
                
                print("RESULT_START")
                if isinstance(result, list):
                    for placement in result:
                        print(",".join(map(str, placement)))
                print("RESULT_END")
                
            except Exception as e:
                print(f"ERROR: {e}")
        """)

        full_code = template.replace("<INJECT_CODE>", code_string)
        full_code = full_code.replace("<INJECT_CONTAINER>", str(container))
        full_code = full_code.replace("<INJECT_ITEMS>", str(items))
        return full_code

    def _check_overlap(self, dim, p1, p2):
        if dim == 2:
            _, x1, y1, w1, h1 = p1
            _, x2, y2, w2, h2 = p2
            return not (
                x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1
            )
        else:
            _, x1, y1, z1, w1, h1, d1 = p1
            _, x2, y2, z2, w2, h2, d2 = p2
            return not (
                x1 + w1 <= x2
                or x2 + w2 <= x1
                or y1 + h1 <= y2
                or y2 + h2 <= y1
                or z1 + d1 <= z2
                or z2 + d2 <= z1
            )

    def evaluate(self, code_string):
        if not self.instances:
            return EvaluationResult(
                metrics={"score": 0.0, "valid": 0.0},
                artifacts={"error": "No data instances found."},
            )

        total_normalized_score = 0.0
        full_feedback = ""
        valid_instances = 0

        for idx, inst in enumerate(self.instances):
            full_feedback += f"--- Instance {idx + 1}: {inst['name']} ---\n"
            full_code = self._prepare_script(
                code_string, inst["container"], inst["items"]
            )

            with open(self.temp_file, "w") as f:
                f.write(full_code)

            try:
                result = subprocess.run(
                    ["python3", self.temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    full_feedback += f"[Crash] {result.stderr.strip().splitlines()[-1] if result.stderr else 'Unknown error'}\n"
                    continue

                placements = []
                in_result = False
                for line in result.stdout.splitlines():
                    if line.strip() == "RESULT_START":
                        in_result = True
                        continue
                    if line.strip() == "RESULT_END":
                        break
                    if in_result and line.strip():
                        try:
                            placements.append(tuple(map(float, line.split(","))))
                        except:
                            pass

                current_profit = 0.0
                item_usage = {}
                is_valid = True

                for i, p in enumerate(placements):
                    expected_len = 5 if inst["dim"] == 2 else 7
                    if len(p) != expected_len:
                        full_feedback += f"[Fail] Placement {i} has wrong dimensions.\n"
                        is_valid = False
                        break

                    item_id = int(p[0])
                    item_ref = next(
                        (it for it in inst["items"] if it["id"] == item_id), None
                    )

                    if not item_ref:
                        full_feedback += f"[Fail] Unknown Item ID {item_id}.\n"
                        is_valid = False
                        break

                    item_usage[item_id] = item_usage.get(item_id, 0) + 1
                    if item_usage[item_id] > item_ref["count"]:
                        full_feedback += f"[Fail] Exceeded count for item {item_id}.\n"
                        is_valid = False
                        break

                    if inst["dim"] == 2:
                        _, x, y, w, h = p
                        if (
                            x < 0
                            or y < 0
                            or x + w > inst["container"][0]
                            or y + h > inst["container"][1]
                        ):
                            full_feedback += f"[Fail] Item {item_id} out of bounds.\n"
                            is_valid = False
                            break
                    else:
                        _, x, y, z, w, h, d = p
                        if (
                            x < 0
                            or y < 0
                            or z < 0
                            or x + w > inst["container"][0]
                            or y + h > inst["container"][1]
                            or z + d > inst["container"][2]
                        ):
                            full_feedback += f"[Fail] Item {item_id} out of bounds.\n"
                            is_valid = False
                            break

                    for j in range(i + 1, len(placements)):
                        if self._check_overlap(inst["dim"], p, placements[j]):
                            full_feedback += (
                                f"[Fail] Overlap between items {i} and {j}.\n"
                            )
                            is_valid = False
                            break

                    if not is_valid:
                        break
                    current_profit += item_ref["p"]

                if is_valid:
                    norm_score = (
                        current_profit / inst["total_possible_profit"]
                        if inst["total_possible_profit"] > 0
                        else 0
                    )
                    total_normalized_score += norm_score
                    valid_instances += 1
                    full_feedback += f"[Valid] Profit: {current_profit}\n"

            except subprocess.TimeoutExpired:
                full_feedback += "[Timeout] Execution exceeded 10s.\n"
            finally:
                if os.path.exists(self.temp_file):
                    os.remove(self.temp_file)

        final_score = (
            (total_normalized_score / len(self.instances))
            if self.instances
            else 0.0
        )

        return EvaluationResult(
            metrics={
                "score": final_score,
                "valid": 1.0 if valid_instances == len(self.instances) else 0.0,
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

    return _evaluator.evaluate(code)
