# Description: Generate blif file for SMV benchmarks with coloring constraints
#
# Modified from sudoku/blif_gen_auto.py
# This script generates a blif file for SMV benchmarks with coloring constraints.
#
# Author: Arhtur Nieh
# Date: 2026-01-22
# Reference: https://www.notion.so/DQBF-on-Graphs-1ac570d5afa980eca2deef656ebd8b68?pvs=4

import sys
import math
import argparse

# three parameters
case_name = ''
colorability = ''

blif_lines = []
FF_num = 0

u_num = v_num = 0
c_num = d_num = 0
c_digits = 0

FF_D_map = dict()
FF_Q_map = dict()
FF_ind_map = dict()

PI_num = 0
PI_dict = dict()
PO_list = []

def parse_bench(abc_file):
    global FF_num, u_num, v_num, PI_num
    global FF_D_map, FF_Q_map, FF_ind_map
    global PI_dict

    print(f"Reading file: {abc_file}\n")
    with open(abc_file, "r") as f:
        lines = f.readlines()

    for line in lines:
        if 'Warning' in line:
            continue
        line = line.split(' ')
        if len(line) < 2:
            continue

        elif line[1] == "inputs":
            PI_num = int(line[2].strip("():"))
            for i in range(PI_num):
                pi = line[4+i].strip('\n').split('=')[1]
                PI_dict.update({i: pi})
                # print(f"PI_dict: {i} -> {pi}")
            print(f"Number of inputs: {PI_num}")

        elif line[1] == "outputs":
            PO_num = int(line[2].strip("():\n"))
            for i in range(PO_num):
                po = line[3+i].strip('\n').split('=')[1]
                PO_list.append(po)
                # print(f"PO_list {i}: {po}")
            print(f"Number of outputs: {PO_num}")

        elif line[0] == "Latches":

            FF_num = int(line[1].strip("():"))
            u_num = v_num = FF_num
            print(f"Number of nodes: {FF_num}")

            for i in range(FF_num):
                ff = line[4+i].replace('(','=').replace(')','=').split('=')

                FF_Q_map.update({i: ff[1]})
                FF_D_map.update({i: ff[2]})
                # print(f"FF_D_map: {i} -> {FF_D_map[i]}")
                # print(f"FF_Q_map: {i} -> {FF_Q_map[i]}")
                FF_ind_map.update({ff[1]: i})
                FF_ind_map.update({ff[2]: i})
                # print(f"FF_ind_map: {ff[1]} -> {FF_ind_map[ff[1]]}")
                # print(f"FF_ind_map: {ff[2]} -> {FF_ind_map[ff[2]]}")
            break

    return u_num, PI_num

def add_main_model():
    global u_num, v_num, c_num, d_num, PI_num
    global blif_lines

### I/O parameters
    blif_lines.append(f".model {case_name}\n")
    blif_lines.append(".inputs ")
    for i in range(u_num):
        blif_lines.append("u" + str(i) + " ")
    for i in range(v_num):
        blif_lines.append("v" + str(i) + " ")
    for i in range(c_num):
        blif_lines.append("c" + str(i) + " ")
    for i in range(d_num):
        blif_lines.append("d" + str(i) + " ")
    for i in range(PI_num):
        blif_lines.append("pi" + str(i) + " ")
    blif_lines.append("\n")
    blif_lines.append(".outputs f\n")

