#!/bin/bash
# Hybrid versi checker untuk OpenClash
# Cek versi lokal, lalu coba ambil versi online (via CDN), tapi tetap aman kalau offline

. /usr/share/openclash/uci.sh
. /usr/share/openclash/openclash_curl.sh

LOCK_FILE="/tmp/lock/openclash_version.lock"
DOWNLOAD_FILE="/tmp/openclash_last_version"

set_lock() {
   mkdir -p /tmp/lock 2>/dev/null
   exec 869>"$LOCK_FILE" 2>/dev/null
   flock -x 869 2>/dev/null
}
del_lock() {
   flock -u 869 2>/dev/null
   rm -f "$LOCK_FILE" 2>/dev/null
}

set_lock

# --- Ambil versi terinstall ---
if [ -x "/bin/opkg" ]; then
   OP_CV=$(rm -f /var/lock/opkg.lock && opkg status luci-app-openclash 2>/dev/null |grep 'Version' |awk -F 'Version: ' '{print $2}' 2>/dev/null)
elif [ -x "/usr/bin/apk" ]; then
   OP_CV=$(apk list luci-app-openclash 2>/dev/null |grep 'installed' | grep -oE '[0-9]+(\.[0-9]+)*' | head -1 2>/dev/null)
fi

[ -z "$OP_CV" ] && OP_CV="0.0.0"

# --- Tentukan URL CDN ---
RELEASE_BRANCH=$(uci_get_config "release_branch" || echo "master")
CDN_URL="https://cdn.jsdelivr.net/gh/vernesong/OpenClash@package/${RELEASE_BRANCH}/version"

# --- Coba ambil versi online ---
DOWNLOAD_FILE_CURL "$CDN_URL" "$DOWNLOAD_FILE"
if [ "$?" -ne 0 ] || ! grep -q '^v[0-9]' "$DOWNLOAD_FILE" 2>/dev/null; then
   # Kalau gagal, buat file dummy dengan versi lokal
   cat > "$DOWNLOAD_FILE" << EOF
v${OP_CV}
# Offline mode - using local version
EOF
else
   # Cek versi online dan bandingkan
   OP_LV=$(sed -n 1p "$DOWNLOAD_FILE" 2>/dev/null | sed 's/^v//' | tr -d '\n')

   # Gunakan sort -V kalau tersedia
   if echo "1.0.0" | sort -V >/dev/null 2>&1; then
      if [ "$(printf '%s\n%s\n' "$OP_CV" "$OP_LV" | sort -V | head -n1)" = "$OP_LV" ] && [ "$OP_CV" != "$OP_LV" ]; then
         echo "# Update available: v${OP_LV}" >> "$DOWNLOAD_FILE"
      else
         echo "# Already latest or same version" >> "$DOWNLOAD_FILE"
      fi
   else
      echo "# Version compare skipped (sort -V not supported)" >> "$DOWNLOAD_FILE"
   fi
fi

del_lock
