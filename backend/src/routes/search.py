from fastapi import APIRouter
from pydantic import BaseModel

from ..tools.search_code import search_code

router=APIRouter(prefix='/api/search',tags=['Search'])

class SearchRequest(BaseModel):
    repo_id: str
    query: str
    k: int = 5

@router.post("")
def search_code_endpoint(request: SearchRequest):
    """Search the indexed repository for code relevant to a query"""
    results=search_code(repo_id=request.repo_id,query=request.query,k=request.k)
    return {"results":results}


