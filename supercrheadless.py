#!/usr/bin/env python3
r"""
Crunchyroll Device Keeper - CI-Ready (GitHub Actions)
- Reads all settings from environment variables (renamed for brevity)
- No interactive prompts
- Auto-re-login if session expires
- Keeps devices by location OR device name/model (both optional, but at least one required)
- Supports OR/AND keep mode via KEEP_MODE (default: OR)
- Shows model, device name, and location for deactivated devices
- Summary counts for kept/current/skipped devices
- All logs with IST timestamps
"""

import subprocess
import sys
import importlib
import time
import random
import os
import shutil
import re
import datetime
from pathlib import Path

# ---- Auto-install dependencies ----
required_packages = ["undetected-chromedriver", "setuptools"]
for pkg in required_packages:
    try:
        importlib.import_module(pkg.replace("-", "_"))
    except ImportError:
        print(f"📦 Package '{pkg}' not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        print(f"✅ Installed '{pkg}'.")

import setuptools  # distutils compatibility for Python 3.12+
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ===========================
# TIMESTAMP HELPER
# ===========================
def timestamp():
    """Return current time in IST (HH:MM:SS IST)."""
    now = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=5, minutes=30)
    return now.strftime("%H:%M:%S IST")

def log(message):
    """Print message with IST timestamp."""
    print(f"[{timestamp()}] {message}")

# ===========================
# CONFIGURATION - READ FROM ENV (renamed, no CRUNCHYROLL_ prefix)
# ===========================
DEVICE_URL = "https://www.crunchyroll.com/account/devices"
LOGIN_URL = "https://sso.crunchyroll.com/login"
PROFILE_BASE_DIR = "/tmp/chrome_profile"

# ---- Environment variables ----
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
PIN = os.getenv("PIN", "")
LOCATIONS_RAW = os.getenv("LOCATIONS", "")
DEVICE_NAMES_RAW = os.getenv("KEEP_DEVICE_NAMES", "")
MODE = os.getenv("MODE", "2")  # 1=Normal, 2=Extreme
PREFERRED_PROFILE = int(os.getenv("PREFERRED_PROFILE", "0"))
KEEP_MODE = os.getenv("KEEP_MODE", "OR").upper()  # OR or AND

# Always headless in CI
HEADLESS = True

# Parse locations and device names
allowed_locations = [loc.strip().lower() for loc in LOCATIONS_RAW.split(",") if loc.strip()]
keep_device_names = [name.strip().lower() for name in DEVICE_NAMES_RAW.split(",") if name.strip()]

# Validate that at least one keep condition is provided
if not allowed_locations and not keep_device_names:
    log("❌ At least one of LOCATIONS or KEEP_DEVICE_NAMES must be set")
    sys.exit(1)

# Validate required vars
if not EMAIL or not PASSWORD:
    log("❌ EMAIL and PASSWORD must be set")
    sys.exit(1)

# ===========================
# HELPER: GET DELAY FROM USER (only used in Normal Mode with interactive)
# ===========================
def get_delay(prompt, default, min_val=0.5, max_val=60):
    # In CI mode, we never prompt; we just return default.
    return float(default)

# ===========================
# COOKIE / ONETRUST HANDLER
# ===========================
def accept_cookies_if_present(driver):
    try:
        accept_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Accept All')] | //button[contains(text(),'Accept')] | //button[@id='onetrust-accept-btn-handler']")
        if accept_btn.is_displayed() and accept_btn.is_enabled():
            accept_btn.click()
            log("🍪 Accepted cookies")
            time.sleep(0.5)
            return True
    except:
        pass
    return False

# ===========================
# LOGIN + PROFILE SELECTION (WITH CYCLING & WORKING PIN)
# ===========================
def is_pin_error_present(driver):
    error_texts = ["incorrect pin", "invalid pin", "wrong pin", "pin is incorrect"]
    try:
        page_text = driver.page_source.lower()
        for text in error_texts:
            if text in page_text:
                return True
    except:
        pass
    try:
        error = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'alert')]")
        for el in error:
            if "pin" in el.text.lower():
                return True
    except:
        pass
    return False

