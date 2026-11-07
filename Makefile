IMAGE_NAME ?= pedromol/p3d
TAG ?= latest
TORCH_INDEX_URL ?= https://download.pytorch.org/whl/cu124

.PHONY: build build-cpu push run

build:
	docker build \
		--build-arg TORCH_INDEX_URL=$(TORCH_INDEX_URL) \
		-t $(IMAGE_NAME):$(TAG) .

build-cpu:
	docker build \
		--build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu \
		-t $(IMAGE_NAME):cpu .

push:
	docker push $(IMAGE_NAME):$(TAG)

run:
	docker compose up -d
