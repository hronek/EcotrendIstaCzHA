#!/usr/bin/env python3
"""EcoTrend Screenshot Server - captures screenshots from ista EcoTrend."""

import base64
import gc
import io
import json
import logging
import os
import subprocess
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configuration
ECOTREND_URL = "https://ecotrend.ista.cz/"
SCREENSHOT_DIR = Path("/media/ecotrend_screenshots")
CONFIG_DIR = Path("/config")

# Global lock - only one screenshot at a time!
screenshot_lock = threading.Lock()

# Logging setup
log_level = os.environ.get("LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Mapping for tabs and intervals
TAB_MAPPING = {
    "heat": "Teplo",
    "hot_water": "Teplá voda",
    "cold_water": "Studená voda"
}

INTERVAL_MAPPING = {
    "days": "Dny",
    "weeks": "Týdny",
    "months": "Měsíce",
    "years": "Roky"
}

COMPARISON_MAPPING = {
    "object": "Objekt",
    "last_year": "Minulý rok"
}


def kill_all_chrome():
    """Kill all running Chrome/Chromium processes to free memory."""
    try:
        subprocess.run(["pkill", "-9", "chromium"], capture_output=True)
        subprocess.run(["pkill", "-9", "chrome"], capture_output=True)
        subprocess.run(["pkill", "-9", "chromedriver"], capture_output=True)
        time.sleep(1)
    except Exception as e:
        logger.debug(f"Error killing chrome processes: {e}")


def get_chrome_driver(dark_mode: bool = False) -> webdriver.Chrome:
    """Create and configure Chrome WebDriver with MINIMAL memory usage for RPi."""
    # Kill any existing Chrome processes first
    kill_all_chrome()

    # Force garbage collection and wait
    gc.collect()
    time.sleep(2)

    options = Options()

    # Essential headless options
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # VERY small window = much less memory (will be scaled)
    options.add_argument("--window-size=1024,600")

    # AGGRESSIVE memory optimizations for Raspberry Pi with <1GB RAM
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--single-process")  # Critical for low RAM
    options.add_argument("--no-zygote")  # Critical for low RAM
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-features=IsolateOrigins")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--safebrowsing-disable-auto-update")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-features=AudioServiceOutOfProcess")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--memory-pressure-off")
    options.add_argument("--js-flags=--max-old-space-size=64")  # Very low JS heap
    options.add_argument("--renderer-process-limit=1")
    options.add_argument("--disable-accelerated-2d-canvas")
    options.add_argument("--disable-accelerated-video-decode")
    # NOTE: WebGL is REQUIRED for Unity-based EcoTrend site, don't disable it
    options.add_argument("--disable-threaded-scrolling")
    options.add_argument("--disable-threaded-animation")
    options.add_argument("--num-raster-threads=1")
    options.add_argument("--disable-low-res-tiling")

    # User agent
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    options.binary_location = "/usr/bin/chromium-browser"

    if dark_mode:
        options.add_argument("--force-dark-mode")

    service = Service("/usr/bin/chromedriver")

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(120)  # Longer timeout for slow systems
        driver.set_script_timeout(90)
        return driver
    except Exception as e:
        logger.error(f"Failed to create Chrome driver: {e}")
        kill_all_chrome()
        gc.collect()
        raise


def safe_quit_driver(driver):
    """Safely quit driver and clean up."""
    if driver:
        try:
            driver.quit()
        except Exception as e:
            logger.debug(f"Error quitting driver: {e}")

    # Kill any remaining processes
    kill_all_chrome()

    # Force garbage collection
    gc.collect()


