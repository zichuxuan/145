#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
OFFLINE_MODE="${OFFLINE_MODE:-0}"
VERSION=""
TARGET_MATRIX=(
  "ubuntu20.04_arm64:3.8:py38"
  "ubuntu22.04_arm64:3.10:py310"
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline)
      OFFLINE_MODE="1"
      shift
      ;;
    --version=*)
      VERSION="${1#*=}"
      shift
      ;;
    -*)
      echo "Unknown option: $1"
      echo "Usage: ./deploy/build_release.sh [version] [--offline]"
      exit 1
      ;;
    *)
      if [[ -n "${VERSION}" ]]; then
        echo "Only one positional version argument is allowed."
        exit 1
      fi
      VERSION="$1"
      shift
      ;;
  esac
done

if [[ -z "${VERSION}" ]]; then
  VERSION="$(date +%Y%m%d_%H%M%S)"
fi

PKG_NAME="hmi-rk3588-${VERSION}.tar.gz"
PKG_PATH="${DIST_DIR}/${PKG_NAME}"

mkdir -p "${DIST_DIR}"

if [[ "${OFFLINE_MODE}" == "1" ]]; then
  echo "Preparing multi-target offline wheels..."
  for target in "${TARGET_MATRIX[@]}"; do
    IFS=":" read -r os_key py_ver py_tag <<< "${target}"
    WHEEL_DIR="${ROOT_DIR}/deploy/offline/wheels/${os_key}/${py_tag}"
    mkdir -p "${WHEEL_DIR}"
    rm -rf "${WHEEL_DIR:?}"/*

    echo "  -> ${os_key} / Python ${py_ver} (${py_tag})"
    python3 -m pip download \
      --only-binary=:all: \
      --platform manylinux_2_28_aarch64 \
      --platform manylinux2014_aarch64 \
      --python-version "${py_ver}" \
      --dest "${WHEEL_DIR}" \
      -r "${ROOT_DIR}/requirements.txt"

    python3 -m pip download \
      --only-binary=:all: \
      --platform manylinux_2_28_aarch64 \
      --platform manylinux2014_aarch64 \
      --python-version "${py_ver}" \
      --dest "${WHEEL_DIR}" \
      pip wheel setuptools
  done

  mkdir -p "${ROOT_DIR}/deploy/offline/debs/ubuntu20.04_arm64"
  mkdir -p "${ROOT_DIR}/deploy/offline/debs/ubuntu22.04_arm64"
fi

tar -czf "${PKG_PATH}" \
  --exclude=".git" \
  --exclude=".venv" \
  --exclude="dist" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude="*.pyo" \
  --exclude="err.log" \
  -C "${ROOT_DIR}" .

echo "Build done: ${PKG_PATH}"
if [[ "${OFFLINE_MODE}" == "1" ]]; then
  echo "Offline wheelhouse included: deploy/offline/wheels/{ubuntu20.04_arm64,ubuntu22.04_arm64}"
  echo "Offline deb path         : deploy/offline/debs/{ubuntu20.04_arm64,ubuntu22.04_arm64}"
fi