### Graph subcircuit
    blif_lines.append(".subckt graph ")
    for i in range(u_num):
        blif_lines.append("U" + str(i) + "=u" + str(i) + " ")
    for i in range(v_num):
        blif_lines.append("V" + str(i) + "=v" + str(i) + " ")
    for i in range(PI_num):
        blif_lines.append("I" + str(i) + "=pi" + str(i) + " ")
    blif_lines.append("E=e1\n")

    blif_lines.append(".subckt graph ")
    for i in range(u_num):
        blif_lines.append("U" + str(i) + "=v" + str(i) + " ")
    for i in range(v_num):
        blif_lines.append("V" + str(i) + "=u" + str(i) + " ")
    for i in range(PI_num):
        blif_lines.append("I" + str(i) + "=pi" + str(i) + " ")
    blif_lines.append("E=e2\n")

    # graph = 0, if u = 0000...0, v = 0000...0
    # blif_lines.append(f".subckt or{u_num} ")
    # for i in range(u_num):
    #     blif_lines.append(f"I{i}=u{i} ")
    # blif_lines.append("O=e0\n")

    blif_lines.append(".subckt or2 I0=e1 I1=e2 O=e0\n")

    blif_lines.append(f".subckt UneqV{u_num} ")
    for i in range(u_num):
        blif_lines.append(f"U{i}=u{i} ")
    for i in range(v_num):
        blif_lines.append(f"V{i}=v{i} ")
    blif_lines.append("O_equal=notsame\n")
    blif_lines.append(".subckt and2 I0=e0 I1=notsame O=e\n")

### Color subcircuit
    blif_lines.append(".subckt color_not_equal ")
    for i in range(c_num):
        blif_lines.append("C" + str(i) + "=c" + str(i) + " ")
    for i in range(d_num):
        blif_lines.append("D" + str(i) + "=d" + str(i) + " ")
    blif_lines.append("O_nequal=ncolor\n")

### Binary color subcircuit
    blif_lines.append(".subckt fit_color_limit ")
    for i in range(c_num):
        blif_lines.append(f"I{i}=c{i} ")
    blif_lines.append("G=clessthan\n")
    blif_lines.append(".subckt fit_color_limit ")
    for i in range(d_num):
        blif_lines.append(f"I{i}=d{i} ")
    blif_lines.append("G=dlessthan\n")
    blif_lines.append(".subckt and2 I0=clessthan I1=dlessthan O=colorencode\n")

### Main circuit
    blif_lines.append(".subckt imply I0=e I1=ncolor O=diffcolor\n")

    # not same node
    blif_lines.append(".subckt UneqV" + str(u_num) + " ")
    for i in range(u_num):
        blif_lines.append("U" + str(i) + "=u" + str(i) + " ")
    for i in range(v_num):
        blif_lines.append("V" + str(i) + "=v" + str(i) + " ")
    blif_lines.append("O_equal=notsamenode\n")

    # not same color
    blif_lines.append(".subckt UneqV" + str(c_num) + " ")
    for i in range(c_num):
        blif_lines.append("U" + str(i) + "=c" + str(i) + " ")
    for i in range(d_num):
        blif_lines.append("V" + str(i) + "=d" + str(i) + " ")
    blif_lines.append("O_equal=notsamecolor\n")

    blif_lines.append(".subckt imply I0=notsamecolor I1=notsamenode O=notsamecolornode\n")

    blif_lines.append(".subckt and2 I0=diffcolor I1=colorencode O=temp1\n")
    blif_lines.append(".subckt and2 I0=notsamecolornode I1=temp1 O=f\n")

    blif_lines.append(".end\n\n")

