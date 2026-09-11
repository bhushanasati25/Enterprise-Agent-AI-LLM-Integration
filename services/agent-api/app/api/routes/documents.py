"""
Enterprise Agent AI — Document Routes

API endpoints for document upload and search (RAG pipeline).
"""

from __future__ import annotations

import uuid
from datetime import datetime

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
    """
    Upload a document for RAG indexing.

    Supported formats: PDF, TXT, DOCX, MD
    The document will be chunked, embedded, and stored in pgvector.
    """
    # Validate file type
    allowed_types = {
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    content_type = file.content_type or ""
    filename = file.filename or "unnamed"

    # Also allow by extension
    allowed_extensions = {".pdf", ".txt", ".md", ".docx"}
    file_ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if content_type not in allowed_types and file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. "
            f"Allowed: PDF, TXT, DOCX, MD",
        )

    # Read file content
    content = await file.read()
    text_content = content.decode("utf-8", errors="replace")

    # Chunk the document
    settings = get_settings()
    chunks = _chunk_text(
        text_content,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )

    # In production, embed and store in pgvector
    # For now, return a success response
    doc_id = str(uuid.uuid4())

    return DocumentUploadResponse(
        id=doc_id,
        filename=filename,
        chunks_created=len(chunks),
        status="processed",
        created_at=datetime.utcnow(),
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
    """
    Search indexed documents using semantic similarity.

    Returns the top-K most relevant document chunks.
    """
    # In production, this would query pgvector
    # For now, return simulated results
    mock_results = [
        DocumentSearchResult(
            document_id=str(uuid.uuid4()),
            chunk_id=str(uuid.uuid4()),
            content=(
                "Enterprise security policy requires multi-factor authentication "
                "for all production systems. Password rotation is mandated every 90 days."
            ),
            score=0.94,
            metadata={"source": "Security Policy v2.1", "page": 12},
        ),
        DocumentSearchResult(
            document_id=str(uuid.uuid4()),
            chunk_id=str(uuid.uuid4()),
            content=(
                "All API endpoints must implement rate limiting with a maximum of "
                "1000 requests per minute per authenticated client."
            ),
            score=0.87,
            metadata={"source": "API Standards Guide", "page": 8},
        ),
        DocumentSearchResult(
            document_id=str(uuid.uuid4()),
            chunk_id=str(uuid.uuid4()),
            content=(
                "Data retention policies require all customer data to be anonymized "
                "after 24 months of account inactivity."
            ),
            score=0.82,
            metadata={"source": "Data Governance Handbook", "page": 34},
        ),
    ]

    return DocumentSearchResponse(
        query=request.query,
        results=mock_results[: request.top_k],
        total_results=len(mock_results),
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
