from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from databases import Database
import sqlalchemy
from models import items, metadata
from fastapi.staticfiles import StaticFiles


# database
DATABASE_URL = "sqlite:///./test.db"
database = Database(DATABASE_URL)
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine) # tworzy tabele jesli nie istnieje


app = FastAPI()

# frontend z folderu static
app.mount("/frontend", StaticFiles(directory="static", html=True), name="static")

# Model danych dla POST (dodawanie nowego przedmiotu)
class Item(BaseModel):
    type: str
    name: str
    year: int

# Model danych dla PATCH (aktualizacja istniejącego przedmiotu)
class ItemUpdate(BaseModel):
    type: str | None = None
    name: str | None = None
    year: int | None = None


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

    
# pobierz wszystkie przedmioty
@app.get("/api/items/")
async def get_all_items():
    query = items.select()
    result = await database.fetch_all(query)
    return [dict(r) for r in result]
    

# GET pobierz pojedynczy przedmiot
@app.get("/api/items/{item_id}")
async def read_item(item_id: int):
    query = items.select().where(items.c.id == item_id)
    result = await database.fetch_one(query)
    if result:
        return dict(result)
    return {"error": "item not found"}


# POST - dodaj nowy przedmiot
@app.post("/api/items/")
async def create_item(item: Item):
    query = items.insert().values(type=item.type, name=item.name, year=item.year)
    last_record_id = await database.execute(query)
    return {"item_id": last_record_id, "data": item.dict()}


# DELETE - usun istnejacy przedmiot
@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int):
    query = items.select().where(items.c.id == item_id)
    existing = await database.fetch_one(query)
    if not existing:
        return {"error": "Item not found"}
    
    query = items.delete().where(items.c.id == item_id)
    await database.execute(query)
    return {"message": f"item with id {item_id} deleted"}


# PATCH - aktualizuj wybrane pola istniejącego przedmiotu
@app.patch("/api/items/{item_id}")
async def update_item(item_id: int, item: ItemUpdate):
    query = items.select().where(items.c.id == item_id)
    existing = await database.fetch_one(query)
    if not existing:
        return {"error": "item not found"}
    
    update_data = {}
    if item.type is not None:
        update_data["type"] = item.type
    if item.name is not None:
        update_data["name"] = item.name
    if item.year is not None:
        update_data["year"] = item.year

    if update_data:
        query = items.update().where(items.c.id == item_id).values(**update_data)
        await database.execute(query)

    query = items.select().where(items.c.id ==item_id)
    updated_item = await database.fetch_one(query)

    return {"message": "Item updated", "item_id": item_id, "data": dict(updated_item)}
