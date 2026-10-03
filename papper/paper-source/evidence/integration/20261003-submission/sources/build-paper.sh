#!/usr/bin/env bash
set -eu
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$HERE/../../../.." && pwd)
export TEXINPUTS="$HERE:$ROOT/levels_tex:"
export BSTINPUTS="$HERE:"
export BIBINPUTS="$ROOT:"
cd "$ROOT/levels_tex"
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$HERE/../build" samplepaper.tex
cp "$HERE/../build/samplepaper.pdf" "$HERE/../MoNoTeC-2026-paper.pdf"
