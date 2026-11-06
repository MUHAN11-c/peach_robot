#!/usr/bin/env bash
# Rebuild from source; runtime verification is explicit and mock-only.
set -Eeuo pipefail
script="$(realpath "${BASH_SOURCE[0]}")"
if [[ "${PEACH_DEPLOY_CLEAN_SHELL:-0}" != 1 ]]; then
  exec env -u AMENT_PREFIX_PATH -u COLCON_PREFIX_PATH -u CMAKE_PREFIX_PATH \
    -u PYTHONPATH -u PYTHONHOME -u PYTHONUSERBASE -u LD_LIBRARY_PATH \
    -u VIRTUAL_ENV -u ROS_DISTRO -u ROS_VERSION -u ROS_PACKAGE_PATH -u PIP_CONSTRAINT \
    PEACH_DEPLOY_CLEAN_SHELL=1 PYTHONNOUSERSITE=1 \
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    /bin/bash "$script" "$@"
fi
workspace="$(cd -- "$(dirname -- "$script")/../.." && pwd -P)"
system=0; verify=0; grasp=0; web_e2e=0; jobs=2
output=''
while (($#)); do
  case "$1" in
    --system) system=1; shift ;;
    --verify) verify=1; shift ;;
    --grasp) verify=1; grasp=1; shift ;;
    --web-e2e) verify=1; web_e2e=1; shift ;;
    --jobs) jobs="${2:?missing job count}"; shift 2 ;;
    --output) output="${2:?missing output path}"; shift 2 ;;
    --help)
      printf 'Usage: deploy.sh [--system] [--verify] [--grasp] [--web-e2e] [--jobs 2] [--output DIR]\n'
      printf 'Installs a CPU Python environment, builds web assets and every ROS package.\n'
      printf '%s\n' '--system provisions Ubuntu/Jazzy/Node; --grasp explicitly runs a mock dry cycle.'
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done
[[ "$jobs" =~ ^[1-9][0-9]*$ ]] || exit 2
ascii_path() { local LC_ALL=C; [[ "$1" != *[![:print:]]* && "$1" != *' '* ]]; }
ascii_path "$workspace" || {
  printf 'Deploy from an ASCII workspace path without spaces.\n' >&2; exit 2;
}
cd "$workspace"
output="${output:-$workspace/runs/deployment/$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$output" .cache/pip .cache/npm
output="$(realpath "$output")"
trap 'result=$?; printf "%s\n" "$result" > "$output/deploy.exit"; exit "$result"' EXIT
trap 'printf "Deploy failed at line %s (exit %s); output: %s\n" "$LINENO" "$?" "$output" >&2' ERR
export PIP_CACHE_DIR="$workspace/.cache/pip" PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONNOUSERSITE=1 MPLCONFIGDIR="$workspace/.cache/matplotlib"
export YOLO_CONFIG_DIR="$workspace/.cache/ultralytics"
export PLAYWRIGHT_BROWSERS_PATH="$workspace/.cache/ms-playwright"
if ((system)); then
  printf '[system] Installing Ubuntu/Jazzy/Node prerequisites\n'
  if [[ $EUID == 0 ]]; then
    bash scripts/deployment/bootstrap_ubuntu.sh "$workspace" > "$output/system.log" 2>&1
  else
    sudo bash scripts/deployment/bootstrap_ubuntu.sh "$workspace" > "$output/system.log" 2>&1
  fi
fi
[[ -f /opt/ros/jazzy/setup.bash ]] || { printf 'ROS Jazzy missing; use --system.\n' >&2; exit 2; }
command -v colcon >/dev/null
command -v npm >/dev/null
node -e 'if (Number(process.versions.node.split(".")[0]) < 22) process.exit(1)'

printf '[python] Installing pinned dependencies into aubo_py3.12\n'
python3 -m venv --system-site-packages aubo_py3.12
python_bin="$workspace/aubo_py3.12/bin/python"
mkdir -p "$workspace/.cache/torch-cpu"
# Fetch only the CPU artifacts from PyTorch; resolve all other packages via PyPI.
"$python_bin" -m pip download --no-deps --index-url https://download.pytorch.org/whl/cpu \
  --dest "$workspace/.cache/torch-cpu" 'torch==2.13.0+cpu' 'torchvision==0.28.0+cpu' \
  > "$output/torch.log" 2>&1
"$python_bin" -m pip install --find-links "$workspace/.cache/torch-cpu" \
  'torch==2.13.0+cpu' 'torchvision==0.28.0+cpu' -r requirements.txt \
  > "$output/python.log" 2>&1
cp scripts/deployment/peach-matplotlib-nspkg.pth \
  aubo_py3.12/lib/python3.12/site-packages/peach-matplotlib-nspkg.pth
"$python_bin" -m pip check > "$output/pip_check.log" 2>&1
"$python_bin" -m pip freeze > "$output/python_freeze.txt"
dpkg-query -W -f='${Package}\t${Version}\n' > "$output/apt_packages.tsv"

printf '[web] Installing locked npm packages and generating assets\n'
npm --prefix src/ros2_web_link ci --cache "$workspace/.cache/npm" --no-audit --no-fund \
  > "$output/npm_sdk.log" 2>&1
npm --prefix src/peach/peach_web ci --cache "$workspace/.cache/npm" --no-audit --no-fund \
  > "$output/npm_peach.log" 2>&1
npm --prefix src/ros2_web_link run check > "$output/web_typecheck.log" 2>&1
npm --prefix src/ros2_web_link run build > "$output/web_build.log" 2>&1
npm --prefix src/peach/peach_web run build:vendor > "$output/web_vendor.log" 2>&1
if ((web_e2e)); then
  node src/ros2_web_link/node_modules/playwright/cli.js install chromium \
    > "$output/browser_install.log" 2>&1
fi

printf '[build] Building every discovered ROS package (jobs=%s)\n' "$jobs"
set +u
source /opt/ros/jazzy/setup.bash
set -u
export CMAKE_BUILD_PARALLEL_LEVEL="$jobs" MAKEFLAGS="-j$jobs"
colcon --log-base "$output/colcon" build --base-paths src --executor parallel \
  --parallel-workers "$jobs" --cmake-args -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON > "$output/build.log" 2>&1
colcon list --base-paths src --names-only > "$output/packages.txt"
python3 src/peach/peach_interfaces/scripts/check_interface_manifest.py > "$output/interfaces.log" 2>&1
if ((verify)); then
  printf '[verify] Checking imports, installed assets and mock runtime\n'
  args=(--output "$output/verification")
  ((grasp)) && args+=(--grasp)
  ((web_e2e)) && args+=(--web-e2e)
  bash scripts/deployment/verify.sh "${args[@]}"
fi
printf 'Deployment completed. Evidence: %s\n' "$output"
