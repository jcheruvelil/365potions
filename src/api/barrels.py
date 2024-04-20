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

        # try:
        #     connection.execute(
        #         sqlalchemy.text(
        #             "INSERT INTO processed (job_id, type) VALUES (:order_id, 'barrels')"),
        #             [{"order_id": order_id}]
        #         )
        # except IntegrityError as e:
        #     return "OK"

        gold_paid = 0
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0

        for barrel in barrels_delivered:
            potion_type = barrel.potion_type
            gold_paid += barrel.price*barrel.quantity

            if(potion_type == [1, 0, 0, 0]):
                red_ml += barrel.ml_per_barrel*barrel.quantity

            elif(potion_type == [0, 1, 0, 0]):
                green_ml += barrel.ml_per_barrel*barrel.quantity

            elif(potion_type == [0, 0, 1, 0]):
                blue_ml += barrel.ml_per_barrel*barrel.quantity

            elif(potion_type == [0, 0, 0, 1]):
                dark_ml += barrel.ml_per_barrel*barrel.quantity

            else:
                print("Invalid Potion Type")

        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET
                gold = gold - :gold_paid,
                num_red_ml = num_red_ml + :red_ml,
                num_green_ml = num_green_ml + :green_ml,
                num_blue_ml = num_blue_ml + :blue_ml,
                num_dark_ml = num_dark_ml + :dark_ml
                """
            ),
            [{"gold_paid": gold_paid, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml}]
        )

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    gold = 0
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    # dark_ml = 0
    plan = []

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text(("SELECT * FROM global_inventory"))).one()
        gold = results.gold
        red_ml = results.num_red_ml
        green_ml = results.num_green_ml
        blue_ml = results.num_blue_ml
        # dark_ml = results.num_dark_ml
        print("current gold: ", gold)

    ml_levels = [red_ml, green_ml, blue_ml]
    

    # TODO: add thresholds for medium/large barrels

    sorted_potions_idx = sorted(range(len(ml_levels)), key=lambda i: ml_levels[i])
    for idx in sorted_potions_idx:
        #buying red barrel
        if idx == 0:
            for barrel in wholesale_catalog:
                if(barrel.sku == "SMALL_RED_BARREL"):
                    if(barrel.price <= gold):
                        print("buy red barrel")
                        plan.append({
                            "sku": "SMALL_RED_BARREL",
                            "quantity": 1,
                        })
                        gold -= barrel.price
        
        #buying green barrel
        elif idx == 1:
            for barrel in wholesale_catalog:
                if(barrel.sku == "SMALL_GREEN_BARREL"):
                    if(barrel.price <= gold):
                        print("buy green barrel")
                        plan.append({
                            "sku": "SMALL_GREEN_BARREL",
                            "quantity": 1,
                        })
                        gold -= barrel.price

        #buying blue barrel
        elif idx == 2:
            for barrel in wholesale_catalog:
                if(barrel.sku == "SMALL_BLUE_BARREL"):
                    if(barrel.price <= gold):
                        print("buy blue barrel")
                        plan.append({
                            "sku": "SMALL_BLUE_BARREL",
                            "quantity": 1,
                        })
                        gold -= barrel.price

    return plan              

