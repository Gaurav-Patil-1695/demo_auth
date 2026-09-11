from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PasswordReset(BaseModel):
    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime
