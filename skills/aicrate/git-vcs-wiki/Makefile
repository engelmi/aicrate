install-deps:
	pip install -r ./git-vcs-wiki/scripts/fetch_issues.requirements.txt

install-dev-deps:
	pip install -r ./tests/requirements.txt

unit-tests: install-dev-deps
	pytest tests/

format:
	black tests/ git-vcs-wiki/
