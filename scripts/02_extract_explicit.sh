#!/bin/bash
source "$(dirname "$0")/config.sh"
IN_COMB_BLIF=$1; LATCHES=$2; OUT_EXPLICIT_GRAPH=$3; BENCH_SET=$4

mkdir -p "$(dirname "$OUT_EXPLICIT_GRAPH")"
LOCK_FILE="${OUT_EXPLICIT_GRAPH}.lock"

(
    flock -x 9

    if [ -f "$OUT_EXPLICIT_GRAPH" ]; then
        echo "[Cache Hit] Explicit graph already exists: $OUT_EXPLICIT_GRAPH"
        exit 0
    fi

    TMP_EXP_GRAPH=$(mktemp --suffix=.col)

    if [ "$BENCH_SET" == "rg" ]; then
        RG_FLAG="--rg"
    else
        RG_FLAG=""
    fi

    if python3 "$PY_SCRIPTS_DIR/explicit_gen.py" -b "$IN_COMB_BLIF" --ff "$LATCHES" \
        --explicit_graph_output "$TMP_EXP_GRAPH" --abc_bin "$ABC_BIN" --cache_dir "$CACHE_DIR" "$RG_FLAG"; then

        mv "$TMP_EXP_GRAPH" "$OUT_EXPLICIT_GRAPH"
    else
        echo "[Error/Skip] Explicit graph generation failed or was skipped."
    fi

    rm -f "$TMP_EXP_BLIF" "$TMP_EXP_GRAPH"

) 9> "$LOCK_FILE"
