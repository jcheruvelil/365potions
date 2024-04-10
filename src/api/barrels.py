import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            ml_to_add = barrel.ml_per_barrel
            gold_to_subtract = barrel.price
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {gold_to_subtract}"))
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {ml_to_add}"))

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).one()[0]
        green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).one()[0]

        if(green_potions < 10):

            for barrel in wholesale_catalog:
                if(barrel.sku == "SMALL_GREEN_BARREL"):
                    if(barrel.price <= gold):
                        print("buy green barrel")
                        return [
                        {
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": 1,
                        }
                    ]

        return []
              