def go_back_to_profile_selection(driver):
    """Navigate directly to the discover page to reset the state."""
    driver.get("https://www.crunchyroll.com/discover")
    log("🔄 Navigated to discover page")
    time.sleep(2)
    for _ in range(8):
        try:
            overlay = driver.find_element(By.CSS_SELECTOR, "div.erc-multiple-profiles-layout, div[data-t='profile-selector']")
            if overlay.is_displayed():
                return True
        except:
            pass
        time.sleep(1)
    return True

def get_profile_overlay_and_cards(driver):
    """Return (overlay, cards) or (None, []) if not found."""
    overlay = None
    selectors = [
        "div.erc-multiple-profiles-layout",
        "div[data-t='profile-selector']",
        "div[class*='profile-select']",
        "div[class*='multiple-profiles']",
        "div[class*='profile-picker']",
    ]
    for sel in selectors:
        try:
            overlay = driver.find_element(By.CSS_SELECTOR, sel)
            if overlay.is_displayed():
                break
        except:
            continue
    if not overlay:
        return None, []
    cards = overlay.find_elements(By.CSS_SELECTOR, "[data-t='profile-selector-item'], div[class*='profile-card'], div[class*='profile-item']")
    if not cards:
        cards = overlay.find_elements(By.XPATH, ".//div[contains(@class, 'profile')] | .//button[contains(@class, 'profile')]")
    return overlay, cards

