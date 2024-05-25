import sqlalchemy
from src import database as db
from fastapi import APIRouter


router = APIRouter(
    prefix="/catalog",
    tags=["catalog"],
)


@router.get("/")
def get_catalog():
    catalog = []
    with db.engine.begin() as connection:
        stock = connection.execute(sqlalchemy.text("""SELECT products.id, products.name, products.description, SUM(change) AS quantity, products.sale_price, products.daily_rental_price, categories.type
                                                      FROM stock_ledger
                                                      JOIN products ON products.id = stock_ledger.product_id
                                                      JOIN categories ON products.category_id = categories.id
                                                      GROUP BY products.id, products.name, products.description, products.sale_price, products.daily_rental_price, categories.type;
                                                   """)).fetchall()
        
        print("Current inventory:", stock)

        for item in stock:
            if item.quantity > 0:
                catalog.append(
                    {
                        "productID": item.id,
                        "product_name": item.name,
                        "category": item.type,
                        "sale price": item.sale_price,
                        "rental price": item.daily_rental_price,
                        "stock": item.quantity,
                        "description": item.description
                    }
                )
                
    return catalog


@router.get("/recs")
def get_recs(userId: int):
    """
    REQ:
        {
        "userId": "integer"
        }
    RES:
        [{
            "productID": "integer",
            "product_name": "string",
            "category": "string",
            "sale price": "integer",
            "rental price": "integer",
            "stock": "integer",
            "description": "string"
        }]
    """
    cat = []
    categories = {}

    with db.engine.begin() as connection:
        # get cart item entries for the user in the past month
        carts = connection.execute(sqlalchemy.text("""SELECT c.id, ci.product_id, ci.quantity, ci.price, p.name, p.category_id
                                                   FROM carts as c
                                                   JOIN cart_items as ci on ci.cart_id = c.id
                                                   JOIN products as p on p.id = ci.product_id
                                                   WHERE c.user_id = :user_id and c.created_at >= CURRENT_DATE - INTERVAL '31 days'"""),
                                                   [{
                                                       "user_id": userId
                                                   }]).fetchall()
        
        if carts == []:
            # just give them the normal catalog...
            print("nothing bought before...")
            return get_catalog()
        
        category_rows = connection.execute(sqlalchemy.text("""SELECT id
                                                           FROM categories""")).fetchall()
        for i in category_rows:
            categories[i.id] = 0

        for cart in carts:
            current_cart = cart.id 
            current_item = cart.product_id
            print("current cart: ", current_cart)
            print("current product_id: ", current_item, " ", cart.name)
            categories[i.id] = categories[i.id] + 1

        print(categories)

        sorted_categories = [k for k, v in sorted(categories.items(), key=lambda item: item[1], reverse=True)]
        print(sorted_categories)

        # ORDER BY
        #     CASE id
        #         WHEN 3 THEN 1
        #         WHEN 1 THEN 2
        #         WHEN 4 THEN 3
        #         WHEN 2 THEN 4
        #         ELSE 5 -- For ids not in the list, place them at the end
        #     END;
        stock = connection.execute(sqlalchemy.text("""SELECT products.id, products.name, products.description, SUM(change) AS quantity, products.sale_price, products.daily_rental_price, categories.type
                                                      FROM stock_ledger
                                                      JOIN products ON products.id = stock_ledger.product_id
                                                      JOIN categories ON products.category_id = categories.id
                                                      GROUP BY products.id, products.name, products.description, products.sale_price, products.daily_rental_price, categories.type;
                                                      ORDER BY
                                                        CASE product.category_id
                                                            WHEN :
                                                   """)).fetchall()





            

    return cat