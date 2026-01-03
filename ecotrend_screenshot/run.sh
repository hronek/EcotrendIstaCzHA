#!/usr/bin/with-contenv bashio

bashio::log.info "Starting Ista EcoTrend CZ Screenshot Server..."

# Kill any leftover Chrome processes
pkill -9 chromium 2>/dev/null || true
pkill -9 chrome 2>/dev/null || true
pkill -9 chromedriver 2>/dev/null || true

# Create swap file if possible (helps with low RAM systems)
SWAPFILE="/data/swapfile"
if [ ! -f "$SWAPFILE" ]; then
    bashio::log.info "Creating 512MB swap file for low RAM systems..."
    dd if=/dev/zero of="$SWAPFILE" bs=1M count=512 2>/dev/null || true
    chmod 600 "$SWAPFILE" 2>/dev/null || true
    mkswap "$SWAPFILE" 2>/dev/null || true
fi

# Try to enable swap (may fail due to permissions, that's OK)
swapon "$SWAPFILE" 2>/dev/null || bashio::log.warning "Could not enable swap (requires privileges)"

# Clean up /tmp to free memory
rm -rf /tmp/* 2>/dev/null || true

# Set memory-friendly environment
export MALLOC_ARENA_MAX=2
export LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.info "Starting screenshot server on port 5000..."
exec python3 /screenshot_server.py
