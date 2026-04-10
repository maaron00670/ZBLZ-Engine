#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_NAME="ZBLZ Engine"
APP_EXEC="zblz-engine"
VERSION="${VERSION:-0.1.1}"
ARCH="${ARCH:-$(uname -m)}"

BUILD_DIR="${ROOT_DIR}/build/appimage"
PY_BUILD_DIR="${BUILD_DIR}/pyinstaller"
APPDIR="${BUILD_DIR}/AppDir"
DIST_DIR="${ROOT_DIR}/dist"

APPIMAGETOOL_BIN="${APPIMAGETOOL_BIN:-appimagetool}"
if [[ -x "${ROOT_DIR}/appimagetool.AppImage" ]]; then
    APPIMAGETOOL_BIN="${ROOT_DIR}/appimagetool.AppImage"
fi

rm -rf "${BUILD_DIR}" "${DIST_DIR}/${APP_EXEC}" "${DIST_DIR}/${APP_EXEC}.spec"
mkdir -p "${PY_BUILD_DIR}" "${APPDIR}/usr/bin" "${APPDIR}/usr/lib/zblz" "${DIST_DIR}"

echo "[1/6] Building speedhack library"
"${ROOT_DIR}/scripts/zblz_engine/lib/build.sh"

echo "[2/6] Creating isolated build venv"
python3 -m venv "${BUILD_DIR}/.venv"
source "${BUILD_DIR}/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/scripts/zblz_engine/requirements.txt" pyinstaller

echo "[3/6] Building Python executable with PyInstaller"
pyinstaller \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --name "${APP_EXEC}" \
  --paths "${ROOT_DIR}/scripts/zblz_engine" \
  "${ROOT_DIR}/scripts/zblz_engine/main.py"

echo "[4/6] Assembling AppDir"
cp "${DIST_DIR}/${APP_EXEC}" "${APPDIR}/usr/bin/${APP_EXEC}"
cp "${ROOT_DIR}/scripts/zblz_engine/lib/libspeedhack.so" "${APPDIR}/usr/lib/zblz/libspeedhack.so"
cp "${ROOT_DIR}/scripts/package/zblz-engine.svg" "${APPDIR}/zblz-engine.svg"

cat > "${APPDIR}/AppRun" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(cd "$(dirname "$0")" && pwd)"
export ZBLZ_LIBRARY_PATH="${APPDIR}/usr/lib/zblz/libspeedhack.so"
exec "${APPDIR}/usr/bin/zblz-engine" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

cat > "${APPDIR}/zblz-engine.desktop" << EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=Speedhack para Linux
Exec=${APP_EXEC}
Icon=zblz-engine
Terminal=false
Categories=Utility;Game;
StartupNotify=true
EOF
ln -sf "zblz-engine.svg" "${APPDIR}/.DirIcon"

echo "[5/6] Validating desktop entry"
desktop-file-validate "${APPDIR}/zblz-engine.desktop"

echo "[6/6] Creating AppImage"
if [[ ! -x "${APPIMAGETOOL_BIN}" ]]; then
    echo "Error: appimagetool not found. Set APPIMAGETOOL_BIN or place appimagetool.AppImage in repo root." >&2
    exit 1
fi

APPIMAGE_NAME="ZBLZ-Engine-${VERSION}-${ARCH}.AppImage"
ARCH="${ARCH}" "${APPIMAGETOOL_BIN}" "${APPDIR}" "${DIST_DIR}/${APPIMAGE_NAME}"
chmod +x "${DIST_DIR}/${APPIMAGE_NAME}"

echo
echo "Done: ${DIST_DIR}/${APPIMAGE_NAME}"