def add_implicit_graph(blif_lines, input_file, is_rg=False):
    if is_rg:
        with open(input_file, "r") as f:
            blif_lines.extend(f.readlines())
        return

    global u_num, v_num, PI_num, PI_dict
    global FF_D_map, FF_Q_map, FF_ind_map

    # put the original blif file into the new blif file
    with open(input_file, "r") as f:
        lines = f.readlines()
    model_name = ''
    for line in lines:
        if model_name == '':
            s = line.split(' ')
            if s[0] == '.model':
                model_name = 'D_Q'
                blif_lines.append(f'.model {model_name}\n')
            # print(f"%%%{model_name}%%%")
            continue
        blif_lines.append(line)

    blif_lines.append("\n.model graph\n")
    blif_lines.append(".inputs ")
    for i in range(u_num):
        blif_lines.append("U" + str(i) + " ")
    for i in range(v_num):
        blif_lines.append("V" + str(i) + " ")
    for i in range(PI_num):
        blif_lines.append("I" + str(i) + " ")
    blif_lines.append("\n")
    blif_lines.append(".outputs E\n")

    blif_lines.append(f".subckt {model_name} ")
    for i in range(PI_num):
        blif_lines.append(f"{PI_dict[i]}=I{i} ")
    for i in range(u_num):
        blif_lines.append(f"{FF_Q_map[i]}=U{i} ")
    for po in PO_list:
        blif_lines.append(f"{po}=__dummy_unused_{po} ")
    for i in range(v_num):
        blif_lines.append(f"{FF_D_map[i]}=s{i} ")
    # TODO PO wire not yet assign
    blif_lines.append("\n")

    for i in range(u_num):
        blif_lines.append(f".subckt equiv I0=V{i} I1=s{i} O=E{i}\n")

    blif_lines.append(f".subckt and{u_num} ")
    for i in range(u_num):
        blif_lines.append(f"I{i}=E{i} ")
    blif_lines.append("O=E\n")

    blif_lines.append(".end\n\n")
    return

def add_color_not_equal(blif_lines, c_num):
    blif_lines.append(".model color_not_equal\n")
    blif_lines.append(".inputs ")
    for i in range(c_num):
        blif_lines.append("C" + str(i) + " ")
    for i in range(c_num):
        blif_lines.append("D" + str(i) + " ")
    blif_lines.append("\n.outputs O_nequal\n")

    for i in range(c_num):
        blif_lines.append(".subckt xor2 I0=C" + str(i) + " I1=D" + str(i) + " O=unequal" + str(i) + "\n")
    blif_lines.append(".subckt or" + str(c_num))
    for i in range(c_num):
        blif_lines.append(" I" + str(i) + "=unequal" + str(i))
    blif_lines.append(" O=O_nequal\n")
    blif_lines.append(".end\n\n")
    return

def add_1_comparator(blif_lines):
    # G = 1 if A > B
    # C = 1 if A = B
    # E = 1 if A = B in the significant bit
    blif_lines.append(".model comparator\n")
    blif_lines.append(".inputs A B E\n")
    blif_lines.append(".outputs G C\n")
    blif_lines.append(".names A B E G\n")
    blif_lines.append("101 1\n")
    blif_lines.append(".names A B E C\n")
    blif_lines.append("111 1\n")
    blif_lines.append("001 1\n")
    blif_lines.append(".end\n\n")

def add_fit_color_limit(blif_lines, c_limit, c_num):
    if c_limit <= 0 or c_limit > math.pow(2, c_num):
        print("Error: c_limit should be greater than 0 and less than c_num")
        print(f"c_limit: {c_limit}, c_num: {c_num}")
        sys.exit(1)
    b_c_limit = bin(c_limit-1)[2:]
    b_c_limit = b_c_limit.zfill(c_digits)
    print(f"c_limit: {b_c_limit}")

    add_n_comparator(blif_lines, c_num)

    blif_lines.append(".model fit_color_limit\n")
    blif_lines.append(".inputs ")
    for i in range(c_num):
        blif_lines.append(f"I{i} ")
    blif_lines.append("\n")
    blif_lines.append(".outputs G\n")

    # set C[i] = b_c_limit[-i-1]
    for i in range(c_num):
        blif_lines.append(f".names C{i}\n")
        blif_lines.append(f"{b_c_limit[-i-1]}\n")
        print(f"C{i}={b_c_limit[-i-1]}")

    # compare, if C >= I, G = 1
    blif_lines.append(f".subckt comparator{c_num} ")
    for i in range(c_num):
        blif_lines.append(f"A{i}=C{i} ")
    for i in range(c_num):
        blif_lines.append(f"B{i}=I{i} ")
    blif_lines.append("G=G\n")

    blif_lines.append(".end\n\n")

