IMAGE_NAME = lambda
LAMBDA_CODE = .

build-lambda:
	docker build -t $(IMAGE_NAME) $(LAMBDA_CODE)

remove-build:
	docker rmi $(IMAGE_NAME)

remove-build-no-fail:
	$(MAKE) remove-build || true

build-and-run: remove-build-no-fail build-lambda run-lambda

run-lambda:
	docker run --rm -p 9000:8080 $(IMAGE_NAME)

test-lambda:
	curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'

login-ecr:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(IMAGE_NAME)

push-ecr:
	docker push $(IMAGE_NAME)
