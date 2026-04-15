#!/bin/bash
source "$(dirname "$0")/config.sh"
PROBLEM=$1; IN_COMB_BLIF=$2; K=$3; OUT_DQDIMACS=$4; ABC_OUT=$5; BENCH_SET=$6; LATCHES=$7

mkdir -p "$(dirname "$OUT_DQDIMACS")"
LOCK_FILE="${OUT_DQDIMACS}.lock"

(
    flock -x 9

    if [ -f "$OUT_DQDIMACS" ]; then
        echo "[Cache Hit] DQDIMACS already exists: $OUT_DQDIMACS"
        exit 0
    fi

    if [ "$BENCH_SET" == "rg" ]; then
        RG_FLAG="--rg --ff $LATCHES"
        ABC_ARG="--abc /dev/null"
    else
        RG_FLAG=""
        ABC_ARG="--abc $ABC_OUT"
    fi

    TMP_BLIF=$(mktemp --suffix=.blif)
    TMP_CNF=$(mktemp --suffix=.cnf)
    TMP_DQDIMACS=$(mktemp --suffix=.dqdimacs)

    SUCCESS=false

    case "$PROBLEM" in
        clique)
            if python3 "$PY_SCRIPTS_DIR/blif_gen_clique.py" -i "$IN_COMB_BLIF" -o "$TMP_BLIF" -c "$K" $ABC_ARG $RG_FLAG && \
               python3 "$ABC_DQBF_DIR/smv_convert_to_cnf_clique.py" -i "$TMP_BLIF" -c "$TMP_CNF" -d "$TMP_DQDIMACS"; then
               SUCCESS=true
            fi
            ;;
        color)
            if python3 "$PY_SCRIPTS_DIR/blif_gen_coloring.py" -i "$IN_COMB_BLIF" -o "$TMP_BLIF" -c "$K" $ABC_ARG $RG_FLAG && \
               python3 "$ABC_DQBF_DIR/smv_convert_to_cnf.py" -i "$TMP_BLIF" -c "$TMP_CNF" -d "$TMP_DQDIMACS"; then
               SUCCESS=true
            fi
            ;;
        hamiltonian)
            if python3 "$PY_SCRIPTS_DIR/blif_gen_hamiltonian.py" -i "$IN_COMB_BLIF" -o "$TMP_BLIF" $ABC_ARG $RG_FLAG && \
               python3 "$ABC_DQBF_DIR/smv_convert_to_cnf_hamiltonian.py" -i "$TMP_BLIF" -c "$TMP_CNF" -d "$TMP_DQDIMACS"; then
               SUCCESS=true
            fi
            ;;
    esac

    if [ "$SUCCESS" = true ]; then
        mv "$TMP_DQDIMACS" "$OUT_DQDIMACS"
    else
        echo "[Error/Skip] DQBF Encoding failed."
    fi

    rm -f "$TMP_BLIF" "$TMP_CNF" "$TMP_DQDIMACS"

) 9> "$LOCK_FILE"
