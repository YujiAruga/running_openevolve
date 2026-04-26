#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>

using namespace std;

struct Point {
    double x, y;
};

// Helper: Euclidean distance
double dist(const Point& a, const Point& b) {
    return sqrt(pow(a.x - b.x, 2) + pow(a.y - b.y, 2));
}

// Helper: Calculate the total cost of the closed loop
double get_tour_distance(int N, const vector<int>& tour, const vector<Point>& cities) {
    double total = 0;
    for (int i = 0; i < N; ++i) {
        double dx = cities[tour[i]].x - cities[tour[(i + 1) % N]].x;
        double dy = cities[tour[i]].y - cities[tour[(i + 1) % N]].y;
        total += sqrt(dx * dx + dy * dy);
    }
    return total;
}

// EVOLVE-BLOCK-START
vector<int> solve_tsp(int N, const vector<Point>& cities) {
    if (N == 0) return {};

    // No dense distance matrix is used; distances are computed on demand via dist()

    // 1. Farthest‑Insertion Initial Tour
    vector<int> tour;
    vector<bool> visited(N, false);
    tour.push_back(0);
    visited[0] = true;
    int visited_count = 1;

    while (visited_count < N) {
        // Find the unvisited city with the largest distance to any visited city
        int farthest_city = -1;
        double max_min_dist = -1.0;
        for (int c = 0; c < N; ++c) {
            if (visited[c]) continue;
            double min_to_visited = 1e18;
            for (int v : tour) {
                // use the helper dist() instead of a pre‑computed matrix
                double d = distSq(cities[c], cities[v]);
                if (d < min_to_visited)
                    min_to_visited = d;
            }
            if (min_to_visited > max_min_dist) {
                max_min_dist = min_to_visited;
                farthest_city = c;
            }
        }

        // Find best insertion position for the farthest city
        int best_pos = 0;
        double best_increase = 1e18;
        int sz = tour.size();
        for (int i = 0; i < sz; ++i) {
            int next = (i + 1) % sz;
            double old_edge = distSq(cities[tour[i]], cities[tour[next]]);
            double new_edges = distSq(cities[tour[i]], cities[farthest_city]) +
                               distSq(cities[farthest_city], cities[tour[next]]);
            double increase = new_edges - old_edge;
            if (increase < best_increase) {
                best_increase = increase;
                best_pos = next;
            }
        }
        tour.insert(tour.begin() + best_pos, farthest_city);
        visited[farthest_city] = true;
        ++visited_count;
    }

    // 2. 2‑Opt Optimization using squared distances for comparisons
    // Limit 2‑Opt iterations to avoid excessive runtime on large instances
    const int max_passes = 3;
    int passes = 0;
    bool improved = true;
    while (improved && passes < max_passes) {
        improved = false;
        for (int i = 1; i < N - 1; ++i) {
            for (int j = i + 1; j < N; ++j) {
                double old_dist = distSq(cities[tour[i-1]], cities[tour[i]]) +
                                  distSq(cities[tour[j]], cities[tour[(j+1)%N]]);
                double new_dist = distSq(cities[tour[i-1]], cities[tour[j]]) +
                                  distSq(cities[tour[i]], cities[tour[(j+1)%N]]);
                if (new_dist < old_dist) {
                    reverse(tour.begin() + i, tour.begin() + j + 1);
                    improved = true;
                }
            }
        }
        ++passes;
    }

    return tour;
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