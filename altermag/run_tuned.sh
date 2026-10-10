#!/bin/bash
# Two-stage annealed SCF -> bands for the remaining QE candidates.
# Stage 1: high smearing + very gentle mixing, loose threshold (find the basin)
# Stage 2: restart from stage-1 density/wfc, normal smearing, target threshold
set -uo pipefail
ROOT=/Users/a404/Documents/materialsScience/altermag
QE=$ROOT/qe-native/bin; OMPI=/opt/homebrew/opt/open-mpi/bin; NP=8

prep_common () { # $1=file
  # uniform k-grid (no 1-k directions destabilizing the magnetic SCF)
  sed -i '' -E 's/^  [0-9]+ [0-9]+ [0-9]+ 0 0 0/  2 2 2 0 0 0/' "$1"
  sed -i '' "s/smearing = '[a-z]*'/smearing = 'mv'/" "$1"
  sed -i '' "/mixing_mode/d" "$1"
  grep -q mixing_ndim "$1" || sed -i '' '/mixing_beta/a\
  mixing_ndim = 20
' "$1"
}

for mid in mp-1277787 mp-1048863 mp-1272506; do
  d=$ROOT/qe_inputs/$mid; cd "$d"
  if ls out/*.save/data-file-schema.xml >/dev/null 2>&1 && grep -q "JOB DONE" bands.out 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] $mid: done already"; continue; fi
  rm -rf out; mkdir -p out

  # ---- stage 1: anneal ----
  cp scf.in s1.in; prep_common s1.in
  sed -i '' 's/degauss = [0-9.]*/degauss = 0.05/'                       s1.in
  sed -i '' 's/mixing_beta = [0-9.]*/mixing_beta = 0.05/'               s1.in
  sed -i '' 's/conv_thr = [0-9.d-]*/conv_thr = 1.0d-3/'                 s1.in
  sed -i '' 's/electron_maxstep = [0-9]*/electron_maxstep = 200/'       s1.in
  grep -q mixing_fixed_ns s1.in || sed -i '' '/mixing_beta/a\
  mixing_fixed_ns = 30
' s1.in
  echo "[$(date +%H:%M:%S)] $mid stage1 (anneal, ns frozen 30 it) start"
  $OMPI/mpirun -np $NP $QE/pw.x -in s1.in > s1.out 2>&1
  grep -q "convergence has been achieved" s1.out \
    || { echo "[$(date +%H:%M:%S)] $mid stage1 FAILED"; continue; }
  echo "[$(date +%H:%M:%S)] $mid stage1 ok. $(grep 'total magnetization' s1.out | tail -1)"

  # ---- stage 2: refine from stage-1 density ----
  cp scf.in s2.in; prep_common s2.in
  sed -i '' 's/degauss = [0-9.]*/degauss = 0.02/'                       s2.in
  sed -i '' 's/mixing_beta = [0-9.]*/mixing_beta = 0.1/'                s2.in
  sed -i '' 's/conv_thr = [0-9.d-]*/conv_thr = 2.0d-4/'                 s2.in
  sed -i '' 's/electron_maxstep = [0-9]*/electron_maxstep = 200/'       s2.in
  sed -i '' "/&ELECTRONS/a\\
  startingpot = 'file'\\
  startingwfc = 'file'
" s2.in
  echo "[$(date +%H:%M:%S)] $mid stage2 (refine) start"
  $OMPI/mpirun -np $NP $QE/pw.x -in s2.in > scf.out 2>&1
  grep -q "convergence has been achieved" scf.out \
    || { echo "[$(date +%H:%M:%S)] $mid stage2 FAILED"; continue; }
  echo "[$(date +%H:%M:%S)] $mid stage2 ok. $(grep 'total magnetization' scf.out | tail -1)"

  # ---- bands ----
  prep_common bands.in 2>/dev/null || true
  echo "[$(date +%H:%M:%S)] $mid bands start"
  $OMPI/mpirun -np $NP $QE/pw.x -in bands.in > bands.out 2>&1
  grep -q "JOB DONE" bands.out && echo "[$(date +%H:%M:%S)] $mid bands DONE" \
    || echo "[$(date +%H:%M:%S)] $mid bands ended (check)"
done
cd $ROOT
.venv/bin/python analyze_qe_xml.py qe_inputs --threshold 0.05 | tee qe_all_results.txt
