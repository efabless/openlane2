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

.PHONY: test
test: venv/created
	./venv/bin/python3 -m openlane ./designs/spm/config.json

.PHONY: test-opt
test-opt: venv/created
	./venv/bin/python3 -m openlane -f optimizing ./designs/spm/config.json


venv: venv/created
venv/created: $(FILE) requirements_lint.txt requirements.txt
	rm -rf venv
	python3 -m venv ./venv
	./venv/bin/python3 -m pip install --upgrade pip
	./venv/bin/python3 -m pip install --upgrade wheel
	./venv/bin/python3 -m pip install --upgrade -r $(FILE)
	./venv/bin/python3 -m pip install .
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
	rm -rf designs/*/runs