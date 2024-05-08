from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup 
import json
import os
import random
import time
import pandas as pd
import datetime as dt
import random

AUTHENTICATE = False
AUTHENTICATED_STATE_JSON = "state.json"
DEFAULT_DELAY = 1
DEFAULT_TIMEOUT = 20000 # 20 seconds
MAX_ATTEMPTS = 3

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

def login_via_google(new_page_info, login_data):
    new_page = new_page_info.value
    new_page.wait_for_load_state()
    new_page.get_by_role("textbox").fill(login_data["email"])
    time.sleep(DEFAULT_DELAY*5)
    new_page.keyboard.press("Enter")
    # Delay between email and password
    time.sleep(DEFAULT_DELAY*5)
    new_page.get_by_role("textbox").fill(login_data["password"])
    time.sleep(DEFAULT_DELAY*5)
    new_page.keyboard.press("Enter")

    # Captcha
    try:
        new_page.frame_locator("[title='title=\"reCAPTCHA\"']").click()
    except Exception as e:
        print(f"Exception: No Google reCAPTCHA Pop Up - {e}")

def extract_tweets_to_df(soup):
    tweet_elemets = soup.select("div[data-testid=\"cellInnerDiv\"]")
    base_url = "https://twitter.com"
    post_links_lst     = [] 
    post_username_lst  = []
    post_date_lst      = []
    post_time_lst      = []
    post_replies_lst   = []
    post_reposts_lst   = []
    post_likes_lst     = []
    post_bookmarks_lst = []
    post_views_lst     = []
    post_text_lst = []
    post_response_text_lst = []
    post_has_photo_lst = []
    post_has_video_lst = []
    for tweet in tweet_elemets:
        # Fetching all tags containing post links
        post_info_a_tags = [a_tag.parent for a_tag in tweet.select("a > time")] # Fetching all <a> tags that have time as a child (they are the specific ones for the tweets in the page, this filters the responses and other non related tweets)
        post_time_elements = tweet.select("a > time")
        # Fetches Replies | Reposts | Likes | Bookmarks | Views
        post_views_elements = tweet.select("div[role=\"group\"]")
        post_text_elements = tweet.select("div[data-testid=\"tweetText\"]")
        post_photo_elements = tweet.select("div[data-testid=\"tweetPhoto\"]")
        post_video_elements = tweet.select("div[data-testid=\"videoComponent\"]")
        # Fetching all links and infos
        post_link = [base_url+a_tag["href"] for a_tag in post_info_a_tags if (not "analytics" in a_tag["href"]) and (a_tag["href"].count("/") == 3)] # Number 3 here, becauce we add +2 with base url, so not 5, in fact 3
        post_username = [a_tag["href"][1:a_tag["href"].find("/", 1)] for a_tag in post_info_a_tags if (not "analytics" in a_tag["href"]) and (a_tag["href"].count("/") == 3)]
        post_date = [time_tag["datetime"][:time_tag["datetime"].find("T")] for time_tag in post_time_elements]
        post_time = [time_tag["datetime"][time_tag["datetime"].find("T")+1:time_tag["datetime"].find(".")] for time_tag in post_time_elements]        

        # We do not consider an element that does not have a tweet link (it's not a tweet)
        if not post_link:
            continue

        post_links_lst.append(post_link[0])
        post_username_lst.append(post_username[0])
        post_date_lst.append(post_date[0])
        post_time_lst.append(post_time[0])

        for a_tag in post_views_elements:
            replies, reposts, likes, bookmarks, views = [0 for _ in range(5)]
            # Checking if multiple elements
            if ", " in a_tag["aria-label"]:
                infos_lst = a_tag["aria-label"].split(", ")
                for info in infos_lst:
                    if "replie" in info:
                        replies = int(info.split(" ")[0])  
                    elif "repost" in info:
                        reposts = int(info.split(" ")[0])
                    elif "like" in info:
                        likes = int(info.split(" ")[0])
                    elif "bookmark" in info:
                        bookmarks = int(info.split(" ")[0])
                    elif "view" in info:
                        views = int(info.split(" ")[0])

            post_replies_lst.append(replies)
            post_reposts_lst.append(reposts)
            post_likes_lst.append(likes)
            post_bookmarks_lst.append(bookmarks)
            post_views_lst.append(views)

            # Collecting tweet and tweet_response texts
            tweet_text = ""
            # Main tweet text
            for _, child in enumerate(post_text_elements[0].children):
                tweet_text += child.text
            post_text_lst.append(tweet_text)
            response_tweet_text = "No response tweet"
            if len(post_text_elements)>1:
                # Response tweet text
                response_tweet_text = ""
                for _, child in enumerate(post_text_elements[1].children):
                    response_tweet_text += child.text
            post_response_text_lst.append(response_tweet_text)

            # Checking if post has photo | video
            post_has_video = "no"
            post_has_photo = "no"
            if len(post_video_elements)>0:
                post_has_video = "yes"
            else:
                if len(post_photo_elements)>0:
                    post_has_photo = "yes"
            post_has_video_lst.append(post_has_video)
            post_has_photo_lst.append(post_has_photo)

    # Compacting data into a dictionary
    data_dict = {"url":post_links_lst, 
                    "username":post_username_lst, 
                    "post-date":post_date_lst, 
                    "post-GMT-time":post_time_lst, 
                    "replies":post_replies_lst, 
                    "reposts":post_reposts_lst, 
                    "likes":post_likes_lst, 
                    "bookmarks":post_bookmarks_lst, 
                    "views":post_views_lst,
                    "tweet-text":post_text_lst,
                    "response-tweet-text":post_response_text_lst,
                    "has-photo":post_has_photo_lst,
                    "has-video":post_has_video_lst}
    
    # Print for debugging
    # for key, value in data_dict.items():
    #     print(f"{key}: Len: {len(value)}")
    # print(data_dict)
    
    df = pd.DataFrame(data_dict)
    return df

