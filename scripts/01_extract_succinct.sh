#!/bin/bash
source "$(dirname "$0")/config.sh"
IN_FILE=$1; LATCHES=$2; OUT_COMB_BLIF=$3; ABC_OUT=$4

mkdir -p "$(dirname "$OUT_COMB_BLIF")"
LOCK_FILE="${OUT_COMB_BLIF}.lock"
EXT="${IN_FILE##*.}"

(
    flock -x 9

    if [ -f "$OUT_COMB_BLIF" ] && [ -f "$ABC_OUT" ]; then
        echo "[Cache Hit] Combinational BLIF and ABC log already exist: $OUT_COMB_BLIF"
        exit 0
    fi

    TMP_SIMP=$(mktemp --suffix=.$EXT)
    TMP_COMB=$(mktemp --suffix=.blif)
    TMP_ABC=$(mktemp --suffix=.abc)

    if python3 "$PY_SCRIPTS_DIR/simplify_circuit.py" -i "$IN_FILE" -o "$TMP_SIMP" -n "$LATCHES" && \
       python3 "$PY_SCRIPTS_DIR/to_combinational_blif.py" -i "$TMP_SIMP" -o "$TMP_COMB" --abc_out "$TMP_ABC" --abc_bin "$ABC_BIN"; then

        mv "$TMP_COMB" "$OUT_COMB_BLIF"
        mv "$TMP_ABC" "$ABC_OUT"
    else
        echo "[Error/Skip] Succinct graph extraction failed."
    fi

    rm -f "$TMP_SIMP" "$TMP_COMB" "$TMP_ABC"

) 9> "$LOCK_FILE"
