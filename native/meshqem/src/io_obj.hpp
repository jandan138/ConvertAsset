// io_obj.hpp — Minimal OBJ (triangles-only) loader/saver for meshqem.
//
// Scope and limitations:
// - Supports only vertex positions (v) and triangle faces (f i j k).
// - Ignores texture/normal indices (vt/vn) and materials; ideal for algorithm I/O.
// - Parses positive indices only (1-based per OBJ spec), converts to 0-based.
// - Lines starting with '#' are treated as comments and skipped.
//
#pragma once
#include "mesh.hpp"
#include <string>

// Load triangles from an OBJ file located at `path` into `mesh`.
// On failure, returns false and writes a human-readable message to `err`.
bool load_obj_tri(const std::string& path, Mesh& mesh, std::string& err);

// Save the triangle mesh to an OBJ file located at `path`.
// On failure, returns false and writes a human-readable message to `err`.
bool save_obj_tri(const std::string& path, const Mesh& mesh, std::string& err);
