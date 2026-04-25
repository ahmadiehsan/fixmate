import "_share.just"
import "_working_dir.just"

init_hooks:
    uv run --only-dev pre-commit install -t pre-commit -t pre-push -t commit-msg

run_hooks:
    uv run --only-dev pre-commit run

run_hooks_for_all:
    uv run --only-dev pre-commit run --all-files
