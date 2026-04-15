## Call abc -f to_cnf.sh to convert the input file to CNF format

import os
from pathlib import Path
# from subprocess import check_output
import sys
import argparse
from subprocess import Popen, PIPE

def gen_parse_bench_script(input_file, blif_output):
    print('[log] Generating parse_bench.sh...')
    print(f'read input {input_file}')
    print(f'write output {blif_output}\n')

    script = (
        f"read {input_file}\n"
        "print_io\n"
        "comb\n"
        "fraig\n"
        "strash\n"
        f"write_blif {blif_output}\n"
        "quit\n"
    )
    return script

def convert_to_blif(input_file, blif_output, abc_output_file, abc_bin):
    script = gen_parse_bench_script(input_file, blif_output)
    abc_dir = os.path.dirname(abc_bin) or "."

    p = Popen([abc_bin], stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=abc_dir, text=True)
    out, err = p.communicate(script)
    with open(abc_output_file, "w") as f:
        f.write(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Convert blif file to combinational format"
    )
    parser.add_argument("-i", "--input_file", type=str, required=True)
    parser.add_argument("-o", "--output_file", type=str, required=True)
    parser.add_argument("--abc_out", required=True)
    parser.add_argument("--abc_bin", default=os.environ.get("ABC_BIN", "abc"))
    args = parser.parse_args()

    convert_to_blif(args.input_file, args.output_file, args.abc_out, args.abc_bin)
