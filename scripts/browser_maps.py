"""Browser harness: Manus reference + GCP Maps API key."""
import sys
import time
sys.path.insert(0, r"C:\Users\abiyy\.cursor\skills\browser-harness\src")

from browser_harness.helpers import (
    capture_screenshot,
    goto_url,
    js,
    new_tab,
    page_info,
    wait_for_load,
)

# 1) Manus reference
new_tab("https://niagacrm-odnhqj3c.manus.space/")
wait_for_load(20)
time.sleep(3)
capture_screenshot("manus-reference-home.png")
info = page_info()
print("MANUS_URL:", info.get("url"))
print("MANUS_TITLE:", info.get("title"))
# Grab colors / structure hints
structure = js("""
(() => {
  const styles = getComputedStyle(document.body);
  const h1 = document.querySelector('h1');
  const buttons = [...document.querySelectorAll('button,a')].slice(0, 8).map(el => ({
    tag: el.tagName,
    text: (el.innerText||'').slice(0, 40),
    bg: getComputedStyle(el).backgroundColor,
    color: getComputedStyle(el).color,
  }));
  return JSON.stringify({
    bodyBg: styles.backgroundColor,
    bodyColor: styles.color,
    fontFamily: styles.fontFamily,
    h1: h1 ? h1.innerText.slice(0, 80) : null,
    buttons,
    navLinks: [...document.querySelectorAll('nav a, header a')].slice(0, 10).map(a => a.innerText.trim()),
  }, null, 2);
})()
""")
print("MANUS_STRUCTURE:", structure)

# 2) GCP credentials (user must be logged in)
new_tab("https://console.cloud.google.com/apis/credentials?project=niaga-496405")
wait_for_load(25)
time.sleep(4)
capture_screenshot("gcp-credentials.png")
print("GCP_URL:", page_info().get("url"))
print("GCP_TITLE:", page_info().get("title"))
