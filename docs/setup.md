# ConvertAsset Setup

## Runtime Requirement

ConvertAsset relies on USD Python bindings from NVIDIA Isaac Sim. The `pxr`
package is not treated as a normal pip dependency in this project; run CLI
commands through Isaac Sim's Python environment.

Recommended entry:

```bash
./scripts/isaac_python.sh ./main.py <subcommand> [args]
```

The wrapper looks for Isaac Sim in this order:

1. `ISAAC_SIM_ROOT` when it contains `python.sh`
2. `/isaac-sim/python.sh`
3. `~/.local/share/ov/pkg/isaac_sim-*`
4. `/opt/nvidia/isaac-sim`, `/opt/NVIDIA/isaac-sim`, `/opt/omniverse/isaac-sim`

Set an explicit root when auto-detection is not enough:

```bash
export ISAAC_SIM_ROOT=/abs/path/to/isaac-sim
./scripts/isaac_python.sh ./main.py no-mdl /abs/path/to/scene.usd
```

## Python Package Imports

Keep heavy Isaac Sim imports lazy. Do not import `pxr`, `omni.*`, or other Isaac
Sim-only modules at package import time. Import them inside functions or command
handlers so lightweight tools and documentation checks can run without Isaac
Sim.

## Optional Native Mesh Backend

The Python QEM backend works without compiling native code. To enable the C++
backend, build `native/meshqem` and copy the generated `meshqem_py` extension
into `convert_asset/mesh/`.

Detailed instructions:

- [Native meshqem usage](operations/native-meshqem-usage.md)
- [Python calls C++ tutorial](operations/native-meshqem-python-calls-cpp.md)

## Documentation Map

- [Design](design/README.md)
- [Operations](operations/README.md)
- [Records](records/README.md)
- [Reference](reference/README.md)
