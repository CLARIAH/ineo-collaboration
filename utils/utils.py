import re
import logging
from markdown_plain_text.extention import convert_to_plain_text


def is_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def remove_html_tags(html_str: str) -> str:
    """Remove html tags from a string"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_str)


def shorten_text(text: str, limit: int, more_characters: str = "...") -> str:
    """
    Shorten the text to a given limit and add more characters if the text is longer than the limit.
    """
    text = convert_to_plain_text(text)
    if text.startswith("{}"):
        text = "{code:und}" + text[2:]
    return text[:limit] + more_characters if len(text) > limit else text


def shorten_list_or_string(long_text: str | list, limit: int | None, more_characters: str):
    """
    Shorten the text to the given limit and add more_characters at the end.
    """
    if limit is None:
        return long_text
    if isinstance(long_text, list):
        shortened = [shorten_text(elem, limit, more_characters) for elem in long_text]
    elif isinstance(long_text, str):
        shortened = shorten_text(long_text, limit, more_characters)
    else:
        raise TypeError(f"Name field is not a string or a list: {type(long_text)} - {long_text}")
    return shortened
