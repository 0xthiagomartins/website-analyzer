from pydantic import BaseModel
from collections import Counter
from typing import List, Tuple, Union, Optional


class W3CMessage(BaseModel):
    type: str  # info | error | non-document-error
    subtype: Optional[str]
    message: Optional[str]
    extract: Optional[
        str
    ]  # The "extract" string represents an extract of the document source from around the point in source designated for the message by the "line" and "column" numbers.
    offset: Optional[
        int
    ]  # The "offset" number is an UTF-16 code unit index into the "extract" string. The index identifies the same UTF-16 code unit in the extract that the "line" and "column" numbers identify in the full source. The first code unit has the index 0.
    url: Optional[str]
    line: Optional[int]
    column: Optional[int]


class W3Object(BaseModel):
    code: str
    type: Optional[str]
    encoding: Optional[str]


class W3CResponse(BaseModel):
    messages: list[W3CMessage]
    url: str | None
    source: str | None
    language: str | None


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
    w3c_validation: W3CResponse


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
