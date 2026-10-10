#!/bin/bash
# Run the QE altermagnet-confirmation workflow LOCALLY (e.g. Mac Studio).
# For each candidate: scf -> bands. No scheduler; runs them one at a time.
#
# Prereqs (one-time):
#   brew install quantum-espresso          # provides pw.x
#   # download SSSP efficiency pseudos and put the .upf files in ./pseudos/
#   # renamed/symlinked as <Element>.upf (Fe.upf, O.upf, Sr.upf, ...).
#   # See README_qe.md and qe_inputs/pseudos_needed.txt
#
# Usage:
#   ./run_qe_local.sh [qe_inputs] [ncores]

set -euo pipefail

INDIR="${1:-qe_inputs}"
NCORES="${2:-8}"                 # M1 Max: 8 performance cores
PW="${PW:-/Users/a404/Documents/materialsScience/altermag/qe-native/bin/pw.x}"                 # override with PW=/path/to/pw.x if needed

command -v "$PW" >/dev/null || { echo "pw.x not found. brew install quantum-espresso"; exit 1; }

for d in "$INDIR"/mp-*; do
  [ -d "$d" ] || continue
  echo "============================================================"
  echo " $(basename "$d")  (started $(date '+%H:%M:%S'))"
  echo "============================================================"
  ( cd "$d" && mkdir -p out
    echo " -> scf ..."
    mpirun -np "$NCORES" "$PW" -in scf.in > scf.out 2>&1 || { echo "  scf FAILED, see $d/scf.out"; exit 1; }
    # net magnetization sanity (should be ~0 for compensated AFM)
    grep "total magnetization" scf.out | tail -1 || true
    echo " -> bands ..."
    mpirun -np "$NCORES" "$PW" -in bands.in > bands.out 2>&1 || { echo "  bands FAILED, see $d/bands.out"; exit 1; }
    echo " done $(basename "$PWD") $(date '+%H:%M:%S')"
  )
done

echo
echo "All done. Analyze with:  python analyze_qe.py $INDIR"
