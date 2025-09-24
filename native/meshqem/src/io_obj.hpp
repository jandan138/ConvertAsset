#pragma once
#include "mesh.hpp"
#include <string>

bool load_obj_tri(const std::string& path, Mesh& mesh, std::string& err);
bool save_obj_tri(const std::string& path, const Mesh& mesh, std::string& err);
