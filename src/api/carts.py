import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
from sqlalchemy import exc


cart_dict = {}

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name, character_class, level) VALUES (:name, :char_class, :level) RETURNING cart_id"), 
                                    [{"name": new_cart.customer_name, "char_class": new_cart.character_class, "level": new_cart.level}])
        
        cart_id = result.scalar()

    return {"cart_id": cart_id}

class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        # potion_id = connection.execute(sqlalchemy.text("SELECT potion_id FROM potions WHERE sku = :item_sku"), [{"item_sku": item_sku}]).scalar_one()
        # print(potion_id)
        # connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, quantity, potion_id) VALUES( :cart_id, :quantity, :potion_id)"),
        #                    [{"cart_id": cart_id, "quantity": cart_item.quantity, "potion_id": potion_id}])

        connection.execute(sqlalchemy.text("""
                                           INSERT INTO cart_items (cart_id, quantity, potion_id)
                                           SELECT :cart_id, :quantity, potion_id
                                           FROM potions WHERE potions.sku = :item_sku
                                           """), 
                           [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """

    total_potions = 0
    amount_paid = 0
    with db.engine.begin() as connection:
        try:
            connection.execute(
                sqlalchemy.text(
                    "INSERT INTO processed (job_id, type) VALUES (:order_id, 'checkout')"),
                    [{"order_id": cart_id}]
                )
        except exc.IntegrityError as e:
            return "OK"
        
        connection.execute(sqlalchemy.text("""
                                           INSERT into potion_ledger (potion_id, job_id, change) 
                                           SELECT cart_items.potion_id, :cart_id, cart_items.quantity*-1
                                           FROM cart_items
                                           WHERE cart_items.cart_id = :cart_id
                                           """), [{"cart_id": cart_id}])

        result = connection.execute(sqlalchemy.text("""
            SELECT cart_items.quantity, potions.price
            FROM cart_items
            JOIN potions ON cart_items.potion_id = potions.potion_id
            WHERE cart_items.cart_id = :cart_id
        """), [{"cart_id": cart_id}])
        
        # Calculate the total amount paid based on quantities and prices
        for row in result:
            quantity, price = row
            amount_paid += quantity * price
            total_potions += quantity
        connection.execute(sqlalchemy.text("INSERT into gold_ledger (job_id, change) VALUES (:cart_id, :change)"),
                           [{"cart_id": cart_id, "change": amount_paid}])

    return {"total_potions_bought": total_potions, "total_gold_paid": amount_paid}
