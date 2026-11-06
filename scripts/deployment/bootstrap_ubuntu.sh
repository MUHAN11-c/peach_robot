#!/usr/bin/env bash
# Install system prerequisites on Ubuntu 24.04; run as root (also in a container).
set -Eeuo pipefail
trap 'printf "bootstrap failed at line %s (exit %s)\n" "$LINENO" "$?" >&2' ERR

if [[ "${1:-}" == --help ]]; then
  printf 'Usage: sudo bash scripts/deployment/bootstrap_ubuntu.sh [workspace]\n'
  exit 0
fi
workspace="$(realpath "${1:-$(dirname -- "${BASH_SOURCE[0]}")/../..}")"
[[ $EUID == 0 ]] || { printf 'System setup requires root; use sudo or validate_clean.sh.\n' >&2; exit 2; }
source /etc/os-release
[[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || {
  printf 'Supported system: Ubuntu 24.04 only.\n' >&2; exit 2;
}
[[ "$(dpkg --print-architecture)" == amd64 ]] || {
  printf 'The delivered vendor libraries require amd64.\n' >&2; exit 2;
}
export DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONNOUSERSITE=1
apt-get -o Acquire::Retries=3 -o APT::Update::Error-Mode=any update
apt-get -o Acquire::Retries=3 install -y --no-install-recommends ca-certificates curl gnupg locales \
  python3 python3-venv xz-utils iproute2

# Official ROS repository setup, as documented for Jazzy. Pin the source package.
ros_source_version="${ROS_APT_SOURCE_VERSION:-1.1.0}"
[[ "$ros_source_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2
if [[ "$(dpkg-query -W -f='${Status}' ros2-apt-source 2>/dev/null || true)" != 'install ok installed' ]]; then
  source_deb="$(mktemp --suffix=.deb)"
  curl --fail --location --retry 3 --connect-timeout 20 \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ros_source_version}/ros2-apt-source_${ros_source_version}.noble_all.deb" \
    --output "$source_deb"
  dpkg -i "$source_deb"
  rm -f -- "$source_deb"
fi
if [[ -n "${PEACH_ROS_APT_MIRROR:-}" ]]; then
  [[ "$PEACH_ROS_APT_MIRROR" == https://* ]] || exit 2
  # This override is explicit; keep the source package's original configuration.
  if [[ -e /etc/apt/sources.list.d/ros2.sources ]]; then
    mv /etc/apt/sources.list.d/ros2.sources /etc/apt/sources.list.d/ros2.sources.disabled
  fi
  printf 'Types: deb\nURIs: %s\nSuites: noble\nComponents: main\nSigned-By: /usr/share/keyrings/ros2-archive-keyring.gpg\n' \
    "$PEACH_ROS_APT_MIRROR" > /etc/apt/sources.list.d/peach-ros2-mirror.sources
fi
apt-get -o Acquire::Retries=3 -o APT::Update::Error-Mode=any update
apt-get -o Acquire::Retries=3 install -y --no-install-recommends build-essential cmake git ripgrep zstd \
  python3-pip python3-colcon-common-extensions python3-colcon-python-setup-py \
  python3-rosdep nlohmann-json3-dev ros-jazzy-ros-base \
  ros-jazzy-camera-info-manager ros-jazzy-image-transport ros-jazzy-image-publisher \
  ros-jazzy-pcl-conversions ros-jazzy-tf2-sensor-msgs \
  ros-jazzy-pilz-industrial-motion-planner ros-jazzy-moveit-planners-stomp \
  libgl1 libglib2.0-0t64 libasound2t64 libatk1.0-0t64 libatk-bridge2.0-0t64 \
  libcups2t64 libdbus-1-3 libdrm2 libgbm1 libnspr4 libnss3 libx11-6 libxcb1 \
  libxcomposite1 libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2 \
  libpango-1.0-0 libcairo2 fonts-liberation fonts-noto-cjk

node_version="${PEACH_NODE_VERSION:-24.18.0}"
[[ "$node_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2
if ! command -v node >/dev/null || [[ "$(node --version)" != "v$node_version" ]]; then
  node_tmp="$(mktemp -d)"
  node_archive="node-v${node_version}-linux-x64.tar.xz"
  curl --fail --location --retry 3 --connect-timeout 20 \
    "https://nodejs.org/dist/v${node_version}/$node_archive" --output "$node_tmp/$node_archive"
  curl --fail --location --retry 3 --connect-timeout 20 \
    "https://nodejs.org/dist/v${node_version}/SHASUMS256.txt" --output "$node_tmp/SHASUMS256.txt"
  (cd "$node_tmp"; awk -v name="$node_archive" '$2 == name' SHASUMS256.txt > selected.sha256
    test -s selected.sha256; sha256sum --check selected.sha256)
  tar -xJf "$node_tmp/$node_archive" -C /opt
  for executable in node npm npx; do
    ln -sfn "/opt/node-v${node_version}-linux-x64/bin/$executable" "/usr/local/bin/$executable"
  done
  rm -rf -- "$node_tmp"
fi

if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  rosdep init
fi
rosdep update --rosdistro jazzy
# setup.bash reads unset variables in normal ROS distributions.
set +u
source /opt/ros/jazzy/setup.bash
set -u
cd "$workspace"
mapfile -t all_packages < <(colcon list --base-paths src --paths-only)
mapfile -t main_packages < <(colcon list --base-paths src --paths-only \
  --packages-up-to peach_system_tests peach_web peach_stereo peach_vegetation)
[[ ${#all_packages[@]} -gt 0 && ${#main_packages[@]} -gt 0 ]]
skip_keys='ament_python nlohmann_json ros_web_link'
# ament_python is supplied by colcon; nlohmann_json by nlohmann-json3-dev.
# ros_web_link belongs to the unsupported legacy IVG dashboard.
rosdep install --from-paths "${all_packages[@]}" --ignore-src --rosdistro jazzy -y \
  --dependency-types=build --dependency-types=buildtool \
  --dependency-types=build_export --dependency-types=buildtool_export \
  --dependency-types=test --skip-keys "$skip_keys"
# Only the active Peach application's runtime is provisioned. Gazebo stays off.
rosdep install --from-paths "${main_packages[@]}" --ignore-src --rosdistro jazzy -y \
  --dependency-types exec --skip-keys "$skip_keys"
rosdep check --from-paths "${main_packages[@]}" --ignore-src --rosdistro jazzy \
  --skip-keys "$skip_keys"
printf 'System prerequisites ready; node=%s, packages=%s\n' "$(node --version)" "${#all_packages[@]}"
