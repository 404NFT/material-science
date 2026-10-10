#!/bin/bash
# Hypothetical CaBa2FeMoO5 in the Sr3Fe2O5 (Immm two-leg-ladder) structure.
# Waits for the Ba2FeMoO6 batch (run.sh) to finish so the two don't fight for cores.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
QE=/Users/a404/Documents/materialsScience/altermag/qe-native/bin
OMPI=/opt/homebrew/opt/open-mpi/bin; NP=8
PY=/Users/a404/Documents/materialsScience/altermag/.venv/bin/python; [ -x "$PY" ] || PY=python3
while /usr/bin/pgrep -f "bash run.sh" >/dev/null; do sleep 60; done
echo "[$(date +%H:%M:%S)] vc-relax start"
grep -q "End final coordinates" relax.out 2>/dev/null || \
  $OMPI/mpirun -np $NP $QE/pw.x -in relax.in > relax.out 2>&1
grep -E "bfgs converged|The maximum number of steps has been reached|End final coordinates" relax.out | tail -2
$PY post_relax.py || { echo "relax failed -- stopping"; exit 1; }
for c in fim fm nm; do
  cd "$HERE/$c"
  echo "[$(date +%H:%M:%S)] $c scf"
  $OMPI/mpirun -np $NP $QE/pw.x -in scf.in > scf.out 2>&1
  grep -E "convergence has been achieved|convergence NOT achieved" scf.out | tail -1
  if [ -f nscf.in ] && grep -q "convergence has been achieved" scf.out; then
    echo "[$(date +%H:%M:%S)] $c nscf + dos"
    $OMPI/mpirun -np $NP $QE/pw.x -in nscf.in > nscf.out 2>&1
    $OMPI/mpirun -np 1 $QE/dos.x -in dos.in > dos.out 2>&1
  fi
done
cd "$HERE"; $PY analyze.py | tee results.txt
