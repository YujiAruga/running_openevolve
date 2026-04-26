#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <random>
#include <limits>

using namespace std;
static std::mt19937 rng(std::random_device{}());

struct Point {
    double x, y;
};

// Helper: Euclidean distance
double dist(const Point& a, const Point& b) {
    return sqrt(pow(a.x - b.x, 2) + pow(a.y - b.y, 2));
}

double dist2(const Point& a, const Point& b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return dx*dx + dy*dy;
}

/* ------------------------------------------------------------------
   Helper: Calculate the total cost of the closed loop
   ------------------------------------------------------------------*/
double get_tour_distance(int N, const vector<int>& tour, const vector<Point>& cities) {
    double total = 0;
    for (int i = 0; i < N; ++i)
        total += dist(cities[tour[i]], cities[tour[(i + 1) % N]]);
    return total;
}

/* ------------------------------------------------------------------
   Reusable 2‑opt optimizer
   ------------------------------------------------------------------*/
void apply_2opt(vector<int>& tour, const vector<Point>& cities) {
    const int N = tour.size();
    bool improved = true;
    while (improved) {
        improved = false;
        for (int i = 1; i < N - 1; ++i) {
            for (int j = i + 1; j < N; ++j) {
                double old_dist = dist(cities[tour[i-1]], cities[tour[i]]) +
                                  dist(cities[tour[j]], cities[tour[(j+1)%N]]);
                double new_dist = dist(cities[tour[i-1]], cities[tour[j]]) +
                                  dist(cities[tour[i]], cities[tour[(j+1)%N]]);
                if (new_dist + 1e-12 < old_dist) {  // tiny epsilon for robustness
                    reverse(tour.begin() + i, tour.begin() + j + 1);
                    improved = true;
                }
            }
        }
    }
}

/* ------------------------------------------------------------------
   Generate a random tour by shuffling city indices
   ------------------------------------------------------------------*/
vector<int> generate_random_tour(int N) {
    vector<int> tour(N);
    for (int i = 0; i < N; ++i) tour[i] = i;
    std::shuffle(tour.begin(), tour.end(), rng);
    return tour;
}

void random_swap(vector<int>& tour) {
    int n = tour.size();
    if (n < 2) return;
    std::uniform_int_distribution<int> dist(0, n - 1);
    int i = dist(rng);
    int j = dist(rng);
    while (j == i) j = dist(rng);
    std::swap(tour[i], tour[j]);
}

/* ------------------------------------------------------------------
   Main TSP solver with multiple random restarts
   ------------------------------------------------------------------*/
vector<int> solve_tsp(int N, const vector<Point>& cities) {
    if (N == 0) return {};

    // Random number generator for restarts
    static std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<int> dist_start(0, N-1);

    // Keep the best tour found
    vector<int> best_tour;
    double best_dist = std::numeric_limits<double>::infinity();

    // Decide number of restarts: more for small instances, one for very large
    const int restarts = (N <= 2000) ? 4 : 1;

    for (int restart = 0; restart < restarts; ++restart) {
        // Build initial greedy tour starting from a chosen city
        vector<int> tour;
        vector<bool> visited(N, false);
        int start = (restart == 0) ? 0 : dist_start(rng);
        int curr = start;
        tour.push_back(curr);
        visited[curr] = true;

        for (int i = 1; i < N; ++i) {
            int best_next = -1;
            double min_d = std::numeric_limits<double>::infinity();
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

        if (restart > 0 && N > 200) { tour = generate_random_tour(N); }

        // Optimize tour with 2‑opt
        apply_2opt(tour, cities);

        // Random swaps to escape local optima
        for (int p = 0; p < 3; ++p) {
            random_swap(tour);
            apply_2opt(tour, cities);
        }

        double cur_dist = get_tour_distance(N, tour, cities);
        if (cur_dist < best_dist) {
            best_dist = cur_dist;
            best_tour = tour;
        }
    }
    return best_tour;
}

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