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


.PHONY: check-license
check-license: venv/created
	./venv/bin/python3 -m pip freeze > ./requirements.frz.txt
	docker run -v `pwd`:/volume \
		-it --rm pilosus/pip-license-checker \
		java -jar app.jar \
		--requirements '/volume/requirements.frz.txt'

venv: venv/created
venv/created: ./requirements_dev.txt requirements.txt
	rm -rf venv
	python3 -m venv ./venv
	./venv/bin/python3 -m pip install --upgrade pip
	./venv/bin/python3 -m pip install --upgrade wheel
	./venv/bin/python3 -m pip install --upgrade -r ./requirements_dev.txt -r ./requirements.txt
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