def add_n_comparator(blif_lines, num):
    if ".model comparator\n" not in blif_lines:
        add_1_comparator(blif_lines)
    if f".model comparator{num}\n" in blif_lines:
        return

    # G = 1 if A >= B
    blif_lines.append(f".model comparator{num}\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append(f"A{i} ")
    for i in range(num):
        blif_lines.append(f"B{i} ")
    blif_lines.append("\n")
    blif_lines.append(".outputs G\n")

    # set C_num = 1
    blif_lines.append(f".names C{num}\n")
    blif_lines.append("1\n")

    for i in range(num-1, -1, -1):
        blif_lines.append(f".subckt comparator A=A{i} B=B{i} E=C{i+1} G=G{i} C=C{i}\n")
    blif_lines.append(f".subckt or{num}")
    for i in range(num):
        blif_lines.append(f" I{i}=G{i}")
    blif_lines.append(" O=o1\n")
    blif_lines.append(".subckt or2 I0=o1 I1=C0 O=G\n")

    blif_lines.append(".end\n\n")

def add_1_adder(blif_lines):
    # A + B = S, C_out
    blif_lines.append(".model adder\n")
    blif_lines.append(".inputs A B C_in\n")
    blif_lines.append(".outputs S C_out\n")
    blif_lines.append(".names A B C_in S\n")
    # blif_lines.append("000 0\n")
    blif_lines.append("001 1\n")
    blif_lines.append("010 1\n")
    # blif_lines.append("011 0\n")
    blif_lines.append("100 1\n")
    # blif_lines.append("101 0\n")
    # blif_lines.append("110 0\n")
    blif_lines.append("111 1\n")

    blif_lines.append(".names A B C_in C_out\n")
    # blif_lines.append("000 0\n")
    # blif_lines.append("001 0\n")
    # blif_lines.append("010 0\n")
    blif_lines.append("011 1\n")
    # blif_lines.append("100 0\n")
    blif_lines.append("101 1\n")
    blif_lines.append("110 1\n")
    blif_lines.append("111 1\n")

    blif_lines.append(".end\n\n")

def add_n_adder(blif_lines, num):
    # A + B = S, do a mod sum, no addition bit
    if ".model adder\n" not in blif_lines:
        add_1_adder(blif_lines)
    if f".model adder{num}\n" in blif_lines:
        return

    blif_lines.append(f".model adder{num}\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append(f"A{i} ")
    for i in range(num):
        blif_lines.append(f"B{i} ")
    blif_lines.append("\n.outputs ")
    for i in range(num):
        blif_lines.append(f"S{i} ")
    blif_lines.append("\n")

    # set C_num = 0
    blif_lines.append(f".names C0\n")
    blif_lines.append("0\n")

    for i in range(0, num):
        blif_lines.append(f".subckt adder A=A{i} B=B{i} C_in=C{i} S=S{i} C_out=C{i+1}\n")

    blif_lines.append(".end\n\n")

def add_is_0(blif_lines, num):

    blif_lines.append(".model is_zero\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append(f"I{i} ")
    blif_lines.append("\n.outputs O\n")
    blif_lines.append(".names ")
    for i in range(num):
        blif_lines.append(f"I{i} ")
    blif_lines.append("O\n")
    blif_lines.append("0" * num + " 1\n")
    blif_lines.append(".end\n\n")

### All fundamental gates
def add_not_gate(blif_lines):
    blif_lines.append(".model not\n")
    blif_lines.append(".inputs I\n")
    blif_lines.append(".outputs O\n")
    blif_lines.append(".names I O\n")
    blif_lines.append("0 1\n")
    blif_lines.append(".end\n\n")
    return

def add_imply_gate(blif_lines):
    blif_lines.append(".model imply\n")
    blif_lines.append(".inputs I0 I1\n")
    blif_lines.append(".outputs O\n")
    blif_lines.append(".names I0 I1 O\n")
    blif_lines.append("0- 1\n")
    blif_lines.append("-1 1\n")
    blif_lines.append(".end\n\n")
    return

def add_equiv_gate(blif_lines):
    blif_lines.append(".model equiv\n")
    blif_lines.append(".inputs I0 I1\n")
    blif_lines.append(".outputs O\n")
    blif_lines.append(".names I0 I1 O\n")
    blif_lines.append("11 1\n")
    blif_lines.append("00 1\n")
    blif_lines.append(".end\n\n")
    return

def add_nequiv_gate(blif_lines): # xor gate
    blif_lines.append(".model xor2\n")
    blif_lines.append(".inputs I0 I1\n")
    blif_lines.append(".outputs O\n")
    blif_lines.append(".names I0 I1 O\n")
    blif_lines.append("01 1\n")
    blif_lines.append("10 1\n")
    blif_lines.append(".end\n\n")
    return

def add_or_num(blif_lines, num):
    if f".model or{num}\n" in blif_lines:
        return
    blif_lines.append(".model or" + str(num) + "\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append("I" + str(i) + " ")
    blif_lines.append("\n.outputs O\n")
    blif_lines.append(".names ")
    for i in range(num):
        blif_lines.append("I" + str(i) + " ")
    blif_lines.append("O\n")
    for i in range(num):
        line = "-" * num + " 1\n"
        line = line[:i] + '1' + line[i+1:]
        blif_lines.append(line)

    blif_lines.append(".end\n\n")
    return

def add_and_num(blif_lines, num):
    if f".model and{num}\n" in blif_lines:
        return
    # num = int(u_num/2)
    blif_lines.append(".model and" + str(num) + "\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append("I" + str(i) + " ")
    blif_lines.append("\n.outputs O\n")
    blif_lines.append(".names ")
    for i in range(num):
        blif_lines.append("I" + str(i) + " ")
    blif_lines.append("O\n")
    blif_lines.append("1" * num + " 1\n")

    blif_lines.append(".end\n\n")
    return

# def add_xor_num(blif_lines, num):
#     if num <= 2:
#         print("Error: num should be greater than 2 for xor_num")
#         return
#     blif_lines.append(".model xor" + str(num) + "\n")
#     blif_lines.append(".inputs ")
#     for i in range(num):
#         blif_lines.append("I" + str(i) + " ")
#     blif_lines.append("\n.outputs O\n")
#     blif_lines.append(".subckt xor2 I0=I0 I1=I1 O=t1\n")
#     for i in range(2, num-1):
#         blif_lines.append(f".subckt xor2 I0=I{i} I1=t{i-1} O=t{i}\n")
#     blif_lines.append(f".subckt xor2 I0=I{num-1} I1=t{num-2} O=O\n")
#     blif_lines.append(".end\n\n")
#     return

def add_UnequivV(blif_lines, num):
    # vector U and V are not equivalent
    blif_lines.append(".model UneqV" + str(num) + "\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append("U" + str(i) + " ")
    for i in range(num):
        blif_lines.append("V" + str(i) + " ")
    blif_lines.append("\n")
    blif_lines.append(".outputs O_equal\n")

    for i in range(num):
        blif_lines.append(".subckt xor2 I0=U" + str(i) + " I1=V" + str(i) + " O=unequal" + str(i) + "\n")
    blif_lines.append(".subckt or" + str(num))
    for i in range(num):
        blif_lines.append(" I" + str(i) + "=unequal" + str(i))
    blif_lines.append(" O=O_equal\n")
    blif_lines.append(".end\n\n")
    return

def add_UequivV(blif_lines, num):
    # vector U and V are equivalent
    blif_lines.append(".model UequV" + str(num) + "\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append("U" + str(i) + " ")
    for i in range(num):
        blif_lines.append("V" + str(i) + " ")
    blif_lines.append("\n")
    blif_lines.append(".outputs O_equal\n")

    for i in range(num):
        blif_lines.append(".subckt equiv I0=U" + str(i) + " I1=V" + str(i) + " O=equal" + str(i) + "\n")
    blif_lines.append(".subckt and" + str(num))
    for i in range(num):
        blif_lines.append(" I" + str(i) + "=equal" + str(i))
    blif_lines.append(" O=O_equal\n")
    blif_lines.append(".end\n\n")
    return

def add_UxequivVx(blif_lines):
    # vector Ux and Vx are equivalent
    num = int(u_num/2)
    blif_lines.append(".model UxequVx\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append("U" + str(i) + " ")
    for i in range(num):
        blif_lines.append("V" + str(i) + " ")
    blif_lines.append("\n")
    blif_lines.append(".outputs O_equal\n")

    for i in range(num):
        blif_lines.append(".subckt equiv I0=U" + str(i) + " I1=V" + str(i) + " O=equal" + str(i) + "\n")
    blif_lines.append(".subckt and" + str(num))
    for i in range(num):
        blif_lines.append(" I" + str(i) + "=equal" + str(i))
    blif_lines.append(" O=O_equal\n")
    blif_lines.append(".end\n\n")
    return

def add_onehot(blif_lines, num):
    blif_lines.append(".model onehot" + str(num) + "\n")
    blif_lines.append(".inputs ")
    for i in range(num):
        blif_lines.append("I" + str(i) + " ")
    blif_lines.append("\n.outputs O\n")
    blif_lines.append(".names ")
    for i in range(num):
        blif_lines.append("I" + str(i) + " ")
    blif_lines.append("O\n")
    for i in range(num):
        line = "0" * num + " 1\n"
        line = line[:i] + '1' + line[i+1:]
        blif_lines.append(line)

    blif_lines.append(".end\n\n")
    return

def add_subcircuit_model():
    global u_num, c_num, d_num, c_digits
    global blif_lines
    global colorability
    # add_not_gate()
    add_or_num(blif_lines, 2)
    add_and_num(blif_lines, 2)
    # add_xor_2()       #
    add_imply_gate(blif_lines)    #
    add_equiv_gate(blif_lines)    #
    add_nequiv_gate(blif_lines)   # xor2
    add_or_num(blif_lines, u_num)   #
    add_and_num(blif_lines, u_num)  #
    add_UnequivV(blif_lines, u_num) #
    if u_num != c_num:
        if c_num != 2:
            add_or_num(blif_lines, c_num)
        add_UnequivV(blif_lines, c_num)
    # add_and_num(int(u_num/2))

    add_fit_color_limit(blif_lines, colorability, c_num)

    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate blif file for SMV benchmarks with coloring constraints")
    parser.add_argument("-i", "--input", type=str, help="Input blif file path", required=True)
    parser.add_argument("-o", "--output", type=str, help="Output blif file path", required=True)
    parser.add_argument("--case", type=str, help="benchmark case name", default="coloring")
    parser.add_argument("-c", "--colorability", type=int, help="Colorability constraint", default=2)
    parser.add_argument("--abc", type=str, help="ABC output file path", required=True)
    parser.add_argument("--rg", action="store_true", help="Random Graph mode")
    parser.add_argument("--ff", type=int, default=0, help="Number of nodes (for RG mode)")

    args = parser.parse_args()

    case_name = args.case
    colorability = args.colorability

    input_file = args.input
    output_file = args.output

    abc_file = args.abc

    c_num = d_num = c_digits = math.ceil(math.log2(colorability))

    if args.rg:
        u_num = v_num = args.ff
        PI_num = 0
        add_main_model()
        add_implicit_graph(blif_lines, input_file, is_rg=True)
    else: # parse blif file generated by abc
        parse_bench(abc_file)
        add_main_model()
        add_implicit_graph(blif_lines, input_file)
    add_color_not_equal(blif_lines, c_num)
    add_subcircuit_model()
    # print("\nWriting blif file...")
    with open(output_file, "w") as f:
        f.writelines(blif_lines)
    print(f"Colorability: {colorability}")
    print("\nGenerate Color blif sample file successfully!\n")
