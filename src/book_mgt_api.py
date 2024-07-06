from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext
from sqlalchemy.pool import NullPool
import os
import secrets

# Initialize DB variables
DB_USERNAME=os.environ["DB_USERNAME"]
DB_PASSWORD=os.environ["DB_PASSWORD"]
DB_ENDPOINT=os.environ["DB_ENDPOINT"]
DB_NAME=os.environ["DB_NAME"]

DATABASE_URL = f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True, poolclass= NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

app = FastAPI()

# Basic Authentication setup
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(credentials: HTTPBasicCredentials):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = verify_password(credentials.password, get_password_hash("password"))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# Database Models
class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)
    genre = Column(String)
    year_published = Column(Integer)
    summary = Column(Text)
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)
    review_text = Column(Text)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False)
    book = relationship("Book", back_populates="reviews")

# Pydantic Models
class BookCreate(BaseModel):
    title: str
    author: str
    genre: Optional[str] = None
    year_published: Optional[int] = None
    summary: Optional[str] = None

class ReviewCreate(BaseModel):
    user_id: int
    review_text: str
    rating: int

class BookResponse(BookCreate):
    id: int

class ReviewResponse(ReviewCreate):
    id: int
    book_id: int

# Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

@app.post("/books/", response_model=BookResponse)
async def create_book(book: BookCreate, db: AsyncSession = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(credentials)
    db_book = Book(**book.dict())
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book

@app.get("/books/", response_model=List[BookResponse])
async def read_books(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(credentials)
    result = await db.execute(select(Book).offset(skip).limit(limit))
    books = result.scalars().all()
    return books

@app.get("/books/{id}", response_model=BookResponse)
async def read_book(id: int, db: AsyncSession = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(credentials)
    result = await db.execute(select(Book).where(Book.id == id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{id}", response_model=BookResponse)
async def update_book(id: int, book: BookCreate, db: AsyncSession = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(credentials)
    result = await db.execute(select(Book).where(Book.id == id))
    db_book = result.scalar_one_or_none()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.dict().items():
        setattr(db_book, key, value)
    await db.commit()
    await db.refresh(db_book)
    return db_book

@app.delete("/books/{id}")
async def delete_book(id: int, db: AsyncSession = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(credentials)
    result = await db.execute(select(Book).where(Book.id == id))
    db_book = result.scalar_one_or_none()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(db_book)
    await db.commit()
    return {"detail": "Book deleted"}

@app.post("/books/{id}/reviews", response_model=ReviewResponse)
async def create_review(id: int, review: ReviewCreate, db: AsyncSession = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(credentials)
    result = await db.execute(select(Book).where(Book.id == id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db_review = Review(**review.dict(), book_id=id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review

@app.get("/books/{id}/reviews", response_model=List[ReviewResponse])
async def read_reviews(id: int, db: AsyncSession = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(credentials)
    result = await db.execute(select(Review).where(Review.book_id == id))
    reviews = result.scalars().all()
    return reviews

@app.get("/books/{id}/summary")
async def book_summary(id: int, db: AsyncSession = Depends(get_db), credentials: HTTPBasicCredentials = Depends(security)):
    authenticate_user(credentials)
    result = await db.execute(select(Review).where(Review.book_id == id))
    reviews = result.scalars().all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this book")
    average_rating = sum(review.rating for review in reviews) / len(reviews)
    summary = " ".join(review.review_text for review in reviews)
    return {"average_rating": average_rating, "summary": summary}

# Initialize database and create tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

import asyncio
asyncio.run(init_db())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