def login_and_select_profile(driver, email, password, pin, preferred_profile=0):
    log("🔐 Logging in...")
    driver.get(LOGIN_URL)
    time.sleep(3)

    # Check for Cloudflare
    try:
        if "Verifying you are human" in driver.page_source:
            log("⚠️ Cloudflare challenge detected!")
            log("   Please solve the CAPTCHA manually in the browser window.")
            input("👉 Press ENTER once you have completed the verification...")
            time.sleep(2)
    except:
        pass

    # Fill login form
    try:
        email_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
        email_input.clear()
        email_input.send_keys(email)
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.clear()
        password_input.send_keys(password)
        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit.click()
        log("✅ Login form submitted")
    except Exception as e:
        log(f"❌ Login form error: {e}")
        return False

    time.sleep(5)

    overlay, cards = get_profile_overlay_and_cards(driver)
    if not overlay:
        log("ℹ️ No profile selection overlay detected – assuming single profile.")
        return True

    if not cards:
        log("⚠️ No profile cards found – assuming single profile.")
        return True

    log(f"👤 Found {len(cards)} profile(s).")

    # Determine which profiles to try
    if preferred_profile > 0:
        if len(cards) == 1:
            profile_indices = [0]
            log(f"🎯 Only one profile available, using it.")
        else:
            if preferred_profile <= len(cards) - 1:
                idx = preferred_profile
            else:
                idx = len(cards) - 1
            profile_indices = [idx]
            log(f"🎯 Using preferred profile {preferred_profile} (card index {idx})")
    else:
        profile_indices = list(range(len(cards)))
        log("🔄 Will cycle through all profiles.")

    for idx in profile_indices:
        log(f"\n🔄 Trying Profile {idx + 1}...")

        overlay, cards = get_profile_overlay_and_cards(driver)
        if not overlay:
            log("⚠️ Overlay disappeared. Reloading...")
            driver.refresh()
            time.sleep(4)
            overlay, cards = get_profile_overlay_and_cards(driver)
            if not overlay:
                log("❌ Could not recover overlay. Exiting.")
                return False
        if idx >= len(cards):
            log("❌ Profile index out of range.")
            break

        card = cards[idx]
        try:
            card.click()
            log(f"👤 Selected Profile {idx + 1}")
            time.sleep(0.3)
        except Exception as e:
            log(f"❌ Could not click profile {idx + 1}: {e}")
            time.sleep(1)
            overlay, cards = get_profile_overlay_and_cards(driver)
            if not overlay:
                log("⚠️ Overlay lost, reloading...")
                driver.refresh()
                time.sleep(4)
                overlay, cards = get_profile_overlay_and_cards(driver)
                if not overlay:
                    log("❌ Could not recover. Exiting.")
                    return False
            continue

        if pin:
            try:
                pin_input = None
                pin_selectors = [
                    "input[type='password'][placeholder*='PIN']",
                    "input[type='password'][placeholder*='pin']",
                    "input[type='password'][aria-label*='PIN']",
                    "input[data-t='pin-input']",
                    "input[class*='pin']",
                ]
                for ps in pin_selectors:
                    try:
                        pin_input = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ps))
                        )
                        if pin_input.is_displayed():
                            break
                    except:
                        continue

                if pin_input:
                    pin_input.clear()
                    pin_input.send_keys(pin)
                    log(f"✅ PIN entered for Profile {idx + 1}.")
                    time.sleep(0.1)

                    confirm_btns = driver.find_elements(By.XPATH, "//button[contains(text(),'Continue') or contains(text(),'Submit') or contains(text(),'Confirm') or contains(text(),'Unlock')]")
                    if confirm_btns:
                        confirm_btns[0].click()
                        log(f"✅ PIN confirmed for Profile {idx + 1}.")
                        time.sleep(0.3)
                    else:
                        pin_input.send_keys(Keys.RETURN)
                        log(f"✅ PIN submitted (Enter key) for Profile {idx + 1}.")
                        time.sleep(0.3)
                else:
                    log(f"⚠️ PIN input not found for Profile {idx + 1} – skipping.")
            except Exception as e:
                log(f"⚠️ PIN entry error for Profile {idx + 1}: {e}")
        else:
            log("ℹ️ No PIN provided – skipping PIN entry.")

        time.sleep(1.0)
        overlay_still_visible = driver.find_elements(By.CSS_SELECTOR, "div.erc-multiple-profiles-layout, div[data-t='profile-selector']")
        if not overlay_still_visible or not overlay_still_visible[0].is_displayed():
            log(f"✅ Profile {idx + 1} unlocked successfully!")
            return True

        if is_pin_error_present(driver):
            log(f"❌ Incorrect PIN for Profile {idx + 1}.")
            if preferred_profile > 0:
                log(f"❌ Preferred profile {preferred_profile} failed. Exiting.")
                return False
            if idx < len(cards) - 1:
                log(f"🔄 Going back to select next profile...")
                if not go_back_to_profile_selection(driver):
                    log("⚠️ Could not go back. Trying to navigate directly to device page.")
                    driver.get(DEVICE_URL)
                    time.sleep(5)
                    if "device" in driver.current_url:
                        log("✅ Skipped profile selection (already in device page).")
                        return True
                    else:
                        log("❌ Failed to recover. Exiting.")
                        return False
                time.sleep(2)
                continue
            else:
                log(f"❌ All profiles failed. Exiting.")
                return False
        else:
            time.sleep(1.5)
            overlay_still_visible = driver.find_elements(By.CSS_SELECTOR, "div.erc-multiple-profiles-layout, div[data-t='profile-selector']")
            if not overlay_still_visible or not overlay_still_visible[0].is_displayed():
                log(f"✅ Profile {idx + 1} unlocked successfully!")
                return True
            else:
                log(f"⚠️ Unknown state for Profile {idx + 1}. Trying next.")
                if preferred_profile > 0:
                    log(f"❌ Preferred profile {preferred_profile} failed. Exiting.")
                    return False
                go_back_to_profile_selection(driver)
                continue

    log("❌ All profiles failed with the given PIN.")
    return False

# ===========================
# DEVICE MANAGEMENT FUNCTIONS
# ===========================
def human_move_mouse(driver, element, fast=False):
    action = ActionChains(driver)
    action.move_to_element_with_offset(element, random.randint(-5, 5), random.randint(-5, 5))
    pause_time = 0.05 if fast else random.uniform(0.1, 0.3)
    action.pause(pause_time)
    action.perform()

