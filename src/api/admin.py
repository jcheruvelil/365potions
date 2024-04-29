import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("DELETE from processed"))
        connection.execute(sqlalchemy.text("DELETE from cart_items"))
        connection.execute(sqlalchemy.text("DELETE from carts"))
        connection.execute(sqlalchemy.text("INSERT into processed (job_id, type) VALUES (0, 'reset')"))
        connection.execute(sqlalchemy.text("INSERT into gold_ledger (job_id, change) VALUES (0, 100)"))
        connection.execute(sqlalchemy.text("""
                                           INSERT into ml_ledger (job_id, color, change) VALUES
                                           (0, 'red', 0),
                                           (0, 'green', 0),
                                           (0, 'blue', 0),
                                           (0, 'dark', 0) 
                                           """))
        connection.execute(sqlalchemy.text("""
                                           INSERT into potion_ledger (job_id, potion_id, change)
                                           SELECT 0, potion_id, 0 FROM potions
                                           """))

    return "OK"

