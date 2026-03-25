from pydantic import BaseModel, Field
from collections import Counter


class W3CMessage(BaseModel):
    type: str  # info | error | non-document-error
    subtype: str | None
    message: str | None
    extract: str | None  # The "extract" string represents an extract of the document source from around the point in source designated for the message by the "line" and "column" numbers.
    url: str | None
    first_line: int | None  # "firstLine",
    last_line: int | None  # "lastLine",
    first_column: int | None  # "firstColumn",
    last_column: int | None  # "lastColumn",
    hiliteStart: int | None  # "hiliteStart",
    hiliteLength: int | None  # "hiliteLength"


class W3CResponse(BaseModel):
    messages: list[W3CMessage]
    url: str | None
    source: str | None
    language: str | None


class KeyWord(BaseModel):
    word: str
    count: int


class Page(BaseModel):
    url: str
    title: str
    description: str
    word_count: int
    keywords: list[KeyWord] = Field(default_factory=list)
    bigrams: list[Counter[str]] = Field(default_factory=list)
    trigrams: list[Counter[str]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    content_hash: str | None = None  # Allow None values
    w3c_validation: W3CResponse | None = None


class Report(BaseModel):
    pages: list[Page]
    keywords: list[KeyWord]
    errors: list[str] = Field(default_factory=list)
    total_time: float
    duplicate_pages: list[list[str]]
