# The AI Canon — task runner.
#
# We run modules with PYTHONPATH=src rather than an editable install: the
# editable .pth/finder is honored only intermittently when the venv lives under
# ~/Desktop (macOS file-access mediation), whereas PYTHONPATH is deterministic.
# pytest reads `pythonpath = src` from pyproject.toml, so tests need no install.

PY ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: install ingest score test guard all

install:
	$(PY) -m pip install -q pydantic openpyxl pyyaml pytest

ingest:
	$(PY) -m canon.ingest

score:
	$(PY) -m canon.score --fixtures --scenario academic --work-type book

test:
	$(PY) -m pytest -q

guard:
	bash scripts/guard_no_trackers.sh

all: guard test
