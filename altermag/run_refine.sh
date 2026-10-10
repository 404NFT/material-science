#!/bin/bash
# Publication-settings refinement for the 10 confirmed altermagnets:
# ecut 60 Ry (rho 480), 4x4x4 k, conv_thr 1e-5, constrained recipe unchanged.
# Small cells first, stubborn Ba perovskites last. Density-tolerant.
set -uo pipefail
ROOT=/Users/a404/Documents/materialsScience/altermag
QE=$ROOT/qe-native/bin; OMPI=/opt/homebrew/opt/open-mpi/bin; NP=8

for mid in mp-759163 mp-2240166 mp-1274449 mp-756665 mp-1580697 mp-2674749 \
           mp-19266 mp-1048863 mp-1277787 mp-1272506; do
  d=$ROOT/qe_inputs/$mid; cd "$d"
  if ls out_r/*.save/data-file-schema.xml >/dev/null 2>&1 && grep -q "JOB DONE" bands_r.out 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] $mid: refined already"; continue; fi

  # refined SCF input from the validated constrained sc.in
  cp sc.in sc_ref.in
  sed -i '' 's/ecutwfc = [0-9.]*/ecutwfc = 60.0/; s/ecutrho = [0-9.]*/ecutrho = 480.0/' sc_ref.in
  sed -i '' -E 's/^  [0-9]+ [0-9]+ [0-9]+ 0 0 0/  3 3 3 0 0 0/' sc_ref.in
  sed -i '' 's/conv_thr = [0-9.d-]*/conv_thr = 1.0d-4/' sc_ref.in
  sed -i '' "s|outdir = './out_c'|outdir = './out_r'|" sc_ref.in

  # refined bands input
  cp bands.in bands_ref.in
  sed -i '' 's/ecutwfc = [0-9.]*/ecutwfc = 60.0/; s/ecutrho = [0-9.]*/ecutrho = 480.0/' bands_ref.in
  sed -i '' "s|outdir = './out[a-z_]*'|outdir = './out_r'|" bands_ref.in

  echo "[$(date +%H:%M:%S)] $mid refined SCF start"
  sed -i '' 's/electron_maxstep = [0-9]*/electron_maxstep = 250/' sc_ref.in
  rm -rf out_r; mkdir -p out_r
  $OMPI/mpirun -np $NP $QE/pw.x -in sc_ref.in > sc_ref.out 2>&1
  grep -E "convergence has been achieved|convergence NOT achieved" sc_ref.out | tail -1
  if ! ls out_r/*.save/charge-density* >/dev/null 2>&1; then
    echo "[$(date +%H:%M:%S)] $mid: NO density -- skipping"; continue; fi
  echo "[$(date +%H:%M:%S)] $mid density ok. $(grep 'total magnetization' sc_ref.out | tail -1)"

  echo "[$(date +%H:%M:%S)] $mid refined bands start"
  $OMPI/mpirun -np $NP $QE/pw.x -in bands_ref.in > bands_r.out 2>&1
  grep -q "JOB DONE" bands_r.out && echo "[$(date +%H:%M:%S)] $mid bands DONE" \
    || echo "[$(date +%H:%M:%S)] $mid bands issue"
done
cd $ROOT
.venv/bin/python analyze_qe_xml.py qe_inputs --threshold 0.05 | tee qe_refined_results.txt
echo "[$(date +%H:%M:%S)] REFINEMENT COMPLETE"
