import asyncio
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

import src.web.routes.upload.newapi_services as newapi_routes
from src.database.session import DatabaseSessionManager
from src.web.routes.upload.newapi_services import NewapiServiceCreate, NewapiServiceUpdate


def _build_fake_get_db(manager):
    @contextmanager
    def fake_get_db():
        with manager.session_scope() as session:
            yield session

    return fake_get_db


def test_create_newapi_service_rejects_non_ascii_api_key(tmp_path, monkeypatch):
    manager = DatabaseSessionManager(f"sqlite:///{tmp_path}/newapi-create.db")
    manager.create_tables()
    manager.migrate_tables()
    monkeypatch.setattr(newapi_routes, "get_db", _build_fake_get_db(manager))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            newapi_routes.create_newapi_service(
                NewapiServiceCreate(
                    name="bad-token",
                    api_url="https://newapi.example.com",
                    api_key="系统访问令牌 (System Access Token)",
                )
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Authorization Token 包含非 ASCII 字符，请确认填写的是实际令牌而不是中文说明"


def test_update_newapi_service_rejects_non_ascii_api_key(tmp_path, monkeypatch):
    manager = DatabaseSessionManager(f"sqlite:///{tmp_path}/newapi-update.db")
    manager.create_tables()
    manager.migrate_tables()
    monkeypatch.setattr(newapi_routes, "get_db", _build_fake_get_db(manager))

    created = asyncio.run(
        newapi_routes.create_newapi_service(
            NewapiServiceCreate(
                name="good-token",
                api_url="https://newapi.example.com",
                api_key="token-123",
            )
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            newapi_routes.update_newapi_service(
                created.id,
                NewapiServiceUpdate(api_key="系统访问令牌 (System Access Token)"),
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Authorization Token 包含非 ASCII 字符，请确认填写的是实际令牌而不是中文说明"
