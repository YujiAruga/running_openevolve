import subprocess
import os
import glob

from openevolve.evaluation_result import EvaluationResult


class Evaluator:
    def __init__(self, data_path=None):
        self.language = "cpp"
        if data_path is None:
            data_path = "examples/job_scheduling/data"
        self.cpp_file = "temp_algo.cpp"
        self.exe_file = "./temp_algo.out"
        self.instances = self._load_instances(data_path)

        if not self.instances:
            print(
                f"WARNING: No data files found in {data_path}. Ensure .txt files are present."
            )

    def _load_instances(self, data_path):
        instances = []
        for filepath in glob.glob(os.path.join(data_path, "*.txt")):
            with open(filepath, "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]

            n, m = map(int, lines[0].split())
            jobs = []
            max_job_duration = 0
            machine_workloads = [0] * m

            for i in range(1, n + 1):
                row = list(map(int, lines[i].split()))
                job_ops = []
                current_job_dur = 0
                for j in range(0, len(row), 2):
                    m_id, dur = row[j], row[j + 1]
                    job_ops.append({"m": m_id, "d": dur})
                    current_job_dur += dur
                    machine_workloads[m_id] += dur
                jobs.append(job_ops)
                max_job_duration = max(max_job_duration, current_job_dur)

            L = max(max_job_duration, max(machine_workloads))

            instances.append(
                {"n": n, "m": m, "jobs": jobs, "L": L, "raw": " ".join(lines)}
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

    def evaluate(self, code_string):
        if not self.instances:
            return EvaluationResult(
                metrics={"score": 0.0, "valid": 0.0},
                artifacts={"error": "No data instances found."},
            )

        clean_code = self._extract_cpp_code(code_string)

        with open(self.cpp_file, "w") as f:
            f.write(clean_code)

        compile_proc = subprocess.run(
            ["g++", "-O3", "-std=c++17", self.cpp_file, "-o", self.exe_file],
            capture_output=True,
            text=True,
        )
        if compile_proc.returncode != 0:
            if os.path.exists(self.cpp_file):
                os.remove(self.cpp_file)
            err_msg = (
                compile_proc.stderr.strip().splitlines()[-1]
                if compile_proc.stderr
                else "Unknown Compilation Error"
            )
            return EvaluationResult(
                metrics={"score": 0.0, "valid": 0.0},
                artifacts={"error": f"[Compilation Failed] {err_msg}"},
            )

        total_fitness = 0.0
        full_feedback = ""
        valid_instances = 0

        for idx, inst in enumerate(self.instances):
            try:
                run_proc = subprocess.run(
                    [self.exe_file],
                    input=inst["raw"],
                    text=True,
                    capture_output=True,
                    timeout=5,
                )

                if "RESULT_START" in run_proc.stdout:
                    result = int(
                        run_proc.stdout.split("RESULT_START")[1]
                        .split("RESULT_END")[0]
                        .strip()
                    )
                    fitness = (inst["L"] / result)
                    total_fitness += fitness
                    valid_instances += 1
                    full_feedback += f"Instance {idx + 1}: Makespan={result}, L={inst['L']}, Fitness={fitness:.2f}\n"
                else:
                    full_feedback += f"Instance {idx + 1}: Invalid output format\n"

            except subprocess.TimeoutExpired:
                full_feedback += f"Instance {idx + 1}: Timeout\n"
            except Exception as e:
                full_feedback += f"Instance {idx + 1}: Error - {str(e)}\n"
            finally:
                if os.path.exists(self.cpp_file):
                    os.remove(self.cpp_file)

        if os.path.exists(self.exe_file):
            os.remove(self.exe_file)

        final_score = total_fitness / len(self.instances) if self.instances else 0.0

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
