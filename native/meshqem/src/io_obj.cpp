#include "io_obj.hpp"
#include <fstream>
#include <sstream>

static inline void trim(std::string& s) {
    while (!s.empty() && (s.back()=='\n' || s.back()=='\r' || s.back()==' ' || s.back()=='\t')) s.pop_back();
}

bool load_obj_tri(const std::string& path, Mesh& mesh, std::string& err) {
    mesh.clear();
    std::ifstream ifs(path);
    if (!ifs) { err = "cannot open: " + path; return false; }
    std::string line;
    while (std::getline(ifs, line)) {
        trim(line);
        if (line.empty() || line[0]=='#') continue;
        std::istringstream iss(line);
        std::string tok; iss >> tok;
        if (tok == "v") {
            Vec3 v; iss >> v.x >> v.y >> v.z; mesh.verts.push_back(v);
        } else if (tok == "f") {
            // support f i j k (ignore tex/normal indices)
            std::string s1,s2,s3; iss >> s1 >> s2 >> s3;
            auto parse_idx = [](const std::string& s)->int{
                size_t p = s.find('/');
                std::string a = (p==std::string::npos)? s : s.substr(0,p);
                int idx = std::stoi(a);
                return idx; // positive indices assumed
            };
            int i = parse_idx(s1), j = parse_idx(s2), k = parse_idx(s3);
            mesh.faces.push_back({i-1, j-1, k-1});
        }
    }
    if (mesh.verts.empty() || mesh.faces.empty()) { err = "empty mesh from: " + path; return false; }
    return true;
}

bool save_obj_tri(const std::string& path, const Mesh& mesh, std::string& err) {
    std::ofstream ofs(path);
    if (!ofs) { err = "cannot write: " + path; return false; }
    ofs << "# meshqem output\n";
    for (auto& v : mesh.verts) {
        ofs << "v " << v.x << ' ' << v.y << ' ' << v.z << '\n';
    }
    for (auto& f : mesh.faces) {
        ofs << "f " << (f.a+1) << ' ' << (f.b+1) << ' ' << (f.c+1) << '\n';
    }
    return true;
}
