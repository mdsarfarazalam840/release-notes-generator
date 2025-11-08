.PHONY: build docker-run zip

build:
	pip install -r requirements.txt

docker-build:
	docker build -t release-notes-generator:latest -f docker/Dockerfile .

docker-run:
	docker run --env-file .env -v $(PWD):/app release-notes-generator:latest

zip:
	python3 build_zip.py
