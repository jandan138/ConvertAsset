// qem.cpp — Quadric Error Metrics simplification core (triangle-only).
//
// High-level flow:
// 1) For each triangle, compute its plane equation and derive a 4x4 quadric K = p p^T.
// 2) Accumulate K onto each incident vertex's quadric Q[v].
// 3) Build vertex adjacency and initialize a min-heap of candidate edges with cost
//    evaluated at the optimal position (solving a small linear system) or midpoint fallback.
// 4) Repeatedly pop the cheapest edge and collapse v->u, updating vertex position, quadrics,
//    adjacency, and affected faces; push updated neighbor edges back into the heap.
// 5) Stop when target face count or time/collapse caps are reached; compact arrays.
//
// Notes:
// - This is a compact, dependency-free reference; it skips advanced guards such as flip detection,
//   boundary preservation, attribute remapping, etc., to keep it readable and robust.
// - Numerical robustness: we use double precision and drop degenerate faces early.

#include "qem.hpp"
#include <cmath>
#include <chrono>
#include <unordered_set>

static inline void q_zero(Quadric& Q){ for(int i=0;i<16;++i) Q.m[i]=0; }
static inline void q_add(Quadric& A,const Quadric& B){ for(int i=0;i<16;++i) A.m[i]+=B.m[i]; }
static inline Quadric q_sum(const Quadric& A,const Quadric& B){ Quadric C; for(int i=0;i<16;++i) C.m[i]=A.m[i]+B.m[i]; return C; }

// Build a quadric from plane parameters a,b,c,d (ax + by + cz + d = 0): K = p p^T.
// Storing full 4x4 keeps code simple; for performance you could store symmetric upper triangle.
static inline Quadric plane_quadric(double a,double b,double c,double d){
    Quadric K; double p[4]={a,b,c,d};
    int k=0; for(int r=0;r<4;++r) for(int c2=0;c2<4;++c2) K.m[k++]=p[r]*p[c2];
    return K;
}

static inline Vec3 sub(const Vec3&a,const Vec3&b){ return {a.x-b.x,a.y-b.y,a.z-b.z}; }
static inline Vec3 cross(const Vec3&a,const Vec3&b){ return {a.y*b.z-a.z*b.y, a.z*b.x-a.x*b.z, a.x*b.y-a.y*b.x}; }
static inline double dot3(const Vec3&a,const Vec3&b){ return a.x*b.x+a.y*b.y+a.z*b.z; }
static inline double len3(const Vec3&a){ return std::sqrt(dot3(a,a)); }

// Solve a 3x3 linear system A x = b with partial pivoting; returns false if near-singular.
// Used to find the point minimizing v'^T Q v' where Q is a merged quadric of an edge's endpoints.
static bool solve3(const double A[9], const double b[3], double x[3]){
    double M[3][4]={{A[0],A[1],A[2],b[0]},{A[3],A[4],A[5],b[1]},{A[6],A[7],A[8],b[2]}};
    for(int i=0;i<3;++i){
        // Pivot on the largest absolute value in the current column to improve stability.
        int piv=i; double pv=std::abs(M[i][i]);
        for(int r=i+1;r<3;++r){ double av=std::abs(M[r][i]); if(av>pv){piv=r; pv=av;} }
        if(pv<1e-12) return false; // treat as singular; caller will fallback to midpoint
        if(piv!=i) for(int c=0;c<4;++c) std::swap(M[i][c],M[piv][c]);
        // Normalize the pivot row.
        double div=M[i][i]; for(int c=0;c<4;++c) M[i][c]/=div;
        // Eliminate rows below.
        for(int r=i+1;r<3;++r){ double f=M[r][i]; for(int c=i;c<4;++c) M[r][c]-=f*M[i][c]; }
    }
    // Back substitution.
    for(int i=2;i>=0;--i){ double s=M[i][3]; for(int c=i+1;c<3;++c) s-=M[i][c]*x[c]; x[i]=s; }
    return true;
}

