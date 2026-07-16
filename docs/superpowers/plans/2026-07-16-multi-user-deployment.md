# Glimmer Multi-User Deployment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Glimmer from a single-user localhost tool into a multi-user cloud-deployable platform with GitHub OAuth, Docker sandboxes, PostgreSQL persistence, and production networking.

**Architecture:** Nginx → FastAPI (JWT middleware) → PostgreSQL + Docker daemon. New Python modules: `harness/auth/`, `harness/db/`, `harness/sandbox/`. Frontend adds AuthContext + LoginPage.

**Tech Stack:** FastAPI, asyncpg + SQLAlchemy, Alembic, python-jose (JWT), httpx (OAuth), docker-py, slowapi, React Context (auth state)

## Global Constraints

- No breaking changes to the existing Agent state machine or feedback analyzer
- Frontend retains all current pages and fairy-tale theme (visual unchanged)
- Local single-user mode still works when DATABASE_URL is not set (graceful fallback)
- Docker daemon required on host for sandboxed execution
- All API routes except `/api/auth/*` require valid JWT
- APi keys encrypted at rest with AES-256-GCM (key from GLIMMER_SECRET_KEY)

---

### Task 1: Database Foundation

**Files:**
- Create: `harness/db/__init__.py`
- Create: `harness/db/database.py`
- Create: `harness/db/models.py`
- Create: `harness/db/migrations/env.py`
- Create: `harness/db/migrations/versions/001_initial.py`
- Modify: `requirements.txt`
- Create: `alembic.ini`

**Interfaces:**
- Produces: `async def get_db() -> AsyncGenerator[AsyncSession]` — FastAPI dependency
- Produces: `async def init_db()` — create tables, run migrations
- Produces: SQLAlchemy models: `User`, `UserConfig`, `Session`, `Message`

- [ ] **Step 1: Install database dependencies**

```bash
pip install sqlalchemy[asyncio] asyncpg alembic
```

Add to `requirements.txt`:
```
sqlalchemy[asyncio]>=2.0
asyncpg>=0.29
alembic>=1.13
```

- [ ] **Step 2: Create database connection module**

Write `harness/db/database.py`:

