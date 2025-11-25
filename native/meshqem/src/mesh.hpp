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
// v1 只在几何层面工作；为配合 Python 侧的 face-varying UV 携带，这里额外提供
// 一个可选的每面 UV 三元组数组（face_uvs）。
// - face_uvs.size() == faces.size() 时，表示每个三角面有一个 (u0,v0,u1,v1,u2,v2) triplet，
//   用于在简化时“跟着面一起删/压缩”，不在 C++ 端修改具体值；
// - 为空时，表示当前运行不关心 UV 属性，qem_simplify 将忽略它。
// 该字段只在嵌入式调用（例如 Python 绑定）中使用，命令行 OBJ I/O 仍然保持 v1 的几何-only 语义。
struct Mesh {
    // Vertex positions (units agnostic; typically scene units in USD/OBJ).
    std::vector<Vec3> verts;
    // Triangle faces. Each entry is a 3-tuple of indices into verts.
    std::vector<Tri>  faces; // triangles only

    // Optional per-face UV triplets: (u0,v0,u1,v1,u2,v2) for each triangle.
    // 保持与 faces 同长度/顺序，用于“删面时同步删对应的 UV triplet；压缩时同步压缩”。
    std::vector<std::array<double, 6>> face_uvs;

    // Clear all geometry. Does not shrink capacity (standard vector behavior).
    void clear();

    // Convenience counters.
    size_t num_faces() const { return faces.size(); }
    size_t num_verts() const { return verts.size(); }
};
