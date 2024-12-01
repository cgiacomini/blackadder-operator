# Makefile for blackadder-operator

# Variables
PDOC = pdoc
DOCKER_IMAGE = blackadder-operator:0.1
DOCKERFILE = Dockerfile
SCRIPT = controller-ng.py
BUILD_DIR = html-docs
CLUSTER_NAME=singleton

# Default target
.PHONY: help

help:
	@echo "Available targets:"
	@echo "  docs    - Generate documentation using pdoc"
	@echo "  docker  - Build the Docker image"
	@echo "  clean   - Clean up the build directory"
	@echo "  load    - Load the Docker image into the kind cluster"
	@echo "  deploy  - Deploy Pods and Deployments for testing
	@echo "  all	 - Generate documentation, build the Docker image, and load it into the kind cluster"

# Targets
.PHONY: all docs docker load clean

all: docs docker load

docs:
	@echo "Generating documentation..."
	$(PDOC) --output-dir $(BUILD_DIR) $(SCRIPT)

docker:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) -f $(DOCKERFILE) .

load:
	@echo "Loading image in kind cluster $(CLUSTER_NAME)"
	kind load docker-image $(DOCKER_IMAGE) --name $(CLUSTER_NAME)

deploy:
	@echo "Deploy Pods and Deployments for testing"
	kubectl run --image docker.io/nginx test -n kube-public
	kubectl run --image docker.io/nginx test -n default
	kubectl create deployment my-dep --image=nginx --replicas=3 -n default
	echo "Deploy Controller"
	kubectl apply -f k8s/ClusterRole.yml
	kubectl apply -f k8s/ClusterRoleBinding.yml
	kubectl create -f k8s/Namespace.yml
	kubectl create -f k8s/blackadder-crd.yml
	kubectl create -f k8s/edmund-v1beta1.yml
	kubectl create -f k8s/Deployment.yml
clean:
	@echo "Cleaning up..."
	rm -rf $(BUILD_DIR)
	kubectl delete --ignore-not-found pod test -n kube-public
	kubectl delete --ignore-not-found pod test -n default
	kubectl delete --ignore-not-found deployment my-dep -n default
	echo "Deploy Controller"
	kubectl delete --ignore-not-found -f k8s/ClusterRole.yml
	kubectl delete --ignore-not-found -f k8s/ClusterRoleBinding.yml
	kubectl delete --ignore-not-found -f k8s/blackadder-crd.yml
	kubectl delete --ignore-not-found -f k8s/edmund-v1beta1.yml
	kubectl delete --ignore-not-found -f k8s/Namespace.yml
