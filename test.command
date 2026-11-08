#!/bin/bash
cd "$(dirname "$0")"
test_save_dir=$(mktemp -d -t silicon-professor-tests)
trap 'rmdir "$test_save_dir" 2>/dev/null || true' EXIT
SILICON_PROFESSOR_SAVE_DIR="$test_save_dir" QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
