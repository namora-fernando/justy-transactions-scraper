#!/usr/bin/env python
# coding: utf-8

import os
import re
import time
import getpass
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager

# =========================
# Configuration
# =========================

ESB_URL_LOGIN = "https://poslite.esb.co.id/"
ESB_URL_SALES_DETAIL = "https://poslite.esb.co.id/report/sales-detail/index"

OUTPUT_DIR = "output"
OUTPUT_FILENAME_PREFIX = "transactions"  # final file becomes transactions_YYYYMMDD_HHMMSS.csv

# How long to wait for common UI elements
DEFAULT_WAIT = 20
SHORT_WAIT = 5
VERY_SHORT_WAIT = 2


# =========================
# Utility helpers
# =========================

def log(msg: str):
    """Uniform console logging."""
    print(msg, flush=True)


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)


def timestamp_str():
    return time.strftime("%Y%m%d_%H%M%S")


def safe_click(driver, element):
    """
    Safely click an element by:
    1) Scrolling into view,
    2) Trying normal click,
    3) Falling back to JS click.
    """
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.2)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


# =========================
# Core scraping functions
# =========================

def launch_browser():
    log("Starting Justy Transactions Scraper")
    log("⏳ Initializing browser and dependencies... Please wait.")

    options = Options()
    # Suppress "DevTools listening" & USB/GCM spam
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver


def login(driver, email, password):
    log("🌐 Opening ESB Login page...")
    driver.get(ESB_URL_LOGIN)

    log("🔐 Filling credentials...")
    WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.presence_of_element_located((By.ID, "email"))
    ).send_keys(email)

    driver.find_element(By.ID, "password").send_keys(password)

    log("Submitting login form...")
    login_btn = WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(., 'Masuk')]"))
    )
    login_btn.click()

    WebDriverWait(driver, DEFAULT_WAIT).until(EC.url_contains("dashboard"))
    log("✅ Login success!")


def go_to_sales_detail(driver):
    log("➡️ Navigating to Sales Detail page...")
    driver.get(ESB_URL_SALES_DETAIL)


def prompt_date_range(driver):
    """
    Opens the date picker and prompts the user to manually select date range.
    The script resumes after the user presses ENTER in the terminal.
    """
    log("🗓️ Opening date range picker...")
    date_input = WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.element_to_be_clickable((By.XPATH, "//input[contains(@class,'filter-calendar')]"))
    )
    safe_click(driver, date_input)
    time.sleep(0.8)

    log('📌 Please select the initial and end date in the popup, then click "Pilih".')
    input("👉 Press ENTER here when you are done selecting the dates...")

    log('✅ Date range confirmed. Clicking "Tampilkan" to load data...')
    tampilkan_btn = WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Tampilkan']"))
    )
    safe_click(driver, tampilkan_btn)

    # Wait for the first table render (or refresh)
    WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span.table-anchor"))
    )
    log("📊 Transactions list loaded.")


def scrape_popup(driver, trans_id, debug=False):
    """
    Scrape the line items from the popup/drawer of a single transaction.
    Returns a list of dict rows with keys:
      - No_Transaksi
      - Nama_Item
      - Jumlah
      - Harga_Satuan
    """
    try:
        # Wait for modal/drawer to appear
        WebDriverWait(driver, SHORT_WAIT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-modal-body, .ant-drawer-body"))
        )
        # Wait for table inside
        WebDriverWait(driver, SHORT_WAIT).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ant-modal-body table, .ant-drawer-body table")
            )
        )
        # Wait for any skeletons to go away
        WebDriverWait(driver, SHORT_WAIT).until_not(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-skeleton, .ant-skeleton-element"))
        )

        rows_text = driver.execute_script("""
            const rows = document.querySelectorAll(
                '.ant-modal-body table tbody tr, .ant-drawer-body table tbody tr'
            );
            return Array.from(rows).map(r =>
                Array.from(r.querySelectorAll('td')).map(td => td.innerText.trim())
            );
        """)

        # Identify the slice of rows containing items
        start_idx = next((i for i, r in enumerate(rows_text) if len(r) >= 1 and r[0] == "Print"), None)
        end_idx = next((i for i, r in enumerate(rows_text) if len(r) >= 1 and r[0] == "Subtotal"), None)

        items = []
        if start_idx is not None and end_idx is not None and end_idx > start_idx:
            for r in rows_text[start_idx + 1:end_idx]:
                # skip empty rows
                if not any(r):
                    continue

                # Two possible shapes:
                # - main item: ['1 Jus Alpukat', 'Rp16.000']
                # - modifier : ['', '1 NORMAL ICE', 'Rp0']
                if r[0]:
                    name_qty = r[0]
                    price = r[-1] if len(r) > 1 else "0"
                else:
                    name_qty = r[1] if len(r) > 1 else ""
                    price = r[2] if len(r) > 2 else "0"

                # Parse quantity and item name
                parts = name_qty.split(" ", 1)
                if parts[0].isdigit():
                    qty = int(parts[0])
                    item_name = parts[1] if len(parts) > 1 else ""
                else:
                    qty = 1
                    item_name = name_qty

                items.append({
                    "No_Transaksi": trans_id,
                    "Nama_Item": item_name.strip(),
                    "Jumlah": qty,
                    "Harga_Satuan": price.replace("Rp", "").replace(".", "").strip()
                })

        return items

    except Exception as e:
        if debug:
            log(f"[debug] scrape_popup error for {trans_id}: {e}")
        return []


