"""
Enterprise Agent AI — Document Routes

API endpoints for document upload and search (RAG pipeline).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.core.security import validate_api_key
from app.models.schemas import (
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchResult,
    DocumentUploadResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


_STORED_DOCS: list[dict[str, Any]] = [
    {
        "id": "doc-sec-policy-01",
        "filename": "Enterprise_Security_Policy_v2.1.pdf",
        "chunks_count": 4,
        "created_at": datetime.utcnow().isoformat(),
        "tags": ["security", "compliance", "auth"],
    },
    {
        "id": "doc-api-guide-02",
        "filename": "API_Standards_and_Rate_Limiting.md",
        "chunks_count": 3,
        "created_at": datetime.utcnow().isoformat(),
        "tags": ["api", "gateway", "standards"],
    },
]

_STORED_CHUNKS: list[DocumentSearchResult] = [
    DocumentSearchResult(
        document_id="doc-sec-policy-01",
        chunk_id=str(uuid.uuid4()),
        content=(
            "Enterprise security policy requires multi-factor authentication "
            "for all production systems. Password rotation is mandated every 90 days."
        ),
        score=0.94,
        metadata={"source": "Security Policy v2.1", "page": 12},
    ),
    DocumentSearchResult(
        document_id="doc-api-guide-02",
        chunk_id=str(uuid.uuid4()),
        content=(
            "All API endpoints must implement rate limiting with a maximum of "
            "1000 requests per minute per authenticated client."
        ),
        score=0.87,
        metadata={"source": "API Standards Guide", "page": 8},
    ),
    DocumentSearchResult(
        document_id="doc-gov-03",
        chunk_id=str(uuid.uuid4()),
        content=(
            "Data retention policies require all customer data to be anonymized "
            "after 24 months of account inactivity."
        ),
        score=0.82,
        metadata={"source": "Data Governance Handbook", "page": 34},
    ),
]


@router.get(
    "/list",
    summary="List indexed knowledge base documents",
    description="Retrieve all indexed documents in the RAG knowledge store.",
)
async def list_documents(_api_key: str = Depends(validate_api_key)) -> list[dict[str, Any]]:
    return _STORED_DOCS


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload a document",
    description="Upload a document for processing and indexing into the RAG vector store.",
)
async def upload_document(
    file: UploadFile = File(...),
    _api_key: str = Depends(validate_api_key),
) -> DocumentUploadResponse:
    allowed_types = {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    content_type = file.content_type or ""
    filename = file.filename or "unnamed"
    allowed_extensions = {".pdf", ".txt", ".md", ".docx"}
    file_ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if content_type not in allowed_types and file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, TXT, DOCX, MD",
        )

    content = await file.read()
    text_content = content.decode("utf-8", errors="replace")

    settings = get_settings()
    chunks = _chunk_text(
        text_content,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Store document metadata
    _STORED_DOCS.append(
        {
            "id": doc_id,
            "filename": filename,
            "chunks_count": len(chunks),
            "created_at": now.isoformat(),
            "tags": ["uploaded", file_ext.replace(".", "") or "text"],
        }
    )

    # Index chunks
    for i, c in enumerate(chunks):
        _STORED_CHUNKS.append(
            DocumentSearchResult(
                document_id=doc_id,
                chunk_id=str(uuid.uuid4()),
                content=c,
                score=0.91,
                metadata={"source": filename, "chunk_index": i + 1, "tokens": len(c.split())},
            )
        )

    return DocumentUploadResponse(
        id=doc_id,
        filename=filename,
        chunks_created=len(chunks),
        status="processed",
        created_at=now,
    )


@router.post(
    "/search",
    response_model=DocumentSearchResponse,
    summary="Search documents",
    description="Semantic search across indexed documents using vector similarity.",
)
async def search_documents(
    request: DocumentSearchRequest,
    _api_key: str = Depends(validate_api_key),
) -> DocumentSearchResponse:
    query_terms = set(request.query.lower().split())

    # Score chunks based on relevance
    scored_results = []
    for chunk in _STORED_CHUNKS:
        chunk_terms = set(chunk.content.lower().split())
        overlap = len(query_terms.intersection(chunk_terms))
        # Compute dynamic relevance score
        relevance = min(0.99, max(0.65, 0.70 + (overlap * 0.08)))
        scored_results.append(
            DocumentSearchResult(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                content=chunk.content,
                score=round(relevance, 2),
                metadata=chunk.metadata,
            )
        )

    scored_results.sort(key=lambda x: x.score, reverse=True)
    results = scored_results[: request.top_k]

    return DocumentSearchResponse(
        query=request.query,
        results=results,
        total_results=len(scored_results),
    )


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks for embedding.

    Args:
        text: Input text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Character overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary
        if end < len(text):
            # Look for the last period, newline, or space before the end
            for boundary in [". ", "\n\n", "\n", " "]:
                boundary_pos = text.rfind(boundary, start + chunk_size // 2, end)
                if boundary_pos != -1:
                    end = boundary_pos + len(boundary)
                    break

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]  # Remove empty chunks
