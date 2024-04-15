import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            potions_to_add = potion.quantity

            if(potion.potion_type == [0, 100, 0, 0]):
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = num_green_potions + {potions_to_add}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml - ({potions_to_add}*100)"))

            elif(potion.potion_type == [100, 0, 0, 0]):
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_potions = num_red_potions + {potions_to_add}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml - ({potions_to_add}*100)"))

            elif(potion.potion_type == [0, 0, 100, 0]):
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_potions = num_blue_potions + {potions_to_add}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml - ({potions_to_add}*100)"))
            

    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into green potions.

    plan = []

    green_ml = db.get_green_ml()
    red_ml = db.get_red_ml()
    blue_ml = db.get_blue_ml()

    if green_ml >= 100:
        plan.append(
                {
                    "potion_type": [0, 100, 0, 0],
                    "quantity": green_ml // 100,
                }
        )

    if red_ml >= 100:
        plan.append(
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": red_ml // 100,
                }
        )

    if blue_ml >= 100:
        plan.append(
                {
                    "potion_type": [0, 0, 100, 0],
                    "quantity": blue_ml // 100,
                }
        )

    return plan

if __name__ == "__main__":
    print(get_bottle_plan())