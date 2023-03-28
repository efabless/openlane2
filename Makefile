all: dist
.PHONY: dist
dist: venv/created
	./venv/bin/python3 setup.py sdist bdist_wheel

.PHONY: openlane
openlane:
	@echo "make openlane is deprecated. Please use make docker-image."
	@echo "----"
	@$(MAKE) docker-image

.PHONY: docker-image
docker-image: venv
	$(shell nix-build docker.nix) | docker load

.PHONY: docs
docs: venv
	$(MAKE) -C docs html

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
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade pip
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade wheel
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade -r ./requirements_dev.txt -r ./requirements.txt
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