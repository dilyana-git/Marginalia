from enum import Enum


class WorkFormat(str, Enum):
    book = "book"
    essay = "essay"
    article = "article"
    video = "video"
    podcast = "podcast"
    course = "course"
    series = "series"
    reference = "reference"
    other = "other"


class WorkTier(str, Enum):
    footpath = "footpath"
    ridge = "ridge"
    summit = "summit"
    unranked = "unranked"


class WorkStatus(str, Enum):
    want = "want"
    reading = "reading"
    read = "read"
    abandoned = "abandoned"
    saved = "saved"


class SeedOrigin(str, Enum):
    course = "course"
    dispatch = "dispatch"
    addition = "addition"
    manual = "manual"


class JournalKind(str, Enum):
    reflection = "reflection"
    quote = "quote"
    summary = "summary"
    question = "question"
    free = "free"


class FeedType(str, Enum):
    rss = "rss"
    reddit = "reddit"
    youtube = "youtube"
    x = "x"
    other = "other"


class FeedKind(str, Enum):
    blog = "blog"
    substack = "substack"
    subreddit = "subreddit"
    youtube_channel = "youtube_channel"
    magazine = "magazine"
    podcast = "podcast"
    aggregator = "aggregator"


class NewsletterItemStatus(str, Enum):
    new = "new"
    sent = "sent"
    saved_to_works = "saved_to_works"
    dismissed = "dismissed"