def login_to_ecotrend(driver: webdriver.Chrome, username: str, password: str) -> bool:
    """Login to ista EcoTrend."""
    try:
        logger.info("Navigating to EcoTrend...")
        driver.get(ECOTREND_URL)

        # Wait for page to load
        time.sleep(8)

        wait = WebDriverWait(driver, 30)

        # Check if already logged in
        try:
            driver.find_element(By.CSS_SELECTOR, ".itsecurity.authorized")
            logger.info("Already logged in")
            return True
        except:
            pass

        # Wait for Unity to load
        logger.info("Waiting for login form...")
        time.sleep(10)

        # Try to find login form
        try:
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[name='username'], input[name='email']"))
            )
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)

            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .login-button, button")
            login_button.click()

            time.sleep(8)
            logger.info("Login submitted")
            return True

        except Exception as e:
            logger.warning(f"Standard login form not found: {e}")

            # Try Unity JavaScript login
            try:
                time.sleep(5)
                js_login = f"""
                if (typeof unityInstance !== 'undefined') {{
                    unityInstance.SendMessage('LoginManager', 'SetUsername', '{username}');
                    unityInstance.SendMessage('LoginManager', 'SetPassword', '{password}');
                    unityInstance.SendMessage('LoginManager', 'DoLogin');
                }}
                """
                driver.execute_script(js_login)
                time.sleep(10)
                logger.info("Unity login attempted")
                return True
            except Exception as e2:
                logger.error(f"Unity login failed: {e2}")
                return False

    except Exception as e:
        logger.error(f"Login failed: {e}")
        return False


def select_view(driver: webdriver.Chrome, tab: str, interval: str, comparison: str) -> bool:
    """Select the specified view."""
    try:
        time.sleep(3)

        tab_text = TAB_MAPPING.get(tab, tab)
        interval_text = INTERVAL_MAPPING.get(interval, interval)
        comparison_text = COMPARISON_MAPPING.get(comparison, comparison)

        logger.info(f"Selecting: {tab_text} / {interval_text} / {comparison_text}")

        # Try clicking via JavaScript (more reliable)
        js_click = f"""
        function clickByText(selector, text) {{
            var elements = document.querySelectorAll(selector);
            for (var i = 0; i < elements.length; i++) {{
                if (elements[i].textContent.includes(text)) {{
                    elements[i].click();
                    return true;
                }}
            }}
            return false;
        }}

        // Click tab
        clickByText('div, span, button', '{tab_text}');

        // Wait and click interval
        setTimeout(function() {{
            clickByText('div, span, button', '{interval_text}');
        }}, 1000);

        // Wait and click comparison
        setTimeout(function() {{
            clickByText('div, span, button, h3', '{comparison_text}');
        }}, 2000);
        """

        driver.execute_script(js_click)
        time.sleep(5)

        return True

    except Exception as e:
        logger.error(f"Failed to select view: {e}")
        return False


def apply_theme(driver: webdriver.Chrome, dark_mode: bool) -> None:
    """Apply dark or light theme."""
    try:
        if dark_mode:
            driver.execute_script("""
                document.body.classList.add('Dark');
                document.body.classList.remove('Light');
            """)
        else:
            driver.execute_script("""
                document.body.classList.remove('Dark');
                document.body.classList.add('Light');
                document.body.style.backgroundColor = 'white';
            """)
        time.sleep(1)
    except Exception as e:
        logger.debug(f"Could not apply theme: {e}")


def capture_screenshot(driver: webdriver.Chrome) -> Optional[bytes]:
    """Capture screenshot."""
    try:
        # Try specific selectors first
        for selector in [".graph", "#chart", ".dxc-chart", "#overview-main-container", ".container"]:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                screenshot = element.screenshot_as_png
                logger.info(f"Captured using selector: {selector}")
                return screenshot
            except:
                continue

        # Fallback to full page
        logger.info("Capturing full page screenshot")
        return driver.get_screenshot_as_png()

    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return None


def take_screenshot(
    username: str,
    password: str,
    tab: str = "heat",
    interval: str = "months",
    comparison: str = "last_year",
    dark_mode: bool = True
) -> Optional[bytes]:
    """Take a screenshot of the specified EcoTrend view."""
    driver = None

    try:
        logger.info(f"Taking screenshot: tab={tab}, interval={interval}, comparison={comparison}")

        # Extra cleanup before starting
        gc.collect()
        time.sleep(1)

        driver = get_chrome_driver(dark_mode)

        if not login_to_ecotrend(driver, username, password):
            logger.error("Login failed")
            return None

        # Give memory time to settle
        gc.collect()
        time.sleep(8)

        apply_theme(driver, dark_mode)

        if not select_view(driver, tab, interval, comparison):
            logger.warning("View selection may have failed")

        # Wait longer for chart to render on slow systems
        time.sleep(5)
        gc.collect()

        screenshot = capture_screenshot(driver)

        return screenshot

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return None

    finally:
        safe_quit_driver(driver)
        gc.collect()
        time.sleep(2)  # Let memory settle before next request


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "lock_available": not screenshot_lock.locked()
    })


