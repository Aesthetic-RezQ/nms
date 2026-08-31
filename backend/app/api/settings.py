from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.system_setting import SystemSetting
from app.schemas.settings import SettingRead, SettingBulkUpdate
from app.schemas.common import MessageResponse
from app.services.audit_service import AuditService
from app.api.deps import require_admin
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("", response_model=List[SettingRead])
@router.get("/", response_model=List[SettingRead], include_in_schema=False)
async def get_settings(db: AsyncSession = Depends(get_db), _ = Depends(require_admin)):
    result = await db.execute(select(SystemSetting))
    return result.scalars().all()

@router.put("", response_model=MessageResponse)
@router.put("/", response_model=MessageResponse, include_in_schema=False)
async def update_settings(data: SettingBulkUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    for setting_update in data.settings:
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == setting_update.key))
        setting = result.scalars().first()
        if setting:
            old_value = setting.value
            setting.value = setting_update.value
            setting.updated_by = current_user.id
            
            await AuditService.create_log(
                db, 
                user_id=current_user.id, 
                username=current_user.username, 
                action="SETTING_CHANGED", 
                object_type="setting", 
                object_id=setting_update.key,
                old_value={"value": old_value},
                new_value={"value": setting_update.value}
            )
            
    await db.commit()
    return MessageResponse(message="Settings updated successfully")

audit_router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])

@audit_router.get("")
@audit_router.get("/", include_in_schema=False)
async def get_audit_logs(
    page: int = 1, 
    page_size: int = 10, 
    action_filter: str = None, 
    object_type_filter: str = None, 
    db: AsyncSession = Depends(get_db), 
    _ = Depends(require_admin)
):
    return await AuditService.get_logs(db, page, page_size, action_filter, object_type_filter)
