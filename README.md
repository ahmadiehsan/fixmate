# Fixmate

Your project's best mate for checking and fixing code

## Direct Usage

```shell
pip install git+<this/repo/url>.git@<version_tag>
dir_checker
python_checker
compose_checker
```

## PreCommit Usage

```yaml
repos:
  - repo: <this/repo/url>
    rev: <version_tag>
    hooks:
      - id: dir_checker
      - id: python_checker
      - id: compose_checker
        args: [--env-file, "<path/to/env/file>"]
```

## Developers

```shell
git clone <this/repo/url>
cd <cloned_dir>

npm install -g opencommit
oco config set OCO_API_URL="<llm/provider/api/url>"
oco config set OCO_API_KEY="<llm_provider_api_key>"
oco config set OCO_MODEL="<desired_llm_name>"

curl -LsSf https://astral.sh/uv/0.8.10/install.sh | sh

make dependencies.install
make git.init_hooks
make help
```
