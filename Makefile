all: dist
.PHONY: dist
dist: venv/manifest.txt
	./venv/bin/python3 setup.py sdist bdist_wheel

.PHONY: mount
mount:
	@echo "make mount is not needed in OpenLane 2+. You may simply call 'openlane --dockerized'."

.PHONY: pdk pull-openlane
pdk pull-openlane:
	@echo "OpenLane 2+ will automatically pull PDKs and/or Docker containers when it needs them."

.PHONY: openlane
openlane:
	@echo "make openlane is deprecated. Please use make docker-image."
	@echo "----"
	@$(MAKE) docker-image

.PHONY: docker-image
docker-image:
	cat $(shell nix build --no-link --print-out-paths .#openlane-docker -L --verbose) | docker load

.PHONY: docs
docs:
	$(MAKE) -C docs html

.PHONY: host-docs
host-docs:
	python3 -m http.server --directory ./docs/build/html
	
.PHONY: watch-docs
watch-docs:
	nodemon\
		-w .\
		-e md,py,css\
		-i "docs/build/**/*"\
		-i "docs/build/*"\
		-i "docs/source/reference/*_vars.md"\
		-i "docs/source/reference/flows.md"\
		-x "$(MAKE) docs && python3 -m http.server --directory docs/build/html"

.PHONY: lint
lint:
	black --check .
	flake8 .
	mypy --check-untyped-defs .

.PHONY: coverage-infrastructure
coverage-infrastructure:
	python3 -m pytest -n auto\
		--cov=openlane --cov-config=.coveragerc --cov-report html:htmlcov_infra --cov-report term

.PHONY: coverage-steps
coverage-steps:
	python3 -m pytest -n auto\
		--cov=openlane.steps --cov-config=.coveragerc-steps --cov-report html:htmlcov_steps --cov-report term\
		--step-rx "." -k test_all_steps

.PHONY: check-license
check-license: venv/manifest.txt
	./venv/bin/python3 -m pip freeze > ./requirements.frz.txt
	docker run -v `pwd`:/volume \
		-it --rm pilosus/pip-license-checker \
		java -jar app.jar \
		--requirements '/volume/requirements.frz.txt'

venv: venv/manifest.txt
venv/manifest.txt: ./requirements_dev.txt ./requirements.txt
	rm -rf venv
	python3 -m venv ./venv
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade pip
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade wheel
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade -r ./requirements_dev.txt
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade -r ./requirements.txt
	PYTHONPATH= ./venv/bin/python3 -m pip freeze > $@
	@echo ">> Venv prepared. To install documentation dependencies, invoke './venv/bin/python3 -m pip install --upgrade -r requirements_docs.txt'"

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
	rm -rf test_data/designs/*/runs
	rm -rf test/designs/*/runs
