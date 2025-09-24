cmake_minimum_required(VERSION 3.12)
project(meshqem CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(meshqem
    src/main.cpp
    src/mesh.hpp
    src/mesh.cpp
    src/qem.hpp
    src/qem.cpp
    src/io_obj.hpp
    src/io_obj.cpp
)

target_compile_definitions(meshqem PRIVATE -DMEQ_VERSION="0.1.0")
target_compile_options(meshqem PRIVATE -O3 -DNDEBUG)