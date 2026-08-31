from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.audit_log import AuditLog
from uuid import UUID
from typing import Optional, Any
import math

class AuditService:
    @staticmethod
    async def create_log(
        db: AsyncSession,
        user_id: Optional[UUID],
        username: Optional[str],
        action: str,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        source_ip: Optional[str] = None
    ):
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            object_type=object_type,
            object_id=object_id,
            old_value=old_value,
            new_value=new_value,
            source_ip=source_ip
        )
        db.add(log)
        await db.commit()
        return log

    @staticmethod
    async def get_logs(db: AsyncSession, page: int = 1, page_size: int = 10, action_filter: Optional[str] = None, object_type_filter: Optional[str] = None):
        query = select(AuditLog)
        
        if action_filter:
            query = query.where(AuditLog.action == action_filter)
        if object_type_filter:
            query = query.where(AuditLog.object_type == object_type_filter)
            
        count_query = select(func.count(AuditLog.id))
        if action_filter:
            count_query = count_query.where(AuditLog.action == action_filter)
        if object_type_filter:
            count_query = count_query.where(AuditLog.object_type == object_type_filter)
            
        result = await db.execute(count_query)
        total = result.scalar() or 0
        
        query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return {
            "data": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }
