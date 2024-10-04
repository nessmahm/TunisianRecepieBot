from typing import TypedDict, List
from langchain_core.pydantic_v1 import BaseModel
class AgentState(TypedDict):
    task: str
    draft: str
    content: List[str]
    sources: List[str]
    revision_number: int
    max_revisions: int
    hallucination_check : str

class Queries(BaseModel):
    queries: List[str]
