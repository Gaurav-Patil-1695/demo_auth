from datetime import datetime

from pydantic import BaseModel


class PasswordReset(BaseModel):
    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime
