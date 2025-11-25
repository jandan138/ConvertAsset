//======================================================================
// 文件总体说明：
//
// 这个文件通过 pybind11 把 C++ 的 meshqem QEM 简化函数暴露给 Python 使用，
// 并且支持可选的每面 UV（face-varying UV）携带。
//
// 从 Python 的视角看：这里只暴露了一个名为 simplify_with_uv 的函数，
//   - 传入：
//       verts:  List[(x,y,z)]              顶点坐标列表
//       faces:  List[(i,j,k)]              三角形索引列表（0-based）
//       face_uvs: Optional[List[(u0,v0,u1,v1,u2,v2)]]  每面 3 个顶点的 UV
//       ratio / target_faces / max_collapses / time_limit / progress_interval
//   - 返回：
//       (new_verts, new_faces, new_face_uvs_or_None)
//
// 对于 C++/pybind11 初学者：下面会对每一行做中文注释，帮你理解整体流程。
//======================================================================

#include "mesh.hpp"          // 引入本项目定义的 Mesh / Vec3 / Tri 等结构和与几何相关的声明
#include "qem.hpp"           // 引入 QEM 简化算法相关的声明（SimplifyOptions, SimplifyReport, qem_simplify 等）

#include <pybind11/pybind11.h>  // 引入 pybind11 的主头文件，提供和 Python 交互的 API
#include <pybind11/stl.h>       // 引入 pybind11 对 STL 容器（std::vector/std::array 等）的自动转换支持

namespace py = pybind11;        // 给 pybind11 起一个简短别名 py，方便后面书写

//======================================================================
// 函数：simplify_with_uv
// 作用：
//   - 这是暴露给 Python 的核心函数的 C++ 实现。
//   - pybind11 会把 Python 传进来的列表/对象转换成下面这些 C++ 类型，
//     再由我们手动填充 Mesh 结构，调用 qem_simplify，最后把结果打包为 Python 可用的类型返回。
//
// 形参说明（已经是 pybind11 转换后的 C++ 形式）：
//   verts          : std::vector<std::array<double,3>>     顶点坐标列表
//   faces          : std::vector<std::array<int,3>>        三角形面索引列表
//   face_uvs_obj   : py::object                            可能是 None，也可能是 Python 里的 UV 列表
//   ratio          : double                                目标面数比例
//   target_faces   : int                                   目标面数（绝对值）
//   max_collapses  : int                                   最多允许的折叠次数
//   time_limit     : double                                单个 mesh 的时间上限
//   progress_interval : int                                每多少次折叠输出一次进度
// 返回值：
//   py::tuple（三元组）：(out_verts, out_faces, out_face_uvs_or_None)
//======================================================================

