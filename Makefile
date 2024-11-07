install-helm: ## Install Helm
	@echo "🚀 Installing Helm Chart"
	@curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
	@chmod 700 get_helm.sh
	@./get_helm.sh

add-repo: ## Add Helm Repo for Dask and Dagster
	@echo "🚀 Add Helm Repo for Dask and Dagster"
	@helm repo add dagster https://dagster-io.github.io/helm
	@helm repo add dask https://helm.dask.org/

upgrade-repo: ## Upgrade Helm Repo with values.yaml file from Dagster and Dask
	@echo "🚀 Upgrade Helm Repo for Dagster"
	@helm upgrade --install dagster dagster/dagster -f cluster/dagster/values.yaml
	@echo "🚀 Upgrade Helm Repo for Dask"
	@helm upgrade --install dask dask/dask -f cluster/dask/values.yaml

delete-repo: ## Delete Helm Repo
	@echo "🚀 Delete Helm Repo for Dagster"
	@helm delete dagster
	@echo "🚀 Delete Helm Repo for Dask"
	@helm delete dask

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help