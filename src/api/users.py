from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy import text
from src import database as db
from enum import Enum
from typing import List
from pydantic import BaseModel

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(auth.get_api_key)],
)

class PreferredActivity(str, Enum):
    Hiking = "Hiking"
    Camping = "Camping"


class User(BaseModel):
    name: str
    email: str
    phone_number: str
    preferred_activities: List[PreferredActivity]


@router.post("/user/{userID}")
def user_register(newUser: User):
    """
    REQ
        {
        "name": "string",
        "email": "string",
        "phone_number": "string",
        "preferred_activities": List[PreferredActivity]
        }
    RES
        {
        "userID": "integer",
        "success": "boolean"
        }

    """

    with db.engine.begin() as connection:
        userID = connection.execute(
            sqlalchemy.text("INSERT INTO users (name, email, phone_number, preferred_activities) "
                            "VALUES (:name, :email, :phone_number, :preferred_activities) RETURNING id"),
                            {"name": newUser.name,
                             "email": newUser.email,
                            "phone_number": newUser.phone_number, 
                            "preferred_activities": newUser.preferred_activities}).scalar_one()
    
        print(f"Creating user for {newUser.name} with id {userID}")

        if (userID):
            success = True
        else:
            success = False

        return {"userID": userID, "success": success}