// Evaluate the quadratic form v^T Q v at homogeneous coordinate v=[x,y,z,1].
static inline double quadric_eval(const Quadric& Q, const double v[4]){
    double Qv[4]={0,0,0,0}; int k=0;
    for(int r=0;r<4;++r){
        for(int c=0;c<4;++c){ Qv[r]+=Q.m[k++]*v[c]; }
    }
    return v[0]*Qv[0]+v[1]*Qv[1]+v[2]*Qv[2]+v[3]*Qv[3];
}

static inline double clamp(double x,double lo,double hi){ return x<lo?lo:(x>hi?hi:x); }

bool qem_simplify(Mesh& mesh, const SimplifyOptions& opt, SimplifyReport& rep){
    rep.faces_before = mesh.faces.size();
    rep.verts_before = mesh.verts.size();
    if(mesh.faces.empty()) { rep.faces_after=0; rep.verts_after=mesh.verts.size(); return true; }

    // target faces
    int faces0 = (int)mesh.faces.size();
    int target = opt.target_faces>0? opt.target_faces : (int)std::max(0.0, std::floor(faces0 * clamp(opt.ratio,0.0,1.0)));
    int max_collapses = opt.max_collapses>0? opt.max_collapses : (faces0 - target);
    if(max_collapses<0) max_collapses=0;

    // build per-vertex quadrics
    std::vector<Quadric> vq(mesh.verts.size());
    for(auto& Q: vq) q_zero(Q);
    std::vector<char> face_alive(mesh.faces.size(), 1);
    for(size_t fi=0; fi<mesh.faces.size(); ++fi){
        auto& f = mesh.faces[fi];
        auto& p = mesh.verts[f.a];
        auto& q = mesh.verts[f.b];
        auto& r = mesh.verts[f.c];
        // Compute geometric normal via cross product; drop zero-area faces for stability.
        Vec3 n = cross({q.x-p.x,q.y-p.y,q.z-p.z}, {r.x-p.x,r.y-p.y,r.z-p.z});
        double L = len3(n);
        if(L<1e-12){ face_alive[fi]=0; continue; }
        n.x/=L; n.y/=L; n.z/=L; double d = - (n.x*p.x + n.y*p.y + n.z*p.z);
        Quadric K = plane_quadric(n.x,n.y,n.z,d);
        q_add(vq[f.a], K); q_add(vq[f.b], K); q_add(vq[f.c], K);
    }

    // adjacency
    std::vector<std::unordered_set<int>> adj(mesh.verts.size());
    for(auto& f: mesh.faces){
        adj[f.a].insert(f.b); adj[f.a].insert(f.c);
        adj[f.b].insert(f.a); adj[f.b].insert(f.c);
        adj[f.c].insert(f.a); adj[f.c].insert(f.b);
    }

    // heap init
    std::priority_queue<EdgeCand> heap;
    auto push_edge = [&](int u,int v){
        // Canonicalize ordering so each undirected edge is pushed once (u<v).
        if(u==v) return; if(u>v) std::swap(u,v); if(!adj[u].count(v)) return; 
        // Combine vertex quadrics and estimate the best collapse position.
        Quadric Quv = q_sum(vq[u], vq[v]);
        // Extract 3x3 (upper-left) and 3x1 (-Q[0:3,3]) to solve for [x,y,z].
        double A[9]={Quv.m[0],Quv.m[1],Quv.m[2], Quv.m[4],Quv.m[5],Quv.m[6], Quv.m[8],Quv.m[9],Quv.m[10]};
        double B[3]={-Quv.m[3], -Quv.m[7], -Quv.m[11]};
        double x[3]; bool ok = solve3(A,B,x);
        if(!ok){ // fallback midpoint for robustness when A is singular (common near boundaries)
            x[0]=(mesh.verts[u].x+mesh.verts[v].x)*0.5;
            x[1]=(mesh.verts[u].y+mesh.verts[v].y)*0.5;
            x[2]=(mesh.verts[u].z+mesh.verts[v].z)*0.5;
        }
        double v4[4]={x[0],x[1],x[2],1.0};
        double cost = quadric_eval(Quv, v4);
        heap.push({u,v,cost});
    };

    for(size_t u=0; u<adj.size(); ++u){ for(int v: adj[u]) if((int)u<v) push_edge((int)u,v); }

    auto t0 = std::chrono::steady_clock::now();
    int collapsed=0;
    int faces_cur = faces0;
    int next_progress = opt.progress_interval>0? opt.progress_interval: 20000;

    // alive flags
    std::vector<char> v_alive(mesh.verts.size(), 1);

    while(faces_cur>target && !heap.empty() && collapsed<max_collapses){
        // time limit
        if(opt.time_limit>0){
            auto dt = std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
            if(dt >= opt.time_limit) break;
        }

        auto e = heap.top(); heap.pop();
        int u=e.u, v=e.v; if(!v_alive[u] || !v_alive[v]) continue; if(!adj[u].count(v)) continue;

        // new position: midpoint (simple, robust). For quality, you could also set to x[] above
        // and re-evaluate local costs; we keep midpoint to avoid repeated re-solves.
        double nx=(mesh.verts[u].x+mesh.verts[v].x)*0.5;
        double ny=(mesh.verts[u].y+mesh.verts[v].y)*0.5;
        double nz=(mesh.verts[u].z+mesh.verts[v].z)*0.5;
        mesh.verts[u].x=nx; mesh.verts[u].y=ny; mesh.verts[u].z=nz;

        // merge quadrics
        q_add(vq[u], vq[v]);

        // rewire adjacency: move neighbors of v to u
        for(int w: adj[v]){ if(w==u) continue; adj[w].erase(v); adj[w].insert(u); adj[u].insert(w); }
        adj[v].clear(); v_alive[v]=0;

        // update faces: replace v with u, drop degenerate
        for(size_t fi=0; fi<mesh.faces.size(); ++fi){ if(!face_alive[fi]) continue; auto& f=mesh.faces[fi];
            int a=f.a, b=f.b, c=f.c; if(a==v) a=u; if(b==v) b=u; if(c==v) c=u; 
            if(a==b || b==c || a==c){ face_alive[fi]=0; faces_cur--; continue; }
            f.a=a; f.b=b; f.c=c; }

        // refresh candidate edges around u
        for(int w: adj[u]){ int a=u,b=w; if(a>b) std::swap(a,b); push_edge(a,b); }

        if(++collapsed >= next_progress){
            // emit a single-line progress to stderr (Python side collects if needed)
            fprintf(stderr, "[cpp] collapsed=%d faces_now=%d target=%d\n", collapsed, faces_cur, target);
            next_progress += opt.progress_interval>0? opt.progress_interval: 20000;
        }
    }

    // compact vertices and faces — remove dead vertices and reindex faces.
    std::vector<int> remap(mesh.verts.size(), -1); remap.reserve(mesh.verts.size());
    std::vector<Vec3> v2; v2.reserve(mesh.verts.size());
    for(size_t i=0;i<mesh.verts.size();++i){ if(v_alive[i]){ remap[i]=(int)v2.size(); v2.push_back(mesh.verts[i]); } }
    std::vector<Tri> f2; f2.reserve(mesh.faces.size());
    for(size_t fi=0; fi<mesh.faces.size(); ++fi){ if(!face_alive[fi]) continue; auto f=mesh.faces[fi];
        int a=remap[f.a], b=remap[f.b], c=remap[f.c]; if(a<0||b<0||c<0) continue; f2.push_back({a,b,c}); }
    mesh.verts.swap(v2); mesh.faces.swap(f2);

    rep.faces_after = mesh.faces.size();
    rep.verts_after = mesh.verts.size();
    return true;
}
