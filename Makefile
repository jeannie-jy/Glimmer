.PHONY: test test-unit test-integration run build-docker build-binary clean

test: test-unit test-integration

test-unit:
	python -m pytest tests/unit/ -v

test-integration:
	python -m pytest tests/integration/ -v

run:
	uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload

build-web:
	cd web && npm install && npm run build

build-docker:
	docker build -t lite-agent-harness .

build-binary:
	pyinstaller pyinstaller.spec

clean:
	rm -rf build/ dist/ __pycache__/ .pytest_cache/ web/dist/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
