from pydantic import BaseModel
from typing import List

class QuestionRequest(BaseModel):
    question: str

class Source(BaseModel):
    page: int
    content: str
    score: float

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Source]
