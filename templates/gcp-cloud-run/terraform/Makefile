# Target a landscape with isolated state:
#   make ENV=dev plan
#   make ENV=prod apply
# Each environment gets its own state prefix, so dev/qa/uat/prod never collide.

ENV ?= dev
VARS := environments/$(ENV).tfvars
SERVICE := $(shell awk -F'"' '/service_name/ {print $$2}' $(VARS))
PREFIX := cloud-run/$(SERVICE)/$(ENV)

.PHONY: init plan apply destroy output _guard

_guard:
	@test -f $(VARS) || { echo "No tfvars for ENV=$(ENV) (expected $(VARS))"; exit 1; }

init: _guard
	terraform init -reconfigure -backend-config="prefix=$(PREFIX)"

plan: init
	terraform plan -var-file=$(VARS)

apply: init
	terraform apply -var-file=$(VARS)

destroy: init
	terraform destroy -var-file=$(VARS)

output: _guard
	terraform output
