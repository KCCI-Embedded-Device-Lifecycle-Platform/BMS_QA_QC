#!/usr/bin/env bash
set -euo pipefail

clone_at_ref() {
  local repository="$1"
  local reference="$2"
  local destination="$3"
  git clone --filter=blob:none --no-checkout "$repository" "$destination"
  git -C "$destination" fetch --depth 1 origin "$reference"
  git -C "$destination" checkout --detach FETCH_HEAD
  test "$(git -C "$destination" rev-parse HEAD)" = "$reference"
  test -z "$(git -C "$destination" status --porcelain)"
}

mkdir -p .products
clone_at_ref "$BMS_PRODUCT_REPO" "$BMS_PRODUCT_REF" .products/BMS
clone_at_ref "$EVSE_PRODUCT_REPO" "$EVSE_CAN_PRODUCT_REF" .products/EVSE-Application
clone_at_ref "$OTA_PRODUCT_REPO" "$OTA_PRODUCT_REF" .products/ota-platform

# Ensure linker script filename case compatibility on Linux
for dir in .products/EVSE-Application .products/ota-platform/EVSE_BOOT; do
  if [ -d "$dir" ]; then
    if [ -f "$dir/STM32F429xx_FLASH.ld" ] && [ ! -f "$dir/STM32F429XX_FLASH.ld" ]; then
      cp -p "$dir/STM32F429xx_FLASH.ld" "$dir/STM32F429XX_FLASH.ld"
    elif [ -f "$dir/STM32F429XX_FLASH.ld" ] && [ ! -f "$dir/STM32F429xx_FLASH.ld" ]; then
      cp -p "$dir/STM32F429XX_FLASH.ld" "$dir/STM32F429xx_FLASH.ld"
    fi
  fi
done