def wait_for_cloudflare(driver):
    try:
        if "Verifying you are human" in driver.page_source:
            log("⚠️ Cloudflare challenge detected!")
            log("   Please solve the CAPTCHA manually in the browser window.")
            input("👉 Press ENTER once you have completed the verification...")
            time.sleep(2)
            return True
    except:
        pass
    return False

def find_device_card(button):
    parent = button
    for _ in range(10):
        parent = parent.find_element(By.XPATH, "..")
        if "Location:" in parent.text:
            return parent
    return None

def get_device_buttons(driver, retries=2, headless=False):
    """Return list of (button, card, location, model, device_name) for non-ALL devices."""
    for attempt in range(retries):
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-t='deactivate-button']"))
            )
        except:
            if headless and attempt == 0:
                log("⏳ Waiting for device page to load...")
            time.sleep(1)
            continue

        buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-t='deactivate-button']")
        if buttons:
            result = []
            for btn in buttons:
                if "ALL" in btn.text.upper():
                    continue
                card = find_device_card(btn)
                if card is None:
                    continue
                lines = card.text.split('\n')
                # Extract location
                location = None
                for line in lines:
                    if "Location:" in line:
                        location = line.replace("Location:", "").strip()
                        break
                # Extract non-label lines (exclude "DEACTIVATE" and labels)
                name_lines = []
                for line in lines:
                    clean = line.strip()
                    if (clean and 
                        "Location:" not in clean and 
                        "Activation Date:" not in clean and 
                        "Last Used:" not in clean and
                        "Current Device" not in clean and
                        clean != "DEACTIVATE"):
                        name_lines.append(clean)
                # Assign model and device name
                model = name_lines[0] if len(name_lines) > 0 else "Unavailable"
                device_name = name_lines[1] if len(name_lines) > 1 else "Unavailable"
                result.append((btn, card, location or "Unknown Location", model, device_name))
            if result:
                return result
        if attempt < retries - 1:
            time.sleep(1)
    return []

def deactivate_device(driver, button, fast=False):
    accept_cookies_if_present(driver)

    try:
        human_move_mouse(driver, button, fast)
        time.sleep(0.1 if fast else random.uniform(0.2, 0.4))
        button.click()
        log("🔄 Deactivate clicked")
    except Exception as e:
        log(f"❌ Could not click device button: {e}")
        return False

    try:
        wait = WebDriverWait(driver, 5 if fast else 8)
        modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "dialog[data-t='deactivate-selected-modal']")))
        log("✅ Modal appeared")
    except:
        log("⚠️ Modal did not appear – assuming success")
        return True

    try:
        modal_btn = modal.find_element(By.CSS_SELECTOR, "button[data-t='deactivate-button']")
        human_move_mouse(driver, modal_btn, fast)
        time.sleep(0.1 if fast else random.uniform(0.2, 0.4))
        modal_btn.click()
        log("✅ Confirmed deactivation in modal")
    except:
        try:
            modal_btns = modal.find_elements(By.XPATH, ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'deactivate')]")
            if modal_btns:
                human_move_mouse(driver, modal_btns[0], fast)
                time.sleep(0.1 if fast else random.uniform(0.2, 0.4))
                modal_btns[0].click()
                log("✅ Confirmed (fallback)")
        except Exception as e2:
            log(f"❌ Modal confirm error: {e2}")
            return False

    try:
        WebDriverWait(driver, 5 if fast else 8).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "dialog[data-t='deactivate-selected-modal']")))
        log("✅ Modal closed")
    except:
        pass
    time.sleep(0.2 if fast else random.uniform(0.3, 0.7))
    return True

# ===========================
# CHECK IF LOGGED OUT
# ===========================
def is_logged_out(driver):
    current_url = driver.current_url
    return current_url.startswith("https://sso.crunchyroll.com/login")

