#include <iostream>
#include <vector>

#include <algorithm>
#include <random>
#include <limits>
#include <chrono>

using namespace std;

struct Point {
    double x, y;
};

// Helper: Euclidean distance
double dist(const Point& a, const Point& b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return sqrt(dx*dx + dy*dy);
}

// Euclidean distance with sqrt
# Remove unused helper

# remove unused improve_2opt function

double tour_distance(const vector<int>& tour, const vector<Point>& cities) {
    double total = 0.0;
    int N = tour.size();
    for (int i = 0; i < N; ++i) {
        total += dist(cities[tour[i]], cities[tour[(i+1)%N]]);
    }
    return total;
}


// EVOLVE-BLOCK-START
vector<int> solve_tsp(int N, const vector<Point>& cities) {
    if (N == 0) return {};
    
    // Compute centroid of all cities to use as a deterministic alternative start point
    double centroid_x = 0.0, centroid_y = 0.0;
    for (const auto& p : cities) {
        centroid_x += p.x;
        centroid_y += p.y;
    }
    centroid_x /= N;
    centroid_y /= N;
    // Find the city farthest from the centroid
    int farthest_city = 0;
    double max_dist_sq = 0.0;
    for (int i = 0; i < N; ++i) {
        double dx = cities[i].x - centroid_x;
        double dy = cities[i].y - centroid_y;
        double dist_sq = dx * dx + dy * dy;
        if (dist_sq > max_dist_sq) {
            max_dist_sq = dist_sq;
            farthest_city = i;
        }
    }

    const int restart_count = 3;
    vector<int> best_tour;
    double best_dist = numeric_limits<double>::infinity();

    for (int restart = 0; restart < restart_count; ++restart) {
        vector<int> tour;
        vector<bool> visited(N, false);

        int start_city;
        if (restart == 0) {
            start_city = farthest_city;
        } else {
            // pick random start
            static std::mt19937 rng(42);
            static std::uniform_int_distribution<int> dist_start(0, N - 1);
            start_city = dist_start(rng);
        }

        int curr = start_city;
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

        // 2-Opt Optimization (Untwisting the loop)
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

        double current_dist = 0.0;
        for (int i = 0; i < N; ++i) {
            current_dist += dist(cities[tour[i]], cities[tour[(i+1)%N]]);
        }

        if (current_dist < best_dist) {
            best_dist = current_dist;
            best_tour = tour;
        }
    }

    return best_tour;

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