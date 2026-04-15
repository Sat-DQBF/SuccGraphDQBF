# blif_gen_iscas_clique.py
#
# This script generates a blif form Clique problem.
# import functions from blif_gen_coloring.py
#
# Author: Arthur Nieh
# Date: 2026-01-23

import sys
import math
from blif_gen_coloring import *


def clique_add_main_model(blif_lines, case_name, u_num, PI_num, clique_size, clique_digit_num):
    print(f"u_num: {u_num}")
    print(f"case_name: {case_name}")
    print(f"PI_num: {PI_num}")
    print(f"clique_size: {clique_size}")
    print(f"clique_digit_num: {clique_digit_num}")

### I/O parameters
    blif_lines.append(f".model {case_name}\n")
    blif_lines.append(".inputs ")
    blif_lines.extend(f"i{i} " for i in range(clique_digit_num))
    blif_lines.extend(f"j{i} " for i in range(clique_digit_num))
    blif_lines.extend(f"u{i} " for i in range(u_num))
    blif_lines.extend(f"v{i} " for i in range(u_num))

    blif_lines.extend(f"x{i} " for i in range(PI_num))
    blif_lines.append("\n.outputs f\n")

### Graph subcircuit
    # graph(u,v,x)
    blif_lines.append(".subckt graph ")
    blif_lines.extend(f"U{i}=u{i} " for i in range(u_num))
    blif_lines.extend(f"V{i}=v{i} " for i in range(u_num))
    blif_lines.extend(f"I{i}=x{i} " for i in range(PI_num))
    blif_lines.append("E=e1\n")

    blif_lines.append(".subckt graph ")
    blif_lines.extend(f"U{i}=v{i} " for i in range(u_num))
    blif_lines.extend(f"V{i}=u{i} " for i in range(u_num))
    blif_lines.extend(f"I{i}=x{i} " for i in range(PI_num))
    blif_lines.append("E=e2\n")
    blif_lines.append(".subckt or2 I0=e1 I1=e2 O=euvx\n")

### u, v the same
    blif_lines.append(f".subckt UequV{u_num} ")
    blif_lines.extend(f"U{i}=u{i} " for i in range(u_num))
    blif_lines.extend(f"V{i}=v{i} " for i in range(u_num))
    blif_lines.append("O_equal=uvsame\n")

### i, j the same
    blif_lines.append(f".subckt UequV{clique_digit_num} ")
    blif_lines.extend(f"U{i}=i{i} " for i in range(clique_digit_num))
    blif_lines.extend(f"V{i}=j{i} " for i in range(clique_digit_num))
    blif_lines.append("O_equal=ijsame\n")

### i, j nequal (not ij same)
    blif_lines.append(f".subckt not ")
    blif_lines.append("I=ijsame O=ijnequal\n")

### i, j < clique_size
    blif_lines.append(f".subckt fit_color_limit ")
    blif_lines.extend(f"I{i}=i{i} " for i in range(clique_digit_num))
    blif_lines.append("G=ifit\n")

    blif_lines.append(f".subckt fit_color_limit ")
    blif_lines.extend(f"I{i}=j{i} " for i in range(clique_digit_num))
    blif_lines.append("G=jfit\n")

    blif_lines.append(".subckt and2 I0=ifit I1=jfit O=ijfit\n")

### main circuit

    blif_lines.append(".subckt imply I0=ijnequal I1=euvx O=phi1\n")

    blif_lines.append(f".subckt equiv I0=ijsame I1=uvsame O=phi2\n")

    blif_lines.append(f".subckt and2 I0=phi1 I1=phi2 O=phi\n")
    blif_lines.append(f".subckt imply I0=ijfit I1=phi O=f\n")

    blif_lines.append(".end\n\n")

def clique_add_subcircuit(blif_lines, u_num, clique_digit_num):
    add_not_gate(blif_lines)
    add_or_num(blif_lines, 2)
    add_and_num(blif_lines, 2)
    add_imply_gate(blif_lines)
    add_equiv_gate(blif_lines)
    # add_nequiv_gate(blif_lines)
    if u_num != 2:
        add_and_num(blif_lines, u_num)
    if clique_digit_num != u_num and clique_digit_num != 2:
        add_and_num(blif_lines, clique_digit_num)

    if clique_digit_num != 2:
        add_or_num(blif_lines, clique_digit_num)

    add_UequivV(blif_lines, u_num)
    if clique_digit_num != u_num:
        add_UequivV(blif_lines, clique_digit_num)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate blif file for SMV benchmarks with coloring constraints")
    parser.add_argument("-i", "--input", type=str, help="Input blif file path", required=True)
    parser.add_argument("-o", "--output", type=str, help="Output blif file path", required=True)
    parser.add_argument("--case", type=str, help="benchmark case name", default="clique")
    parser.add_argument("-c", "--clique", type=int, help="Clique size", default=3)
    parser.add_argument("--abc", type=str, help="ABC output file path", required=True)
    parser.add_argument("--rg", action="store_true", help="Random Graph mode")
    parser.add_argument("--ff", type=int, default=0, help="Number of nodes (for RG mode)")

    args = parser.parse_args()

    case_name = args.case
    clique_size = args.clique

    clique_digit_num = math.ceil(math.log2(clique_size)) if clique_size > 1 else exit(1)

    input_file = args.input
    output_file = args.output
    abc_file = args.abc

    blif_lines = []

    if args.rg:
        u_num = args.ff
        PI_num = 0
        clique_add_main_model(blif_lines, case_name, u_num, PI_num, clique_size, clique_digit_num)
        add_implicit_graph(blif_lines, input_file, is_rg=True)
    else:
        u_num, PI_num = parse_bench(abc_file)
        clique_add_main_model(blif_lines, case_name, u_num, PI_num, clique_size, clique_digit_num)
        add_implicit_graph(blif_lines, input_file)
    add_fit_color_limit(blif_lines, clique_size, clique_digit_num)
    print("\nAdding graph subcircuit...")

    clique_add_subcircuit(blif_lines, u_num, clique_digit_num)
    print("\nWriting blif file...")
    with open(output_file, "w") as f:
        f.writelines(blif_lines)
    print("\nGenerate blif file successfully!\n")
