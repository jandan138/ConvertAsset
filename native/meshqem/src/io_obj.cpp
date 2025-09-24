// io_obj.cpp — Tiny triangle-only OBJ reader/writer used as an interchange format
// between the Python USD bridge and the native QEM kernel. We deliberately keep
// this parser tiny (no dependencies) and robust enough for well-formed files that
// our own exporter writes.

#include "io_obj.hpp"
#include <fstream>
#include <sstream>

// Trim trailing whitespace (incl. CR/LF). OBJ is line-oriented so this is sufficient
// to normalize lines before tokenizing with stringstreams.
static inline void trim(std::string& s) {
    while (!s.empty() && (s.back()=='\n' || s.back()=='\r' || s.back()==' ' || s.back()=='\t')) s.pop_back();
}

bool load_obj_tri(const std::string& path, Mesh& mesh, std::string& err) {
    mesh.clear(); // ensure target is empty before filling
    std::ifstream ifs(path);
    if (!ifs) { err = "cannot open: " + path; return false; }
    std::string line;
    while (std::getline(ifs, line)) {
        trim(line);
        if (line.empty() || line[0]=='#') continue; // ignore comments/blank lines
        std::istringstream iss(line);
        std::string tok; iss >> tok; // first token is the record type
        if (tok == "v") {
            // Vertex position: v x y z
            Vec3 v; iss >> v.x >> v.y >> v.z; mesh.verts.push_back(v);
        } else if (tok == "f") {
            // Triangle face: f i j k (we ignore vt/vn and only read position indices)
            std::string s1,s2,s3; iss >> s1 >> s2 >> s3;
            auto parse_idx = [](const std::string& s)->int{
                // Accept tokens like "12", "12/34", "12/34/56" and only use the first field.
                size_t p = s.find('/');
                std::string a = (p==std::string::npos)? s : s.substr(0,p);
                int idx = std::stoi(a);
                return idx; // positive indices assumed (per our own writer)
            };
            int i = parse_idx(s1), j = parse_idx(s2), k = parse_idx(s3);
            // Convert 1-based OBJ indices to 0-based internal indices.
            mesh.faces.push_back({i-1, j-1, k-1});
        }
        // Other directives (vt, vn, usemtl, mtllib, o, g, s, etc.) are ignored.
    }
    // Basic sanity: require at least one vertex and one face.
    if (mesh.verts.empty() || mesh.faces.empty()) { err = "empty mesh from: " + path; return false; }
    return true;
}

bool save_obj_tri(const std::string& path, const Mesh& mesh, std::string& err) {
    std::ofstream ofs(path);
    if (!ofs) { err = "cannot write: " + path; return false; }
    ofs << "# meshqem output\n"; // simple banner for debugging
    // Emit vertex positions.
    for (auto& v : mesh.verts) {
        ofs << "v " << v.x << ' ' << v.y << ' ' << v.z << '\n';
    }
    // Emit triangle faces. OBJ is 1-based, so we add 1 to each index.
    for (auto& f : mesh.faces) {
        ofs << "f " << (f.a+1) << ' ' << (f.b+1) << ' ' << (f.c+1) << '\n';
    }
    return true;
}
