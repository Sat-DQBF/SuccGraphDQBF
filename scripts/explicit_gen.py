### This file is used to generate explicit graph of comb blif circuits

import os
import sys
import time
import argparse
from subprocess import Popen, PIPE
from pathlib import Path

def parse_benchmark_file(file_path):
    print(f"Parsing {file_path}...")

    input_num = 0
    in_inputs_block = False

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Start of .inputs
            if line.startswith(".inputs"):
                in_inputs_block = True
                has_continuation = line.endswith("\\")

                # remove ".inputs" and trailing "\"
                content = line[len(".inputs"):].rstrip("\\").strip()
                if content:
                    input_num += len(content.split())

                if not has_continuation:
                    in_inputs_block = False
                continue

            # Continuation of .inputs
            if in_inputs_block:
                has_continuation = line.endswith("\\")
                content = line.rstrip("\\").strip()
                if content:
                    input_num += len(content.split())

                if not has_continuation:
                    in_inputs_block = False
                continue

    print(f"Input num: {input_num}")
    return input_num

def generate_test_cases(bit_number, output_file):
    """Generates 2^bit_number binary strings with atomic caching."""
    if os.path.exists(output_file):
        print(f"[Cache Hit] Test cases already exist: {output_file}")
        return

    print(f"Generating test cases for {bit_number} bits...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    temp_file = f"{output_file}.tmp.{os.getpid()}"
    limit = 1 << bit_number

    try:
        with open(temp_file, 'w') as f:
            for i in range(limit):
                f.write(f"{i:0{bit_number}b}\n")

        os.replace(temp_file, output_file)

    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e

def gen_abc_sim_script(input_file, test_case_file):
    script = (
        f"read {input_file}\n"
        "fraig\n"
        "strash\n"
        "time\n"
        f"sim -A {test_case_file} -v\n"
        "time\n"
        "quit\n"
    )
    return script

def exec_abc(script, abc_bin):
    # Dynamically infer the directory containing the abc binary
    abc_dir = os.path.dirname(abc_bin) or "."

    p = Popen(
        [str(abc_bin)],
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        cwd=str(abc_dir),
        text=True
    )

    out, err = p.communicate(script)
    if p.returncode != 0:
        print(f"Error: Command returned non-zero exit status {p.returncode}")
        print(f"Stderr: {err}")
        raise RuntimeError()

    return out, err


def extract_edges_smv(out, FF_num, directed_flag):
    """Extraction logic for SMV/ISCAS state-transition graphs."""
    E = []
    for line in out.splitlines():
        if line.startswith('0') or line.startswith('1'):
            spl = line.split()
            if len(spl) == 2:
                a = int(spl[0][-FF_num:], base=2) + 1
                b = int(spl[1][-FF_num:], base=2) + 1
                if directed_flag:
                    E.append((a, b))
                else:
                    if a == b: continue
                    elif a > b: E.append((b, a))
                    else: E.append((a, b))
    return E

def extract_edges_rg(out, FF_num, directed_flag):
    """Extraction logic for Combinational Random Graphs."""
    E = []
    for line in out.splitlines():
        if line.startswith('0') or line.startswith('1'):
            spl = line.split()
            if len(spl) == 2:
                # Random graphs only have an edge if output is 1
                if int(spl[1], base=2) == 0:
                    continue
                assert len(spl[0]) == 2 * FF_num
                a = int(spl[0][:FF_num], base=2) + 1
                b = int(spl[0][-FF_num:], base=2) + 1
                if directed_flag:
                    E.append((a, b))
                else:
                    if a == b: continue
                    if a > b: E.append((b, a))
                    else: E.append((a, b))
    return E

def print_stats(E):
    print("========Stats========")
    print(f"total edge num = {len(E)}")

def dump_graph(E, output_file, FF_num):
    total_states = 2 ** FF_num

    with open(output_file, "w") as f:
        f.write(f"p edge {total_states} {len(E)}\n")
        for e in E:
            f.write(f"e {e[0]} {e[1]}\n")

def remove_dup(x):
    # Remove duplicates from list while preserving order
    return list(dict.fromkeys(x))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate explicit graph from SMV benchmark.')
    parser.add_argument('-b', '--benchmark', type=str, required=True, help='Path to the benchmark file')
    parser.add_argument('--ff', type=int, required=True, help='Number of flip-flops in the benchmark')
    parser.add_argument('--explicit_graph_output', type=str, default='iscas_explicit_graph.txt', help='Output file for the explicit graph edges')
    parser.add_argument('-d', '--directed', action='store_true', help='Generate directed graph')
    parser.add_argument('--abc_bin', type=str, default=os.environ.get("ABC_BIN", "abc"), help='Path to the ABC binary executable')
    parser.add_argument('--cache_dir', type=str, default=os.environ.get("CACHE_DIR", "cache"), help='Path to the cache directory')
    parser.add_argument('--rg', action='store_true', help="Random Graph mode")

    args = parser.parse_args()

    benchmark_file = args.benchmark
    FF_num = args.ff
    explicit_graph_output = args.explicit_graph_output
    directed_flag = args.directed
    abc_bin = args.abc_bin
    cache_dir = args.cache_dir

    start_time = time.time()

    if args.rg: # Random graphs are already succinct graphs
        input_num = 2 * FF_num
    else: # State transition systems
        input_num = parse_benchmark_file(benchmark_file)

    if input_num > 29:
        print("Error: The total number of inputs exceeds 29. Exiting.")
        sys.exit(1)

    # Step 3: Generate and cache input test cases
    test_case_file = os.path.join(cache_dir, "testcases", f"test_cases_{input_num}.txt")
    generate_test_cases(input_num, test_case_file)

    # Step 4: Run ABC simulation
    script = gen_abc_sim_script(benchmark_file, test_case_file)
    gen_script_time = time.time()
    abc_output, abc_error = exec_abc(script, abc_bin)

    exec_abc_time = time.time()
    print(f"Exec abc time: {exec_abc_time - gen_script_time:.2f} seconds")

    if args.rg:
        E = extract_edges_rg(abc_output, FF_num, directed_flag)
    else:
        E = extract_edges_smv(abc_output, FF_num, directed_flag)
    gen_explicit_time = time.time()
    print(f"Generate explicit graph time: {gen_explicit_time - exec_abc_time:.2f} seconds")

    E = remove_dup(E)
    remove_dup_time = time.time()
    print(f"Remove duplicate time: {remove_dup_time - gen_explicit_time:.2f} seconds")

    dump_graph(E, explicit_graph_output, FF_num)

    dump_time = time.time()
    print(f"Dump graph time: {dump_time - remove_dup_time:.2f} seconds")
    print(f"Total time: {dump_time - start_time:.2f} seconds")
    print("\nExplicit Graph is generated successfully\n")
    print_stats(E)
