#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

using namespace std;

static inline uint16_t apply_rel(int rel, uint16_t a, uint16_t b, uint16_t mask) {
    uint16_t na = uint16_t((~a) & mask);
    uint16_t nb = uint16_t((~b) & mask);
    uint16_t out = 0;
    if (rel & 1) out |= uint16_t(na & nb);
    if (rel & 2) out |= uint16_t(na & b);
    if (rel & 4) out |= uint16_t(a & nb);
    if (rel & 8) out |= uint16_t(a & b);
    return out;
}

static vector<uint16_t> projections(int n) {
    vector<uint16_t> out;
    int rows = 1 << n;
    for (int j = 0; j < n; ++j) {
        uint16_t v = 0;
        for (int r = 0; r < rows; ++r) {
            if ((r >> j) & 1) v |= uint16_t(1u << r);
        }
        out.push_back(v);
    }
    return out;
}

int main(int argc, char** argv) {
    if (argc != 5) {
        cerr << "usage: nucleus_irreducibility_v1_fast REL N REGIME OUT\n";
        return 2;
    }

    const int rel = stoi(argv[1]);
    const int n = stoi(argv[2]);
    const string regime = argv[3];
    const string outpath = argv[4];

    if (rel < 0 || rel >= 16 || n < 1 || n > 4) return 2;
    if (!(regime == "none" || regime == "zero" || regime == "one" || regime == "both")) return 2;

    const int rows = 1 << n;
    const uint32_t total = 1u << rows;
    const uint16_t mask = uint16_t(total - 1);
    const int INF = 1000000000;

    vector<int> cost(total, INF);
    vector<int> depth(total, INF);
    vector<string> expr(total);
    vector<vector<uint16_t>> layers(256);
    vector<vector<uint16_t>> depth_layers(64);

    const auto ps = projections(n);
    vector<pair<uint16_t, string>> seeds;
    for (int j = 0; j < n; ++j) seeds.push_back({ps[j], "x" + to_string(j)});
    if (regime == "zero" || regime == "both") seeds.push_back({0, "0"});
    if (regime == "one" || regime == "both") seeds.push_back({mask, "1"});

    sort(seeds.begin(), seeds.end(), [](const auto& a, const auto& b) {
        return a.second < b.second;
    });

    for (const auto& p : seeds) {
        if (cost[p.first] == INF) {
            cost[p.first] = 0;
            depth[p.first] = 0;
            expr[p.first] = p.second;
            layers[0].push_back(p.first);
            depth_layers[0].push_back(p.first);
        } else if (p.second < expr[p.first]) {
            expr[p.first] = p.second;
        }
    }

    sort(layers[0].begin(), layers[0].end(), [&](auto a, auto b) {
        if (expr[a] != expr[b]) return expr[a] < expr[b];
        return a < b;
    });
    depth_layers[0] = layers[0];

    size_t reached = layers[0].size();
    vector<uint8_t> pending(total, 0);
    vector<pair<uint16_t, uint16_t>> parent(total, {0, 0});
    int max_cost_seen = 0;

    // Exact minimum node-count cost. For a fixed cost c, pairs are visited in
    // lexical expression order, so the first witness for a semantic function
    // is also its canonical lexicographically least minimum-cost expression.
    for (int c = 1; c < 256 && reached < total; ++c) {
        vector<uint16_t> known;
        known.reserve(reached);
        for (int k = 0; k < c; ++k) {
            known.insert(known.end(), layers[k].begin(), layers[k].end());
        }
        sort(known.begin(), known.end(), [&](auto a, auto b) {
            if (expr[a] != expr[b]) return expr[a] < expr[b];
            return a < b;
        });

        vector<uint16_t> current;
        fill(pending.begin(), pending.end(), 0);

        for (uint16_t a : known) {
            const int j = c - 1 - cost[a];
            if (j < 0 || j >= c || layers[j].empty()) continue;
            for (uint16_t b : layers[j]) {
                const uint16_t s = apply_rel(rel, a, b, mask);
                if (cost[s] == INF && !pending[s]) {
                    pending[s] = 1;
                    parent[s] = {a, b};
                    current.push_back(s);
                }
            }
        }

        if (!current.empty()) {
            for (uint16_t s : current) {
                const auto [a, b] = parent[s];
                cost[s] = c;
                expr[s] = "R(" + expr[a] + "," + expr[b] + ")";
            }
            sort(current.begin(), current.end(), [&](auto a, auto b) {
                if (expr[a] != expr[b]) return expr[a] < expr[b];
                return a < b;
            });
            layers[c] = move(current);
            reached += layers[c].size();
            max_cost_seen = c;
        }

        if (layers[c].empty() && c >= 2 * max_cost_seen + 1) break;
    }

    // The original closure-round statistic is minimum term depth. Process each
    // pair when its maximum child depth first becomes available.
    size_t depth_reached = depth_layers[0].size();
    int rounds = 0;
    vector<uint8_t> depth_pending(total, 0);

    for (int d = 1; d < 64 && depth_reached < total; ++d) {
        vector<uint16_t> known;
        for (int k = 0; k < d; ++k) {
            known.insert(known.end(), depth_layers[k].begin(), depth_layers[k].end());
        }

        vector<uint16_t> current;
        fill(depth_pending.begin(), depth_pending.end(), 0);
        const auto& frontier = depth_layers[d - 1];

        for (uint16_t a : frontier) {
            for (uint16_t b : known) {
                const uint16_t s1 = apply_rel(rel, a, b, mask);
                if (depth[s1] == INF && !depth_pending[s1]) {
                    depth_pending[s1] = 1;
                    current.push_back(s1);
                }
                const uint16_t s2 = apply_rel(rel, b, a, mask);
                if (depth[s2] == INF && !depth_pending[s2]) {
                    depth_pending[s2] = 1;
                    current.push_back(s2);
                }
            }
        }

        if (current.empty()) break;
        for (uint16_t s : current) depth[s] = d;
        depth_layers[d] = move(current);
        depth_reached += depth_layers[d].size();
        rounds = d;
    }

    if (depth_reached != reached) {
        cerr << "cost/depth closure mismatch: " << reached << " vs " << depth_reached << "\n";
        return 3;
    }

    ofstream out(outpath);
    out << "#META\t" << reached << "\t" << total << "\t"
        << (reached == total) << "\t" << rounds << "\t"
        << (cost[0] != INF) << "\t" << (cost[mask] != INF) << "\n";

    for (uint32_t s = 0; s < total; ++s) {
        if (cost[s] != INF) {
            out << s << "\t" << cost[s] << "\t" << expr[s] << "\n";
        }
    }
    return 0;
}
