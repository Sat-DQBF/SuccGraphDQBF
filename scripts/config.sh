#!/bin/bash
# config.sh - Centralized path and environment configuration

# Resolve directories relative to this script's location (./scripts)
export SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export ISCAS89_DIR="${ISCAS89_DIR:-$ROOT_DIR/iscas89}"
export SMV_DIR="${SMV_DIR:-$ROOT_DIR/smv}"
export RG_DIR="${RG_DIR:-$ROOT_DIR/rg}"

# Working Directories
export RESULT_DIR="${RESULT_DIR:-$ROOT_DIR/result}"
export CACHE_DIR="${CACHE_DIR:-$ROOT_DIR/cache}"
export PY_SCRIPTS_DIR="${PY_SCRIPTS_DIR:-$SCRIPT_DIR}"

# External Binaries & Tools
export ABC_BIN="${ABC_BIN:-$ROOT_DIR/abc/abc}"
export ABC_DQBF_DIR="${ABC_DQBF_DIR:-$ROOT_DIR/abc/dqbf}"
export DQBDD_BIN="${DQBDD_BIN:-$ROOT_DIR/DQBDD/Release/src/dqbdd}"
export PEDANT_BIN="${PEDANT_BIN:-$ROOT_DIR/pedant-solver/build/src/pedant}"
export CEGAR_FIX_BIN="${CEGAR_FIX_BIN:-$ROOT_DIR/SAT-based-CEGAR/src/cegar-fix/target/release/cegar-fix}"
export POPSAT_BIN="${POPSAT_BIN:-$ROOT_DIR/popsatgcpbcp/source/main.py}"
