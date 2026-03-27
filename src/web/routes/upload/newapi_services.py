"""
NEWAPI 服务管理 API 路由
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ....database import crud
from ....database.session import get_db
from ....core.upload.newapi_upload import normalize_authorization_token

router = APIRouter()


class NewapiServiceCreate(BaseModel):
    name: str
    api_url: str
    api_key: str
    channel_type: int = 57
    channel_base_url: str = ""
    channel_models: str = "gpt-5.4,gpt-5,gpt-5-codex,gpt-5-codex-mini,gpt-5.1,gpt-5.1-codex,gpt-5.1-codex-max,gpt-5.1-codex-mini,gpt-5.2,gpt-5.2-codex,gpt-5.3-codex,gpt-5-openai-compact,gpt-5-codex-openai-compact,gpt-5-codex-mini-openai-compact,gpt-5.1-openai-compact,gpt-5.1-codex-openai-compact,gpt-5.1-codex-max-openai-compact,gpt-5.1-codex-mini-openai-compact,gpt-5.2-openai-compact,gpt-5.2-codex-openai-compact,gpt-5.3-codex-openai-compact"
    enabled: bool = True
    priority: int = 0


class NewapiServiceUpdate(BaseModel):
    name: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    channel_type: Optional[int] = None
    channel_base_url: Optional[str] = None
    channel_models: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


class NewapiServiceResponse(BaseModel):
    id: int
    name: str
    api_url: str
    has_key: bool
    channel_type: int = 57
    channel_base_url: str = ""
    channel_models: str = ""
    enabled: bool
    priority: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


def _to_response(svc) -> NewapiServiceResponse:
    return NewapiServiceResponse(
        id=svc.id,
        name=svc.name,
        api_url=svc.api_url,
        has_key=bool(svc.api_key),
        channel_type=svc.channel_type if svc.channel_type is not None else 57,
        channel_base_url=svc.channel_base_url or "",
        channel_models=svc.channel_models or "",
        enabled=svc.enabled,
        priority=svc.priority,
        created_at=svc.created_at.isoformat() if svc.created_at else None,
        updated_at=svc.updated_at.isoformat() if svc.updated_at else None,
    )


def _validated_newapi_api_key(api_key: str) -> str:
    try:
        return normalize_authorization_token(api_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=List[NewapiServiceResponse])
async def list_newapi_services(enabled: Optional[bool] = None):
    with get_db() as db:
        services = crud.get_newapi_services(db, enabled=enabled)
        return [_to_response(s) for s in services]


@router.post("", response_model=NewapiServiceResponse)
async def create_newapi_service(request: NewapiServiceCreate):
    with get_db() as db:
        svc = crud.create_newapi_service(
            db,
            name=request.name,
            api_url=request.api_url,
            api_key=_validated_newapi_api_key(request.api_key),
            channel_type=request.channel_type,
            channel_base_url=request.channel_base_url,
            channel_models=request.channel_models,
            enabled=request.enabled,
            priority=request.priority,
        )
        return _to_response(svc)


@router.get("/{service_id}", response_model=NewapiServiceResponse)
async def get_newapi_service(service_id: int):
    with get_db() as db:
        svc = crud.get_newapi_service_by_id(db, service_id)
        if not svc:
            raise HTTPException(status_code=404, detail="NEWAPI 服务不存在")
        return _to_response(svc)


@router.patch("/{service_id}", response_model=NewapiServiceResponse)
async def update_newapi_service(service_id: int, request: NewapiServiceUpdate):
    with get_db() as db:
        svc = crud.get_newapi_service_by_id(db, service_id)
        if not svc:
            raise HTTPException(status_code=404, detail="NEWAPI 服务不存在")

        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.api_url is not None:
            update_data["api_url"] = request.api_url
        if request.api_key:
            update_data["api_key"] = _validated_newapi_api_key(request.api_key)
        if request.enabled is not None:
            update_data["enabled"] = request.enabled
        if request.priority is not None:
            update_data["priority"] = request.priority
        if request.channel_type is not None:
            update_data["channel_type"] = request.channel_type
        if request.channel_base_url is not None:
            update_data["channel_base_url"] = request.channel_base_url
        if request.channel_models is not None:
            update_data["channel_models"] = request.channel_models

        svc = crud.update_newapi_service(db, service_id, **update_data)
        return _to_response(svc)


@router.delete("/{service_id}")
async def delete_newapi_service(service_id: int):
    with get_db() as db:
        svc = crud.get_newapi_service_by_id(db, service_id)
        if not svc:
            raise HTTPException(status_code=404, detail="NEWAPI 服务不存在")
        crud.delete_newapi_service(db, service_id)
        return {"success": True, "message": f"NEWAPI 服务 {svc.name} 已删除"}
