from fastapi import FastAPI, Query
from pydantic import BaseModel
from VectorSearch import *
from fastapi import HTTPException, status
from typing import List  


app = FastAPI()

@app.get("/")
def root():
    return {"Hello": "World"}


@app.get("/search")
async def search(query: str, limit: int = 5):
    """TF-IDF 向量搜索"""
    inverted_index = create_inverted_index(documents.documents)
    matches = perform_tfidf_search(query, documents.documents, inverted_index)
    return {"results": matches[:limit]}

@app.get("/search/boolean")
async def boolean_search(query: str):
    """支持 AND/OR/NOT 的布林搜索"""
    inverted_index = create_inverted_index(documents.documents)
    matches = perform_boolean_search(query, documents.documents, inverted_index)
    return {"results": matches}

@app.post("/documents")
async def add_document(content: str):
    """添加新文檔"""
    new_id = add_new_document(content)
    return {"id": new_id, "message": "Document added"}


@app.post("/documents/batch")
async def add_documents_batch(contents: List[str]):
    """批量添加多個文檔"""
    try:
        new_ids = add_new_documents_batch(contents)
        if not new_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid documents were added"
            )
        return {
            "message": f"Successfully added {len(new_ids)} documents",
            "ids": new_ids
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding documents: {str(e)}"
        )

@app.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    """根據 ID 獲取文檔"""
    if doc_id not in documents.documents:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": doc_id, "content": documents.documents[doc_id]}

@app.delete("/documents/{doc_id}")
async def delete_document_by_id(doc_id: int):
    """刪除特定 ID 的文檔"""
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": f"Document {doc_id} deleted successfully"}

class DeleteBatchRequest(BaseModel):
    doc_ids: List[int]
    
#這裡批量刪除使用了post而不是delete
@app.post("/documents/batch/delete")
async def delete_documents_batch(request: DeleteBatchRequest):
    """批量刪除指定文檔 (使用JSON body版本)"""
    doc_ids = request.doc_ids
    not_found_ids = []
    deleted_count = 0

    for doc_id in doc_ids:
        if doc_id not in documents.documents:
            not_found_ids.append(doc_id)
            continue
        
        del documents.documents[doc_id]
        deleted_count += 1

    save_documents_to_file()

    response = {
        "message": "刪除操作完成",
        "deleted_count": deleted_count,
    }
    
    if not_found_ids:
        response.update({
            "detail": "部分文檔不存在",
            "not_found_ids": not_found_ids
        })
    else:
        response["detail"] = "所有文檔已成功刪除"

    return response



@app.delete("/clear_cache") 
def clear_cache():
    try:
        clear_all_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )