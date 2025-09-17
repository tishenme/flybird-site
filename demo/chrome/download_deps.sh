#!/bin/bash

DEB_FILE="google-chrome-stable_current_amd64.deb"

if [ ! -f "$DEB_FILE" ]; then
    echo "❌ File not found: $DEB_FILE"
    exit 1
fi

echo "🔍 Extracting dependencies from $DEB_FILE..."

# 更健壮地提取 Depends, Recommends
DEPENDS_RAW=$(dpkg-deb -f "$DEB_FILE" Depends 2>/dev/null | tr ',' '\n' | sed 's/|.*$//; s/ ([^)]*)//g; s/^[ \t]*//; s/[ \t]*$//')
RECOMMENDS_RAW=$(dpkg-deb -f "$DEB_FILE" Recommends 2>/dev/null | tr ',' '\n' | sed 's/|.*$//; s/ ([^)]*)//g; s/^[ \t]*//; s/[ \t]*$//')

ALL_RAW="$DEPENDS_RAW
$RECOMMENDS_RAW"

# 去重 + 过滤
PKGS=""
declare -A SEEN
for pkg in $ALL_RAW; do
    [[ -z "$pkg" ]] && continue
    [[ "${pkg}" == *":"* ]] && { echo "⚠️ Skipping arch-specific: $pkg"; continue; }
    [[ "$pkg" == "www-browser" || "$pkg" == "Provides" ]] && { echo "⚠️ Skipping virtual: $pkg"; continue; }
    [[ "${SEEN[$pkg]}" == "1" ]] && continue
    SEEN[$pkg]=1

    if apt-cache show "$pkg" >/dev/null 2>&1; then
        PKGS="$PKGS $pkg"
        echo "✅ Valid package: $pkg"
    else
        echo "⚠️ No candidate for: $pkg (skipping)"
    fi
done

# 获取完整递归依赖（推荐使用 apt-rdepends）
if command -v apt-rdepends >/dev/null 2>&1; then
    echo "🧩 Resolving recursive dependencies..."
    RECURSIVE_PKGS=$(apt-rdepends --print-state-followed --follow=Depends,Recommends,PreDepends --show=Depends,PreDepends,Recommends $PKGS 2>/dev/null | grep -v "^[^ ]" | sort -u)
else
    echo "⚠️ apt-rdepends not installed, using direct dependencies only."
    RECURSIVE_PKGS=$PKGS
fi

echo "📥 Downloading packages (including recursive dependencies):"
echo "$RECURSIVE_PKGS" | tr ' ' '\n' | grep -v "^$" | sort -u

# 下载所有包
apt-get download $(echo "$RECURSIVE_PKGS" | tr '\n' ' ')

echo "✅ All packages downloaded to current directory."
echo "📦 To install offline: dpkg -i *.deb (may need --force-depends or apt install -f after)"
