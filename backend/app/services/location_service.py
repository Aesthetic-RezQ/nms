from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.location import Location
from app.models.device import Device
from app.schemas.location import LocationCreate, LocationUpdate
from app.core.exceptions import DuplicateException, NotFoundException, ValidationException

class LocationService:
    @staticmethod
    async def get_all(db: AsyncSession):
        query = select(Location, func.count(Device.id).label('device_count')).outerjoin(Device, Location.id == Device.location_id).group_by(Location.id).order_by(Location.name)
        result = await db.execute(query)
        rows = result.all()
        return [{"id": c.Location.id, "name": c.Location.name, "description": c.Location.description, "address": c.Location.address, "created_at": c.Location.created_at, "device_count": c.device_count} for c in rows]

    @staticmethod
    async def get_by_id(db: AsyncSession, location_id: int):
        result = await db.execute(select(Location).where(Location.id == location_id))
        location = result.scalars().first()
        if not location:
            raise NotFoundException("Location not found")
        return location

    @staticmethod
    async def create(db: AsyncSession, data: LocationCreate):
        result = await db.execute(select(Location).where(Location.name == data.name))
        if result.scalars().first():
            raise DuplicateException("Location name already exists")
            
        location = Location(
            name=data.name,
            description=data.description,
            address=data.address
        )
        db.add(location)
        await db.commit()
        await db.refresh(location)
        return location

    @staticmethod
    async def update(db: AsyncSession, location_id: int, data: LocationUpdate):
        location = await LocationService.get_by_id(db, location_id)
        
        if data.name and data.name != location.name:
            result = await db.execute(select(Location).where(Location.name == data.name))
            if result.scalars().first():
                raise DuplicateException("Location name already exists")
            location.name = data.name
            
        if data.description is not None:
            location.description = data.description
        if data.address is not None:
            location.address = data.address
            
        await db.commit()
        await db.refresh(location)
        return location

    @staticmethod
    async def delete(db: AsyncSession, location_id: int):
        location = await LocationService.get_by_id(db, location_id)
        
        result = await db.execute(select(func.count(Device.id)).where(Device.location_id == location_id))
        if result.scalar() > 0:
            raise ValidationException("Cannot delete location with associated devices")
            
        await db.delete(location)
        await db.commit()
