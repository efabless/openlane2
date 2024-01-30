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
docker-image: venv
	cat $(shell nix-build docker.nix) | docker load

.PHONY: docs
docs: venv
	$(MAKE) -C docs html

.PHONY: host-docs
host-docs: venv
	./venv/bin/python3 -m http.server --directory ./docs/build/html
	
.PHONY: watch-docs
watch-docs: venv
	nodemon\
		-w .\
		-e md,py,css\
		-i "docs/build/**/*"\
		-i "docs/source/reference/*_vars.md"\
		-i "docs/source/reference/flows.md"\
		-x "$(MAKE) docs && python3 -m http.server --directory docs/build/html"

.PHONY: lint
lint: venv/manifest.txt
	./venv/bin/black --check .
	./venv/bin/flake8 .
	./venv/bin/mypy --check-untyped-defs .

.PHONY: test
test: venv/manifest.txt
	./venv/bin/coverage run -m pytest -n auto
	./venv/bin/coverage report
	./venv/bin/coverage html

.PHONY: test-all
test-all: venv/manifest.txt
	./venv/bin/coverage run -m pytest --step-rx "." -n auto
	./venv/bin/coverage report
	./venv/bin/coverage html

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
