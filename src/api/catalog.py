import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    with db.engine.begin() as connection:
        green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).one()[0]
        if green_potions > 0:
            return [
                    {
                        "sku": "GREEN_POTION_0",
                        "name": "green potion",
                        "quantity": 1,
                        "price": 10,
                        "potion_type": [0, 100, 0, 0],
                    }
                ]
        return []
