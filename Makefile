install:
	pip install --upgrade pip && \
	pip install -r requirements.txt

lint:
	pylint --disable=R,C *.py

test:
	python -m pytest -vv --cov=. test_*.py

format:
	black *.py

build:
	docker build -t advisor-app .

deploy:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com
	docker build -t advisor-app .
	docker tag advisor-app:latest $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/advisor-app:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com/advisor-app:latest

run:
	streamlit run adviseme.py --server.port 8501

all: install lint format build

.PHONY: install lint test format build deploy run all
