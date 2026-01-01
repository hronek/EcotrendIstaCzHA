#!/usr/bin/env python3
"""EcoTrend Screenshot Server - captures screenshots from ista EcoTrend."""

import base64
import io
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_file
from PIL import Image
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


def get_chrome_driver(dark_mode: bool = False) -> webdriver.Chrome:
    """Create and configure Chrome WebDriver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.binary_location = "/usr/bin/chromium-browser"

    if dark_mode:
        options.add_argument("--force-dark-mode")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)

    return driver


def login_to_ecotrend(driver: webdriver.Chrome, username: str, password: str) -> bool:
    """Login to ista EcoTrend."""
    try:
        logger.info("Navigating to EcoTrend...")
        driver.get(ECOTREND_URL)

        # Wait for page to load (Unity WebGL takes time)
        time.sleep(5)

        # Wait for login form or already logged in state
        wait = WebDriverWait(driver, 30)

        # Check if already logged in (look for authorized class)
        try:
            driver.find_element(By.CSS_SELECTOR, ".itsecurity.authorized")
            logger.info("Already logged in")
            return True
        except:
            pass

        # Wait for Unity to load and show login
        logger.info("Waiting for Unity to load...")
        time.sleep(10)

        # Try to find and fill login form
        # The login is inside Unity canvas, so we need to interact with it differently
        # For Unity WebGL, we might need to use JavaScript injection

        # Try finding input fields
        try:
            # Look for standard HTML login form first
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[name='username'], input[name='email']"))
            )
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)

            # Find and click login button
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .login-button, button")
            login_button.click()

            time.sleep(5)
            logger.info("Login submitted")
            return True

        except Exception as e:
            logger.warning(f"Standard login form not found: {e}")

            # Unity WebGL login - try JavaScript approach
            try:
                # Wait for Unity instance
                time.sleep(5)

                # Try to send login via Unity SendMessage
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
    """Select the specified view (tab, interval, comparison)."""
    try:
        wait = WebDriverWait(driver, 20)

        # Wait for the page to be fully loaded
        time.sleep(3)

        # Select tab (Teplo, Teplá voda, Studená voda)
        tab_text = TAB_MAPPING.get(tab, tab)
        logger.info(f"Selecting tab: {tab_text}")

        try:
            # Find tab by text content
            tab_element = driver.find_element(By.XPATH, f"//div[contains(@class, 'nav')]//div[contains(text(), '{tab_text}')] | //span[contains(text(), '{tab_text}')]/parent::div")
            tab_element.click()
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Could not click tab via HTML: {e}, trying JavaScript...")
            driver.execute_script(f"""
                var tabs = document.querySelectorAll('.nav div, .active span');
                tabs.forEach(function(t) {{
                    if (t.textContent.includes('{tab_text}')) {{
                        t.click();
                    }}
                }});
            """)
            time.sleep(2)

        # Select interval (Dny, Týdny, Měsíce, Roky)
        interval_text = INTERVAL_MAPPING.get(interval, interval)
        logger.info(f"Selecting interval: {interval_text}")

        try:
            interval_element = driver.find_element(By.XPATH, f"//div[contains(@class, 'interval') and contains(text(), '{interval_text}')] | //div[text()='{interval_text}']")
            interval_element.click()
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Could not click interval via HTML: {e}, trying JavaScript...")
            driver.execute_script(f"""
                var intervals = document.querySelectorAll('.interval, div');
                intervals.forEach(function(i) {{
                    if (i.textContent.trim() === '{interval_text}') {{
                        i.click();
                    }}
                }});
            """)
            time.sleep(2)

        # Select comparison (Objekt, Minulý rok)
        comparison_text = COMPARISON_MAPPING.get(comparison, comparison)
        logger.info(f"Selecting comparison: {comparison_text}")

        try:
            comparison_element = driver.find_element(By.XPATH, f"//h3[contains(text(), '{comparison_text}')]/parent::div | //div[contains(text(), '{comparison_text}')]")
            comparison_element.click()
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Could not click comparison via HTML: {e}, trying JavaScript...")
            driver.execute_script(f"""
                var comparisons = document.querySelectorAll('h3, div');
                comparisons.forEach(function(c) {{
                    if (c.textContent.trim() === '{comparison_text}') {{
                        c.click();
                    }}
                }});
            """)
            time.sleep(2)

        # Wait for chart to update
        time.sleep(3)
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
        logger.warning(f"Could not apply theme: {e}")


def capture_chart_screenshot(driver: webdriver.Chrome) -> Optional[bytes]:
    """Capture screenshot of the chart area."""
    try:
        # Try to find the chart/graph element
        chart_selectors = [
            ".graph",
            "#chart",
            ".dxc-chart",
            "#overview-main-container",
            ".container"
        ]

        for selector in chart_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                screenshot = element.screenshot_as_png
                logger.info(f"Captured chart screenshot using selector: {selector}")
                return screenshot
            except:
                continue

        # Fallback: capture full page
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
        logger.info(f"Taking screenshot: tab={tab}, interval={interval}, comparison={comparison}, dark={dark_mode}")

        driver = get_chrome_driver(dark_mode)

        # Login
        if not login_to_ecotrend(driver, username, password):
            logger.error("Login failed")
            return None

        # Wait for dashboard to load
        time.sleep(5)

        # Apply theme
        apply_theme(driver, dark_mode)

        # Select view
        if not select_view(driver, tab, interval, comparison):
            logger.warning("View selection may have failed, trying to capture anyway")

        # Wait for content to render
        time.sleep(3)

        # Capture screenshot
        screenshot = capture_chart_screenshot(driver)

        return screenshot

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return None

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/screenshot", methods=["POST"])
def screenshot():
    """Take a screenshot and return it."""
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
            # Return as base64
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


@app.route("/screenshot/file", methods=["POST"])
def screenshot_file():
    """Take a screenshot and save to file, return path."""
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
            # Ensure directory exists
            SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

            # Generate filename if not provided
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


@app.route("/screenshot/image", methods=["POST"])
def screenshot_image():
    """Take a screenshot and return as image directly."""
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


if __name__ == "__main__":
    logger.info("Starting EcoTrend Screenshot Server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
