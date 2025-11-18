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

# Optional: build pybind11-based Python module `meshqem_py` for in-process calls
option(BUILD_MESHQEM_PY "Build pybind11 Python module meshqem_py" OFF)

if (BUILD_MESHQEM_PY)
    find_package(pybind11 REQUIRED)

    pybind11_add_module(meshqem_py
        src/python_bindings.cpp
        src/mesh.cpp
        src/qem.cpp
    )

    target_include_directories(meshqem_py PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
    )

    target_compile_features(meshqem_py PRIVATE cxx_std_17)
    target_compile_options(meshqem_py PRIVATE -O3 -DNDEBUG)
endif()