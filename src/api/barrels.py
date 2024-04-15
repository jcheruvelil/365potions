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
            barrel_color = barrel.sku
            ml_to_add = barrel.ml_per_barrel
            gold_to_subtract = barrel.price
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {gold_to_subtract}"))

            if(barrel_color == "SMALL_RED_BARREL"):
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_red_ml = num_red_ml + {ml_to_add}"))

            elif(barrel_color == "SMALL_GREEN_BARREL"):
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = num_green_ml + {ml_to_add}"))

            elif(barrel_color == "SMALL_BLUE_BARREL"):
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_blue_ml = num_blue_ml + {ml_to_add}"))

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    plan = []

    gold = db.get_gold()
    potions = [db.get_red_potions(), db.get_green_potions(), db.get_blue_potions()]

    sorted_potions_idx = sorted(range(len(potions)), key=lambda i: potions[i])
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

