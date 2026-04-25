#include <iostream>
#include <vector>
#include <random>
#include <limits>

#include <algorithm>
#include <cmath>

using namespace std;

struct Point {
    double x, y;
};

/* Helper: Euclidean distance (returns actual distance) */
double dist(const Point& a, const Point& b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return sqrt(dx*dx + dy*dy);
}

// Helper: Calculate the total cost of the closed loop


// EVOLVE-BLOCK-START
vector<int> solve_tsp(int N, const vector<Point>& cities) {
    if (N == 0) return {};

    // Use multiple deterministic restarts to escape local minima
    const int restart_count = 3;
    vector<int> best_tour;
    double best_dist = numeric_limits<double>::infinity();

    // Random number generator for deterministic restarts
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist_start(0, N - 1);

    // Compute centroid of all cities (for deterministic alternative start point)
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

    for (int restart = 0; restart < restart_count; ++restart) {
        vector<int> tour;
        vector<bool> visited(N, false);

        // Choose start city: farthest from centroid on first restart, random otherwise
        int start_city = (restart == 0) ? farthest_city : dist_start(rng);

        // Build initial tour
        if (N <= 2000) {
            /* Nearest‑Insertion (good quality for smaller instances) */
            tour.push_back(start_city);
            visited[start_city] = true;

            // Find nearest neighbor of the start city
            int best_next = -1;
            double min_d = 1e18;
            for (int j = 0; j < N; ++j) {
                if (j == start_city) continue;
                double d = dist(cities[start_city], cities[j]);
                if (d < min_d) {
                    min_d = d;
                    best_next = j;
                }
            }
            tour.push_back(best_next);
            visited[best_next] = true;

            // Insert remaining cities
            while (tour.size() < static_cast<size_t>(N)) {
                int city_to_insert = -1;
                double best_increase = 1e18;
                size_t insert_pos = 0;
                for (int c = 0; c < N; ++c) {
                    if (visited[c]) continue;
                    for (size_t pos = 0; pos < tour.size(); ++pos) {
                        size_t next = (pos + 1) % tour.size();
                        double added = dist(cities[c], cities[tour[pos]]) +
                                       dist(cities[c], cities[tour[next]]) -
                                       dist(cities[tour[pos]], cities[tour[next]]);
                        if (added < best_increase) {
                            best_increase = added;
                            city_to_insert = c;
                            insert_pos = pos + 1; // insert after pos
                        }
                    }
                }
                tour.insert(tour.begin() + insert_pos, city_to_insert);
                visited[city_to_insert] = true;
            }
        } else {
            /* Nearest‑Neighbor (fast for very large instances) */
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
        }

        // 2-Opt Optimization (Untwisting the loop)
        bool improved = true;
        while (improved) {
            improved = false;
            for (int i = 1; i < N - 1; ++i) {
                for (int j = i + 1; j < N; ++j) {
                    double old_dist = dist(cities[tour[i - 1]], cities[tour[i]]) +
                                      dist(cities[tour[j]], cities[tour[(j + 1) % N]]);
                    double new_dist = dist(cities[tour[i - 1]], cities[tour[j]]) +
                                      dist(cities[tour[i]], cities[tour[(j + 1) % N]]);
                    if (new_dist < old_dist) {
                        reverse(tour.begin() + i, tour.begin() + j + 1);
                        improved = true;
                    }
                }
            }
        }

        // Evaluate current tour
        double current_dist = 0.0;
        for (int i = 0; i < N; ++i) {
            current_dist += dist(cities[tour[i]], cities[tour[(i + 1) % N]]);
        }

        if (current_dist < best_dist) {
            best_dist = current_dist;
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