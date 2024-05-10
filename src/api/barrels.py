import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from sqlalchemy import exc

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

        try:
            connection.execute(
                sqlalchemy.text(
                    "INSERT INTO processed (order_id, type) VALUES (:order_id, 'barrels')"),
                    [{"order_id": order_id}]
                )
        except exc.IntegrityError as e:
            return "OK"

        gold_paid = 0
        red_ml = 0
        green_ml = 0
        blue_ml = 0
        dark_ml = 0

        for barrel in barrels_delivered:
            potion_type = barrel.potion_type
            gold_paid += barrel.price*barrel.quantity
            ml_to_add = barrel.ml_per_barrel*barrel.quantity
            color = None

            if(potion_type == [1, 0, 0, 0]):
                color = 'red'

            elif(potion_type == [0, 1, 0, 0]):
                color = 'green'

            elif(potion_type == [0, 0, 1, 0]):
                color = 'blue'

            elif(potion_type == [0, 0, 0, 1]):
                color = 'dark'

            else:
                print("Invalid Potion Type")

            connection.execute(sqlalchemy.text("INSERT into ml_ledger (color, job_id, type, change) VALUES (:color, :order_id, 'barrels', :change)"),
                               [{"color": color, "order_id": order_id, "change": ml_to_add}])

        connection.execute(
            sqlalchemy.text("INSERT into gold_ledger (job_id, type, change) VALUES (:order_id, 'barrels', :change)"),
            [{"order_id": order_id, "change": gold_paid*-1}]
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
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger")).one()[0]
        ml_cap = connection.execute(sqlalchemy.text("SELECT ml_cap FROM global_inventory")).one()[0]
        result = connection.execute(sqlalchemy.text("""
            SELECT
                color,
                SUM(change) AS current_inventory
            FROM ml_ledger
            GROUP BY color
        """)).fetchall()

        inventory = {row[0]: row[1] for row in result}
        red_ml = inventory['red']
        green_ml = inventory['green']
        blue_ml = inventory['blue']
        dark_ml = inventory['dark']


    ml_cap = ml_cap*10000
    ind_ml_cap = ml_cap / 3
    

    sorted_wholesale_catalog = sorted(wholesale_catalog, key=lambda x: x.ml_per_barrel / x.price, reverse=True)
    print(sorted_wholesale_catalog)
    for barrel in sorted_wholesale_catalog:
        if barrel.potion_type == [1, 0, 0, 0]:
            to_fill = (ind_ml_cap-red_ml)//barrel.ml_per_barrel
            to_buy = min(barrel.quantity, gold // barrel.price, to_fill)
            if to_buy > 0:
                plan.append({"sku": barrel.sku, "quantity": int(to_buy)})
                gold -= barrel.price*to_buy
                red_ml += barrel.quantity

        elif barrel.potion_type == [0, 1, 0, 0]:
            to_fill = (ind_ml_cap-green_ml)//barrel.ml_per_barrel
            to_buy = min(barrel.quantity, gold // barrel.price, to_fill)
            if to_buy > 0:
                plan.append({"sku": barrel.sku, "quantity": int(to_buy)})
                gold -= barrel.price*to_buy
                green_ml += barrel.quantity

        elif barrel.potion_type == [0, 0, 1, 0]:
            to_fill = (ind_ml_cap-blue_ml)//barrel.ml_per_barrel
            to_buy = min(barrel.quantity, gold // barrel.price, to_fill)
            if to_buy > 0:
                plan.append({"sku": barrel.sku, "quantity": int(to_buy)})
                gold -= barrel.price*to_buy
                blue_ml += barrel.quantity

        elif barrel.potion_type == [0, 0, 0, 1]:
            continue
            # to_fill = (ind_ml_cap-dark_ml)//barrel.ml_per_barrel
            # to_buy = min(barrel.quantity, gold // barrel.price, to_fill)
            # if to_buy > 0:
            #     plan.append({"sku": barrel.sku, "quantity": int(to_buy)})
            #     gold -= barrel.price*to_buy
            #     dark_ml += barrel.quantity

    return plan              

