import "_share.just"
import "_working_dir.just"

install:
    uv sync

upgrade:
    uv sync --upgrade

lock:
    uv lock
