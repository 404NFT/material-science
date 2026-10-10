#!/bin/bash
# Run the full altermagnet-confirmation chain (SCF -> bands) for EVERY QE
# candidate, natively, using the convergence recipe learned for correlated
# oxides. Skips candidates already done (out/*.save XML present). Detached-safe.
#
# Usage:  nohup ./run_all_qe.sh > all_qe.log 2>&1 &
set -uo pipefail

ROOT=/Users/a404/Documents/materialsScience/altermag
QE=$ROOT/qe-native/bin
OMPI=/opt/homebrew/opt/open-mpi/bin
NP=8

for d in "$ROOT"/qe_inputs/mp-*; do
  [ -d "$d" ] || continue
  mid=$(basename "$d")
  cd "$d"

  # already analyzed? skip.
  if ls out/*.save/data-file-schema.xml >/dev/null 2>&1 && grep -q "JOB DONE" bands.out 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] $mid: already done, skipping"
    continue
  fi

  # convergence recipe for correlated oxides (idempotent edits)
  sed -i '' 's/mixing_beta = 0.[0-9]*/mixing_beta = 0.1/' scf.in
  grep -q "mixing_mode" scf.in || sed -i '' "/mixing_beta/a\\
  mixing_mode = 'local-TF'
" scf.in
  sed -i '' 's/conv_thr = [0-9.d-]*/conv_thr = 2.0d-4/' scf.in
  sed -i '' 's/electron_maxstep = [0-9]*/electron_maxstep = 300/' scf.in

  echo "============================================================"
  echo "[$(date +%H:%M:%S)] $mid: SCF start"
  rm -rf out; mkdir -p out
  $OMPI/mpirun -np $NP $QE/pw.x -in scf.in > scf.out 2>&1
  if ! grep -q "convergence has been achieved" scf.out; then
    echo "[$(date +%H:%M:%S)] $mid: SCF did NOT converge (see scf.out) -- skipping bands"
    continue
  fi
  echo "[$(date +%H:%M:%S)] $mid: SCF converged. $(grep 'total magnetization' scf.out | tail -1)"
  ls out/*.save/charge-density* >/dev/null 2>&1 || { echo "[$(date +%H:%M:%S)] $mid: no density saved"; continue; }

  echo "[$(date +%H:%M:%S)] $mid: bands start"
  $OMPI/mpirun -np $NP $QE/pw.x -in bands.in > bands.out 2>&1
  grep -q "JOB DONE" bands.out && echo "[$(date +%H:%M:%S)] $mid: bands DONE" \
    || echo "[$(date +%H:%M:%S)] $mid: bands ended (check bands.out)"
done

echo "============================================================"
echo "[$(date +%H:%M:%S)] all candidates processed. Analyzing..."
cd "$ROOT"
.venv/bin/python analyze_qe_xml.py qe_inputs --threshold 0.05 | tee qe_all_results.txt
echo "[$(date +%H:%M:%S)] DONE -> qe_all_results.txt / qe_results.csv"
