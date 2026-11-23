from pydantic import BaseModel
from typing import Optional

class UserProfileResponse(BaseModel):
    id: int
    email: str
    password_hash: Optional[str] = None
