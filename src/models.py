from pydantic import BaseModel
from collections import Counter
from typing import List, Tuple, Union, Optional


class Page(BaseModel):
    url: str
    title: str
    description: str
    word_count: int
    keywords: List[
        Union[Tuple[int, str], List[Union[int, str]]]
    ]  # Allow both tuple and list formats
    bigrams: List[Counter]
    trigrams: List[Counter]
    warnings: List[str]
    content_hash: Optional[str] = None  # Allow None values


class KeyWord(BaseModel):
    word: str
    count: int


class Errors(BaseModel):
    pass


class Report(BaseModel):
    pages: list[Page]
    keywords: list[KeyWord]
    errors: list[Errors] | None
    total_time: float
    duplicate_pages: list[list[str]]
