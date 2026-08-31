import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.category import Category
from app.models.group import DeviceGroup
from app.models.location import Location
from app.core.security import hash_password
from app.services.auth_service import AuthService

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

async def override_get_db():
    async with test_session_maker() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def test_db():
    async with test_session_maker() as session:
        yield session

@pytest_asyncio.fixture
async def admin_user(test_db):
    user = User(username="admin", email="admin@test.com", password_hash=hash_password("adminpass"), role="admin")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest_asyncio.fixture
async def viewer_user(test_db):
    user = User(username="viewer", email="viewer@test.com", password_hash=hash_password("viewerpass"), role="viewer")
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest_asyncio.fixture
def admin_token(admin_user):
    tokens = AuthService.create_tokens(admin_user.id, admin_user.username, admin_user.role)
    return tokens.access_token

@pytest_asyncio.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest_asyncio.fixture
def viewer_token(viewer_user):
    tokens = AuthService.create_tokens(viewer_user.id, viewer_user.username, viewer_user.role)
    return tokens.access_token

@pytest_asyncio.fixture
def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}

@pytest_asyncio.fixture
async def test_category(test_db):
    category = Category(name="Test Category", description="Test")
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    return category
