from typing import Any
from dataclasses import dataclass

@dataclass
class UserRequestDto:
    id:str
    user_id:str
    session_id:str
    search_term:str
    data:dict

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "search_term": self.search_term,
            "data": self.data or {}
        }
    
    def from_dict(document:dict):
        return UserRequestDto(
            id=document["id"],
            user_id=document["user_id"],
            session_id=document["session_id"],
            search_term=document["search_term"],
            data=document.get("data", {}) or {}
        )