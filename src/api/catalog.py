import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []

    green_potions = db.get_green_potions()
    red_potions = db.get_red_potions()
    blue_potions = db.get_blue_potions()

    if green_potions > 0:
        catalog.append(
                {
                    "sku": "GREEN_POTION_0",
                    "name": "green potion",
                    "quantity": green_potions,
                    "price": 40,
                    "potion_type": [0, 100, 0, 0],
                }
        )

    if red_potions > 0:
        catalog.append(
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": red_potions,
                    "price": 60,
                    "potion_type": [100, 0, 0, 0],
                }
        )

    if blue_potions > 0:
        catalog.append(
                {
                    "sku": "BLUE_POTION_0",
                    "name": "blue potion",
                    "quantity": blue_potions,
                    "price": 60,
                    "potion_type": [0, 0, 100, 0],
                }
        )
    
    return catalog
