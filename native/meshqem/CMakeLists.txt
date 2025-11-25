############################################################
# 工程基础配置块：告诉 CMake 需要的最低版本和项目类型
# 这一块在任何 CMake 工程里基本都是必须的
############################################################

cmake_minimum_required(VERSION 3.12)  # 声明本工程要求的 CMake 最低版本为 3.12，版本太低则会拒绝生成
project(meshqem CXX)                  # 定义一个名为 meshqem 的项目，并指定使用 C++ 作为主要语言

############################################################
# C++ 语言标准配置块：控制使用 C++17 以及是否允许编译器扩展
# 这一块不是“绝对必须”，但在现代 C++ 项目里几乎必配
############################################################

set(CMAKE_CXX_STANDARD 17)        # 把全局变量 CMAKE_CXX_STANDARD 设为 17，表示希望用 C++17 标准编译
set(CMAKE_CXX_STANDARD_REQUIRED ON)  # 强制要求编译器必须支持 C++17，否则配置会报错，而不是悄悄降级到更低标准
set(CMAKE_CXX_EXTENSIONS OFF)     # 关闭编译器的“方言扩展”（如 gnu++17），尽量使用纯标准 C++17，提升可移植性

############################################################
# 可执行程序目标块：定义一个叫 meshqem 的可执行文件以及它的源文件列表
# 在这里至少要有一个 add_executable 或 add_library 才能生成有用的目标
############################################################

add_executable(meshqem             # 定义一个名为 meshqem 的可执行目标（最终会生成名为 meshqem 的二进制）
    src/main.cpp                   # 主程序入口文件，包含 main 函数
    src/mesh.hpp                   # Mesh 相关的头文件，这里也列入以便某些 IDE 能看到它属于该目标
    src/mesh.cpp                   # Mesh 相关的实现文件，参与编译
    src/qem.hpp                    # QEM 算法相关的头文件，同样列出以便 IDE 索引
    src/qem.cpp                    # QEM 算法实现文件，参与编译
    src/io_obj.hpp                 # 读取/写入 OBJ 的头文件
    src/io_obj.cpp                 # 读取/写入 OBJ 的实现文件，参与编译
)                                   # add_executable 调用结束

############################################################
# 编译选项与宏定义块：为 meshqem 这个目标添加宏定义和优化级别
# 这些都不是 CMake 必须的，但几乎所有实际工程都会做类似配置
############################################################

target_compile_definitions(meshqem PRIVATE -DMEQ_VERSION="0.1.0")  # 给 meshqem 目标添加一个预编译宏 MEQ_VERSION，用于在代码里获取版本号
target_compile_options(meshqem PRIVATE -O3 -DNDEBUG)                # 为 meshqem 启用 O3 优化，并定义 NDEBUG（通常表示关闭断言等调试开关）

############################################################
# Python 模块构建开关块：通过选项控制是否构建 pybind11 的 Python 模块 meshqem_py
# 这一块在 CMake 里不是必须，只是给用户一个可选开关（默认关闭）
############################################################

# Optional: build pybind11-based Python module `meshqem_py` for in-process calls
option(BUILD_MESHQEM_PY "Build pybind11 Python module meshqem_py" OFF)  # 定义一个布尔开关 BUILD_MESHQEM_PY，默认 OFF，用户可在命令行 -DBUILD_MESHQEM_PY=ON 打开

############################################################
# Python 模块目标块：只有在 BUILD_MESHQEM_PY=ON 时才会执行
# 负责找到 pybind11，并构建名为 meshqem_py 的 Python 扩展模块
############################################################

if (BUILD_MESHQEM_PY)                              # 如果用户显式开启了 BUILD_MESHQEM_PY，则进入这个条件分支
    find_package(pybind11 REQUIRED)                # 查找并加载 pybind11 包，REQUIRED 表示找不到就直接报错终止配置

    pybind11_add_module(meshqem_py                 # 使用 pybind11 提供的宏创建一个 Python 扩展模块，模块名为 meshqem_py
        src/python_bindings.cpp                    # Python 绑定的 C++ 实现文件，负责把 C++ 函数导出给 Python
        src/mesh.cpp                               # 复用 Mesh 的实现文件，供 Python 模块调用（与上面的可执行目标共享源码）
        src/qem.cpp                                # 复用 QEM 算法实现文件，同样供 Python 模块使用
    )                                              # pybind11_add_module 调用结束

    target_include_directories(meshqem_py PRIVATE  # 为 meshqem_py 目标添加私有头文件搜索路径
        ${CMAKE_CURRENT_SOURCE_DIR}/src            # 指定当前目录下的 src 目录，这样 python_bindings.cpp 中的 #include "mesh.hpp" 等可以被找到
    )                                              # include 目录设置结束

    target_compile_features(meshqem_py PRIVATE cxx_std_17)  # 要求构建 meshqem_py 时使用 C++17 特性（与上面的全局设置相呼应）
    target_compile_options(meshqem_py PRIVATE -O3 -DNDEBUG)  # 为 Python 模块也开启 O3 优化并关闭调试（NDEBUG）
endif()                                            # 结束条件块：如果没有打开 BUILD_MESHQEM_PY，则这一整块会被跳过