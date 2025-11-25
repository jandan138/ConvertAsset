// mesh.cpp — Implementation of small helpers on top of the Mesh POD container.
// Keeping implementation minimal to make algorithmic code in qem.cpp easy to follow.

#include "mesh.hpp"

// Clear geometry buffers; this is used by I/O to reset target before loading.
void Mesh::clear() {
    verts.clear();   // drop all vertex positions
    faces.clear();   // drop all triangle indices
    face_uvs.clear(); // drop any per-face UV triplets (if present)
}
