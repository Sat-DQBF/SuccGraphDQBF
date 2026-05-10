#!/bin/bash
source "$(dirname "$0")/config.sh"
SOLVER=$1; INPUT_FILE=$2; K=$3

CMD=(timeout 1h)
case "$SOLVER" in
    dqbdd)
        CMD+=("$DQBDD_BIN" "$INPUT_FILE")
        ;;
    pedant)
        CMD+=("$PEDANT_BIN" "$INPUT_FILE" --cnf model)
        ;;
    sat)
        CMD+=(python3 "$PY_SCRIPTS_DIR/clique_sat_solver.py" -k "$K" --graph_file "$INPUT_FILE")
        ;;
    popsat)
        CMD+=(python3 "$POPSAT_BIN" --instance="$INPUT_FILE" --model=POP-S --timelimit=3600)
        ;;
    ortools)
        CMD+=(python3 "$PY_SCRIPTS_DIR/hamiltonian_solve_ortools.py" -i "$INPUT_FILE")
        ;;
    cegar)
        CMD+=("$CEGAR_FIX_BIN" -i "$INPUT_FILE" -e 1 -b 3 -t 3 -l 1)
        ;;
    generate)
        CMD+=(true)
        ;;
    *)
        echo "[Error] Unknown solver: $SOLVER"
        exit 1
        ;;
esac

# Print the command to stdout (which is redirected to the log file)
echo ""
echo "================ Solver Invocation ================"
echo "${CMD[*]}"
echo "==================================================="
echo ""

# Execute the array as a command
"${CMD[@]}"
