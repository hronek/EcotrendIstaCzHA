#!/usr/bin/with-contenv bashio

bashio::log.info "Starting EcoTrend Screenshot Server..."

export LOG_LEVEL=$(bashio::config 'log_level')

python3 /screenshot_server.py