static py::tuple simplify_with_uv(
    const std::vector<std::array<double, 3>>& verts,   // 从 Python 传入的顶点坐标列表，已经被 pybind11 转成 C++ 容器
    const std::vector<std::array<int, 3>>& faces,      // 从 Python 传入的三角形面索引列表，同样是 C++ 容器
    py::object face_uvs_obj,                           // 从 Python 传来的 UV 列表或 None，这里用 py::object 先接住
    double ratio,                                      // 目标面数比例
    int target_faces,                                  // 目标面数（绝对值）
    int max_collapses,                                 // 最多折叠次数
    double time_limit,                                 // 时间上限（秒）
    int progress_interval)                             // 输出进度的间隔（多少次折叠打印一次）
{
    Mesh mesh;                                         // 创建一个 Mesh 实例，用于传给 C++ QEM 简化核心
    mesh.verts.reserve(verts.size());                  // 预先为 mesh.verts 分配和输入顶点数量相同的容量，避免 push_back 反复扩容
    for (const auto& v : verts) {                      // 遍历输入的每一个顶点（std::array<double,3>）
        mesh.verts.push_back(Vec3{v[0], v[1], v[2]});  // 把数组里的 (x,y,z) 拷贝到 Mesh 自己的 Vec3 结构中
    }
    mesh.faces.reserve(faces.size());                  // 为 mesh.faces 预留和输入三角面数量相同的容量
    for (const auto& f : faces) {                      // 遍历输入的每一个三角面（std::array<int,3>）
        mesh.faces.push_back(Tri{f[0], f[1], f[2]});   // 把 (i,j,k) 拷贝到 Mesh 自己的 Tri 结构中
    }

    //======================= 处理 face_uvs（可选） ======================
    // 这里的逻辑是：
    //   - 如果 Python 传进来的 face_uvs 不是 None，就尝试把它转换成
    //     std::vector<std::array<double,6>>。
    //   - 只有当长度正好与 faces 数量相等时，才认为是合法的 per-face UV，
    //     并赋值给 mesh.face_uvs；否则就直接忽略（不报错，只是相当于没传 UV）。
    //====================================================================

    if (!face_uvs_obj.is_none()) {                                                     // 如果传入的 face_uvs 不是 Python 的 None
        auto face_uvs = face_uvs_obj.cast<std::vector<std::array<double, 6>>>();       // 用 pybind11 把它转换成 C++ 的 vector<array<double,6>>
        if (face_uvs.size() == mesh.faces.size()) {                                    // 只有当 UV 条目数和三角面数量相同才认为合法
            mesh.face_uvs = std::move(face_uvs);                                       // 把 UV 列表 move 进 mesh.face_uvs（避免拷贝，提高效率）
        }
        // 如果尺寸不匹配，就什么也不做，相当于不携带 UV（mesh.face_uvs 仍为空）
    }

    //======================= 构造简化参数 ===============================
    // SimplifyOptions 是 QEM 算法的配置结构体，这里把 Python 传入的参数填进去。
    //====================================================================

    SimplifyOptions opt;                           // 创建一个配置结构体实例
    opt.ratio = ratio;                             // 设置目标面数比例
    opt.target_faces = target_faces;               // 设置目标面数；当 >0 时通常优先于 ratio
    opt.max_collapses = max_collapses;             // 设置最多允许的折叠次数；当 <=0 时由算法内部推导
    opt.time_limit = time_limit;                   // 设置时间上限；<=0 通常表示不限制
    opt.progress_interval = progress_interval;     // 设置每隔多少次折叠输出一次进度（打印在 C++ 侧的日志里）

    //======================= 调用 QEM 简化核心 ==========================
    // SimplifyReport 用于承载算法的统计信息（比如最终面数/折叠次数等），
    // qem_simplify 则会直接在 mesh 上进行原地修改，把结果写回 mesh.verts/mesh.faces/mesh.face_uvs。
    //====================================================================

    SimplifyReport rep;                            // 创建一个报告对象，用于接收统计信息
    qem_simplify(mesh, opt, rep);                  // 调用 C++ 的 QEM 简化核心，对 mesh 进行原地简化

    //======================= 把结果拷贝回 Python 友好的结构 =============
    // 这里我们把 mesh.verts / mesh.faces 转回成 std::vector<std::array<...>>，
    // 这样 pybind11 能够按自动规则转换成 Python 里的 list[tuple]。
    //====================================================================

    std::vector<std::array<double, 3>> out_verts;  // 用于返回给 Python 的顶点数组
    out_verts.reserve(mesh.verts.size());          // 预留容量等于简化后的顶点数量
    for (const auto& v : mesh.verts) {             // 遍历简化后的每一个顶点（Vec3）
        out_verts.push_back({v.x, v.y, v.z});      // 把 Vec3 转成 {x,y,z} 的 std::array 放入 out_verts
    }

    std::vector<std::array<int, 3>> out_faces;     // 用于返回给 Python 的三角面索引数组
    out_faces.reserve(mesh.faces.size());          // 预留容量等于简化后的面数量
    for (const auto& f : mesh.faces) {             // 遍历简化后的每一个三角面（Tri）
        out_faces.push_back({f.a, f.b, f.c});      // 把 Tri 转成 {a,b,c} 的 std::array 放入 out_faces
    }

    //======================= 处理返回的 UV 列表 ==========================
    // 逻辑与输入时类似：
    //   - 如果 mesh.face_uvs 非空，且大小和 mesh.faces 一致，说明简化过程中正确携带了 UV，
    //     就把它一并作为第三个返回值返回。
    //   - 否则，第三个返回值为 None（在 Python 侧看到的是 None）。
    //====================================================================

    if (!mesh.face_uvs.empty() && mesh.face_uvs.size() == mesh.faces.size()) {  // 如果有 UV 且数量和面数一致
        return py::make_tuple(out_verts, out_faces, mesh.face_uvs);             // 返回 (顶点, 面, UV 列表)
    } else {                                                                    // 否则认为没有可用的 UV 输出
        return py::make_tuple(out_verts, out_faces, py::none());                // 返回 (顶点, 面, None)
    }
}

