#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <random>

using namespace std;

struct Point {
    double x, y;
};

// Helper: Euclidean distance
double dist(const Point& a, const Point& b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return sqrt(dx*dx + dy*dy); // used only for final tour length
}
 
// Squared Euclidean distance for fast comparisons
inline double dist2(const Point& a, const Point& b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return dx*dx + dy*dy;
}
 
void two_opt(vector<int>& tour, const vector<Point>& cities) {
    int N = tour.size();
    bool improved = true;
    while (improved) {
        improved = false;
        for (int i = 1; i < N - 1; i++) {
            for (int j = i + 1; j < N; j++) {
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
    
    // 1. Initial Greedy Tour (Nearest Neighbor)
    vector<int> tour;
    vector<bool> visited(N, false);
    int curr = 0;
    tour.push_back(curr);
    visited[curr] = true;

    for (int i = 1; i < N; i++) {
        int best_next = -1;
        double min_d = 1e18;
        for (int j = 0; j < N; j++) {
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

    // 2. 2-Opt Optimization (Untwisting the loop)
    bool improved = true;
    while (improved) {
        improved = false;
        for (int i = 1; i < N - 1; i++) {
            for (int j = i + 1; j < N; j++) {
                // Check if swapping edges (i-1, i) and (j, j+1) reduces distance
                // Current edges: (i-1 -> i) and (j -> j+1)
                // New edges: (i-1 -> j) and (i -> j+1)
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
    
    // Random restarts to escape local minima
    double best_dist = get_tour_distance(N, tour, cities);
    vector<int> best_tour = tour;
    std::mt19937 rng(std::random_device{}());
    for (int restart = 0; restart < 3; ++restart) {
        std::vector<int> rand_tour(N);
        std::iota(rand_tour.begin(), rand_tour.end(), 0);
        std::shuffle(rand_tour.begin(), rand_tour.end(), rng);
        two_opt(rand_tour, cities);
        double dist_val = get_tour_distance(N, rand_tour, cities);
        if (dist_val < best_dist) {
            best_dist = dist_val;
            best_tour = rand_tour;
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