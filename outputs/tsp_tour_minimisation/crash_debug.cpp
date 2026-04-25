#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <random>
#include <limits>

using namespace std;

struct Point {
    double x, y;
};

// Helper: Euclidean distance
double dist(const Point& a, const Point& b) {
    // Return true Euclidean distance
    return sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
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

    const int restarts = 3;
    vector<int> best_tour;
    double best_dist = numeric_limits<double>::infinity();
    std::mt19937 rng(std::random_device{}());

    for (int r = 0; r < restarts; ++r) {
        vector<int> tour;
        vector<bool> visited(N, false);
        int curr = rng() % N;
        tour.push_back(curr);
        visited[curr] = true;

        for (int i = 1; i < N; ++i) {
            int best_next = -1;
            double min_d = numeric_limits<double>::infinity();
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
        // Random shake to escape local optimum
        const int shake_iters = 5;
        for (int s = 0; s < shake_iters; ++s) {
            int i = rng() % (N - 1) + 1;
            int j = rng() % (N - 1) + 1;
            if (i > j) swap(i, j);
            double old_dist = dist(cities[tour[i-1]], cities[tour[i]]) +
                              dist(cities[tour[j]], cities[tour[(j+1)%N]]);
            double new_dist = dist(cities[tour[i-1]], cities[tour[j]]) +
                              dist(cities[tour[i]], cities[tour[(j+1)%N]]);
            if (new_dist < old_dist) reverse(tour.begin() + i, tour.begin() + j + 1);
        }
        double cur_dist = 0;

        bool improved = true;
        while (improved) {
            improved = false;
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
            }
        }

        double cur_dist = get_tour_distance(N, tour, cities); // use helper for consistency
        if (cur_dist < best_dist) {
            best_dist = cur_dist;
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