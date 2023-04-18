all: dist
.PHONY: dist
dist: venv/manifest.txt
	./venv/bin/python3 setup.py sdist bdist_wheel

.PHONY: mount
mount:
	@echo "make mount is not needed in OpenLane 2. You may simply call 'openlane --dockerized'."

.PHONY: pdk
pdk:
	@echo "make pdk is not needed in OpenLane 2."

.PHONY: openlane
openlane:
	@echo "make openlane is not needed in OpenLane 2."

.PHONY: mount
mount:
	@echo "make mount is not needed in OpenLane 2. You may simply call 'openlane --dockerized'."

.PHONY: pdk pull-openlane
pdk pull-openlane:
	@echo "This command is not needed in OpenLane 2."

.PHONY: docker-image
docker-image: venv
	$(shell nix-build docker.nix) | docker load

.PHONY: docs
docs: venv
	$(MAKE) -C docs html

.PHONY: lint
lint: venv/manifest.txt
	./venv/bin/black --check .
	./venv/bin/flake8 .
	./venv/bin/mypy .

.PHONY: test
test: venv/manifest.txt
	./venv/bin/python3 -m openlane ./designs/spm/config.json

.PHONY: test-opt
test-opt: venv/manifest.txt
	./venv/bin/python3 -m openlane -f optimizing ./designs/spm/config.json


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
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade -r ./requirements_dev.txt -r ./requirements.txt
	PYTHONPATH= yes | ./venv/bin/mypy --install-types
	PYTHONPATH= yes | ./venv/bin/mypy --install-types
	PYTHONPATH= ./venv/bin/python3 -m pip freeze > $@

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