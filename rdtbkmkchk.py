import os

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from praw import Reddit
from praw.models import Comment, ListingGenerator, Subreddit, Submission
from typing import Dict, List, Tuple, Union


def load_env() -> Union[Dict[str, str], None]:
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
    creds = load_env()
    if not creds:
        print("Failed to load creds... Are any env vars blank/missing?")
    try:
        print(creds["username"])
    except Exception as e:
        print(f"Failed to load creds: {e} \n")


def get_saved_items_of_subreddit(
    reddit_obj: Reddit, limit: Union[int, None], subreddit_name: str
) -> List[Union[Submission, Comment]]:
    saved_items_gen: ListingGenerator = Reddit.saved(limit=limit)
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


if __name__ == "__main__":
    test_loading_env()
    creds = load_env()
    rdt = get_reddit_instance(creds)
    print(authenticated(creds))
