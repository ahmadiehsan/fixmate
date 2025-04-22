#!/bin/bash
# Verifies that files passed in are valid for docker-compose

set -e

# Parse arguments
env_file=""
while [[ $# -gt 0 ]]; do
  case $1 in
  --env-file)
    env_file="$2"
    shift 2
    ;;
  *)
    echo "error: unknown argument: $1"
    exit 1
    ;;
  esac
done

# Check if docker or podman commands are available
if [[ -z "${CONTAINER_ENGINE}" ]]; then
  if command -v docker &>/dev/null; then
    CONTAINER_ENGINE=docker
  elif command -v podman &>/dev/null; then
    CONTAINER_ENGINE=podman
  else
    echo "error: neither 'docker' or 'podman' were found"
    exit 1
  fi
fi

# Check if compose command is available
if command -v "${CONTAINER_ENGINE}" &>/dev/null && ${CONTAINER_ENGINE} help compose &>/dev/null; then
  COMPOSE="${CONTAINER_ENGINE} compose"
elif command -v "${CONTAINER_ENGINE}-compose" &>/dev/null; then
  COMPOSE="${CONTAINER_ENGINE}-compose"
else
  echo "error: neither '${CONTAINER_ENGINE}-compose' or '${CONTAINER_ENGINE} compose' were found"
  exit 1
fi

# Function to discover compose files
discover_compose_files() {
  find . -type f -regextype posix-extended -regex ".*/(docker-)?compose.*\.ya?ml$"
}

# Get base name of compose file
get_base_name() {
  local file="$1"
  local name_without_ext="${file%.*}"
  local suffixes=(".base" "-base" ".dev" "-dev" ".development" "-development"
    ".local" "-local" ".stage" "-stage" ".staging" "-staging" ".prod" "-prod"
    ".production" "-production")

  for suffix in "${suffixes[@]}"; do
    if [[ "$name_without_ext" == *"$suffix" ]]; then
      echo "${name_without_ext%$suffix}"
      return 0
    fi
  done

  echo "$name_without_ext"
  return 0
}

# Checker functions
check_group() {
  local files=("$@")
  local compose_cmd="$COMPOSE"

  for file in "${files[@]}"; do
    compose_cmd="$compose_cmd --file $file"
  done

  if [[ -n "$env_file" ]]; then
    compose_cmd="$compose_cmd --env-file $env_file"
  fi

  $compose_cmd config --quiet 2>&1 | sed "/variable is not set. Defaulting/d"
  return "${PIPESTATUS[0]}"
}

check_files() {
  local all_files=("$@")
  local has_error=0
  declare -A file_groups

  # Group files by their base name
  for file in "${all_files[@]}"; do
    if [[ -f "$file" ]]; then
      local base_name
      base_name=$(get_base_name "$file")
      if [[ -n "$base_name" ]]; then
        file_groups["$base_name"]+=" $file"
      fi
    fi
  done

  # Check each group of files
  for base_name in "${!file_groups[@]}"; do
    read -ra group_files <<<"${file_groups[$base_name]}"
    if ! check_group "${group_files[@]}"; then
      echo "error: failed validation for group: ${group_files[*]}"
      has_error=1
    fi
  done

  return $has_error
}

# Main
files=($(discover_compose_files))

if [ ${#files[@]} -eq 0 ]; then
  echo "error: no compose files found"
  exit 1
fi

if ! check_files "${files[@]}"; then
  echo "some compose files failed"
  exit 1
fi

echo "all checks passed"
exit 0
