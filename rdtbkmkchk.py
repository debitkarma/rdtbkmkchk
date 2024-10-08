import os
import praw

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from praw.models import Comment, ListingGenerator, Reddit, Subreddit, Submission
from typing import Dict, List, Tuple, Union


def load_env() -> Union[Dict[str, str], None]:
    creds = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "password": os.getenv("PASSWORD"),
        "username": os.getenv("USERNAME"),
        "user_agent": os.getenv("USER_AGENT"),
    }
    for key in creds.keys():
        if not creds[key]:
            return None
    return creds


def authenticated(creds: dict) -> bool:
    rdt = praw.Reddit(*creds)
    return creds["username"] == rdt.user.me()


def test_loading_env():
    load_dotenv()
    creds = load_env()
    print(creds["username"])


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
