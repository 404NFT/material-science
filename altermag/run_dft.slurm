#!/bin/bash
#SBATCH --job-name=altermag
#SBATCH --array=0-16            # 17 = 12 novel + 3 validated controls + 2 fragile
#SBATCH --nodes=1
#SBATCH --ntasks=32            # <-- EDIT: MPI ranks (match your node)
#SBATCH --time=12:00:00        # <-- EDIT: walltime per candidate
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
# #SBATCH --account=YOUR_ALLOC   # <-- EDIT/UNCOMMENT for your allocation
# #SBATCH --partition=YOUR_PART  # <-- EDIT/UNCOMMENT for your partition

# ============================================================================
# Altermagnet confirmation: per candidate run static SCF, then line-mode bands.
# Submit from the directory that contains `dft_inputs/`.  One array task per
# candidate.  After it finishes run:  python analyze_splitting.py dft_inputs
# ============================================================================

set -euo pipefail

# ---- EDIT THIS BLOCK FOR YOUR CLUSTER -------------------------------------
module purge
module load vasp/6.4.2                     # <-- EDIT: your VASP module
VASP_BIN="vasp_std"                         # <-- EDIT: VASP executable
MPIRUN="srun"                              # <-- EDIT: srun / mpirun / mpiexec
# pymatgen must know where the VASP pseudopotentials live so POTCARs can be
# built from the POTCAR.spec files written by prep_dft.py. Set this once with
#   pmg config -p /path/to/POT_GGA_PAW_PBE <your_psp_root>
#   pmg config --add PMG_VASP_PSP_DIR <your_psp_root> PMG_DEFAULT_FUNCTIONAL PBE
PYTHON="${PYTHON:-python}"                  # <-- EDIT: python with pymatgen
# ---------------------------------------------------------------------------

mkdir -p logs
INDIR="dft_inputs"

# Pick this task's candidate (sorted, stable order).
mapfile -t CANDS < <(find "$INDIR" -maxdepth 1 -mindepth 1 -type d | sort)
CAND="${CANDS[$SLURM_ARRAY_TASK_ID]}"
echo "=== Candidate: $CAND  (task $SLURM_ARRAY_TASK_ID) ==="

# Build a real POTCAR from POTCAR.spec in a given dir (idempotent).
make_potcar () {
  local d="$1"
  if [[ -f "$d/POTCAR" ]]; then return; fi
  ( cd "$d" && "$PYTHON" - <<'PY'
from pymatgen.io.vasp.inputs import Potcar
syms = [l.strip() for l in open("POTCAR.spec") if l.strip()]
Potcar(symbols=syms, functional="PBE").write_file("POTCAR")
print("wrote POTCAR:", syms)
PY
  )
}

run_vasp () {
  local d="$1"
  echo "--- VASP in $d ---"
  ( cd "$d" && $MPIRUN "$VASP_BIN" )
}

# ---- 1) Static spin-polarized SCF ----------------------------------------
make_potcar "$CAND/static"
run_vasp    "$CAND/static"

# Sanity: report net magnetization (should be ~0 for a compensated AFM).
grep -E "number of electron" "$CAND/static/OUTCAR" | tail -1 || true

# ---- 2) Line-mode band structure (reuse converged charge density) --------
make_potcar "$CAND/bands"
cp "$CAND/static/CHGCAR" "$CAND/bands/CHGCAR"
# ICHARG=11 = non-self-consistent bands from fixed CHGCAR.
if grep -q "^ *ICHARG" "$CAND/bands/INCAR"; then
  sed -i 's/^ *ICHARG.*/ICHARG = 11/' "$CAND/bands/INCAR"
else
  echo "ICHARG = 11" >> "$CAND/bands/INCAR"
fi
run_vasp "$CAND/bands"

echo "=== DONE: $CAND ==="