def scrape_tweets():
    login_json = "twitter_burner_account_login.json"
    with sync_playwright() as p:
        # Opening Browser context with random User Agent
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
        # If we need to login first
        if AUTHENTICATE:
            url = "https://twitter.com/i/flow/login"
            page.goto(url)
            logged_in = False
            login_data = fetch_login_data(login_json)
            try:
                google_login_credentials_pop_up = page.frame_locator("[title='Caixa de diálogo \"Fazer login com o Google\"']")
                if google_login_credentials_pop_up:
                    # Get page after a specific action (e.g. clicking a link)
                    with context.expect_page() as new_page_info:
                        google_login_credentials_pop_up.get_by_text("Continuar").click()
                    login_via_google(new_page_info, login_data)
                    logged_in = True
            except Exception as e:
                print(f"Exception: No Google Credentials Pop Up - {e}")

            # Checking if logged in via Google Credentials Pop Up - if so, ignore the regular login
            if not logged_in:
                # Login into account
                with context.expect_page() as new_page_info:
                    page.get_by_title('Botão \"Fazer login com o Google\"').click() # Opens a new tab
                login_via_google(new_page_info, login_data)

            time.sleep(DEFAULT_DELAY*60)
            
            # Save storage state into the file.
            context.storage_state(path=AUTHENTICATED_STATE_JSON)

        # Redirect to home
        df_keywords = pd.read_excel("keywords.xlsx")
        df_keywords = df_keywords[df_keywords["collect"]=="s"]
        errors_lst = []
        for i, row in df_keywords.iterrows():
            start_time = dt.datetime.now()
            attempts = 0
            success = False
            while attempts < MAX_ATTEMPTS:
                date_filter = f"since:{row['since'].strftime('%Y-%m-%d')} until:{row['until'].strftime('%Y-%m-%d')}"
                search_str = f"{row['keywords']} {date_filter}"
                print(f"Current search: {i} | {search_str}")
                url_explore = "https://twitter.com/explore"
                page.goto(url_explore)

                # Search Query Input
                time.sleep(DEFAULT_DELAY)
                try:
                    search_input = page.get_by_role("combobox")
                    search_input.click()
                    search_input.fill(search_str)
                    page.keyboard.press("Enter")
                except Exception as e:
                    error_str = f"Exception: Search Query Input - N° of attempts: {attempts} - Keyword: {row['keywords']} - {e}"
                    print(error_str)
                    attempts += 1
                    if attempts >= MAX_ATTEMPTS:
                        errors_lst.append(error_str)
                    continue

                # Latest Tweets Tab
                time.sleep(DEFAULT_DELAY)
                try:
                    lastest_tab = page.get_by_text("Latest")
                    lastest_tab.click()
                except Exception as e:
                    error_str = f"Exception: Latest Tweets Tab - N° of attempts: {attempts} - Keyword: {row['keywords']} - {e}"
                    print(error_str)
                    attempts += 1
                    if attempts >= MAX_ATTEMPTS:
                        errors_lst.append(error_str)
                    continue

                # Delay For Fetching Posts
                time.sleep(DEFAULT_DELAY)
                # Start infinite scrolling until we reach the end of the page
                df_lst = []
                prev_height = None
                it_counter = 0
                while True: #make the range as long as needed
                    it_counter +=1
                    print(f"Scroll Iterations Counter: {it_counter} | Keyword: {row['keywords']}")
                    # Fetching All Posts Wrapper
                    try:
                        posts_wrapper = page.locator("[aria-label='Timeline: Search timeline']")
                        soup = BeautifulSoup(posts_wrapper.inner_html(), "html.parser")
                        df_lst.append(extract_tweets_to_df(soup))
                        # Remove these 2 lines down below to normal code execution
                        # success = True 
                        # break
                    except Exception as e:
                        error_str = f"Exception: Fetching All Posts Wrapper - N° of attempts: {attempts} - Keyword: {row['keywords']} - {e}"
                        print(error_str)
                        attempts += 1
                        if attempts >= MAX_ATTEMPTS:
                            errors_lst.append(error_str)
                        break
                    # Fetching current page height
                    curr_height = page.evaluate('(window.innerHeight + window.scrollY)')
                    # The first argument is horizontal scroll | second argument is vertical scroll (positive = down | negative = up)
                    page.mouse.wheel(0, 800)
                    time.sleep(DEFAULT_DELAY*random.randint(1,5))
                    # Starting the scroll
                    if not prev_height:
                        prev_height = curr_height
                        time.sleep(DEFAULT_DELAY*2)
                    # Case where the scroll did not create any effects (meaning we have reached the end of the page) SUCCESS!
                    elif prev_height == curr_height:
                        success = True
                        break
                    # If we are mid scrolling and new content has appeared
                    else:
                        prev_height = curr_height
                        time.sleep(DEFAULT_DELAY*2)
                # Checking if collect went successfully
                if success:
                    end_time = dt.datetime.now()
                    total_collect_time = end_time - start_time
                    print(f"Finished collecting all tweets from - Keyword: {row['keywords']}\nTime Spent: {total_collect_time}")
                    break
            # If no errors
            if df_lst:
                # Generating a single dataframe with all data
                df = pd.concat(df_lst)
                # Remove possible duplicates
                df = df.drop_duplicates(subset=["url"])
                df.to_excel(f"{os.getcwd()}\\coletas\\{row['keywords']}-{dt.datetime.now().strftime('%d-%m-%Y-%H-%M')}.xlsx", index=False)
            if errors_lst:
                with open(f"{os.getcwd()}\\coletas\\error_logs-{row['keywords']}.txt", "w+", encoding="utf-8") as fd:
                    fd.writelines(errors_lst)
        browser.close()

def main():
    scrape_tweets()
    path = f"{os.getcwd()}\\coletas\\twitter-scraper-coletas-finais-com-texto\\"
    if not os.path.isdir(path):
        os.mkdir(path)
    df_lst = []
    for file in os.listdir(path):
        if file.endswith(".xlsx"):
            print(file)
            df = pd.read_excel(path+file)
            df["keywords"] = file.split("-")[0]
            df_lst.append(df)
    df_final = pd.concat(df_lst)
    df_final.to_excel(f"coleta-unificada-{dt.datetime.now().strftime('%d-%m-%Y')}.xlsx", index=False)

if __name__ == "__main__":
    main()
