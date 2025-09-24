#pragma once
#include "mesh.hpp"
#include <vector>
#include <array>
#include <queue>

// Quadric — a 4x4 symmetric matrix representing the squared distance to a set
// of planes (from triangles' plane equations). We store in row-major order.
// The error at a homogeneous point v'=[x,y,z,1] is: E(v') = v'^T Q v'.
struct Quadric { double m[16]; };

// Edge candidate stored in a min-heap. We invert the comparator to get a min-heap
// using std::priority_queue (which is a max-heap by default).
struct EdgeCand {
    int u, v;       // vertex indices forming the edge (u<v canonicalized before push)
    double cost;    // collapse cost estimated from QEM at optimal/midpoint position
    bool operator<(const EdgeCand& o) const { return cost > o.cost; } // min-heap via greater
};

// Tuning knobs for the simplification run. See src/main.cpp for CLI wiring.
struct SimplifyOptions {
    double ratio = 0.5;           // target face ratio (0..1]; used when target_faces<0
    int    target_faces = -1;     // absolute target face count; overrides ratio if >0
    int    max_collapses = -1;    // safety cap on number of edge collapses; default derived from target
    double time_limit = -1.0;     // per-mesh time limit in seconds; <0 disables
    int    progress_interval = 20000; // emit a progress line every N collapses
};

// Summary counters emitted to stdout by main().
struct SimplifyReport {
    size_t faces_before = 0;
    size_t faces_after = 0;
    size_t verts_before = 0;
    size_t verts_after = 0;
};

// In-place simplification: mutates `mesh` to contain the decimated geometry.
// Returns true on success and fills `rep` with before/after counts.
bool qem_simplify(Mesh& mesh, const SimplifyOptions& opt, SimplifyReport& rep);
