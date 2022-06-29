IMAGE_PARTY_NAME = party_bot
IMAGE_HOLIDAY_NAME = holiday_bot
IMAGE_PARTY_FILE = ./Dockerfile.party_bot
IMAGE_HOLIDAY_FILE = ./Dockerfile.holiday_bot
LAMBDA_CODE = .

build-party-lambda:
	docker build -f $(IMAGE_PARTY_FILE) -t $(IMAGE_PARTY_NAME) $(LAMBDA_CODE)

remove-party-build:
	docker rmi $(IMAGE_PARTY_NAME)

remove-party-build-no-fail:
	$(MAKE) remove-party-build || true

run-party-lambda:
	docker run --rm -p 9001:8080 $(IMAGE_PARTY_NAME)
	
party-bot-build-and-run: remove-party-build-no-fail build-party-lambda run-party-lambda

test-party-lambda:
	curl -XPOST "http://localhost:9001/2015-03-31/functions/function/invocations" -d '{}'

build-holiday-lambda:
	docker build -f $(IMAGE_HOLIDAY_FILE) -t $(IMAGE_HOLIDAY_NAME) $(LAMBDA_CODE)

remove-holiday-build:
	docker rmi $(IMAGE_HOLIDAY_NAME)

remove-holiday-build-no-fail:
	$(MAKE) remove-holiday-build || true

run-holiday-lambda:
	docker run --rm -p 9001:8080 $(IMAGE_HOLIDAY_NAME)
	
holiday-bot-build-and-run: remove-holiday-build-no-fail build-holiday-lambda run-holiday-lambda

test-holiday-lambda:
	curl -XPOST "http://localhost:9001/2015-03-31/functions/function/invocations" -d '{}'

