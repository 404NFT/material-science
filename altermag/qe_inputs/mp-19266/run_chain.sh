#!/bin/bash
cd /Users/a404/Documents/materialsScience/altermag/qe_inputs/mp-19266
QE=/Users/a404/Documents/materialsScience/altermag/qe-native/bin
OMPI=/opt/homebrew/opt/open-mpi/bin
rm -rf out; mkdir -p out
echo "[$(date +%H:%M:%S)] SCF start"
$OMPI/mpirun -np 8 $QE/pw.x -in scf.in > scf.out 2>&1
if ! grep -q "convergence has been achieved" scf.out; then
  echo "[$(date +%H:%M:%S)] SCF did NOT converge"; exit 1; fi
echo "[$(date +%H:%M:%S)] SCF converged. $(grep 'total magnetization' scf.out | tail -1)"
ls out/amag.save/charge-density* >/dev/null 2>&1 && echo "density saved" || { echo "no density"; exit 1; }
echo "[$(date +%H:%M:%S)] bands start"
$OMPI/mpirun -np 8 $QE/pw.x -in bands.in > bands.out 2>&1
grep -q "JOB DONE" bands.out && echo "[$(date +%H:%M:%S)] bands DONE" || echo "[$(date +%H:%M:%S)] bands ended (check bands.out)"
cd /Users/a404/Documents/materialsScience/altermag
.venv/bin/python analyze_qe.py qe_inputs --threshold 0.05 > qe_verdict.txt 2>&1
echo "[$(date +%H:%M:%S)] analysis done -> qe_verdict.txt"
