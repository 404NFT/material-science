#!/bin/bash
# Build Quantum ESPRESSO NATIVELY for Apple Silicon (arm64) -- no Rosetta.
#
# The micromamba QE we used earlier is an Intel binary under Rosetta 2 (~2x slow).
# There is no prebuilt arm64 QE package, so we compile from source against
# Homebrew's native ARM gfortran/open-mpi/fftw. Result: pw.x running at full
# M1/M2/M3 speed.
#
# Usage:
#   ./build_qe_native.sh            # builds into ./qe-native
#   PW=./qe-native/bin/pw.x         # the native binary it produces
#
# Time: ~15-30 min (mostly the compile). Needs Xcode command line tools + brew.

set -euo pipefail

QE_VER="7.3.1"                        # QE release to build
PREFIX="$PWD/qe-native"
SRC="$PWD/.qe-src"

echo "=== 1. Native ARM toolchain via Homebrew ==="
# open-mpi + fftw, plus gcc@13 (gfortran 13). The DEFAULT brew gcc is gfortran 16,
# which is too new for QE's bundled MBD library (Fortran/C interop errors). We
# keep Homebrew open-mpi but point its Fortran backend at gfortran-13 via OMPI_FC,
# so we get MPI parallelism AND a compiler QE actually builds with.
for pkg in gcc@13 open-mpi fftw; do
  brew list --versions "$pkg" >/dev/null 2>&1 || brew install "$pkg"
done

GF13="$(brew --prefix gcc@13)/bin/gfortran-13"
GCC13="$(brew --prefix gcc@13)/bin/gcc-13"
[ -x "$GF13" ] || { echo "gfortran-13 not found at $GF13"; exit 1; }
echo "  using $($GF13 --version | head -1)"

# make mpif90/mpicc use gcc@13 underneath instead of the default gfortran 16
export OMPI_FC="$GF13" OMPI_CC="$GCC13"
MPIF90="$(brew --prefix open-mpi)/bin/mpif90"
MPICC="$(brew --prefix open-mpi)/bin/mpicc"
"$MPIF90" --showme:command | grep -q gfortran-13 \
  && echo "  mpif90 -> gfortran-13 ✔" || echo "  (mpif90 backend: $($MPIF90 --showme:command))"
export F90="$MPIF90"

echo "=== 2. Fetch QE $QE_VER source ==="
mkdir -p "$SRC"; cd "$SRC"
TARBALL="q-e-qe-$QE_VER.tar.gz"
if [ ! -f "$TARBALL" ]; then
  curl -L -o "$TARBALL" \
    "https://gitlab.com/QEF/q-e/-/archive/qe-$QE_VER/q-e-qe-$QE_VER.tar.gz"
fi
# fresh tree (a prior failed build left objects from the wrong compiler)
rm -rf "q-e-qe-$QE_VER"
tar xzf "$TARBALL"
cd "q-e-qe-$QE_VER"

echo "=== 3. Configure (native arm64, FFTW, BLAS via Accelerate) ==="
# --with-internal for libxc off; use system Accelerate for BLAS/LAPACK (fast on
# Apple Silicon), Homebrew FFTW for FFTs, open-mpi for parallelism.
./configure \
  MPIF90="$MPIF90" F90="$MPIF90" CC="$MPICC" \
  --enable-parallel \
  --with-scalapack=no \
  BLAS_LIBS="-framework Accelerate" \
  LAPACK_LIBS="-framework Accelerate" \
  FFT_LIBS="-L$(brew --prefix fftw)/lib -lfftw3" \
  CFLAGS="-D__FFTW3 -I$(brew --prefix fftw)/include" \
  FFLAGS="-O3 -fallow-argument-mismatch -fallow-invalid-boz -I$(brew --prefix fftw)/include"

echo "=== 3b. Patch make.inc for macOS + modern-gfortran quirks ==="
# (i) FFTW3 backend macro must be in the *Fortran* DFLAGS (our manual FFT_LIBS
#     override suppresses configure's auto-detect -> 'No fft_scalar backend').
grep -q -- '-D__FFTW3' <(grep '^DFLAGS' make.inc) || \
  sed -i.bak1 '/^DFLAGS *=/ s/$/ -D__FFTW3/' make.inc
# (ii) Apple's clang `cpp` mishandles QE header generation ('cc: no input
#      files'); use GNU cpp from gcc@13 instead.
CPP13="$(brew --prefix gcc@13)/bin/cpp-13"
sed -i.bak2 "s|^CPP  *=.*|CPP            = $CPP13|" make.inc
grep -E '^DFLAGS|^CPP ' make.inc

echo "=== 4. Build pw.x (and postprocessing) ==="
# The FFTW3 backend object must be compiled (with -D__FFTW3 active) BEFORE
# fft_scalar.o, else its module is empty and the parallel build races/fails.
# Build it explicitly first, then parallelize the rest.
( cd FFTXlib/src && make fft_scalar.FFTW3.o ) || true
make -j"$(sysctl -n hw.perflevel0.physicalcpu)" pw pp

echo "=== 5. Install ==="
mkdir -p "$PREFIX/bin"
cp bin/pw.x bin/bands.x bin/dos.x "$PREFIX/bin/" 2>/dev/null || cp bin/pw.x "$PREFIX/bin/"

echo
echo "Native QE built:"
"$PREFIX/bin/pw.x" -h 2>&1 | head -3 || true
echo
echo "Use it with:"
echo "  QE=$PREFIX/bin"
echo "  \$(brew --prefix)/bin/mpirun -np 8 \$QE/pw.x -in scf.in"
echo
echo "Compare speed vs the Rosetta build on a small cell before committing to a run."
