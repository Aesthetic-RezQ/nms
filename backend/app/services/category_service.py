from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.category import Category
from app.models.device import Device
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.core.exceptions import DuplicateException, NotFoundException, ValidationException
import math

class CategoryService:
    @staticmethod
    async def get_all(db: AsyncSession):
        query = select(Category, func.count(Device.id).label('device_count')).outerjoin(Device, Category.id == Device.category_id).group_by(Category.id).order_by(Category.display_order)
        result = await db.execute(query)
        rows = result.all()
        return [{
            "id": c.Category.id, "name": c.Category.name, "description": c.Category.description,
            "icon": c.Category.icon, "display_order": c.Category.display_order,
            "criticality": c.Category.criticality, "incident_enabled": c.Category.incident_enabled,
            "alert_enabled": c.Category.alert_enabled, "sla_enabled": c.Category.sla_enabled,
            "created_at": c.Category.created_at, "device_count": c.device_count
        } for c in rows]

    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: int):
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalars().first()
        if not category:
            raise NotFoundException("Category not found")
        return category

    @staticmethod
    async def create(db: AsyncSession, data: CategoryCreate):
        result = await db.execute(select(Category).where(Category.name == data.name))
        if result.scalars().first():
            raise DuplicateException("Category name already exists")
            
        category = Category(
            name=data.name,
            description=data.description,
            icon=data.icon,
            display_order=data.display_order,
            criticality=data.criticality or "CRITICAL",
            incident_enabled=data.incident_enabled if data.incident_enabled is not None else True,
            alert_enabled=data.alert_enabled if data.alert_enabled is not None else True,
            sla_enabled=data.sla_enabled if data.sla_enabled is not None else True
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def update(db: AsyncSession, category_id: int, data: CategoryUpdate):
        category = await CategoryService.get_by_id(db, category_id)
        
        if data.name and data.name != category.name:
            result = await db.execute(select(Category).where(Category.name == data.name))
            if result.scalars().first():
                raise DuplicateException("Category name already exists")
            category.name = data.name
            
        if data.description is not None:
            category.description = data.description
        if data.icon is not None:
            category.icon = data.icon
        if data.display_order is not None:
            category.display_order = data.display_order
        if data.criticality is not None:
            category.criticality = data.criticality
        if data.incident_enabled is not None:
            category.incident_enabled = data.incident_enabled
        if data.alert_enabled is not None:
            category.alert_enabled = data.alert_enabled
        if data.sla_enabled is not None:
            category.sla_enabled = data.sla_enabled
            
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category_id: int):
        category = await CategoryService.get_by_id(db, category_id)
        
        result = await db.execute(select(func.count(Device.id)).where(Device.category_id == category_id))
        if result.scalar() > 0:
            raise ValidationException("Cannot delete category with associated devices")
            
        await db.delete(category)
        await db.commit()
