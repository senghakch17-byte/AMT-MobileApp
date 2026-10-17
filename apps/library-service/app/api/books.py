import re

from beanie import PydanticObjectId
from beanie.operators import Or, RegEx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pymongo.errors import DuplicateKeyError

from app.api.deps import get_current_user, require_admin
from app.core.security import CurrentUser
from app.database.models import Book
from app.schemas.book import BookBase, BookCreate, BookResponse, BookUpdate
from app.utils.helpers import apply_update

router = APIRouter(prefix="/books", tags=["Books"])


async def _get_or_404(book_id: PydanticObjectId) -> Book:
    book = await Book.get(book_id)
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    return book


def _isbn_taken() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "A book with this ISBN already exists")


# ---------- Admin: manage the catalog ----------

@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(payload: BookCreate, admin: CurrentUser = Depends(require_admin)):
    book = Book(**payload.model_dump(), created_by=admin.id)
    try:
        await book.insert()
    except DuplicateKeyError:
        raise _isbn_taken()
    return book


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: PydanticObjectId, payload: BookUpdate, _: CurrentUser = Depends(require_admin)
):
    if not payload.model_fields_set:  # nothing to change: no need to touch the database
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
    book = await _get_or_404(book_id)
    apply_update(book, BookBase, payload)
    try:
        await book.save()
    except DuplicateKeyError:
        raise _isbn_taken()
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: PydanticObjectId, _: CurrentUser = Depends(require_admin)):
    book = await _get_or_404(book_id)
    await book.delete()


# ---------- Any logged-in user: browse ----------

@router.get("", response_model=list[BookResponse])
async def list_books(
    response: Response,
    q: str | None = Query(None, min_length=1, max_length=100, description="Search title or author"),
    category: str | None = Query(None, min_length=2, max_length=60),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: CurrentUser = Depends(get_current_user),
):
    conditions = []
    if q:
        pattern = re.escape(q)  # user input is matched literally, never as a regex
        conditions.append(
            Or(RegEx(Book.title, pattern, "i"), RegEx(Book.author, pattern, "i"))
        )
    if category:
        conditions.append(Book.category == category.strip().lower())
    query = Book.find(*conditions)
    response.headers["X-Total-Count"] = str(await query.count())
    return await query.sort("+title").skip(skip).limit(limit).to_list()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: PydanticObjectId, _: CurrentUser = Depends(get_current_user)):
    return await _get_or_404(book_id)
