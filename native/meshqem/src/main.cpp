// main.cpp — Command-line wrapper around the QEM kernel.
//
// Responsibilities:
// - Parse minimal flags (in/out, ratio/target-faces, max-collapses, time-limit, progress-interval).
// - Load input OBJ (triangles only), run qem_simplify, and save output OBJ.
// - Print a short summary to stdout so the Python adapter can parse it.

#include "io_obj.hpp"
#include "qem.hpp"
#include <cstdio>
#include <cstring>
#include <string>

static void usage(){
    fprintf(stderr, "meshqem (v%s)\n", MEQ_VERSION);
    fprintf(stderr, "Usage: meshqem --in in.obj --out out.obj [--ratio r|--target-faces n] [--max-collapses n] [--time-limit s] [--progress-interval n]\n");
}

int main(int argc, char** argv){
    const char* in_path=nullptr; const char* out_path=nullptr; 
    SimplifyOptions opt; opt.ratio=0.5; opt.target_faces=-1; opt.max_collapses=-1; opt.time_limit=-1.0; opt.progress_interval=20000;
    for(int i=1;i<argc;i++){
        if(!strcmp(argv[i],"--in") && i+1<argc) in_path=argv[++i];
        else if(!strcmp(argv[i],"--out") && i+1<argc) out_path=argv[++i];
        else if(!strcmp(argv[i],"--ratio") && i+1<argc) opt.ratio=std::stod(argv[++i]);
        else if(!strcmp(argv[i],"--target-faces") && i+1<argc) opt.target_faces=std::stoi(argv[++i]);
        else if(!strcmp(argv[i],"--max-collapses") && i+1<argc) opt.max_collapses=std::stoi(argv[++i]);
        else if(!strcmp(argv[i],"--time-limit") && i+1<argc) opt.time_limit=std::stod(argv[++i]);
        else if(!strcmp(argv[i],"--progress-interval") && i+1<argc) opt.progress_interval=std::stoi(argv[++i]);
        else { fprintf(stderr, "Unknown or incomplete option: %s\n", argv[i]); usage(); return 2; }
    }
    if(!in_path || !out_path){ usage(); return 2; }

    Mesh mesh; std::string err;
    if(!load_obj_tri(in_path, mesh, err)){ fprintf(stderr, "Load error: %s\n", err.c_str()); return 3; }

    SimplifyReport rep;
    if(!qem_simplify(mesh, opt, rep)){ fprintf(stderr, "Simplify failed\n"); return 4; }

    if(!save_obj_tri(out_path, mesh, err)){ fprintf(stderr, "Save error: %s\n", err.c_str()); return 5; }

    // The two-line summary is parsed by the Python adapter; avoid extra stdout noise here.
    fprintf(stdout, "faces: %zu -> %zu\nverts: %zu -> %zu\n", rep.faces_before, rep.faces_after, rep.verts_before, rep.verts_after);
    return 0;
}
