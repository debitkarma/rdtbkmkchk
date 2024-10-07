# rdt bkmk chk

Reddit bookmark check

This is a toy project to learn to use `praw` and build functionality to check the local user's bookmarks.

From there, probably some basic filtering and other stuff will be added.

### Pre-requisites

Presumably, you have already [registered an app with reddit](https://old.reddit.com/prefs/apps/), and followed the [instructions in PRAW's docs](https://praw.readthedocs.io/en/stable/getting_started/authentication.html) on choosing an auth method for the type of app you want. Both will influence each other - make decisions simultaneously.

I chose a scripting app, with a redirect URI of `http://localhost:8080`, since some URI is mandatory.

### Environment Variables

You should have a `.env` file loaded. It should have the following variables:

```
CLIENT_ID=client id is listed right under the app name
SECRET=secret is listed once you register the app on reddit
PASSWORD=
USERNAME=
USER_AGENT="app name by u/USERNAME"
```

You can just load those into a `dict` and pass it to the `praw.Reddit` method. And... you're off to the races!

