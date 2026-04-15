#!/bin/bash
# run_experiments.sh
source "$(dirname "$0")/config.sh"

BENCH_SET=$1    # smv, iscas89, rg
PROBLEM=$2      # clique, color, hamiltonian
APPROACH=$3     # succinct, explicit
SOLVER=$4       # dqbdd, pedant, sat, popsat, ortools, cegar
K_MIN=$5        # Start range for K (color/clique size)
K_MAX=$6        # End range for K
FF_MIN=$7       # Start range for FlipFlops (latches)
FF_MAX=$8       # End range for FlipFlops

MAX_JOBS=8
TARGET_DIR="$RESULT_DIR/$BENCH_SET/$PROBLEM/$SOLVER"
CACHE_PREFIX="$CACHE_DIR/$BENCH_SET"
mkdir -p "$TARGET_DIR"

if [ "$BENCH_SET" == "smv" ]; then
    BENCH_GLOB="$SMV_DIR/benchmarks/blif/*.blif"
elif [ "$BENCH_SET" == "iscas89" ]; then
    BENCH_GLOB="$ISCAS89_DIR/benchmarks/bench/*.bench"
elif [ "$BENCH_SET" == "rg" ]; then
    BENCH_GLOB="$RG_DIR/benchmarks/blif/*.blif"
else
    echo "[Error] Unknown benchmark set: $BENCH_SET"
    exit 1
fi

run_instance() {
    local bench=$1; local ff=$2; local k=$3
    local ins=$(basename "$bench" | sed 's/\.[^.]*$//')
    local log="$TARGET_DIR/${ins}_K${k}_FF${ff}.log"

    echo "[$BENCH_SET][$PROBLEM][$APPROACH][$SOLVER] $ins (K=$k, FF=$ff)" > "$log"

    # --- Step 1: Succinct Extraction ---
    if [ "$BENCH_SET" == "rg" ]; then
        local comb_blif="$bench" # Already a succinct graph
        local abc_out=""
        local time_extract="0.0000 (Bypassed)"
    else
        local comb_blif="$CACHE_PREFIX/succinct/${ins}_FF${ff}.blif"
        local abc_out="$CACHE_PREFIX/succinct/${ins}_FF${ff}.abc"

        local start1=$(date +%s.%N)
        "$SCRIPT_DIR/01_extract_succinct.sh" "$bench" "$ff" "$comb_blif" "$abc_out" >> "$log" 2>&1
        local end1=$(date +%s.%N)

        local time_extract=$(echo "$end1 - $start1" | bc -l | awk '{printf "%.4f", $0}')
    fi

    # --- Step 2 & 3: Encoding and Solving ---
    if [ "$APPROACH" == "succinct" ]; then
        local dqdimacs="$CACHE_PREFIX/dqdimacs/${PROBLEM}/${ins}_K${k}_FF${ff}.dqdimacs"

        local start2=$(date +%s.%N)
        "$SCRIPT_DIR/03_encode_dqbf.sh" "$PROBLEM" "$comb_blif" "$k" "$dqdimacs" "$abc_out" "$BENCH_SET" "$ff" >> "$log" 2>&1
        local end2=$(date +%s.%N)
        time_encode=$(echo "$end2 - $start2" | bc -l | awk '{printf "%.4f", $0}')

        local start3=$(date +%s.%N)
        "$SCRIPT_DIR/04_solve.sh" "$SOLVER" "$dqdimacs" "$k" >> "$log" 2>&1
        local end3=$(date +%s.%N)
        time_solve=$(echo "$end3 - $start3" | bc -l | awk '{printf "%.4f", $0}')
    else
        local exp_graph="$CACHE_PREFIX/explicit/${ins}_FF${ff}.col"

        local start2=$(date +%s.%N)
        "$SCRIPT_DIR/02_extract_explicit.sh" "$comb_blif" "$ff" "$exp_graph" "$BENCH_SET" >> "$log" 2>&1
        local end2=$(date +%s.%N)
        time_encode=$(echo "$end2 - $start2" | bc -l | awk '{printf "%.4f", $0}')

        local start3=$(date +%s.%N)
        "$SCRIPT_DIR/04_solve.sh" "$SOLVER" "$exp_graph" "$k" >> "$log" 2>&1
        local end3=$(date +%s.%N)
        time_solve=$(echo "$end3 - $start3" | bc -l | awk '{printf "%.4f", $0}')
    fi

    # --- Runtime Summary ---
    echo "" >> "$log"
    echo "================ Runtime Summary ================" >> "$log"
    echo "Combinational BLIF Extraction : $time_extract s" >> "$log"
    echo "Graph Gen / DQBF Encoding     : $time_encode s" >> "$log"
    echo "$SOLVER solver execution      : $time_solve s" >> "$log"
    echo "=================================================" >> "$log"
}

for (( ff=$FF_MIN; ff<=$FF_MAX; ff++ )); do
    for (( k=$K_MIN; k<=$K_MAX; k++ )); do
        for bench in $BENCH_GLOB; do
            if [ ! -f "$bench" ]; then continue; fi

            if [[ "$BENCH_SET" == "rg" ]]; then
                # Parse $latch_num from random graph name e.g. random_graph_n3_trial0_graph.blif
                latch_num=$(basename "$bench" | sed -n 's/.*_n\([0-9]*\)_.*/\1/p')
                if (( ff != latch_num )); then continue; fi
            elif [[ "$bench" == *.blif ]]; then
                latch_num=$(grep -c '^\.latch' "$bench")
                if (( ff > latch_num )); then continue; fi
            elif [[ "$bench" == *.bench ]]; then
                latch_num=$(grep -c '= DFF' "$bench")
                if (( ff > latch_num )); then continue; fi
            else
                continue
            fi

            run_instance "$bench" "$ff" "$k" &

            while (( $(jobs -r | wc -l) >= MAX_JOBS )); do sleep 1; done
        done
    done
done
wait
