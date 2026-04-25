# Fixmate

Your project's best mate for checking and fixing code

## Direct Usage

```shell
pip install git+<this/repo/url>.git@<version_tag>
dir_checker
python_checker
compose_checker
just_indexer
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
        args: [--env-file, "<path/to/envs/file.env>"]
      - id: just_indexer
        args: ["<path/to/just/modules>"]
```

## Configuration

Commands can read settings from a `pyproject.toml` file. Pass the file explicitly with `--config` when it is not in the current working directory:

```shell
dir_checker --config <path/to/pyproject.toml>
python_checker --config <path/to/pyproject.toml>
just_indexer --config <path/to/pyproject.toml> <path/to/just/modules>
```

The commands look under their own `tool` section names, so the matching configuration blocks are:

```toml
[tool.dir_checker.per-dir-ignores]
"tests" = ["all"]
"src/generated" = ["empty_validator", "init_py_validator"]

[tool.python_checker.per-file-ignores]
"fixmate/helpers" = ["func_validator"]
"fixmate/*/cli.py" = ["import_validator", "msg_validator"]

[tool.just_indexer]
output-file-name = "_index.just"
modules-optional = true
include-patterns = ["[!_]*.just"]
```

Each block only affects its matching command. If a section is missing, the command falls back to its built-in defaults.

## Developers

```shell
git clone <this/repo/url>
cd <cloned_dir>

curl -LsSf https://astral.sh/uv/0.11.7/install.sh | sh
uv tool install rust-just

just dependencies install
just git init_hooks
just help
```