```python
"""Database connection and session management."""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "")

_engine = None
_session_factory = None


class Base(DeclarativeBase):
    pass


def _get_engine():
    global _engine
    if _engine is None and DATABASE_URL:
        _engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20)
    return _engine


async def get_db():
    """FastAPI dependency: yields an async database session."""
    global _session_factory
    engine = _get_engine()
    if engine is None:
        raise RuntimeError("DATABASE_URL not configured")
    if _session_factory is None:
        _session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables (called at startup)."""
    engine = _get_engine()
    if engine is None:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 3: Create SQLAlchemy models**

Write `harness/db/models.py`:

```python
"""SQLAlchemy ORM models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime, Index, BigInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from harness.db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    login: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    config: Mapped["UserConfig | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserConfig(Base):
    __tablename__ = "user_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="anthropic")
    base_url: Mapped[str | None] = mapped_column(String(500), default="")
    model_id: Mapped[str] = mapped_column(String(200), default="claude-sonnet-5")
    api_key_enc: Mapped[str | None] = mapped_column(Text)
    sandbox_image: Mapped[str | None] = mapped_column(String(200), default="glimmer-sandbox:latest")
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="config")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")
    container_id: Mapped[str | None] = mapped_column(String(100))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")

    __table_args__ = (Index("idx_sessions_user", "user_id", "created_at"),)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_new_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped["Session"] = relationship(back_populates="messages")

    __table_args__ = (Index("idx_messages_session", "session_id", "created_at"),)
```

- [ ] **Step 4: Create Alembic configuration**

Write `alembic.ini`:

```ini
[alembic]
script_location = harness/db/migrations
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

Create `harness/db/migrations/env.py`:

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None  # Use Base.metadata for autogenerate

def run_migrations_offline() -> None:
    url = os.environ.get("DATABASE_URL", "")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    url = os.environ.get("DATABASE_URL", "")
    connectable = async_engine_from_config({"sqlalchemy.url": url}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 5: Verify database connection**

```bash
cd G:/github/lite-agent-harness && python -c "
import os; os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/glimmer'
import asyncio
from harness.db.database import init_db
asyncio.run(init_db())
print('DB OK')
"
```

Skip if no local PostgreSQL — just verify imports work:
```bash
python -c "from harness.db.models import User, UserConfig, Session, Message; print('Models OK')"
```

- [ ] **Step 6: Commit**

```bash
git -C G:/github/lite-agent-harness add requirements.txt harness/db/ alembic.ini
git -C G:/github/lite-agent-harness commit -m "feat: add database foundation — PostgreSQL models, async session, Alembic"
```

---

### Task 2: Authentication — GitHub OAuth + JWT

**Files:**
- Create: `harness/auth/__init__.py`
- Create: `harness/auth/jwt.py`
- Create: `harness/auth/oauth.py`
- Create: `server/api/auth_routes.py`
- Modify: `server/main.py` (register auth routes)
- Modify: `requirements.txt` (python-jose, httpx)

**Interfaces:**
- Produces: `create_token(user_id: str) -> str` — signed JWT
- Produces: `verify_token(token: str) -> dict` — decoded payload or raises
- Produces: `async get_current_user(token, db) -> User` — FastAPI dependency
- GET `/api/auth/login` → redirect to GitHub
- GET `/api/auth/callback?code=xxx` → returns JWT
- GET `/api/auth/me` → current user info (requires JWT)

- [ ] **Step 1: Install dependencies**

```bash
pip install python-jose[cryptography] httpx
```

Add to `requirements.txt`:
```
python-jose[cryptography]>=3.3
httpx>=0.27
```

- [ ] **Step 2: Create JWT module**

Write `harness/auth/jwt.py`:

```python
"""JWT token creation and verification."""
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

SECRET_KEY = os.environ.get("GLIMMER_SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
EXPIRE_DAYS = 7


def create_token(user_id: str) -> str:
    """Create a signed JWT for a user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT. Raises JWTError on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_user_id_from_token(token: str) -> str | None:
    """Extract user_id from token, or None if invalid."""
    try:
        payload = verify_token(token)
        return payload.get("sub")
    except JWTError:
        return None
```

- [ ] **Step 3: Create OAuth module**

Write `harness/auth/oauth.py`:

```python
"""GitHub OAuth integration."""
import os
import httpx

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback")

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"


def get_login_url() -> str:
    return f"{AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user:email"


async def exchange_code(code: str) -> dict | None:
    """Exchange OAuth code for access token, then fetch user info.
    Returns dict with id, login, name, email, avatar_url or None.
    """
    async with httpx.AsyncClient() as client:
        # Exchange code for access_token
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            return None

        # Fetch user info
        resp2 = await client.get(
            USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp2.status_code != 200:
            return None
        user = resp2.json()

        return {
            "id": user["id"],
            "login": user["login"],
            "name": user.get("name") or user["login"],
            "email": user.get("email"),
            "avatar_url": user.get("avatar_url", ""),
        }
```

- [ ] **Step 4: Create auth routes**

Write `server/api/auth_routes.py`:

```python
"""Authentication routes — GitHub OAuth login."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from harness.db.database import get_db
from harness.db.models import User
from harness.auth.oauth import get_login_url, exchange_code
from harness.auth.jwt import create_token, get_user_id_from_token

router = APIRouter(tags=["auth"])


@router.get("/auth/login")
async def login():
    """Redirect user to GitHub for authentication."""
    url = get_login_url()
    if not url:
        raise HTTPException(500, "GitHub OAuth not configured (GITHUB_CLIENT_ID missing)")
    return RedirectResponse(url)


@router.get("/auth/callback")
async def callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle GitHub OAuth callback. Returns JWT token."""
    user_info = await exchange_code(code)
    if user_info is None:
        raise HTTPException(400, "GitHub authentication failed")

    # Upsert user
    result = await db.execute(select(User).where(User.github_id == user_info["id"]))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            github_id=user_info["id"],
            login=user_info["login"],
            name=user_info["name"],
            email=user_info["email"],
            avatar_url=user_info["avatar_url"],
        )
        db.add(user)
        await db.flush()
    else:
        user.login = user_info["login"]
        user.name = user_info["name"]
        user.email = user_info["email"]
        user.avatar_url = user_info["avatar_url"]

    token = create_token(str(user.id))
    return {"token": token, "user": {"id": str(user.id), "login": user.login, "name": user.name, "avatar_url": user.avatar_url}}


