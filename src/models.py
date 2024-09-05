from pydantic import BaseModel, Field
from collections import Counter
from typing import List, Tuple, Union, Optional


class W3CMessage(BaseModel):
    type: str  # info | error | non-document-error
    subtype: Optional[str]
    message: Optional[str]
    extract: Optional[
        str
    ]  # The "extract" string represents an extract of the document source from around the point in source designated for the message by the "line" and "column" numbers.
    first_line: Optional[int]  # "firstLine",
    last_line: Optional[int]  # "lastLine",
    first_column: Optional[int]  # "firstColumn",
    last_column: Optional[int]  # "lastColumn",
    hiliteStart: Optional[int]  # "hiliteStart",
    hiliteLength: Optional[int]  # "hiliteLength"


class W3Object(BaseModel):
    code: str
    type: Optional[str]
    encoding: Optional[str]


class W3CResponse(BaseModel):
    messages: list[W3CMessage]
    url: Optional[str]
    source: Optional[str]
    language: Optional[str]


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
    warnings: List[str] = Field(default_factory=lambda: list(set()))
    content_hash: Optional[str] = None  # Allow None values
    w3c_validation: W3CResponse | None


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
