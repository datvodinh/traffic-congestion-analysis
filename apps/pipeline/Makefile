check: ## Run code quality tools.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry lock --check"
	@poetry check --lock
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@poetry run deptry .

export: ## Export requirements.txt file
	@echo "🚀 Exporting requirements.txt file"
	@poetry export --without-hashes -f requirements.txt --output requirements.txt
	
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
