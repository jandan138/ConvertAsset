#pragma once
#include "mesh.hpp"
#include <vector>
#include <array>
#include <queue>

struct Quadric { double m[16]; };

struct EdgeCand {
    int u, v;
    double cost;
    bool operator<(const EdgeCand& o) const { return cost > o.cost; } // min-heap via greater
};

struct SimplifyOptions {
    double ratio = 0.5;
    int    target_faces = -1;
    int    max_collapses = -1;
    double time_limit = -1.0; // seconds, <0: no limit
    int    progress_interval = 20000; // collapses
};

struct SimplifyReport {
    size_t faces_before = 0;
    size_t faces_after = 0;
    size_t verts_before = 0;
    size_t verts_after = 0;
};

bool qem_simplify(Mesh& mesh, const SimplifyOptions& opt, SimplifyReport& rep);
