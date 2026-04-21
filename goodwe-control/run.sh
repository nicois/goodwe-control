#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

DEST="/config/custom_components/goodwe_battery_control"

bashio::log.info "Installing GoodWe Battery Control integration..."

mkdir -p "$DEST"
rm -rf "$DEST"/*
cp -a /opt/goodwe_battery_control/* "$DEST"/

bashio::log.info "GoodWe Battery Control installed to ${DEST}"
bashio::log.info "Home Assistant must be restarted for changes to take effect."
