from playwright.sync_api import sync_playwright, expect
import json
import os
import random
import time

AUTHENTICATE = True
AUTHENTICATED_STATE_JSON = "state.json"
DEFAULT_TIMEOUT = 5000 # 5 seconds

def fetch_login_data(login_json):
    if os.path.isfile(login_json):
        with open(login_json, "r", encoding="utf-8") as fd:
            login_data = json.load(fd)
            return login_data


def random_ua(k=1):
    # returns a random useragent from the latest user agents strings list, weighted
    # according to observed prevalance
    ua_pct = {"ua": 
    {"0": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36", 
    "1": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "2": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
    "3": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "4": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "5": "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "6": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
    "7": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "8": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
    "9": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "10": "Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "11": "Mozilla/5.0 (Windows NT 10.0; rv:105.0) Gecko/20100101 Firefox/105.0",
    "12": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0",
    "13": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "14": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"},
    "pct": {"0": 28.8, "1": 13.28, "2": 10.98, "3": 8.55, "4": 6.25, "5": 5.56, "6": 4.53, "7": 4.27, "8": 3.57, "9": 2.93, "10": 2.99, "11": 2.55, "12": 2.44, "13": 1.7, "14": 1.59}}
    return random.choices(list(ua_pct['ua'].values()), list(ua_pct['pct'].values()), k=k)

def login_via_google(context, new_page_info, login_data):
    new_page = new_page_info.value
    new_page.wait_for_load_state()
    new_page.get_by_role("textbox").fill(login_data["email"])
    time.sleep(3)
    new_page.keyboard.press("Enter")
    # Delay between email and password
    time.sleep(3)
    new_page.get_by_role("textbox").fill(login_data["password"])
    time.sleep(3)
    new_page.keyboard.press("Enter")

    # Captcha
    try:
        new_page.frame_locator("[title='title=\"reCAPTCHA\"']").click()
    except Exception as e:
        print(f"Exception: No Google reCAPTCHA Pop Up - {e}")

    # Save storage state into the file.
    context.storage_state(path=AUTHENTICATED_STATE_JSON)

def scrape_tweets():
    login_json = "twitter_burner_account_login.json"
    with sync_playwright() as p:
        # Opening Browser context with random User Agent
        url = "https://twitter.com/i/flow/login"
        user_agent = random_ua()[0]
        args = ["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"]
        ignore_default_args = ["--disable-component-extensions-with-background-pages"]
        browser = p.chromium.launch(headless=False, args=args, ignore_default_args=ignore_default_args)
        if AUTHENTICATE:
            context = browser.new_context(user_agent=user_agent)
        else:
            context = browser.new_context(user_agent=user_agent, storage_state=AUTHENTICATED_STATE_JSON)
        # Default timeout to 5 seconds
        context.set_default_timeout(DEFAULT_TIMEOUT)
        page = context.new_page()
        page.goto(url)
        if AUTHENTICATE:
            logged_in = False
            login_data = fetch_login_data(login_json)
            try:
                google_login_credentials_pop_up = page.frame_locator("[title='Caixa de diálogo \"Fazer login com o Google\"']")
                if google_login_credentials_pop_up:
                    # Get page after a specific action (e.g. clicking a link)
                    with context.expect_page() as new_page_info:
                        google_login_credentials_pop_up.get_by_text("Continuar").click()
                    login_via_google(context, new_page_info, login_data)
                    logged_in = True
            except Exception as e:
                print(f"Exception: No Google Credentials Pop Up - {e}")

            # Checking if logged in via Google Credentials Pop Up - if so, ignore the regular login
            if not logged_in:
                # Login into account
                with context.expect_page() as new_page_info:
                    page.get_by_title('Botão \"Fazer login com o Google\"').click() # Opens a new tab
                login_via_google(context, new_page_info, login_data)

        # Redirect to home
        page.goto("https://twitter.com/home")
        time.sleep(10000)
        browser.close()

def main():
    scrape_tweets()

if __name__ == "__main__":
    main()