@app.route("/screenshot", methods=["POST"])
def screenshot():
    """Take a screenshot and return it."""
    # Try to acquire lock without blocking
    if not screenshot_lock.acquire(blocking=False):
        logger.warning("Screenshot already in progress, request queued")
        # Wait for lock with timeout
        if not screenshot_lock.acquire(blocking=True, timeout=180):
            return jsonify({"error": "Timeout waiting for previous screenshot to complete"}), 503

    try:
        data = request.get_json() or {}

        username = data.get("username")
        password = data.get("password")
        tab = data.get("tab", "heat")
        interval = data.get("interval", "months")
        comparison = data.get("comparison", "last_year")
        dark_mode = data.get("dark_mode", True)

        if not username or not password:
            return jsonify({"error": "username and password required"}), 400

        image_data = take_screenshot(
            username=username,
            password=password,
            tab=tab,
            interval=interval,
            comparison=comparison,
            dark_mode=dark_mode
        )

        if image_data:
            return jsonify({
                "success": True,
                "image": base64.b64encode(image_data).decode("utf-8"),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to capture screenshot"}), 500

    except Exception as e:
        logger.exception("Screenshot endpoint error")
        return jsonify({"error": str(e)}), 500

    finally:
        screenshot_lock.release()


@app.route("/screenshot/file", methods=["POST"])
def screenshot_file():
    """Take a screenshot and save to file."""
    if not screenshot_lock.acquire(blocking=True, timeout=180):
        return jsonify({"error": "Timeout waiting for previous screenshot"}), 503

    try:
        data = request.get_json() or {}

        username = data.get("username")
        password = data.get("password")
        tab = data.get("tab", "heat")
        interval = data.get("interval", "months")
        comparison = data.get("comparison", "last_year")
        dark_mode = data.get("dark_mode", True)
        filename = data.get("filename")

        if not username or not password:
            return jsonify({"error": "username and password required"}), 400

        image_data = take_screenshot(
            username=username,
            password=password,
            tab=tab,
            interval=interval,
            comparison=comparison,
            dark_mode=dark_mode
        )

        if image_data:
            SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

            if not filename:
                filename = f"ecotrend_{tab}_{interval}_{comparison}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            filepath = SCREENSHOT_DIR / filename

            with open(filepath, "wb") as f:
                f.write(image_data)

            logger.info(f"Screenshot saved to {filepath}")

            return jsonify({
                "success": True,
                "path": str(filepath),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to capture screenshot"}), 500

    except Exception as e:
        logger.exception("Screenshot file endpoint error")
        return jsonify({"error": str(e)}), 500

    finally:
        screenshot_lock.release()


@app.route("/screenshot/image", methods=["POST"])
def screenshot_image():
    """Take a screenshot and return as image directly."""
    if not screenshot_lock.acquire(blocking=True, timeout=180):
        return jsonify({"error": "Timeout waiting for previous screenshot"}), 503

    try:
        data = request.get_json() or {}

        username = data.get("username")
        password = data.get("password")
        tab = data.get("tab", "heat")
        interval = data.get("interval", "months")
        comparison = data.get("comparison", "last_year")
        dark_mode = data.get("dark_mode", True)

        if not username or not password:
            return jsonify({"error": "username and password required"}), 400

        image_data = take_screenshot(
            username=username,
            password=password,
            tab=tab,
            interval=interval,
            comparison=comparison,
            dark_mode=dark_mode
        )

        if image_data:
            return send_file(
                io.BytesIO(image_data),
                mimetype="image/png"
            )
        else:
            return jsonify({"error": "Failed to capture screenshot"}), 500

    except Exception as e:
        logger.exception("Screenshot image endpoint error")
        return jsonify({"error": str(e)}), 500

    finally:
        screenshot_lock.release()


if __name__ == "__main__":
    # Clean up any leftover Chrome processes on startup
    kill_all_chrome()

    logger.info("Starting Ista EcoTrend CZ Screenshot Server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
