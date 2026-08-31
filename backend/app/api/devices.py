from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceRead, DeviceListFilter, DeviceBulkImportResult
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.device_service import DeviceService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user, require_admin
from uuid import UUID
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/api/devices", tags=["Devices"])

@router.get("/export", response_class=PlainTextResponse)
async def export_devices(
    status: str = None, category_id: int = None, group_id: int = None, location_id: int = None, vlan_id: int = None, search: str = None,
    db: AsyncSession = Depends(get_db), _ = Depends(get_current_user)
):
    filters = DeviceListFilter(status=status, category_id=category_id, group_id=group_id, location_id=location_id, vlan_id=vlan_id, search=search)
    csv_content = await DeviceService.export(db, filters)
    return PlainTextResponse(content=csv_content, headers={"Content-Disposition": "attachment; filename=devices.csv"})

@router.post("/import", response_model=DeviceBulkImportResult)
async def import_devices(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    content = await file.read()
    result = await DeviceService.bulk_import(db, content.decode("utf-8"))
    await AuditService.create_log(db, user_id=current_user.id, username=current_user.username, action="DEVICE_IMPORT", object_type="device")
    return result

@router.get("", response_model=PaginatedResponse[DeviceRead])
@router.get("/", response_model=PaginatedResponse[DeviceRead], include_in_schema=False)
async def list_devices(
    page: int = 1, page_size: int = 10, 
    status: str = None, category_id: int = None, group_id: int = None, location_id: int = None, vlan_id: int = None, search: str = None,
    db: AsyncSession = Depends(get_db), _ = Depends(get_current_user)
):
    filters = DeviceListFilter(status=status, category_id=category_id, group_id=group_id, location_id=location_id, vlan_id=vlan_id, search=search)
    return await DeviceService.get_all(db, page, page_size, filters)

@router.post("", response_model=DeviceRead)
@router.post("/", response_model=DeviceRead, include_in_schema=False)
async def create_device(data: DeviceCreate, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    device = await DeviceService.create(db, data)
    await AuditService.create_log(db, user_id=current_user.id, username=current_user.username, action="DEVICE_CREATED", object_type="device", object_id=str(device['id']))
    return device

@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: UUID, db: AsyncSession = Depends(get_db), _ = Depends(get_current_user)):
    return await DeviceService.get_by_id(db, device_id)

@router.put("/{device_id}", response_model=DeviceRead)
async def update_device(device_id: UUID, data: DeviceUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    device = await DeviceService.update(db, device_id, data)
    await AuditService.create_log(db, user_id=current_user.id, username=current_user.username, action="DEVICE_UPDATED", object_type="device", object_id=str(device_id))
    return device

@router.delete("/{device_id}", response_model=MessageResponse)
async def delete_device(device_id: UUID, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    await DeviceService.delete(db, device_id)
    await AuditService.create_log(db, user_id=current_user.id, username=current_user.username, action="DEVICE_DELETED", object_type="device", object_id=str(device_id))
    return MessageResponse(message="Device deleted successfully")
