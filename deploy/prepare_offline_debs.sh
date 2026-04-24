#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f /etc/os-release ]]; then
  echo "/etc/os-release not found."
  exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
OS_KEY=""
case "${ID:-}:${VERSION_ID:-}" in
  ubuntu:20.04)
    OS_KEY="ubuntu20.04_arm64"
    ;;
  ubuntu:22.04)
    OS_KEY="ubuntu22.04_arm64"
    ;;
  *)
    echo "Unsupported host OS: ${ID:-unknown} ${VERSION_ID:-unknown}"
    echo "Only Ubuntu 20.04 / 22.04 are supported."
    exit 1
    ;;
esac

ARCH="$(dpkg --print-architecture)"
if [[ "${ARCH}" != "arm64" ]]; then
  echo "Unsupported architecture: ${ARCH}. Expected arm64."
  exit 1
fi

DEB_DIR="${ROOT_DIR}/deploy/offline/debs/${OS_KEY}"
mkdir -p "${DEB_DIR}"
rm -f "${DEB_DIR}"/*.deb

PACKAGES=(
  python3
  python3-venv
  python3-pip
  rsync
  systemd
)

echo "Downloading offline debs to ${DEB_DIR}"
for pkg in "${PACKAGES[@]}"; do
  apt-get download "${pkg}"
done

mv ./*.deb "${DEB_DIR}/"
echo "Done. Saved to: ${DEB_DIR}"