# ===========================
# NORMAL MODE (CI: no interactive prompts)
# ===========================
def run_normal_mode(driver, allowed_locations, keep_device_names, keep_mode, headless=False):
    log("\n--- Normal Mode (CI) – using default delays ---\n")
    delay_no_change = 3
    delay_after_deactivation = 3
    delay_no_devices = 5

    log(f"✅ Delays set: no-change={delay_no_change}s, after-deact={delay_after_deactivation}s, no-devices={delay_no_devices}s\n")

    load_wait = 2

    while True:
        # Check if logged out
        if is_logged_out(driver):
            log("🔄 Session expired. Re-logging in...")
            if not login_and_select_profile(driver, EMAIL, PASSWORD, PIN, PREFERRED_PROFILE):
                log("❌ Re-login failed. Exiting.")
                break
            driver.get(DEVICE_URL)
            time.sleep(load_wait)

        driver.get(DEVICE_URL)
        time.sleep(load_wait)
        if wait_for_cloudflare(driver):
            driver.get(DEVICE_URL)
            time.sleep(load_wait)

        accept_cookies_if_present(driver)

        devices = get_device_buttons(driver, retries=2, headless=headless)
        if not devices:
            log("⚠️ No individual device buttons found.")
            log(f"⏳ Waiting {delay_no_devices:.1f} seconds...")
            time.sleep(delay_no_devices)
            continue

        total = len(devices)
        kept = 0
        skipped = 0
        current = 0
        deactivated_any = False

        for btn, card, location, model, device_name in devices:
            is_current = "Current Device" in card.text
            if is_current:
                current += 1
                continue

            # Determine if device should be kept based on KEEP_MODE
            location_match = False
            name_match = False

            if allowed_locations:
                for loc in allowed_locations:
                    if loc.lower() in location.lower():
                        location_match = True
                        break
            if keep_device_names:
                for name in keep_device_names:
                    if name.lower() in model.lower() or name.lower() in device_name.lower():
                        name_match = True
                        break

            if keep_mode == "AND":
                keep = location_match and name_match
            else:  # OR (default)
                keep = location_match or name_match

            if keep:
                kept += 1
                continue

            # Unwanted device – deactivate
            log(f"\n📱 Model: {model}")
            log(f"   📱 Device name: {device_name}")
            log(f"   📍 Location: {location}")
            log("   ❌ Deactivating...")
            success = deactivate_device(driver, btn, fast=False)
            if success:
                log("   ✅ Deactivation completed.")
                deactivated_any = True
                break
            else:
                log("   ❌ Deactivation failed – moving to next device.")
                skipped += 1

        if not deactivated_any:
            log(f"📊 Summary: {total} device(s) found. Current: {current}, Kept: {kept}, Skipped: {skipped}.")
            log(f"⏳ No devices to deactivate. Waiting {delay_no_change:.1f} seconds...")
            time.sleep(delay_no_change)
        else:
            log(f"⏳ Device deactivated. Waiting {delay_after_deactivation:.1f} seconds before re-checking...")
            time.sleep(delay_after_deactivation)

# ===========================
# EXTREME MODE (CI)
# ===========================
def run_extreme_mode(driver, allowed_locations, keep_device_names, keep_mode, headless=False):
    log("\n⚡ EXTREME MODE ENABLED – Very fast, may trigger rate limits!")
    log("   Press Ctrl+C to stop.\n")

    load_wait = 1

    while True:
        # Check if logged out
        if is_logged_out(driver):
            log("🔄 Session expired. Re-logging in...")
            if not login_and_select_profile(driver, EMAIL, PASSWORD, PIN, PREFERRED_PROFILE):
                log("❌ Re-login failed. Exiting.")
                break
            driver.get(DEVICE_URL)
            time.sleep(load_wait)

        driver.get(DEVICE_URL)
        time.sleep(load_wait)
        if wait_for_cloudflare(driver):
            driver.get(DEVICE_URL)
            time.sleep(load_wait)

        accept_cookies_if_present(driver)

        devices = get_device_buttons(driver, retries=2, headless=headless)
        if not devices:
            log("⚠️ No devices found.")
            time.sleep(2)
            continue

        total = len(devices)
        kept = 0
        skipped = 0
        current = 0
        deactivated_any = False

        for btn, card, location, model, device_name in devices:
            is_current = "Current Device" in card.text
            if is_current:
                current += 1
                continue

            location_match = False
            name_match = False

            if allowed_locations:
                for loc in allowed_locations:
                    if loc.lower() in location.lower():
                        location_match = True
                        break
            if keep_device_names:
                for name in keep_device_names:
                    if name.lower() in model.lower() or name.lower() in device_name.lower():
                        name_match = True
                        break

            if keep_mode == "AND":
                keep = location_match and name_match
            else:
                keep = location_match or name_match

            if keep:
                kept += 1
                continue

            # Unwanted device – deactivate
            log(f"\n📱 Model: {model}")
            log(f"   📱 Device name: {device_name}")
            log(f"   📍 Location: {location}")
            log("   ❌ Deactivating...")
            success = deactivate_device(driver, btn, fast=True)
            if success:
                log("   ✅ Deactivation completed.")
                deactivated_any = True
                break
            else:
                log("   ❌ Deactivation failed – moving to next device.")
                skipped += 1

        if not deactivated_any:
            log(f"📊 Summary: {total} device(s) found. Current: {current}, Kept: {kept}, Skipped: {skipped}.")
            time.sleep(1)
        else:
            log("⏳ Device deactivated. Quick pause before re-checking...")
            time.sleep(0.5)

