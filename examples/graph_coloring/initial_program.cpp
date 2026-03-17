#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <set>

using namespace std;

/**
 * Implementation of the DSATUR (Degree of Saturation) algorithm.
 * DSATUR is a powerful heuristic for the Graph Coloring Problem that
 * prioritizes vertices with the highest number of distinct colors in
 * their neighborhood.
 */

// EVOLVE-BLOCK-START
vector<int> solve_coloring(int V, int E, const vector<pair<int, int>>& edges) {
if (V == 0) return {};

vector<vector<int>> adj(V);
vector<int> degree(V, 0);
for (const auto& edge : edges) {
adj[edge.first].push_back(edge.second);
adj[edge.second].push_back(edge.first);
degree[edge.first]++;
degree[edge.second]++;
}

vector<int> colors(V, -1);
vector<set<int>> neighbor_colors(V);
vector<bool> colored(V, false);

for (int i = 0; i < V; ++i) {
int best_v = -1;
int max_sat = -1;
int max_deg = -1;

 // Pick vertex with max saturation degree, tie-break with vertex degree
 for (int v = 0; v < V; ++v) {
     if (!colored[v]) {
         int saturation = (int)neighbor_colors[v].size();
         if (saturation > max_sat) {
             max_sat = saturation;
             max_deg = degree[v];
             best_v = v;
         } else if (saturation == max_sat) {
             if (degree[v] > max_deg) {
                 max_deg = degree[v];
                 best_v = v;
             }
         }
     }
 }

 // Find the lowest available color
 vector<bool> used(V + 1, false);
 for (int neighbor : adj[best_v]) {
     if (colors[neighbor] != -1) {
         used[colors[neighbor]] = true;
     }
 }

 int color = 0;
 while (used[color]) {
     color++;
 }

 colors[best_v] = color;
 colored[best_v] = true;

 // Update neighbors' saturation
 for (int neighbor : adj[best_v]) {
     if (!colored[neighbor]) {
         neighbor_colors[neighbor].insert(color);
     }
 }
}

return colors;
}

// EVOLVE-BLOCK-END

int main() {
ios_base::sync_with_stdio(false);
cin.tie(NULL);

int V = 0, E = 0;
vector<pair<int, int>> edges;
string line;

while (getline(cin, line)) {
    if (line.empty() || line[0] == 'c') continue;
    if (line[0] == 'p') {
        stringstream ss(line);
        string tmp, type;
        ss >> tmp >> type >> V >> E;
    } else if (line[0] == 'e') {
        stringstream ss(line);
        char e;
        int u, v;
        ss >> e >> u >> v;
        if (u <= V && v <= V) {
            edges.push_back({u - 1, v - 1});
        }
    }
}

vector<int> result = solve_coloring(V, E, edges);

cout << "RESULT_START\n";
for (int i = 0; i < V; ++i) {
    cout << result[i] << (i == V - 1 ? "" : " ");
}
cout << "\nRESULT_END\n";

return 0;
}