//======================================================================
// PYBIND11_MODULE 宏块：定义一个名为 meshqem_py 的 Python 扩展模块
//
// 这段宏会被展开成初始化函数，供 Python 在 import meshqem_py 时调用。
// 这里面我们可以：
//   - 设置模块文档字符串（m.doc()）
//   - 用 m.def(...) 把 C++ 函数注册为 Python 可调用的函数
//======================================================================

PYBIND11_MODULE(meshqem_py, m) {   // 定义一个 Python 模块，模块名为 meshqem_py，m 是模块对象句柄
    m.doc() = "Python bindings for native meshqem QEM simplification with optional face-varying UV";  // 设置模块级文档字符串，在 Python 里 meshqem_py.__doc__ 可见

    m.def(                                      // 在模块上定义一个函数（相当于 Python 里的 def simplify_with_uv(...): ...）
        "simplify_with_uv",                    // Python 里看到的函数名
        &simplify_with_uv,                      // 指向上面定义的 C++ 实现函数
        py::arg("verts"),                      // 第一个参数名：verts（必填）
        py::arg("faces"),                      // 第二个参数名：faces（必填）
        py::arg("face_uvs") = py::none(),      // 第三个参数名：face_uvs，默认值为 None（在 Python 中可选参数）
        py::arg("ratio") = 0.5,                // 参数 ratio，默认 0.5（保留一半面数），当 target_faces <= 0 时生效
        py::arg("target_faces") = -1,          // 参数 target_faces，默认 -1（不指定绝对目标面数）
        py::arg("max_collapses") = -1,         // 参数 max_collapses，默认 -1（让算法内部按目标面数推导）
        py::arg("time_limit") = -1.0,          // 参数 time_limit，默认 -1.0（不设时间上限）
        py::arg("progress_interval") = 20000,  // 参数 progress_interval，默认 20000 次折叠打印一次进度
        R"doc(                                  // 下面是 Python 侧看到的文档字符串（多行），使用原始字符串 R"doc(... )doc" 书写更方便
Simplify a triangle mesh using native C++ meshqem with optional face-varying UV triplets.

Parameters
----------
verts : List[(x,y,z)]
    Vertex positions as double triples.
faces : List[(i,j,k)]
    Triangle indices (0-based).
face_uvs : Optional[List[(u0,v0,u1,v1,u2,v2)]]
    Optional per-face UV triplets aligned with `faces`. If provided and length
    matches faces, UV triplets will be filtered/compacted alongside faces.
ratio : float
    Target face ratio (0..1]; used when target_faces <= 0.
target_faces : int
    Absolute target face count; overrides ratio when >0.
max_collapses : int
    Cap on number of edge collapses; derived from target when <=0.
time_limit : float
    Per-mesh time limit in seconds; <=0 disables.
progress_interval : int
    Emit C++ progress lines every N collapses (stderr).

Returns
-------
new_verts : List[(x,y,z)]
new_faces : List[(i,j,k)]
new_face_uvs_or_None : Optional[List[(u0,v0,u1,v1,u2,v2)]]
        )doc");                              // 文档字符串结束，m.def 调用结束
}                                             // PYBIND11_MODULE 模块定义结束