def iterate_pages_and_scrape(driver):
    """
    Iterate through all pages, open each transaction popup, scrape items, and close.
    Returns list of dict rows.
    """
    all_rows = []
    page_index = 1
    wait = WebDriverWait(driver, DEFAULT_WAIT)

    while True:
        # Re-fetch all visible transaction anchors on current page
        trans_spans = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.table-anchor"))
        )
        log(f"📄 Page {page_index}: found {len(trans_spans)} transactions.")

        for i in range(len(trans_spans)):
            # Because the DOM can refresh, re-query by index each time
            trans_spans = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.table-anchor"))
            )
            span = trans_spans[i]
            trans_id = span.text

            log(f"🔎 Opening popup for {trans_id} (#{i+1} on this page)...")
            # Make sure the specific element for this trans_id is clickable
            fresh_span = wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//span[text()='{trans_id}']"))
            )
            safe_click(driver, fresh_span)

            items = scrape_popup(driver, trans_id, debug=False)
            all_rows.extend(items)
            log(f"   ↳ Scraped {len(items)} line(s) from {trans_id}.")

            # Close the popup with ESC and wait for it to disappear (best-effort)
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            try:
                WebDriverWait(driver, VERY_SHORT_WAIT).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-modal-body, .ant-drawer-body"))
                )
            except TimeoutException:
                pass  # continue anyway

        # Try go to next page
        try:
            next_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li.ant-pagination-next button"))
            )
            # In some AntDesign versions, disabled state can be tracked by aria-disabled or class
            is_disabled = next_button.get_attribute("disabled") or "disabled" in (next_button.get_attribute("class") or "")
            if is_disabled:
                log("🏁 No more pages. Scraping complete.")
                break

            log("➡️  Moving to next page...")
            next_button.click()

            # Wait until the old first element becomes stale to ensure page changed
            try:
                WebDriverWait(driver, DEFAULT_WAIT).until(EC.staleness_of(trans_spans[0]))
            except StaleElementReferenceException:
                pass

            page_index += 1

        except TimeoutException:
            log("🏁 Next button not found. End of pagination.")
            break

    return all_rows


def export_csv(rows):
    ensure_output_dir()
    ts = timestamp_str()
    filename = f"{OUTPUT_FILENAME_PREFIX}_{ts}.csv"
    path = os.path.join(OUTPUT_DIR, filename)
    df = pd.DataFrame(rows, columns=["No_Transaksi", "Nama_Item", "Jumlah", "Harga_Satuan"])
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path, len(df)


# =========================
# Main
# =========================

def main():
    # Prompt credentials upfront so the user sees immediate activity (no silent wait)
    log("👤 Please provide your ESB POS credentials.")
    email = input("👉 Enter your email: ")
    password = getpass.getpass("👉 Enter your password: ")

    driver = None
    try:
        driver = launch_browser()
        login(driver, email, password)
        go_to_sales_detail(driver)
        prompt_date_range(driver)

        log("🧲 Starting transaction scraping...")
        all_rows = iterate_pages_and_scrape(driver)
        log(f"📦 Total raw rows scraped: {len(all_rows)}")

        log("💾 Exporting to CSV...")
        output_path, nrows = export_csv(all_rows)
        log(f"🎉 Done. {nrows} rows saved to: {output_path}")

    except Exception as e:
        log(f"❌ Unhandled error: {e}")
        raise
    finally:
        if driver is not None:
            log("👋 Closing browser...")
            try:
                driver.quit()
            except Exception:
                pass
        log("✅ Script finished.")


if __name__ == "__main__":
    main()




