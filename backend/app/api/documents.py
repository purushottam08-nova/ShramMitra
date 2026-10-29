from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


STORAGE_DIR = Path("storage/documents")

MAX_FILE_SIZE = 5 * 1024 * 1024

# MIME type -> file extension
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def detect_file_type(content: bytes) -> str | None:
    """
    Detect file type using file signatures,
    not only the client-provided MIME type.
    """

    if content.startswith(b"%PDF-"):
        return "application/pdf"

    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    if (
        content.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        return "image/png"

    return None


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document_type = document_type.strip()

    if not document_type or len(document_type) > 50:
        raise HTTPException(
            status_code=400,
            detail="Document type must be between 1 and 50 characters",
        )

    # Read one extra byte to detect files over the limit.
    file_content = await file.read(MAX_FILE_SIZE + 1)

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size must be 5 MB or less",
        )

    detected_type = detect_file_type(file_content)

    if detected_type is None:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG, and PNG files are allowed",
        )

    # Reject MIME type mismatch.
    if file.content_type != detected_type:
        raise HTTPException(
            status_code=400,
            detail="File content does not match its declared type",
        )

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = (
        f"{current_user.id}_"
        f"{uuid4().hex}"
        f"{ALLOWED_TYPES[detected_type]}"
    )

    file_path = STORAGE_DIR / safe_filename

    try:
        file_path.write_bytes(file_content)

        document = Document(
            user_id=current_user.id,
            document_type=document_type,
            original_filename=(
                Path(file.filename or "document")
                .name[:255]
            ),
            storage_path=str(file_path),
            mime_type=detected_type,
            file_size=len(file_content),
            verification_status="UPLOADED",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise

    finally:
        await file.close()

    return document


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
        )
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    file_path = Path(document.storage_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found",
        )

    return FileResponse(
        path=file_path,
        media_type=document.mime_type,
        filename=document.original_filename,
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    file_path = Path(document.storage_path)

    try:
        db.delete(document)
        db.commit()

    except Exception:
        db.rollback()
        raise

    # Delete the physical file after successful DB commit.
    if file_path.is_file():
        file_path.unlink()

    return {
        "message": "Document deleted successfully",
    }