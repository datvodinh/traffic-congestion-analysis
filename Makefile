install-helm: ## Install Helm
	@echo "🚀 Installing Helm Chart"
	@curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
	@chmod 700 get_helm.sh
	@./get_helm.sh

add: ## Add Helm Repo for Dask and Dagster
	@echo "🚀 Add Helm Repo"
	@helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	@helm repo add grafana https://grafana.github.io/helm-charts
	@helm repo add dagster https://dagster-io.github.io/helm
	@helm repo add bitnami https://charts.bitnami.com/bitnami
	@helm repo update

upgrade: ## Upgrade Helm Repo with values.yaml file from Dagster and Dask
	@echo "🚀 Upgrade Helm Repo for Prometheus"
	@helm upgrade --install prometheus prometheus-community/prometheus -f cluster/monitoring/prometheus/values.yaml
	@echo "🚀 Upgrade Helm Repo for Grafana"
	@helm upgrade --install grafana grafana/grafana -f cluster/monitoring/grafana/values.yaml
	@echo "🚀 Upgrade Helm Repo for Dagster"
	@helm upgrade --install dagster dagster/dagster -f cluster/apps/dagster/values.yaml
	@echo "🚀 Add Dagster Configmap"
	@kubectl apply -f cluster/apps/dagster/configmap.yaml
	@echo "🚀 Upgrade Helm Repo for Spark"
	@helm upgrade --install spark bitnami/spark -f cluster/apps/spark/values.yaml
	
delete: ## Delete Helm Repo
	@echo "🚀 Delete Helm Repo for Prometheus"
	@helm delete prometheus
	@echo "🚀 Delete Helm Repo for Grafana"
	@helm delete grafana
	@echo "🚀 Delete Helm Repo for Dagster"
	@helm delete dagster
	@echo "🚀 Delete Helm Repo for Spark"
	@helm delete spark

remove: ## Remove Helm Repo
	@echo "🚀 Remove Helm Repo for Prometheus"
	@helm repo remove prometheus-community
	@echo "🚀 Remove Helm Repo for Grafana"
	@helm repo remove grafana
	@echo "🚀 Remove Helm Repo for Dagster"
	@helm repo remove dagster
	@echo "🚀 Remove Helm Repo for Dask"
	@helm repo remove dask
	@echo "🚀 Remove Helm Repo for Minio Operator"
	@helm repo remove operator

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help