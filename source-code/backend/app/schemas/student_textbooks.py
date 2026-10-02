from pydantic import BaseModel


class StudentTextbookTopic(BaseModel):
    topicRef: str
    code: str
    title: str
    pageCount: int
    contentVersion: int
    publishedAt: str


class StudentTextbookGroup(BaseModel):
    code: str
    title: str
    topics: list[StudentTextbookTopic]


class StudentTextbook(BaseModel):
    textbookRef: str
    subjectId: str
    title: str
    edition: str
    publisher: str
    groupLabel: str
    structureVersion: int
    structurePublishedAt: str
    groups: list[StudentTextbookGroup]


class StudentTextbookList(BaseModel):
    textbooks: list[StudentTextbook]


class StudentTextbookSection(BaseModel):
    kind: str
    text: str


class StudentTextbookVisual(BaseModel):
    assetRef: str
    caption: str
    altText: str
    contentUrl: str


class StudentTextbookPage(BaseModel):
    ordinal: int
    pageNumber: int
    printedPage: str | None
    imageUrl: str
    sections: list[StudentTextbookSection]
    visuals: list[StudentTextbookVisual]


class StudentTextbookReferencePage(BaseModel):
    ordinal: int
    pageNumber: int
    printedPage: str
    imageUrl: str


class StudentTextbookReference(BaseModel):
    ordinal: int
    filename: str
    pages: list[StudentTextbookReferencePage]


class StudentTextbookTopicContent(BaseModel):
    textbookRef: str
    textbookTitle: str
    subjectId: str
    groupCode: str
    groupTitle: str
    topicRef: str
    topicCode: str
    topicTitle: str
    contentVersion: int
    publishedAt: str
    pages: list[StudentTextbookPage]
    visualReferences: list[StudentTextbookReference]
    additionalVisuals: list[StudentTextbookVisual]
