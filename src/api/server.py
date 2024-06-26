from fastapi import FastAPI, exceptions
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from src.api import admin, stock, users, carts, catalog, marketplace, millions, rent
import json
import logging
import sys
from starlette.middleware.cors import CORSMiddleware
import sqlalchemy
from src import database as db


description = """
Eco-Trek Equipment Co. is the premier ecommerce site for all your outdoorsy desires.
"""

app = FastAPI(
    title="eco-trek-equipment-co.",
    description=description,
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Isaac Schiffler",
        "email": "ischiffl@calpoly.edu",
    },
)

origins = ["https://potion-exchange.vercel.app"]



app.include_router(admin.router)
app.include_router(stock.router)
app.include_router(users.router)
app.include_router(carts.router)
app.include_router(catalog.router)
app.include_router(marketplace.router)
app.include_router(millions.router)
app.include_router(rent.router)

@app.exception_handler(exceptions.RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    logging.error(f"The client sent invalid data!: {exc}")
    exc_json = json.loads(exc.json())
    response = {"message": [], "data": None}
    for error in exc_json:
        response['message'].append(f"{error['loc']}: {error['msg']}")

    return JSONResponse(response, status_code=422)

@app.get("/")
async def root():
    return {"message": "Welcome to Eco-Trek Equipment Co."}
