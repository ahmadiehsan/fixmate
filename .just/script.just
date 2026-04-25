import "_share.just"
import "_working_dir.just"

dir_checker:
    uv run --no-dev dir_checker

python_checker:
    uv run --no-dev python_checker

just_indexer:
    uv run --no-dev just_indexer .just
