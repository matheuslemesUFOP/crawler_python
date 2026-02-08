.PHONY: run debug test test-cov

run:
	poetry run python main.py

debug:
	poetry run python -m pdb main.py

test:
	poetry run pytest tests/ -v

test-cov:
	poetry run pytest tests/ -v --cov=crawler --cov=main --cov-report=term-missing
