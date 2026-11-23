from pydantic import BaseModel, Field
from typing import Optional

class UserProfileResponse(BaseModel):
    id: int
    email: str
    password_hash: Optional[str] = Field(None, exclude=True)
