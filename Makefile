.PHONY: run debug

run:
	poetry run python main.py

debug:
	poetry run python -m pdb main.py
