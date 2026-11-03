.PHONY: setup test smoke videos

setup:
	python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]"

test:
	.venv/bin/pytest -q

smoke:
	.venv/bin/python scripts/smoke_test_roi.py

videos:
	bash scripts/download_videos.sh
