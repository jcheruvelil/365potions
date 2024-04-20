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

    total_ml_used = [0, 0, 0, 0]


    with db.engine.begin() as connection:
        for potion in potions_delivered:
            
            # result = connection.execute(
            #     sqlalchemy.text("SELECT EXISTS (SELECT 1 FROM potions WHERE potion_type = :potion_type)"), [{"potion_type": potion.potion_type}]
            # )

            # if not result:
            #     #add new potion row to table
            #     pot_type = potion.potion_type
            #     new_sku = "R" + str(pot_type[0]) + "G" + str(pot_type[1]) + "B" + str(pot_type[2]) + "D" + str(pot_type[3])

            ml_used = [x*potion.quantity for x in potion.potion_type]
            print(ml_used)
            total_ml_used = [x + y for x, y in zip(total_ml_used, ml_used)]
            connection.execute(sqlalchemy.text("UPDATE potions SET quantity = quantity +:num_to_add WHERE potion_type = :potion_type"),
                               [{"num_to_add": potion.quantity, "potion_type": str(potion.potion_type)}])
        print(total_ml_used) 
        connection.execute(sqlalchemy.text("""
                                           UPDATE global_inventory SET
                                           num_red_ml = num_red_ml - :red_ml_used, 
                                           num_green_ml = num_green_ml - :green_ml_used, 
                                           num_blue_ml = num_blue_ml - :blue_ml_used, 
                                           num_dark_ml = num_dark_ml - :dark_ml_used
                                           """),
                                           [{"red_ml_used": total_ml_used[0], "green_ml_used": total_ml_used[1], "blue_ml_used": total_ml_used[2], "dark_ml_used": total_ml_used[3]}])
            

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

    red_ml = 0
    green_ml = 0
    blue_ml = 0
    # dark_ml = 0
    plan = []

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text(("SELECT * FROM global_inventory"))).one()
        red_ml = results.num_red_ml
        green_ml = results.num_green_ml
        blue_ml = results.num_blue_ml
        # dark_ml = results.num_dark_ml

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