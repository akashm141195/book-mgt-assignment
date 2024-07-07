import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from book_mgt_api import app, Book, Review, authenticate_user, get_db

class TestBookAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_book = {
            "title": "Test Books",
            "author": "Test Author",
            "genre": "Test Genre",
            "year_published": 2023,
            "summary": "Test Summary"
        }
        self.test_review = {
            "user_id": 1,
            "review_text": "Great book!",
            "rating": 5
        }

    @patch("book_mgt_api.create_async_engine")
    @patch("book_mgt_api.sessionmaker")
    @patch("book_mgt_api.authenticate_user")
    async def test_create_book(self, mock_auth, mock_sessionmaker, mock_create_engine):
        mock_auth.return_value = True
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker.return_value = lambda: mock_session
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine

        with patch("book_mgt_api.get_db", return_value=mock_session):
            response = self.client.post("/books/", json=self.test_book, auth=("admin", "password"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], self.test_book["title"])
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("book_mgt_api.create_async_engine")
    @patch("book_mgt_api.sessionmaker")
    @patch("book_mgt_api.authenticate_user")
    async def test_read_books(self, mock_auth, mock_sessionmaker, mock_create_engine):
        mock_auth.return_value = True
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker.return_value = lambda: mock_session
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_session.execute.return_value.scalars.return_value.all.return_value = [Book(**self.test_book, id=1)]

        with patch("book_mgt_api.get_db", return_value=mock_session):
            response = self.client.get("/books/", auth=("admin", "password"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], self.test_book["title"])

    @patch("book_mgt_api.create_async_engine")
    @patch("book_mgt_api.sessionmaker")
    @patch("book_mgt_api.authenticate_user")
    async def test_read_book(self, mock_auth, mock_sessionmaker, mock_create_engine):
        mock_auth.return_value = True
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker.return_value = lambda: mock_session
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_session.execute.return_value.scalar_one_or_none.return_value = Book(**self.test_book, id=1)

        with patch("book_mgt_api.get_db", return_value=mock_session):
            response = self.client.get("/books/1", auth=("admin", "password"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], self.test_book["title"])

    @patch("book_mgt_api.create_async_engine")
    @patch("book_mgt_api.sessionmaker")
    @patch("book_mgt_api.authenticate_user")
    async def test_update_book(self, mock_auth, mock_sessionmaker, mock_create_engine):
        mock_auth.return_value = True
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker.return_value = lambda: mock_session
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_session.execute.return_value.scalar_one_or_none.return_value = Book(**self.test_book, id=1)

        updated_book = self.test_book.copy()
        updated_book["title"] = "Updated Title"
        with patch("book_mgt_api.get_db", return_value=mock_session):
            response = self.client.put("/books/1", json=updated_book, auth=("admin", "password"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Updated Title")
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("book_mgt_api.create_async_engine")
    @patch("book_mgt_api.sessionmaker")
    @patch("book_mgt_api.authenticate_user")
    async def test_delete_book(self, mock_auth, mock_sessionmaker, mock_create_engine):
        mock_auth.return_value = True
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker.return_value = lambda: mock_session
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_session.execute.return_value.scalar_one_or_none.return_value = Book(**self.test_book, id=1)

        with patch("book_mgt_api.get_db", return_value=mock_session):
            response = self.client.delete("/books/1", auth=("admin", "password"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"detail": "Book deleted"})
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("book_mgt_api.create_async_engine")
    @patch("book_mgt_api.sessionmaker")
    @patch("book_mgt_api.authenticate_user")
    async def test_create_review(self, mock_auth, mock_sessionmaker, mock_create_engine):
        mock_auth.return_value = True
        mock_session = AsyncMock(spec=AsyncSession)
        mock_sessionmaker.return_value = lambda: mock_session
        mock_engine = AsyncMock()
        mock_create_engine.return_value = mock_engine
        mock_session.execute.return_value.scalar_one_or_none.return_value = Book(**self.test_book, id=1)

        with patch("book_mgt_api.get_db", return_value=mock_session):
            response = self.client.post("/books/1/reviews", json=self.test_review, auth=("admin", "password"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["review_text"], self.test_review["review_text"])
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("book_mgt_api.authenticate_user")
    def test_authenticate_user_success(self, mock_auth):
        mock_auth.return_value = True
        credentials = MagicMock()
        credentials.username = "admin"
        credentials.password = "password"
        
        result = authenticate_user(credentials)
        self.assertTrue(result)

    @patch("book_mgt_api.authenticate_user")
    def test_authenticate_user_failure(self, mock_auth):
        mock_auth.side_effect = HTTPException(status_code=401, detail="Incorrect username or password")
        credentials = MagicMock()
        credentials.username = "wrong"
        credentials.password = "wrong"
        
        with self.assertRaises(HTTPException) as context:
            authenticate_user(credentials)
        
        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Incorrect username or password")

if __name__ == "__main__":
    unittest.main()