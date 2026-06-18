#!/usr/bin/env bash
# Copie les icônes générées dans app_icons/ vers les dossiers natifs Android et iOS.
# Usage : bash mobile/scripts/copy-icons.sh (depuis la racine du projet)
# Après exécution : npx cap sync puis rebuilder les apps.
# Le dossier "app_icons" est généré à partir de https://www.appicon.co/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOBILE_DIR="$(dirname "$SCRIPT_DIR")"
ICONS_DIR="$MOBILE_DIR/app_icons"

# Android
ANDROID_RES="$MOBILE_DIR/android/app/src/main/res"

for density in hdpi mdpi xhdpi xxhdpi xxxhdpi; do
    src="$ICONS_DIR/android/mipmap-$density/ic_launcher.png"
    dest="$ANDROID_RES/mipmap-$density"

    if [ ! -f "$src" ]; then
        echo "⚠ Fichier manquant : $src" >&2
        continue
    fi

    cp "$src" "$dest/ic_launcher.png"
    cp "$src" "$dest/ic_launcher_round.png"
    cp "$src" "$dest/ic_launcher_foreground.png"
    echo "✓ Android $density"
done

# iOS
IOS_APPICONSET="$MOBILE_DIR/ios/App/App/Assets.xcassets/AppIcon.appiconset"
GENERATED_APPICONSET="$ICONS_DIR/Assets.xcassets/AppIcon.appiconset"

if [ ! -d "$GENERATED_APPICONSET" ]; then
    echo "⚠ Dossier manquant : $GENERATED_APPICONSET" >&2
    exit 1
fi

cp "$GENERATED_APPICONSET"/*.png "$IOS_APPICONSET/"
cp "$GENERATED_APPICONSET/Contents.json" "$IOS_APPICONSET/Contents.json"
echo "✓ iOS AppIcon.appiconset"

echo ""
echo "Icônes copiées. Prochaines étapes :"
echo "  1. npx cap sync"
echo "  2. Rebuilder l'app Android et iOS"
echo "  3. Uploader app_icons/playstore.png manuellement dans la Play Console"
