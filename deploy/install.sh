#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-hmi}"
APP_DIR="${APP_DIR:-/opt/hmi}"
RUN_USER="${RUN_USER:-pi}"
RUN_GROUP="${RUN_GROUP:-${RUN_USER}}"
OFFLINE_MODE="${OFFLINE_MODE:-0}"
CHECK_ONLY="${CHECK_ONLY:-0}"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
BIN_START="/usr/local/bin/${APP_NAME}-start"
BIN_STOP="/usr/local/bin/${APP_NAME}-stop"
BIN_STATUS="/usr/local/bin/${APP_NAME}-status"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for arg in "$@"; do
  case "${arg}" in
    --offline)
      OFFLINE_MODE="1"
      ;;
    --check-only)
      CHECK_ONLY="1"
      ;;
    *)
      echo "Unknown option: ${arg}"
      echo "Usage: ./deploy/install.sh [--offline] [--check-only]"
      exit 1
      ;;
  esac
done

detect_os_key() {
  local id version
  id=""
  version=""
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    id="${ID:-}"
    version="${VERSION_ID:-}"
  fi
  case "${id}:${version}" in
    ubuntu:20.04)
      echo "ubuntu20.04_arm64"
      ;;
    ubuntu:22.04)
      echo "ubuntu22.04_arm64"
      ;;
    *)
      echo ""
      ;;
  esac
}

detect_arch() {
  if command -v dpkg >/dev/null 2>&1; then
    dpkg --print-architecture
  else
    uname -m
  fi
}

