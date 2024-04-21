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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))

        for item in result:
            if item.quantity > 0:
                potion_type = [item.red_ml, item.green_ml, item.blue_ml, item.dark_ml]
                catalog.append(
                {
                    "sku": item.sku,
                    "name": item.name,
                    "quantity": item.quantity,
                    "price": item.price,
                    "potion_type": potion_type,
                }
            )
                
    
    return catalog
