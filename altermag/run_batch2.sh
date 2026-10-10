#!/bin/bash
# DFT-confirm the 8 remaining altermagnet candidates: constrained-recipe SCF ->
# bands -> next. Density-tolerant (controlled maxstep stop still yields bands).
set -uo pipefail
ROOT=/Users/a404/Documents/materialsScience/altermag
QE=$ROOT/qe-native/bin; OMPI=/opt/homebrew/opt/open-mpi/bin; NP=8

for mid in mp-759163 mp-1277241 mp-2240166 mp-684727 mp-1274449 mp-756665 mp-1580697 mp-2674749; do
  d=$ROOT/qe_inputs/$mid; cd "$d"
  if ls out_c/*.save/data-file-schema.xml >/dev/null 2>&1 && grep -q "JOB DONE" bands.out 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] $mid: done already"; continue; fi

  # constrained recipe
  cp scf.in sc.in
  sed -i '' -E 's/^  [0-9]+ [0-9]+ [0-9]+ 0 0 0/  2 2 2 0 0 0/' sc.in
  sed -i '' "s/smearing = '[a-z]*'/smearing = 'mv'/; s/degauss = [0-9.]*/degauss = 0.03/" sc.in
  sed -i '' "/mixing_mode/d; /mixing_fixed_ns/d; /tot_magnetization/d" sc.in
  sed -i '' "s/mixing_beta = [0-9.]*/mixing_beta = 0.1/" sc.in
  grep -q mixing_ndim sc.in || sed -i '' '/mixing_beta/a\
  mixing_ndim = 20
' sc.in
  grep -q constrained_magnetization sc.in || sed -i '' "/nspin = 2/a\\
  constrained_magnetization = 'atomic'\\
  lambda = 0.5
" sc.in
  sed -i '' 's/conv_thr = [0-9.d-]*/conv_thr = 5.0d-4/; s/electron_maxstep = [0-9]*/electron_maxstep = 400/' sc.in
  sed -i '' "s|outdir = './out'|outdir = './out_c'|" sc.in

  echo "[$(date +%H:%M:%S)] $mid SCF start"
  rm -rf out_c; mkdir -p out_c
  $OMPI/mpirun -np $NP $QE/pw.x -in sc.in > sc.out 2>&1
  grep -E "convergence has been achieved|convergence NOT achieved" sc.out | tail -1
  if ! ls out_c/*.save/charge-density* >/dev/null 2>&1; then
    echo "[$(date +%H:%M:%S)] $mid: NO density (crash?) -- skipping"; continue; fi
  echo "[$(date +%H:%M:%S)] $mid density ok. $(grep 'total magnetization' sc.out | tail -1)"

  sed -i '' "s|outdir = './out'|outdir = './out_c'|" bands.in
  echo "[$(date +%H:%M:%S)] $mid bands start"
  $OMPI/mpirun -np $NP $QE/pw.x -in bands.in > bands.out 2>&1
  grep -q "JOB DONE" bands.out && echo "[$(date +%H:%M:%S)] $mid bands DONE" \
    || echo "[$(date +%H:%M:%S)] $mid bands issue"
done
cd $ROOT
.venv/bin/python analyze_qe_xml.py qe_inputs --threshold 0.05 | tee qe_all_results.txt
echo "[$(date +%H:%M:%S)] BATCH2 COMPLETE"
