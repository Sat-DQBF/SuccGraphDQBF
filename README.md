# Graph Extraction & DQBF Solving Pipeline

An experiment framework for extracting succinct and explicit graphs from Boolean sequential circuits, encoding graph problems (Clique, Coloring, Hamiltonian) into Dependency Quantified Boolean Formulas (DQBF), and evaluating them against state-of-the-art solvers.

## Overview

This experiment framework operates on three primary benchmark sets:
1.  **Sequential Circuits (`iscas89`)**: Sequential circuits in `.bench` format.
2.  **Model Checking (`smv`)**: Sequential circuits in `.blif` format.
3.  **Random Graphs (`rg`)**: Randomly generated XOR functions in `.blif` format.

### Supported Graph Problems
* **k-Coloring**: Determines if the graph can be colored with k colors.
* **k-Clique**: Finds a complete subgraph of size k.
* **Hamiltonian Cycle**: Determines if the graph contains a Hamiltonian cycle.

### Supported Solvers
* **DQBF Solvers**: [DQBDD](https://github.com/jurajsic/DQBDD), [pedant](https://github.com/fslivovsky/pedant-solver) 
* **SAT Solvers**:  [PySAT](https://pysathq.github.io/), [Cadical](https://github.com/arminbiere/cadical), [POP-S](https://github.com/s6dafabe/popsatgcpbcp)
* **Other Graph Solvers**: [Google OR-Tools](https://developers.google.com/optimization/), [SAT-based CEGAR](https://github.com/TakehideSoh/SAT-based-CEGAR)

---

## Main Scripts & Workflow

Execution is completely managed by the script `run_experiments.sh` which delegates tasks to specific modular phases. Intermediate files generated during these phases are automatically saved in the `cache/` directory. This allows reusable assets (like combinational circuits or explicit graphs) to be shared across different solvers or parameters without redundant computation.

### Core Files
* **`run_experiments.sh`**: The master orchestrator. It manages the batch execution, loop parameters, parallel job scheduling, and routes inputs to the appropriate pipeline stages.
* **`01_extract_succinct.sh`**: Uses ABC to flatten sequential circuits into combinational BLIFs by replacing ignored latches with constant ground signals. *(Bypassed for `rg` benchmarks, which are already succinct graphs).*
* **`02_extract_explicit.sh`**: Uses ABC simulation alongside exhaustively generated test cases to evaluate the combinational circuit and extract all valid edges into a DIMACS-like `.col` explicit graph format.
* **`03_encode_dqbf.sh`**: Uses custom Python generators to append problem-specific constraints (e.g., coloring limits) to the combinational BLIF, then calls ABC to convert the entire structure into a `DQDIMACS` format.
* **`04_solve.sh`**: A central dispatcher that formats command-line arguments and invokes the requested target solver with a standard 1-hour timeout.

---

## Setup & Configuration

All external binaries and paths are resolved via `scripts/config.sh`. 

If your tools are installed in custom locations, you can override the defaults using environment variables before executing the pipeline:

```bash
export ABC_BIN="/custom/path/to/abc"
export PEDANT_BIN="/custom/path/to/pedant"
./scripts/run_experiments.sh ...
```

**Python Requirements:**
To ensure a clean workspace and prevent dependency conflicts, it is highly recommended to use a Python virtual environment.

1. **Create the virtual environment** in the root directory:
   ```bash
   python3 -m venv .venv
   ```

2. **Activate the environment**:
   ```bash
   source .venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Execution is handled through `run_experiments.sh`. It accepts 8 positional arguments to define the batch run:

```bash
./scripts/run_experiments.sh <BENCH_SET> <PROBLEM> <APPROACH> <SOLVER> <K_MIN> <K_MAX> <FF_MIN> <FF_MAX>
```

### Parameters
1.  **`BENCH_SET`**: `smv`, `iscas89`, or `rg`
2.  **`PROBLEM`**: `clique`, `color`, or `hamiltonian`
3.  **`APPROACH`**: `succinct` (triggers DQBF solvers) or `explicit` (triggers SAT/Graph solvers)
4.  **`SOLVER`**: `dqbdd`, `pedant`, `sat`, `popsat`, `ortools`, `cegar`
5.  **`K_MIN`**: Start of the problem size range (e.g., minimum colors/clique size). Set to `0` if inapplicable (like Hamiltonian).
6.  **`K_MAX`**: End of the problem size range.
7.  **`FF_MIN`**: Minimum number of latches/nodes to retain.
8.  **`FF_MAX`**: Maximum number of latches/nodes to retain.

### Examples

**1. Evaluate Pedant on Coloring for ISCAS89 Circuits**
Runs a succinct DQBF encoding for colors k ∈ [3, 4] on circuits keeping between 5 and 10 latches.
```bash
./scripts/run_experiments.sh iscas89 color succinct pedant 3 4 5 10
```

**2. Evaluate SAT-based-CEGAR on Hamiltonian for SMV Circuits**
Extracts explicit graphs and attempts to find a cycle. Hamiltonian doesn't utilize a `k` parameter, so `0 0` is passed.
```bash
./scripts/run_experiments.sh smv hamiltonian explicit cegar 0 0 3 16
```

**3. Evaluate Cadical on Random Graphs for Clique**
Evaluates explicit random graphs with 8 to 12 nodes, searching for cliques of size 3 to 5. 
*(Note: For random graphs, `FF` maps exactly to the node index length parsed from the filename, e.g., `..._n12_...`)*
```bash
./scripts/run_experiments.sh rg clique explicit sat 3 5 8 12
```

---

## Logging & Output

Logs are automatically written to `result/<BENCH_SET>/<PROBLEM>/<SOLVER>/`.
Each log file contains:
* The parameters of the execution.
* Standard output and errors from the extraction and encoding scripts.
* The exact CLI invocation used to execute the solver.
* The standard output of the solver (e.g., SAT/UNSAT results, assignments).
* A customized runtime summary detailing the duration of the extraction, encoding, and solving phases.
