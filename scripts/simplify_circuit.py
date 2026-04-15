import argparse
import sys

def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.readlines()

def write_file(file_path, lines):
    with open(file_path, 'w') as f:
        f.writelines(lines)

def simplify_blif(lines, num_latches_to_keep):
    latch_lines, header_lines, other_lines = [], [], []
    seen_latches = False

    for line in lines:
        if line.strip().startswith(".latch"):
            latch_lines.append(line)
            seen_latches = True
        elif not seen_latches:
            header_lines.append(line)
        else:
            other_lines.append(line)

    if len(latch_lines) < num_latches_to_keep:
        num_latches_to_keep = len(latch_lines)

    kept_latches = latch_lines[-num_latches_to_keep:] if num_latches_to_keep > 0 else []
    removed_latches = latch_lines[:-num_latches_to_keep] if num_latches_to_keep > 0 else latch_lines

    new_lines = header_lines + kept_latches
    for line in removed_latches:
        tokens = line.strip().split()
        out_signal = tokens[2]
        init_val = tokens[3] if len(tokens) > 3 else "0"
        new_lines.append(f".names {out_signal}\n{init_val}\n")

    return new_lines + other_lines

def simplify_bench(lines, num_latches_to_keep):
    new_lines = []
    dff_count = 0

    for line in lines:
        if 'DFF' in line:
            if dff_count < num_latches_to_keep:
                new_lines.append(line)
                dff_count += 1
            else:
                continue  # Skip this DFF
        elif 'flipflops' in line:
            # Modify the line to reflect the number of DFFs kept
            parts = line.split()
            if len(parts) > 1:
                if int(parts[1]) >= num_latches_to_keep:
                    print(f"Reducing flipflops from {parts[1]} to {num_latches_to_keep}")
                    parts[1] = str(num_latches_to_keep)
                else:
                    print(f"[Warning] Keeping flipflops at {parts[1]}")
                new_lines.append(' '.join(parts) + '\n')
        else:
            new_lines.append(line)

    return new_lines

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simplify circuits by replacing latches with constants")
    parser.add_argument("-i", "--input_file", type=str, required=True)
    parser.add_argument("-o", "--output_file", type=str, required=True)
    parser.add_argument("-n", "--num_latches_to_keep", type=int, default=3)
    args = parser.parse_args()

    lines = read_file(args.input_file)

    if args.input_file.endswith(".bench"):
        simplified = simplify_bench(lines, args.num_latches_to_keep)
    else:
        simplified = simplify_blif(lines, args.num_latches_to_keep)

    write_file(args.output_file, simplified)
