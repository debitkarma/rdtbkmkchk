import os

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from praw import Reddit
from praw.models import Comment, ListingGenerator, Submission  # , Subreddit
from typing import Dict, List, Tuple, Union
from urllib.parse import ParseResult, urlparse


def load_settings_from_env() -> Union[Dict[str, str], None]:
    load_dotenv()
    creds = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "password": os.getenv("PASSWORD"),
        "username": os.getenv("USERNAME"),
        "user_agent": os.getenv("USER_AGENT"),
    }
    for key in creds.keys():
        if not creds[key]:
            raise KeyError
    creds["blacklist_file"] = os.getenv("BLACKLISTFILE")
    creds["whitelist_file"] = os.getenv("WHITELISTFILE")
    creds["subreddits_file"] = os.getenv("SUBREDDITSFILE")
    LIMIT = os.getenv("LIMIT")
    try:
        LIMIT = int(LIMIT)
    except:  # noqa: E722
        LIMIT = None
    creds["LIMIT"] = LIMIT
    return creds


def get_reddit_instance(creds: Dict[str, str]) -> Reddit:
    rdt = Reddit(**creds)
    return rdt


def authenticated(creds: dict) -> bool:
    logged_in_name = ""
    try:
        rdt = Reddit(**creds)
        logged_in_name = rdt.user.me().name
    except Exception as e:
        print(f"Failed to authenticate: {e}")
    return creds["username"] == logged_in_name


def test_loading_env():
    creds = load_settings_from_env()
    if not creds:
        print("Failed to load creds... Are any env vars blank/missing?")
    try:
        print(creds["username"])
    except Exception as e:
        print(f"Failed to load creds: {e} \n")


def get_saved_items_of_subreddit(
    reddit_obj: Reddit, limit: Union[int, None], subreddit_name: str
) -> List[Union[Submission, Comment]]:
    saved_items_gen: ListingGenerator = reddit_obj.user.me().saved(limit=limit)
    items: List[Union[Submission, Comment]] = []
    for item in saved_items_gen:
        if item.subreddit.display_name == subreddit_name:
            items.append(item)
    return items


def separate_submissions_comments(
    items: List[Union[Submission, Comment]],
) -> Tuple[List[Submission], List[Comment]]:
    submissions_list: List[Submission] = []
    comments_list: List[Comment] = []
    for item in items:
        if type(item) is Submission:
            submissions_list.append(item)
        elif type(item) is Comment:
            comments_list.append(item)

    return (submissions_list, comments_list)


def pull_links_submissions(submission_entry: Submission) -> List[str]:
    html_content = submission_entry.selftext_html
    soup = BeautifulSoup(html_content, "html.parser")
    links = soup.find_all("a")
    urls = [link.get("href") for link in links]
    return urls


def pull_links_comments(comment_entry: Comment) -> List[str]:
    html_content = comment_entry.body_html
    soup = BeautifulSoup(html_content, "html.parser")
    links = soup.find_all("a")
    urls = [link.get("href") for link in links]
    return urls


def filter_urls(
    urls: List[str], blacklist: List[str] = list(), whitelist: List[str] = list()
) -> List[str]:
    parsed_urls = [urlparse(url) for url in urls]
    # reddit urls to users or subs only have path, no netloc
    # '/u/username' or 'r/subreddit'
    filtered_urls: List[ParseResult] = [url for url in parsed_urls if url.netloc]
    if blacklist:
        filtered_urls: List[ParseResult] = [
            url for url in filtered_urls if url.netloc in blacklist
        ]
    if whitelist:
        filtered_urls: List[ParseResult] = [
            url for url in filtered_urls if url.netloc in whitelist
        ]
    return [parsed_url.geturl() for parsed_url in filtered_urls]


def load_list_from_file(list_file: str) -> List[str]:
    lst = []
    try:
        with open(list_file, "r") as f:
            for line in f:
                if line and not line.startswith("#"):
                    lst.append(line.strip().lower())
                else:
                    continue
    except Exception as e:
        print(f"could not load {list_file}: {e} \n\n returning empty list...")
    return lst


if __name__ == "__main__":
    test_loading_env()
    creds = load_settings_from_env()

    LIMIT = creds.pop("LIMIT")

    blacklist_file = creds.pop("blacklist_file")
    blacklist = load_list_from_file(blacklist_file)
    whitelist_file = creds.pop("whitelist_file")
    whitelist = load_list_from_file(whitelist_file)

    subreddits_file = creds.pop("subreddits_file")
    subreddits_list = load_list_from_file(subreddits_file)
    only_one_subreddit = False

    if len(subreddits_list) == 1:
        only_one_subreddit = True

    rdt = get_reddit_instance(creds)
    saved_items: List[Union[Submission, Comment]] = list()

    if only_one_subreddit:
        saved_items = get_saved_items_of_subreddit(rdt, LIMIT, *subreddits_list)
    else:
        for sub in subreddits_list:
            saved_items.extend(get_saved_items_of_subreddit(rdt, LIMIT, sub))

    saved_submissions, saved_comments = separate_submissions_comments(items=saved_items)
    urls = list()

    for submission in saved_submissions:
        urls.extend(pull_links_submissions(submission))

    for comment in saved_comments:
        urls.extend(pull_links_comments(comment))

    filtered_urls = filter_urls(urls, blacklist, whitelist)
    for url in filtered_urls:
        print(url)