missing_prereq_packages() {
  local missing=()
  if ! command -v python3 >/dev/null 2>&1; then
    missing+=("python3")
  fi
  if ! command -v rsync >/dev/null 2>&1; then
    missing+=("rsync")
  fi
  if ! command -v systemctl >/dev/null 2>&1; then
    missing+=("systemd")
  fi
  if command -v python3 >/dev/null 2>&1; then
    if ! python3 -c "import venv" >/dev/null 2>&1; then
      missing+=("python3-venv")
    fi
  fi
  if [[ ${#missing[@]} -gt 0 ]]; then
    printf '%s\n' "${missing[@]}"
  fi
}

install_missing_from_local_debs() {
  local os_key="$1"
  local deb_dir="${SRC_DIR}/deploy/offline/debs/${os_key}"

  if [[ ! -d "${deb_dir}" ]]; then
    echo "Offline deb dir missing: ${deb_dir}"
    return 1
  fi

  shopt -s nullglob
  local debs=("${deb_dir}"/*.deb)
  shopt -u nullglob
  if [[ ${#debs[@]} -eq 0 ]]; then
    echo "No .deb files found in ${deb_dir}"
    return 1
  fi

  echo "Installing local deb packages from ${deb_dir}"
  dpkg -i "${debs[@]}" || true
  dpkg -i "${debs[@]}" || true
}

print_manual_2204_hint() {
  local missing_list="$1"
  if [[ "${OS_KEY}" != "ubuntu22.04_arm64" ]]; then
    return
  fi
  echo "Hint for Ubuntu 22.04 offline install:"
  echo "  - Current missing prerequisites: ${missing_list}"
  echo "  - You currently only have Ubuntu 20.04 online resources, so 22.04 .deb coverage may be incomplete."
  echo "  - Recommended manual fix on target board:"
  echo "      sudo apt-get update"
  echo "      sudo apt-get install -y python3 python3-venv rsync systemd"
  echo "  - If the board cannot access network, prepare ubuntu22.04_arm64 .deb files on a 22.04 arm64 machine"
  echo "    and place them under: deploy/offline/debs/ubuntu22.04_arm64/"
}

ARCH="$(detect_arch)"
if [[ "${ARCH}" != "arm64" && "${ARCH}" != "aarch64" ]]; then
  echo "Unsupported architecture: ${ARCH}. Expected arm64/aarch64."
  exit 1
fi

OS_KEY="$(detect_os_key)"
if [[ -z "${OS_KEY}" ]]; then
  echo "Unsupported OS. This installer currently supports Ubuntu 20.04 and 22.04."
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PY_TAG="$(python3 -c 'import sys; print(f"py{sys.version_info.major}{sys.version_info.minor}")')"
else
  PY_TAG="unknown"
fi

SOURCE_WHEEL_DIR="${SRC_DIR}/deploy/offline/wheels/${OS_KEY}/${PY_TAG}"
SOURCE_LEGACY_WHEEL_DIR="${SRC_DIR}/deploy/offline/wheels"
SOURCE_DEB_DIR="${SRC_DIR}/deploy/offline/debs/${OS_KEY}"

mapfile -t MISSING_PKGS < <(missing_prereq_packages)

if [[ "${CHECK_ONLY}" == "1" ]]; then
  echo "=== Offline Precheck Report ==="
  echo "OS key                : ${OS_KEY}"
  echo "Architecture          : ${ARCH}"
  echo "Python tag            : ${PY_TAG}"
  if [[ "${OFFLINE_MODE}" == "1" ]]; then
    echo "Offline wheel dir     : ${SOURCE_WHEEL_DIR}"
    echo "Legacy wheel dir      : ${SOURCE_LEGACY_WHEEL_DIR}"
    echo "Offline deb dir       : ${SOURCE_DEB_DIR}"
  fi
  if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    echo "Missing prerequisites : ${MISSING_PKGS[*]}"
  else
    echo "Missing prerequisites : none"
  fi

  FAIL=0
  if [[ "${OFFLINE_MODE}" == "1" ]]; then
    if [[ ! -d "${SOURCE_WHEEL_DIR}" && ! -d "${SOURCE_LEGACY_WHEEL_DIR}" ]]; then
      echo "Check result          : FAIL (offline wheels not found)"
      FAIL=1
    fi
    if [[ ! -d "${SOURCE_DEB_DIR}" ]]; then
      echo "Check result          : FAIL (offline deb dir not found)"
      FAIL=1
    fi
  fi
  if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    echo "Check result          : FAIL (missing system prerequisites)"
    print_manual_2204_hint "${MISSING_PKGS[*]}"
    FAIL=1
  fi
  if [[ "${FAIL}" -eq 0 ]]; then
    echo "Check result          : PASS"
    exit 0
  else
    exit 1
  fi
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root: sudo ./deploy/install.sh"
  exit 1
fi

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
  echo "Missing system prerequisites: ${MISSING_PKGS[*]}"
  if [[ "${OFFLINE_MODE}" == "1" ]]; then
    install_missing_from_local_debs "${OS_KEY}" || {
      echo "Offline prerequisite installation failed."
      print_manual_2204_hint "${MISSING_PKGS[*]}"
      exit 1
    }
    mapfile -t MISSING_PKGS < <(missing_prereq_packages)
    if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
      echo "Still missing prerequisites after offline deb install: ${MISSING_PKGS[*]}"
      print_manual_2204_hint "${MISSING_PKGS[*]}"
      exit 1
    fi
  else
    apt-get update
    apt-get install -y "${MISSING_PKGS[@]}"
  fi
fi

echo "Install app to ${APP_DIR}"
mkdir -p "${APP_DIR}"

rsync -a --delete \
  --exclude ".git/" \
  --exclude ".venv/" \
  --exclude "dist/" \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude "err.log" \
  "${SRC_DIR}/" "${APP_DIR}/"

python3 -m venv "${APP_DIR}/.venv"
if [[ "${OFFLINE_MODE}" == "1" ]]; then
  PY_TAG="$(python3 -c 'import sys; print(f"py{sys.version_info.major}{sys.version_info.minor}")')"
  WHEEL_DIR="${APP_DIR}/deploy/offline/wheels/${OS_KEY}/${PY_TAG}"
  LEGACY_WHEEL_DIR="${APP_DIR}/deploy/offline/wheels"

  if [[ ! -d "${WHEEL_DIR}" ]]; then
    if [[ -d "${LEGACY_WHEEL_DIR}" ]]; then
      WHEEL_DIR="${LEGACY_WHEEL_DIR}"
    else
      echo "Offline wheel dir missing: ${WHEEL_DIR}"
      echo "Build release with: ./deploy/build_release.sh <version> --offline"
      exit 1
    fi
  fi

  "${APP_DIR}/.venv/bin/pip" install \
    --no-index \
    --find-links "${WHEEL_DIR}" \
    -r "${APP_DIR}/requirements.txt"
else
  "${APP_DIR}/.venv/bin/pip" install --upgrade pip wheel
  "${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"
fi

chown -R "${RUN_USER}:${RUN_GROUP}" "${APP_DIR}"

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=RK3588 HMI Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
Group=${RUN_GROUP}
WorkingDirectory=${APP_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/${RUN_USER}/.Xauthority
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

cat > "${BIN_START}" <<EOF
#!/usr/bin/env bash
sudo systemctl start ${APP_NAME}.service
EOF

cat > "${BIN_STOP}" <<EOF
#!/usr/bin/env bash
sudo systemctl stop ${APP_NAME}.service
EOF

cat > "${BIN_STATUS}" <<EOF
#!/usr/bin/env bash
sudo systemctl status ${APP_NAME}.service --no-pager
EOF

chmod +x "${BIN_START}" "${BIN_STOP}" "${BIN_STATUS}"

systemctl daemon-reload
systemctl enable "${APP_NAME}.service"

echo "Install done."
echo "Start service: ${APP_NAME}-start"
echo "Stop service : ${APP_NAME}-stop"
echo "Status       : ${APP_NAME}-status"
if [[ "${OFFLINE_MODE}" == "1" ]]; then
  echo "Mode         : offline"
  echo "OS key       : ${OS_KEY}"
fi
