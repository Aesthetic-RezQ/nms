from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.group import DeviceGroup
from app.models.device import Device
from app.schemas.group import GroupCreate, GroupUpdate
from app.core.exceptions import DuplicateException, NotFoundException, ValidationException

class GroupService:
    @staticmethod
    async def get_all(db: AsyncSession):
        query = select(DeviceGroup, func.count(Device.id).label('device_count')).outerjoin(Device, DeviceGroup.id == Device.group_id).group_by(DeviceGroup.id).order_by(DeviceGroup.name)
        result = await db.execute(query)
        rows = result.all()
        return [{"id": c.DeviceGroup.id, "name": c.DeviceGroup.name, "description": c.DeviceGroup.description, "created_at": c.DeviceGroup.created_at, "device_count": c.device_count} for c in rows]

    @staticmethod
    async def get_by_id(db: AsyncSession, group_id: int):
        result = await db.execute(select(DeviceGroup).where(DeviceGroup.id == group_id))
        group = result.scalars().first()
        if not group:
            raise NotFoundException("Group not found")
        return group

    @staticmethod
    async def create(db: AsyncSession, data: GroupCreate):
        result = await db.execute(select(DeviceGroup).where(DeviceGroup.name == data.name))
        if result.scalars().first():
            raise DuplicateException("Group name already exists")
            
        group = DeviceGroup(
            name=data.name,
            description=data.description
        )
        db.add(group)
        await db.commit()
        await db.refresh(group)
        return group

    @staticmethod
    async def update(db: AsyncSession, group_id: int, data: GroupUpdate):
        group = await GroupService.get_by_id(db, group_id)
        
        if data.name and data.name != group.name:
            result = await db.execute(select(DeviceGroup).where(DeviceGroup.name == data.name))
            if result.scalars().first():
                raise DuplicateException("Group name already exists")
            group.name = data.name
            
        if data.description is not None:
            group.description = data.description
            
        await db.commit()
        await db.refresh(group)
        return group

    @staticmethod
    async def delete(db: AsyncSession, group_id: int):
        group = await GroupService.get_by_id(db, group_id)
        
        result = await db.execute(select(func.count(Device.id)).where(Device.group_id == group_id))
        if result.scalar() > 0:
            raise ValidationException("Cannot delete group with associated devices")
            
        await db.delete(group)
        await db.commit()