# ===========================
# GET CHROME VERSION
# ===========================
def get_chrome_version():
    """Get the installed Chrome version."""
    try:
        result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        match = re.search(r"(\d+)\.\d+\.\d+\.\d+", version)
        if match:
            return int(match.group(1))
    except:
        pass
    return None

# ===========================
# MAIN
# ===========================
if __name__ == "__main__":
    log("\n⚡ Crunchyroll Device Keeper – CI Mode (with Device Name & Auto-Re-Login)")
    log("   (Auto‑installs dependencies if missing)\n")

    keep_conditions = []
    if allowed_locations:
        keep_conditions.append(f"Location: {', '.join(allowed_locations)}")
    if keep_device_names:
        keep_conditions.append(f"Device Name/Model: {', '.join(keep_device_names)}")
    log(f"   Keeping devices matching: {' OR '.join(keep_conditions)}")
    log(f"   Keep mode: {KEEP_MODE}")
    log(f"   Mode: {'Extreme' if MODE == '2' else 'Normal'}")
    log(f"   Headless: {HEADLESS}\n")

    # Clear previous session (fresh profile)
    if os.path.exists(PROFILE_BASE_DIR):
        shutil.rmtree(PROFILE_BASE_DIR)
        log("🧹 Cleared previous session cache.")
    os.makedirs(PROFILE_BASE_DIR, exist_ok=True)

    # Launch browser
    log("🚀 Opening Chrome (headless)...")
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_BASE_DIR}")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    # Get Chrome version and pass it to undetected-chromedriver
    chrome_version = get_chrome_version()
    if chrome_version:
        log(f"   Detected Chrome version: {chrome_version}")
        try:
            driver = uc.Chrome(options=options, headless=True, version_main=chrome_version)
        except:
            driver = uc.Chrome(options=options, headless=True)
    else:
        driver = uc.Chrome(options=options, headless=True)

    # Login
    login_success = login_and_select_profile(driver, EMAIL, PASSWORD, PIN, PREFERRED_PROFILE)
    if not login_success:
        log("❌ Login or profile selection failed. Exiting.")
        driver.quit()
        sys.exit(1)

    # Navigate to device page
    driver.get(DEVICE_URL)
    log("\n🔗 Device page opened.")
    if wait_for_cloudflare(driver):
        driver.get(DEVICE_URL)
        time.sleep(2)

    log("\n🔍 Running continuously until all unwanted devices are deactivated.\n")

    try:
        if MODE == "2":
            run_extreme_mode(driver, allowed_locations, keep_device_names, KEEP_MODE, headless=HEADLESS)
        else:
            run_normal_mode(driver, allowed_locations, keep_device_names, KEEP_MODE, headless=HEADLESS)
    except KeyboardInterrupt:
        log("\n🛑 Stopped by user.")
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        log("Browser closed.")
