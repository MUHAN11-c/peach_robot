#!/usr/bin/env bash
# Source this file from any directory to load this deployment only.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  printf 'Use: source scripts/deployment/env.bash\n' >&2
  exit 2
fi

_peach_load_environment() {
  local workspace prefix
  workspace="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)" || return
  if [[ ! -f "$workspace/install/local_setup.bash" ||
        ! -f "$workspace/aubo_py3.12/bin/activate" ]]; then
    printf 'Missing build or venv in %s\n' "$workspace" >&2
    return 1
  fi
  export PYTHONNOUSERSITE=1
  source /opt/ros/jazzy/setup.bash || return
  prefix="$workspace/.deps/root/opt/ros/jazzy"
  if [[ -d "$prefix" ]]; then
    export AMENT_PREFIX_PATH="$prefix${AMENT_PREFIX_PATH:+:$AMENT_PREFIX_PATH}"
    export CMAKE_PREFIX_PATH="$prefix${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
    export LD_LIBRARY_PATH="$prefix/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export PYTHONPATH="$prefix/lib/python3.12/site-packages:$workspace/.deps/root/usr/lib/python3/dist-packages${PYTHONPATH:+:$PYTHONPATH}"
    export PATH="$workspace/.deps/root/usr/bin:$PATH"
  fi
  source "$workspace/install/local_setup.bash" || return
  source "$workspace/aubo_py3.12/bin/activate" || return
  export PYTHONPATH="$workspace/aubo_py3.12/lib/python3.12/site-packages${PYTHONPATH:+:$PYTHONPATH}"
  export PEACH_WORKSPACE="$workspace"
  export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-181}"
  export ROS_LOCALHOST_ONLY=1
  export ROS_LOG_DIR="${ROS_LOG_DIR:-$workspace/log/runtime}"
  export MPLCONFIGDIR="$workspace/.cache/matplotlib"
  export YOLO_CONFIG_DIR="$workspace/.cache/ultralytics"
  export PLAYWRIGHT_BROWSERS_PATH="$workspace/.cache/ms-playwright"
  mkdir -p "$ROS_LOG_DIR" "$MPLCONFIGDIR" "$YOLO_CONFIG_DIR"
}

_peach_load_environment
_peach_env_status=$?
unset -f _peach_load_environment
return "$_peach_env_status"
