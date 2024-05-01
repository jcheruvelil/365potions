import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
from sqlalchemy import exc


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
        try:
            connection.execute(
                sqlalchemy.text(
                    "INSERT INTO processed (order_id, type) VALUES (:order_id, 'bottles')"),
                    [{"order_id": order_id}]
                )
        except exc.IntegrityError as e:
            return "OK"
        
        for potion in potions_delivered:

            ml_used = [x*potion.quantity for x in potion.potion_type]
            total_ml_used = [x + y for x, y in zip(total_ml_used, ml_used)]
            potion_id = connection.execute(sqlalchemy.text("SELECT potion_id FROM potions WHERE red_ml = :red_ml AND green_ml = :green_ml AND blue_ml = :blue_ml AND dark_ml = :dark_ml"),
                               [{"red_ml": potion.potion_type[0], "green_ml": potion.potion_type[1], "blue_ml": potion.potion_type[2], "dark_ml": potion.potion_type[3]}]).first()[0]
            connection.execute(sqlalchemy.text("INSERT into potion_ledger (potion_id, job_id, type, change) VALUES (:potion_id, :job_id, 'bottles', :change)"),
                               [{"potion_id": potion_id, "job_id": order_id, "change": potion.quantity}])

        ledgers_to_insert = [
            ('red', order_id, total_ml_used[0]*-1),
            ('green', order_id, total_ml_used[1]*-1),
            ('blue', order_id, total_ml_used[2]*-1),
            ('dark', order_id, total_ml_used[3]*-1)
        ]    
        ledgers_to_insert = [ledger for ledger in ledgers_to_insert if ledger[2] != 0]
        for led in ledgers_to_insert:
            connection.execute(sqlalchemy.text("""
                                            INSERT into ml_ledger (color, job_id, type, change) VALUES
                                            (:color, :job_id, 'bottles', :change)
                                            """),
                                            [{"color": led[0], "job_id": led[1], "change": led[2] }])
            

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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT
                color,
                SUM(change) AS current_inventory
            FROM ml_ledger
            GROUP BY color
        """)).fetchall()

        inventory = {row[0]: row[1] for row in result}

        curr_ml = [inventory['red'], inventory['green'], inventory['blue'], inventory['dark']]
        potion_cap = connection.execute(sqlalchemy.text("SELECT potion_cap FROM global_inventory")).one()[0]
        ind_potion_cap = (potion_cap*50) // 6
        
        p_result = connection.execute(sqlalchemy.text("""
            SELECT
                potion_id,
                SUM(change) AS current_inventory
            FROM potion_ledger
            GROUP BY potion_id
        """)).fetchall()

        catalog = {row[0]: row[1] for row in p_result}
        
        for pid, quantity in catalog.items():
            red, green, blue, dark = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM potions WHERE potion_id = :pid"), 
                                                        [{"pid": pid}]).first()
            ml_needed = [red, green, blue, dark]

            if(curr_ml[0] >= ml_needed[0] and curr_ml[1] >= ml_needed[1] and curr_ml[2] >= ml_needed[2] and curr_ml[3] >= ml_needed[3]):
                max_quants = [x // y if y!= 0 else -1 for x, y in zip(curr_ml, ml_needed)]
                max_quants = [x for x in max_quants if x>=0]
                max_num = min(max_quants)
                to_bottle = min(max_num, (ind_potion_cap-quantity))
                if to_bottle > 0:
                    plan.append(
                        {
                            "potion_type": [ml_needed[0], ml_needed[1], ml_needed[2], ml_needed[3]],
                            "quantity": to_bottle
                        }
                    )
                    ml_used = [x*max_num for x in ml_needed]
                    curr_ml = [x-y for x, y in zip(curr_ml, ml_used)]

    return plan

if __name__ == "__main__":
    print(get_bottle_plan())