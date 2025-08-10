test:
	PYTHONPATH=backend venv/bin/python -m pytest

cov:
	PYTHONPATH=backend venv/bin/python -m pytest --cov=backend --cov-report=html
