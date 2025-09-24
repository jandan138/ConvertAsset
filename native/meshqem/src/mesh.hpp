// mesh.hpp — Minimal, triangle-only mesh container used by the native QEM backend.
//
// Design goals:
// - Keep data structures tiny and explicit so the algorithm's intent is clear.
// - Avoid coupling to external libraries (Eigen, glm, etc.) for easy embedding.
// - Use double for positions to reduce accumulated numerical error in QEM.
//
// Conventions used across meshqem:
// - Triangle-only: all faces are 3 indices (Tri). Non-tri meshes must be pre-triangulated.
// - Indices are 0-based in memory (OBJ uses 1-based; we convert in I/O layer).
// - No attributes (normals/UVs) are tracked in v1; topology-only simplification.
//
#pragma once
#include <vector>
#include <array>
#include <string>
#include <unordered_set>

// 3D point/vector. We use a plain struct for cache-friendly access.
struct Vec3 { double x{}, y{}, z{}; };

// Triangle face made of 3 vertex indices (0-based).
// The algorithm assumes indices are valid and form a manifold-ish mesh, but we keep
// guards against degeneracy and drop zero-area faces during preprocessing.
struct Tri { int a{}, b{}, c{}; };

// Minimal mesh container: a list of points and a list of triangles.
// Methods provide convenient queries and a clear() helper.
struct Mesh {
    // Vertex positions (units agnostic; typically scene units in USD/OBJ).
    std::vector<Vec3> verts;
    // Triangle faces. Each entry is a 3-tuple of indices into verts.
    std::vector<Tri>  faces; // triangles only

    // Clear all geometry. Does not shrink capacity (standard vector behavior).
    void clear();

    // Convenience counters.
    size_t num_faces() const { return faces.size(); }
    size_t num_verts() const { return verts.size(); }
};
