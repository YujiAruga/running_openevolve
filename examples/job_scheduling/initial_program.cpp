#include <iostream>
#include <vector>
#include <algorithm>
#include <numeric>
#include <limits>

using namespace std;

struct Operation {
    int machine_id;
    int duration;
};

int get_work_remaining(int job_idx, int current_op_idx, int m, const vector<vector<Operation>>& jobs) {
    int remaining = 0;
    for (int j = current_op_idx; j < m; ++j) {
        remaining += jobs[job_idx][j].duration;
    }
    return remaining;
}

int solve_jssp(int n, int m, const vector<vector<Operation>>& jobs) {
    // EVOLVE-BLOCK-START
    vector<int> job_next_op(n, 0);
    vector<int> job_ready_time(n, 0);
    vector<int> machine_free_time(m, 0);
    
    int total_operations = n * m;
    int completed_ops = 0;

    while (completed_ops < total_operations) {
        int best_job = -1;
        int best_priority = -1;
        int earliest_start = numeric_limits<int>::max();

        for (int i = 0; i < n; ++i) {
            if (job_next_op[i] < m) {
                int machine = jobs[i][job_next_op[i]].machine_id;
                int ready = max(job_ready_time[i], machine_free_time[machine]);
                
                int work_rem = get_work_remaining(i, job_next_op[i], m, jobs);
                
                if (best_job == -1 || ready < earliest_start || (ready == earliest_start && work_rem > best_priority)) {
                    earliest_start = ready;
                    best_priority = work_rem;
                    best_job = i;
                }
            }
        }

        int op_idx = job_next_op[best_job];
        Operation& op = const_cast<Operation&>(jobs[best_job][op_idx]);
        
        int start_time = max(job_ready_time[best_job], machine_free_time[op.machine_id]);
        int end_time = start_time + op.duration;

        job_ready_time[best_job] = end_time;
        machine_free_time[op.machine_id] = end_time;
        job_next_op[best_job]++;
        completed_ops++;
    }

    int makespan = 0;
    for (int time : machine_free_time) {
        makespan = max(makespan, time);
    }
    // EVOLVE-BLOCK-END

    return makespan;
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n, m;
    if (!(cin >> n >> m)) return 0;
    vector<vector<Operation>> jobs(n, vector<Operation>(m));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < m; ++j) {
            cin >> jobs[i][j].machine_id >> jobs[i][j].duration;
        }
    }

    int result = solve_jssp(n, m, jobs);
    cout << "RESULT_START" << endl;
    cout << result << endl;
    cout << "RESULT_END" << endl;
    return 0;
}
