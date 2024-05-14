from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db
from datetime import datetime
from math import ceil


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/")
def create_cart(userID: int):
    """ 
    REQ: 
    { "userID": "integer" }
    RES:
    { "cartID": "integer" }
    """
    with db.engine.begin() as connection:
        user_exists = connection.execute(
            sqlalchemy.text("SELECT COUNT(*) FROM users WHERE id = :user_id"),
            {"user_id": userID}
        ).scalar() > 0
        
        if not user_exists:
            return {"Error": f"User with ID {userID} does not exist."}
        
        # user exists in users
        cart_id = connection.execute(
            sqlalchemy.text("""INSERT INTO carts (user_id)
                            VALUES (:user_id) RETURNING id"""),
            {"user_id": userID}
            ).scalar_one()
    

    print(f"creating cart for user {userID} with id {cart_id}")

    return {"cartID": cart_id}
    

class CartItem(BaseModel):
    quantity: int
    

@router.post("/{cart_id}/items/{productID}")
def set_item_quantity(cart_id: int, product_id: int, cart_item: CartItem):
    """ add quantity of items """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""INSERT INTO cart_items (cart_id, product_id, quantity, price)
                                           SELECT :cart_id, :product_id, :quantity, products.sale_price
                                           FROM products
                                           WHERE products.id = :product_id
                                           """),
                                           [{
                                               'cart_id': cart_id,
                                               'quantity': cart_item.quantity,
                                               'product_id': product_id
                                           }])
        
    print("new entry in cart " + str(cart_id) + ". Product id: " + str(product_id))

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """Subtract item quantity and add money"""

    with db.engine.begin() as connection:
        # insert into processed
        trans_id = connection.execute(sqlalchemy.text("""INSERT INTO processed
                                                     (job_id, type) VALUES
                                                     (:job_id, 'item_sale') returning id;
                                                      """),
                                                    [{
                                                        'job_id': cart_id
                                                    }]).fetchone()[0]
        
        connection.execute(sqlalchemy.text("""INSERT INTO stock_ledger 
                                           (trans_id, product_id, change, description)
                                           SELECT :trans_id, product_id, -1 * quantity, :description
                                           FROM cart_items
                                           WHERE cart_items.cart_id = :cart_id"""),
                                           [{
                                               'trans_id': trans_id,
                                               'description': 'sale',
                                               'cart_id': cart_id
                                           }])
        
        connection.execute(sqlalchemy.text("""INSERT INTO money_ledger
                                           (trans_id, change, description)
                                           SELECT :trans_id, SUM(quantity * price), :description
                                           FROM cart_items
                                           WHERE cart_items.cart_id = :cart_id
                                           GROUP BY cart_items.cart_id;"""),
                                           [{
                                               'trans_id': trans_id,
                                               'cart_id': cart_id,
                                               'description': 'sale'
                                           }])
        
        # get quantity of items sold
        quant_bought = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM stock_ledger WHERE trans_id = :trans_id"),
                                          [{
                                              'trans_id': trans_id
                                          }]).fetchone()[0] * -1
        # get money paid
        income = connection.execute(sqlalchemy.text("SELECT change FROM money_ledger WHERE trans_id = :trans_id"),
                                    [{
                                        'trans_id': trans_id
                                    }]).fetchone()[0]
        
    print("stock bought: " + str(quant_bought) + " money paid: " + str(income))

    return {"num_items_bought": quant_bought, "money_paid": income}