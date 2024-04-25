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
    dark_ml = 0
    ml_cap = 0
    plan = []

    with db.engine.begin() as connection:
        gold, red_ml, green_ml, blue_ml, dark_ml, ml_cap = connection.execute(sqlalchemy.text(("SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, ml_cap FROM global_inventory"))).first()
        print("current gold: ", gold)

    ml_cap = ml_cap*10000
    ind_ml_cap = ml_cap / 4
    

    sorted_wholesale_catalog = sorted(wholesale_catalog, key=lambda x: x.ml_per_barrel / x.price)
    for barrel in sorted_wholesale_catalog:
        if barrel.potion_type == [1, 0, 0, 0]:
            to_fill = (ind_ml_cap-red_ml)//barrel.ml_per_barrel
            to_buy = min(barrel.quantity, gold // barrel.price, to_fill)
            if to_buy > 0:
                plan.append({"sku": barrel.sku, "quantity": to_buy})
                gold -= barrel.price*to_buy

        elif barrel.potion_type == [0, 1, 0, 0]:
            to_fill = (ind_ml_cap-green_ml)//barrel.ml_per_barrel
            to_buy = min(barrel.quantity, gold // barrel.price, to_fill)
            if to_buy > 0:
                plan.append({"sku": barrel.sku, "quantity": to_buy})
                gold -= barrel.price*to_buy

        elif barrel.potion_type == [0, 0, 1, 0]:
            to_fill = (ind_ml_cap-blue_ml)//barrel.ml_per_barrel
            to_buy = min(barrel.quantity, gold // barrel.price, to_fill)
            if to_buy > 0:
                plan.append({"sku": barrel.sku, "quantity": to_buy})
                gold -= barrel.price*to_buy

        elif barrel.potion_type == [0, 0, 0, 1]:
            to_fill = (ind_ml_cap-dark_ml)//barrel.ml_per_barrel
            to_buy = min(barrel.quantity, gold // barrel.price, to_fill)
            if to_buy > 0:
                plan.append({"sku": barrel.sku, "quantity": to_buy})
                gold -= barrel.price*to_buy

    return plan              

