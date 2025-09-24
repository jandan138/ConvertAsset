#pragma once
#include <vector>
#include <array>
#include <string>
#include <unordered_set>

struct Vec3 { double x{}, y{}, z{}; };
struct Tri { int a{}, b{}, c{}; };

struct Mesh {
    std::vector<Vec3> verts;
    std::vector<Tri>  faces; // triangles only
    void clear();
    size_t num_faces() const { return faces.size(); }
    size_t num_verts() const { return verts.size(); }
};
