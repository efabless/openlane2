FILE=./requirements_dev.txt

all: dist

.PHONY: dist
dist: venv/created
	./venv/bin/python3 setup.py sdist bdist_wheel

.PHONY: lint
lint: venv/created
	./venv/bin/black --check .
	./venv/bin/flake8 .
	./venv/bin/mypy .

venv: venv/created
venv/created: $(FILE)
	rm -rf venv
	python3 -m venv ./venv
	./venv/bin/python3 -m pip install --upgrade pip
	./venv/bin/python3 -m pip install --upgrade wheel
	./venv/bin/python3 -m pip install --upgrade -r $(FILE)
	touch venv/created

.PHONY: veryclean
veryclean: clean
veryclean:
	rm -rf venv/

.PHONY: clean
clean:
	rm -rf build/
	rm -rf logs/
	rm -rf dist/
	rm -rf *.egg-info