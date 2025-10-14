"""
Notification service for MongoDB operations
"""
from typing import List
from ..models.notification import Notification


class NotificationService:
    """Service for notification operations with MongoDB"""
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            count = await Notification.find(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).count()
            return count
        except:
            # Fallback: return 0 when DB is not available
            return 0
    
    async def get_notifications_for_user(self, user_id: str) -> List[Notification]:
        """Get all notifications for a user"""
        try:
            return await Notification.find(
                Notification.user_id == user_id
            ).sort(-Notification.created_at).to_list()
        except:
            # Fallback: return empty list when DB is not available
            return []


# Global notification service instance
notification_service = NotificationService()