#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <random>
#include <limits>
static std::mt19937 rng(std::random_device{}());

using namespace std;

struct Point {
    double x, y;
};

// Helper: Euclidean distance
double dist(const Point& a, const Point& b) {
    return hypot(a.x - b.x, a.y - b.y);
}

// Helper: Calculate the total cost of the closed loop
double get_tour_distance(int N, const vector<int>& tour, const vector<Point>& cities) {
    double total = 0;
    for (int i = 0; i < N; i++) {
        total += dist(cities[tour[i]], cities[tour[(i + 1) % N]]);
    }
    return total;
}



// EVOLVE-BLOCK-START
vector<int> solve_tsp(int N, const vector<Point>& cities) {
    if (N == 0) return {};

    // Multi‑restart framework
    const int MAX_RESTARTS = 3;
    vector<int> best_tour;
    double best_total = std::numeric_limits<double>::infinity();

    static std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<int> dist_start(0, N - 1);

    for (int attempt = 0; attempt < MAX_RESTARTS; ++attempt) {
        // 1. Initial Greedy Tour (Nearest Neighbor)
        vector<int> tour;
        vector<bool> visited(N, false);
        int curr = (N > 5000) ? 0 : dist_start(rng); // deterministic for very large cases
        tour.push_back(curr);
        visited[curr] = true;

        for (int i = 1; i < N; ++i) {
            int best_next = -1;
            double min_d = 1e18;
            for (int j = 0; j < N; ++j) {
                if (!visited[j]) {
                    double d = dist(cities[curr], cities[j]);
                    if (d < min_d) {
                        min_d = d;
                        best_next = j;
                    }
                }
            }
            tour.push_back(best_next);
            visited[best_next] = true;
            curr = best_next;
        }

        // 2. 2‑Opt Optimization (limited passes)
        const int MAX_PASSES = 10; // reduce runtime while still improving
        int passes = 0;
        while (passes < MAX_PASSES) {
            bool improved = false;
            for (int i = 1; i < N - 1; ++i) {
                for (int j = i + 1; j < N; ++j) {
                    double old_dist = dist(cities[tour[i-1]], cities[tour[i]]) 
                                    + dist(cities[tour[j]], cities[tour[(j+1)%N]]);
                    double new_dist = dist(cities[tour[i-1]], cities[tour[j]]) 
                                    + dist(cities[tour[i]], cities[tour[(j+1)%N]]);
                    if (new_dist < old_dist) {
                        reverse(tour.begin() + i, tour.begin() + j + 1);
                        improved = true;
                    }
                }
                if (improved) break;
            }
            if (!improved) break;
            ++passes;
        }

        // 3. Relocation optimization (delta‑based) for small instances
        const int RELOC_THRESHOLD = 2000;
        if (N <= RELOC_THRESHOLD) {
            double current_total = get_tour_distance(N, tour, cities);
            bool moved = true;
            while (moved) {
                moved = false;
                for (int i = 0; i < N && !moved; ++i) {
                    int city = tour[i];
                    int prev = tour[(i - 1 + N) % N];
                    int next = tour[(i + 1) % N];
                    double remove_delta = -dist(cities[prev], cities[city])
                                        - dist(cities[city], cities[next])
                                        + dist(cities[prev], cities[next]);

                    vector<int> temp = tour;
                    temp.erase(temp.begin() + i);

                    for (int j = 0; j < N - 1; ++j) {
                        int before = temp[(j - 1 + N - 1) % (N - 1)];
                        int after  = temp[j % (N - 1)];
                        double insert_delta = dist(cities[before], cities[city])
                                            + dist(cities[city], cities[after])
                                            - dist(cities[before], cities[after]);

                        double new_total = current_total + remove_delta + insert_delta;
                        if (new_total + 1e-9 < current_total) {
                            temp.insert(temp.begin() + j, city);
                            tour = temp;
                            current_total = new_total;
                            moved = true;
                            break;
                        }
                    }
                }
            }
        }

        double total = get_tour_distance(N, tour, cities);
        if (total < best_total) {
            best_total = total;
            best_tour = tour;
        }
    }
    return best_tour;
}
// EVOLVE-BLOCK-END

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int N;
    if (!(cin >> N)) return 0;

    vector<Point> cities(N);
    for (int i = 0; i < N; ++i) cin >> cities[i].x >> cities[i].y;

    vector<int> tour = solve_tsp(N, cities);

    cout << "RESULT_START\n";
    for (int i = 0; i < N; ++i) cout << tour[i] << (i == N - 1 ? "" : " ");
    cout << "\nRESULT_END\n";

    return 0;
}