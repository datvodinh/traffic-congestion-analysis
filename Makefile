install-helm: ## Install Helm
	@echo "🚀 Installing Helm Chart"
	@curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
	@chmod 700 get_helm.sh
	@./get_helm.sh

add-repo: ## Add Helm Repo for all Service
	@echo "🚀 Add Helm Repo"
	@helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	@helm repo add grafana https://grafana.github.io/helm-charts
	@helm repo add dagster https://dagster-io.github.io/helm
	@helm repo add dask https://helm.dask.org/
	@helm repo add bitnami https://charts.bitnami.com/bitnami
	@helm repo add superset http://apache.github.io/superset/
	@helm repo update

delete-repo: ## Remove Helm Repo
	@echo "🗑️ Remove Helm Repo for Prometheus"
	@helm repo remove prometheus-community
	@echo "🗑️ Remove Helm Repo for Grafana"
	@helm repo remove grafana
	@echo "🗑️ Remove Helm Repo for Dagster"
	@helm repo remove dagster
	@echo "🗑️ Remove Helm Repo for dask"
	@helm repo remove dask
	@echo "🗑️ Remove Helm Repo for ClickHouse"
	@helm repo remove clickhouse

up: ## Apply all Service to Kubernetes
	@echo "🚀 Upgrade Helm Repo for Prometheus"
	@helm upgrade --install prometheus prometheus-community/prometheus -f cluster/monitoring/prometheus/values.yaml
	@echo "🚀 Upgrade Helm Repo for Grafana"
	@helm upgrade --install grafana grafana/grafana -f cluster/monitoring/grafana/values.yaml
	@echo "🚀 Upgrade Helm Repo for Dagster"
	@helm upgrade --install dagster dagster/dagster -f cluster/apps/dagster/values.yaml
	@echo "🚀 Add Dagster Configmap"
	@kubectl apply -f cluster/apps/dagster/configmap.yaml
	@echo "🚀 Upgrade Helm Repo for Dask"
	@helm upgrade --install dask dask/dask -f cluster/apps/dask/values.yaml
	@echo "🚀 Add ClickHouse"
	@helm upgrade --install clickhouse bitnami/clickhouse -f cluster/apps/clickhouse/values.yaml
	@echo "🚀 Add Kafka"
	@helm upgrade --install kafka bitnami/kafka -f cluster/apps/kafka/values.yaml
	@echo "🚀 Add Superset"
	@helm upgrade --install superset superset/superset -f cluster/apps/superset/values.yaml

down: ## Delete all Service from Kubernetes
	@echo "🗑️ Delete Helm Repo for Prometheus"
	@helm delete prometheus
	@echo "🗑️ Delete Helm Repo for Grafana"
	@helm delete grafana
	@echo "🗑️ Delete Helm Repo for Dagster"
	@helm delete dagster
	@echo "🗑️ Delete Helm Repo for Dask"
	@helm delete dask
	@echo "🗑️ Delete Helm Repo for ClickHouse"
	@helm delete clickhouse
	@echo "🗑️ Delete Helm Repo for Kafka"
	@helm delete kafka
	@echo "🗑️ Delete Helm Repo for Superset"
	@helm delete superset

expose:
	@echo "🌐 Expose Service"
	@minikube service dagster-webserver dask-scheduler grafana superset

cleanup:
	@kubectl delete pods --field-selector=status.phase=Succeeded
	@kubectl delete pods --field-selector=status.phase=Failed	
	
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help