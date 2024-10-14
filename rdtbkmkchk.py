import os

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from praw import Reddit
from praw.models import Comment, ListingGenerator, Submission  # , Subreddit
from sys import stderr
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
            logger.error(f"Missing setting for {key}; FAILURE")
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
        logger.error(f"Failed to authenticate: {e}")
    return creds["username"] == logged_in_name


def test_loading_env():
    creds = load_settings_from_env()
    if not creds:
        logger.error("Failed to load creds... Are any env vars blank/missing?")
    try:
        logger.info(creds["username"])
    except Exception as e:
        logger.error(f"Failed to load creds: {e} \n")


def get_saved_items_of_subreddit(
    reddit_obj: Reddit, limit: Union[int, None], subreddit_name: str
) -> List[Union[Submission, Comment]]:
    saved_items_gen: ListingGenerator = reddit_obj.user.me().saved(limit=limit)
    items: List[Union[Submission, Comment]] = []
    for item in saved_items_gen:
        if item.subreddit.display_name == subreddit_name:
            items.append(item)
    return items


def filter_title_for_saved_items(
    submissions_list: List[Submission], filter_terms: List[str]
) -> List[Submission]:
    filtered_list = []
    for submission in submissions_list:
        if any([True if term in submission.title else False for term in filter_terms]):
            logger.debug(f"EXCLUDING (Title Filter) {submission.id}")
            continue
        else:
            filtered_list.append(submission)
    logger.debug(
        f"Title filter reduced submissions down to {len(filtered_list)/len(submissions_list)}"
    )


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
    logger.info(
        f"pulling links from {submission_entry.id}: {submission_entry.selftext}"
    )
    html_content = submission_entry.selftext_html
    if not html_content:
        logger.warning(
            f"Submission {submission_entry.id}/{submission_entry.title} looks to be removed"
        )
        return []
    logger.debug(f"{html_content = }")
    soup = BeautifulSoup(html_content, "html.parser")
    links = soup.find_all("a")
    urls = [link.get("href") for link in links]
    return urls


def pull_links_comments(comment_entry: Comment) -> List[str]:
    logger.info(f"pulling links from {comment_entry.id}: {comment_entry.body}")
    html_content = comment_entry.body_html
    if not html_content:
        logger.warning(f"Comment {comment_entry.id} looks to be removed")
        return []
    soup = BeautifulSoup(html_content, "html.parser")
    links = soup.find_all("a")
    urls = [link.get("href") for link in links]
    return urls


def put_urls_through_filters(
    urls: List[str], blacklist: List[str] = list(), whitelist: List[str] = list()
) -> List[str]:
    parsed_urls = [urlparse(url) for url in urls]
    # reddit urls to users or subs only have path, no netloc
    # '/u/username' or 'r/subreddit'
    filtered_urls: List[ParseResult] = [url for url in parsed_urls if url.netloc]
    logger.debug(f"{filtered_urls = }")

    if blacklist:
        not_blacklisted = []
        for url in filtered_urls:
            if any([True if item in url.netloc else False for item in blacklist]):
                logger.debug(f"EXCLUDING (Blacklisted) {url}")
                continue
            else:
                not_blacklisted.append(url)
        logger.debug(f"Found blacklist, filtered list down to: \n {not_blacklisted}")
        filtered_urls = not_blacklisted

    if whitelist:
        whitelisted = []
        for url in filtered_urls:
            if any([True if item in url.netloc else False for item in whitelist]):
                whitelisted.append(url)
            else:
                logger.debug(f"EXCLUDING (!Whitelisted) {url}")
        logger.debug(f"Found whitelist, filtered list down to: \n {filtered_urls}")
        filtered_urls = whitelisted

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
        logger.warning(f"could not load {list_file}: {e} \n\n returning empty list...")
    return lst


if __name__ == "__main__":
    # test_loading_env()
    logger.remove()
    logger.add(stderr, level="DEBUG")

    creds = load_settings_from_env()
    logger.debug(f"loaded creds for {creds["username"]}")

    LIMIT = creds.pop("LIMIT")
    logger.info(f"limit of saved entries to pull is {LIMIT}")

    blacklist_file = creds.pop("blacklist_file")
    blacklist = load_list_from_file(blacklist_file)
    logger.debug(f"blacklist ({len(blacklist)}): {blacklist}")

    whitelist_file = creds.pop("whitelist_file")
    whitelist = load_list_from_file(whitelist_file)
    logger.debug(f"whitelist ({len(whitelist)}): {whitelist}")

    subreddits_file = creds.pop("subreddits_file")
    subreddits_list = load_list_from_file(subreddits_file)
    logger.debug(f"subreddits_list ({len(subreddits_list)}): {subreddits_list}")

    only_one_subreddit = False

    if len(subreddits_list) == 1:
        only_one_subreddit = True

    logger.info(f"{only_one_subreddit = }")
    rdt = get_reddit_instance(creds)
    saved_items: List[Union[Submission, Comment]] = list()

    if only_one_subreddit:
        saved_items = get_saved_items_of_subreddit(rdt, LIMIT, *subreddits_list)
    else:
        for sub in subreddits_list:
            saved_items.extend(get_saved_items_of_subreddit(rdt, LIMIT, sub))

    saved_submissions, saved_comments = separate_submissions_comments(items=saved_items)
    logger.info(
        f"Counts:\nSubmittions: {len(saved_submissions)} ; Comments: {len(saved_comments)}"
    )
    logger.debug(f"{saved_submissions = } \n\n {saved_comments = }")

    urls = list()

    for submission in saved_submissions:
        urls.extend(pull_links_submissions(submission))

    for comment in saved_comments:
        urls.extend(pull_links_comments(comment))

    logger.debug(f"List of URLS: {urls}")

    filtered_urls = put_urls_through_filters(urls, blacklist, whitelist)
    logger.info("URLs found:\n")
    for url in filtered_urls:
        logger.info(f"{url}")