@router.get("/auth/me")
async def me(token: str = Depends(_extract_token_from_header), db: AsyncSession = Depends(get_db)):
    """Return current authenticated user info."""
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": str(user.id), "login": user.login, "name": user.name, "email": user.email, "avatar_url": user.avatar_url}


# ---------------------------------------------------------------------------
# JWT dependency for protected routes
# ---------------------------------------------------------------------------
from fastapi import Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_security = HTTPBearer(auto_error=False)


async def _extract_token_from_header(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> str:
    if credentials is None:
        raise HTTPException(401, "Authorization header required")
    return credentials.credentials


async def get_current_user(
    token: str = Depends(_extract_token_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: extract and validate JWT, return User or raise 401."""
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")
    return user
```

- [ ] **Step 5: Register auth routes in main.py**

Read `server/main.py`, add after existing router registration:

```python
from server.api.auth_routes import router as auth_router

# ... inside create_app(), after other routers:
app.include_router(auth_router, prefix="/api")
```

- [ ] **Step 6: Verify imports**

```bash
cd G:/github/lite-agent-harness && python -c "from harness.auth.jwt import create_token, verify_token; t = create_token('test'); print(verify_token(t)); print('JWT OK')"
```

- [ ] **Step 7: Commit**

```bash
git -C G:/github/lite-agent-harness add requirements.txt harness/auth/ server/api/auth_routes.py server/main.py
git -C G:/github/lite-agent-harness commit -m "feat: add GitHub OAuth authentication and JWT middleware"
```

---

### Task 3: Per-User Config + Encrypted Credentials

**Files:**
- Create: `harness/auth/crypto.py`
- Modify: `server/api/config_routes.py` (per-user)
- Modify: `server/api/credential_routes.py` (per-user, rename as config)

**Interfaces:**
- Consumes: `get_current_user` from Task 2
- Produces: `encrypt_credential(plaintext, secret) -> bytes`, `decrypt_credential(data, secret) -> str`
- GET/PUT `/api/config` → per-user config (reads/writes UserConfig row)
- POST/DELETE `/api/config/credentials` → store/delete encrypted API key

- [ ] **Step 1: Create crypto module**

Write `harness/auth/crypto.py`:

```python
"""AES-256-GCM encryption for API keys at rest."""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

_SECRET = os.environ.get("GLIMMER_SECRET_KEY", "dev-secret-change-me")


def _derive_key() -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"glimmer-creds").derive(_SECRET.encode())


def encrypt_credential(plaintext: str) -> bytes:
    key = _derive_key()
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode(), None)
    return nonce + ct


def decrypt_credential(data: bytes) -> str | None:
    try:
        key = _derive_key()
        return AESGCM(key).decrypt(data[:12], data[12:], None).decode()
    except Exception:
        return None
```

- [ ] **Step 2: Rewrite config_routes.py for per-user**

Rewrite `server/api/config_routes.py` to read/write from `UserConfig` table instead of file-based `ConfigManager`. Use `get_current_user` dependency. Keep existing file-based fallback when no DATABASE_URL:

```python
"""Per-user configuration REST endpoints."""
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from harness.db.database import get_db
from harness.db.models import User, UserConfig
from server.api.auth_routes import get_current_user
from harness.auth.crypto import encrypt_credential, decrypt_credential
from harness.models import ConfigData

router = APIRouter(tags=["config"])

# Fallback for local mode (no DATABASE_URL)
_fallback_config_manager = None
_fallback_credential_manager = None


def configure_fallback(config_mgr, cred_mgr):
    global _fallback_config_manager, _fallback_credential_manager
    _fallback_config_manager = config_mgr
    _fallback_credential_manager = cred_mgr


class ConfigUpdate(BaseModel):
    provider: str | None = None
    base_url: str | None = None
    model_id: str | None = None
    max_tokens: int | None = None
    max_retries: int | None = None
    timeout_seconds: int | None = None

class CredentialStore(BaseModel):
    api_key: str


@router.get("/config")
async def get_config(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's LLM configuration."""
    if not os.environ.get("DATABASE_URL"):
        cfg = _fallback_config_manager.load()
        return cfg.model_dump()

    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()

    if cfg is None:
        cfg = UserConfig(user_id=user.id)
        db.add(cfg)
        await db.flush()

    return {
        "provider": cfg.provider,
        "base_url": cfg.base_url or "",
        "model_id": cfg.model_id,
        "max_tokens": cfg.max_tokens,
        "max_retries": cfg.max_retries,
        "timeout_seconds": cfg.timeout_seconds,
        "has_api_key": bool(cfg.api_key_enc),
    }


@router.put("/config")
async def update_config(
    update: ConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's LLM configuration."""
    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = UserConfig(user_id=user.id)
        db.add(cfg)

    for field, value in update.model_dump(exclude_none=True).items():
        setattr(cfg, field, value)

    await db.flush()
    return {"status": "ok"}


@router.post("/config/credentials")
async def store_credential(
    body: CredentialStore,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Store encrypted API key for current user."""
    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = UserConfig(user_id=user.id)
        db.add(cfg)

    encrypted = encrypt_credential(body.api_key)
    cfg.api_key_enc = encrypted.hex()
    await db.flush()
    return {"status": "ok"}


@router.delete("/config/credentials")
async def delete_credential(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete stored API key for current user."""
    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg:
        cfg.api_key_enc = None
        await db.flush()
    return {"status": "ok"}


async def get_user_config(user: User, db: AsyncSession) -> ConfigData | None:
    """Helper: fetch user's config as ConfigData model (used by WebSocket handler)."""
    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        return None
    return ConfigData(
        model_provider=cfg.provider,
        model_id=cfg.model_id,
        base_url=cfg.base_url or "",
        max_tokens=cfg.max_tokens,
        max_retries=cfg.max_retries,
        timeout_seconds=cfg.timeout_seconds,
    )


async def get_user_api_key(user: User, db: AsyncSession) -> str | None:
    """Helper: fetch and decrypt user's API key."""
    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user.id))
    cfg = result.scalar_one_or_none()
    if cfg is None or not cfg.api_key_enc:
        return None
    return decrypt_credential(bytes.fromhex(cfg.api_key_enc))
```

- [ ] **Step 3: Update server/main.py to register new config routes**

Replace old config/credential route registration with new per-user routes. Add `configure_fallback()` call for local mode.

- [ ] **Step 4: Commit**

```bash
git -C G:/github/lite-agent-harness add harness/auth/crypto.py server/api/config_routes.py server/api/credential_routes.py server/main.py
git -C G:/github/lite-agent-harness rm server/api/credential_routes.py 2>/dev/null; true
git -C G:/github/lite-agent-harness commit -m "feat: add per-user config with encrypted credential storage"
```

---

### Task 4: Docker Sandbox Manager

**Files:**
- Create: `harness/sandbox/__init__.py`
- Create: `harness/sandbox/docker_manager.py`
- Create: `Dockerfile.sandbox`

**Interfaces:**
- `<DockerManager>.create(user_id, session_id) -> container_id`
- `<DockerManager>.exec(container_id, cmd) -> ExecResult`
- `<DockerManager>.destroy(container_id)`

- [ ] **Step 1: Install docker-py**

```bash
pip install docker
```

Add to `requirements.txt`: `docker>=7.1`

- [ ] **Step 2: Create DockerManager**

Write `harness/sandbox/docker_manager.py`:

```python
"""Docker-based sandbox manager for isolated Agent execution."""
import os
import asyncio
from dataclasses import dataclass

DOCKER_HOST = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "glimmer-sandbox:latest")
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "/workspace")


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str


class DockerManager:
    """Manages lifecycle of sandbox containers for Agent sessions."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import docker
            self._client = docker.DockerClient(base_url=DOCKER_HOST)
        return self._client

    async def create(self, user_id: str, session_id: str) -> str:
        """Create and start a sandbox container. Returns container_id."""
        container_name = f"agent-{session_id[:12]}"
        user_workspace = os.path.join(WORKSPACE_ROOT, user_id)
        os.makedirs(user_workspace, exist_ok=True)

        container = await asyncio.to_thread(
            self.client.containers.run,
            image=SANDBOX_IMAGE,
            command=["sleep", "infinity"],
            name=container_name,
            network_mode="none",
            mem_limit="512m",
            nano_cpus=1_000_000_000,  # 1 CPU
            pids_limit=100,
            volumes={user_workspace: {"bind": "/workspace", "mode": "rw"}},
            remove=True,
            detach=True,
        )
        return container.id

    async def exec(self, container_id: str, cmd: str, timeout: int = 600) -> ExecResult:
        """Execute a command inside the container and return result."""
        async def _run():
            container = self.client.containers.get(container_id)
            exit_code, output = container.exec_run(
                ["sh", "-c", cmd],
                stdout=True,
                stderr=True,
            )
            return ExecResult(
                exit_code=exit_code,
                stdout=output[0].decode("utf-8", errors="replace") if output[0] else "",
                stderr=output[1].decode("utf-8", errors="replace") if output[1] else "",
            )

        try:
            return await asyncio.wait_for(asyncio.to_thread(_run), timeout=timeout + 5)
        except asyncio.TimeoutError:
            return ExecResult(exit_code=-1, stdout="", stderr="Command timed out")

    async def destroy(self, container_id: str) -> None:
        """Stop and remove a container."""
        try:
            await asyncio.to_thread(
                lambda: self.client.containers.get(container_id).kill()
            )
        except Exception:
            pass
```

- [ ] **Step 3: Create sandbox Dockerfile**

Write `Dockerfile.sandbox`:

```dockerfile
FROM python:3.12-slim

RUN pip install --no-cache-dir pytest pytest-json-report && \
    apt-get update && \
    apt-get install -y --no-install-recommends ripgrep git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
CMD ["sleep", "infinity"]
```

- [ ] **Step 4: Build sandbox image**

```bash
docker build -f Dockerfile.sandbox -t glimmer-sandbox:latest .
```

- [ ] **Step 5: Commit**

```bash
git -C G:/github/lite-agent-harness add requirements.txt harness/sandbox/ Dockerfile.sandbox
git -C G:/github/lite-agent-harness commit -m "feat: add Docker sandbox manager for isolated agent execution"
```

---

### Task 5: Refactor WebSocket Handler for Multi-User

**Files:**
- Modify: `server/ws_handler.py`
- Modify: `harness/tools/shell.py` (use DockerManager.exec instead of local subprocess)

**Changes:**
- WebSocket handler extracts JWT from `?token=xxx` query param
- Loads per-user config and API key from PostgreSQL
- Creates DockerManager, spawns sandbox container per session
- Routes tool execution through DockerManager
- Saves session and messages to PostgreSQL
- Destroys container on session end

- [ ] **Step 1: Refactor WebSocket handler**

Replace the single-user file-based config loading with per-user DB config. Add JWT auth on connection. Use DockerManager for tool execution.

Key changes in `server/ws_handler.py`:

```python
# In websocket_session():
token = websocket.query_params.get("token", "")
user_id = get_user_id_from_token(token)
if not user_id:
    await websocket.close(code=4001, reason="Invalid token")
    return

# Get user from DB
db = ...get_db()
user = await db.get(User, user_id)
config = await get_user_config(user, db)
api_key = await get_user_api_key(user, db)

# Create Docker container
docker_mgr = DockerManager()
container_id = await docker_mgr.create(str(user.id), str(session_id))

# Run agent loop (tool execution goes through docker_mgr.exec)
loop = AgentLoop(tools, guardrails, analyzer, policy, docker_mgr=docker_mgr)
session = await loop.run(task, llm, container_id=container_id)

# Save session + messages to DB
await save_session(db, session_id, user.id, task, messages)

# Cleanup
await docker_mgr.destroy(container_id)
```

- [ ] **Step 2: Update AgentLoop to accept DockerManager**

Modify `harness/loop.py` to accept optional `docker_mgr` and `container_id`. When present, tool execution routes through `docker_mgr.exec(container_id, cmd)`. When absent, falls back to local subprocess (local single-user mode).

- [ ] **Step 3: Update ShellTool to use DockerManager**

Modify `harness/tools/shell.py` to accept an optional `DockerManager + container_id` and use `docker_mgr.exec()` instead of `subprocess.run()`.

- [ ] **Step 4: Add session persistence helpers**

Add to `server/ws_handler.py` or create `harness/db/session_store.py`:

```python
async def save_session(db, session_id, user_id, task, messages, container_id, status="completed"):
    from harness.db.models import Session, Message
    session = Session(id=session_id, user_id=user_id, task=task, status=status, container_id=container_id)
    db.add(session)
    for msg in messages:
        db.add(Message(session_id=session_id, type=msg["type"], payload=msg))
    await db.flush()
```

- [ ] **Step 5: Commit**

```bash
git -C G:/github/lite-agent-harness add server/ws_handler.py harness/loop.py harness/tools/shell.py
git -C G:/github/lite-agent-harness commit -m "feat: refactor agent loop for multi-user — Docker sandbox, per-user config, session persistence"
```

---

### Task 6: Session History API

**Files:**
- Modify: `server/api/session_routes.py`

- [ ] **Step 1: Implement real session history endpoints**

```python
@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.user_id == user.id).order_by(Session.created_at.desc()).limit(50)
    )
    sessions = result.scalars().all()
    return {"sessions": [{"id": str(s.id), "task": s.task, "status": s.status, "created_at": s.created_at.isoformat()} for s in sessions]}

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Session).where(Session.id == session_id, Session.user_id == user.id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    messages = session.messages
    return {"id": str(session.id), "task": session.task, "status": session.status, "messages": [{"type": m.type, "payload": m.payload} for m in messages]}
```

- [ ] **Step 2: Commit**

---

### Task 7: Frontend — Auth + Relative URLs

**Files:**
- Create: `web/src/contexts/AuthContext.tsx`
- Create: `web/src/pages/LoginPage.tsx`
- Create: `web/src/components/ProtectedRoute.tsx`
- Modify: `web/src/App.tsx` (add login route, wrap in AuthProvider)
- Modify: `web/src/hooks/useWebSocket.ts` (relative WS URL + JWT query param)
- Modify: `web/src/services/api.ts` (relative base URL + JWT header)

- [ ] **Step 1: Create AuthContext**

Write `web/src/contexts/AuthContext.tsx`:

```tsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface User { id: string; login: string; name: string; avatar_url: string; }
interface AuthState { user: User | null; token: string | null; loading: boolean; login: () => void; logout: () => void; }

const AuthContext = createContext<AuthState>({ user: null, token: null, loading: true, login: () => {}, logout: () => {} });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('glimmer_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(u => u ? setUser(u) : setToken(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = useCallback(() => { window.location.href = '/api/auth/login'; }, []);
  const logout = useCallback(() => { localStorage.removeItem('glimmer_token'); setToken(null); setUser(null); }, []);

  return <AuthContext.Provider value={{ user, token, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
```

- [ ] **Step 2: Create LoginPage**

Write `web/src/pages/LoginPage.tsx`:

```tsx
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: 'var(--color-bg-primary)' }}>
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} style={{ textAlign: 'center' }}>
        <h1 className="gradient-text" style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-hero)', marginBottom: 16 }}>Glimmer</h1>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: 32 }}>登录后开始使用</p>
        <button onClick={login} style={{ padding: '12px 32px', background: 'var(--color-accent)', color: '#fff', border: 'none', borderRadius: 'var(--radius-full)', fontSize: 'var(--text-base)', cursor: 'pointer' }}>
          Sign in with GitHub
        </button>
      </motion.div>
    </div>
  );
};

export default LoginPage;
```

- [ ] **Step 3: Create ProtectedRoute**

Write `web/src/components/ProtectedRoute.tsx`:

```tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, loading } = useAuth();
  if (loading) return <div style={{ padding: 80, textAlign: 'center', color: 'var(--color-text-tertiary)' }}>Loading...</div>;
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export default ProtectedRoute;
```

- [ ] **Step 4: Update App.tsx routes**

Add AuthProvider wrapper, LoginPage route, wrap Agent route in ProtectedRoute. Handle OAuth callback (extract token from URL on `/auth/callback`).

- [ ] **Step 5: Update useWebSocket.ts and api.ts to use relative URLs**

```typescript
// useWebSocket.ts
const token = localStorage.getItem('glimmer_token');
const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${wsProtocol}//${location.host}/ws/session?token=${token}`;

// api.ts
const BASE = '';
async function authHeaders() {
  const token = localStorage.getItem('glimmer_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}
```

- [ ] **Step 6: Build and commit**

```bash
cd G:/github/lite-agent-harness/web && npx vite build --outDir ../server/static --emptyOutDir
git -C G:/github/lite-agent-harness add web/src/contexts/ web/src/pages/LoginPage.tsx web/src/components/ProtectedRoute.tsx web/src/App.tsx web/src/hooks/useWebSocket.ts web/src/services/api.ts server/static/
git -C G:/github/lite-agent-harness commit -m "feat: add frontend auth — login page, protected routes, relative URLs"
```

---

### Task 8: Rate Limiting + Deployment

**Files:**
- Modify: `server/main.py` (slowapi middleware)
- Create: `nginx.conf`
- Create: `docker-compose.yml`
- Modify: `Dockerfile` (update for multi-user)
- Modify: `requirements.txt` (slowapi)

- [ ] **Step 1: Add rate limiting**

```bash
pip install slowapi
```

Add to `server/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# In create_app():
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Add `@limiter.limit("5/minute")` to agent task creation routes.

- [ ] **Step 2: Create nginx.conf**

Write `nginx.conf`:

```nginx
events { worker_connections 1024; }

http {
    include mime.types;
    server {
        listen 80;
        server_name _;

        location /ws/ {
            proxy_pass http://api:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 1800s;
        }

        location /api/ {
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            root /usr/share/nginx/html;
            try_files $uri /index.html;
        }
    }
}
```

- [ ] **Step 3: Create docker-compose.yml**

Write `docker-compose.yml` per spec section 11 (deployment config with nginx, api, db services).

- [ ] **Step 4: Update main Dockerfile**

Add Docker SDK dependency, ensure static files and nginx config are included.

- [ ] **Step 5: Commit**

```bash
git -C G:/github/lite-agent-harness add requirements.txt server/main.py nginx.conf docker-compose.yml Dockerfile
git -C G:/github/lite-agent-harness commit -m "feat: add rate limiting, nginx config, docker-compose deployment"
```

---

### Task 9: Local Mode Fallback

**Files:**
- Modify: `server/main.py` (detect DATABASE_URL, fall back to local mode)
- Modify: `server/api/config_routes.py` (file-based fallback already exists)

**Changes:**
- When `DATABASE_URL` not set: skip DB init, skip auth middleware, use file-based config/credentials
- Auth routes return 404 in local mode
- Frontend detects local mode (no auth needed)

- [ ] **Step 1: Add local mode detection to main.py**

```python
LOCAL_MODE = not os.environ.get("DATABASE_URL")

if LOCAL_MODE:
    # Skip auth middleware, use file-based config
    from harness.config import ConfigManager
    from harness.credentials import CredentialManager
    config_manager = ConfigManager(project_root)
    credential_manager = CredentialManager(project_root)
    configure_fallback(config_manager, credential_manager)
else:
    # Init DB, register auth routes
    await init_db()
```

- [ ] **Step 2: Build, verify both modes**

```bash
# Local mode:
python -c "from server.main import create_app; app = create_app(); print('Local OK')"

# (Set DATABASE_URL to test multi-user mode)
```

- [ ] **Step 3: Commit**

```bash
git -C G:/github/lite-agent-harness add server/main.py server/api/config_routes.py
git -C G:/github/lite-agent-harness commit -m "feat: add local-mode fallback when DATABASE_URL is not set"
```
