from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from databases import Database
import sqlalchemy
from models import items, metadata, wishlist_items
from fastapi.staticfiles import StaticFiles



# database
DATABASE_URL = "sqlite:///./test.db"
database = Database(DATABASE_URL)
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine) # tworzy tabele jesli nie istnieje


app = FastAPI()

# frontend z folderu static
app.mount("/main", StaticFiles(directory="static", html=True), name="static")

# Model danych dla POST (dodawanie nowego przedmiotu)
class Item(BaseModel):
    type: str
    name: str
    year: str
    color: str

# Model danych dla PATCH (aktualizacja istniejącego przedmiotu)
class ItemUpdate(BaseModel):
    type: str | None = None
    name: str | None = None
    year: str | None = None
    color: str | None = None

class WishlistItem(BaseModel):
    type: str
    name: str
    year: Optional[str] = None
    color: Optional[str] = None


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# OWNED ITEMS    

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
    raise HTTPException(status_code=404, detail="Item not found")


# POST - dodaj nowy przedmiot
@app.post("/api/items/")
async def create_item(item: Item):
    query = items.insert().values(type=item.type, name=item.name, year=item.year, color=item.color)
    last_record_id = await database.execute(query)
    return {"item_id": last_record_id, "data": item.model_dump()}


# DELETE - usun istnejacy przedmiot
@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int):
    query = items.select().where(items.c.id == item_id)
    existing = await database.fetch_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    query = items.delete().where(items.c.id == item_id)
    await database.execute(query)
    return {"message": f"item with id {item_id} deleted"}


# PATCH - aktualizuj wybrane pola istniejącego przedmiotu
@app.patch("/api/items/{item_id}")
async def update_item(item_id: int, item: ItemUpdate):
    query = items.select().where(items.c.id == item_id)
    existing = await database.fetch_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = {}
    if item.type is not None:
        update_data["type"] = item.type
    if item.name is not None:
        update_data["name"] = item.name
    if item.year is not None:
        update_data["year"] = item.year
    if item.color is not None:
        update_data["color"] = item.color

    if update_data:
        query = items.update().where(items.c.id == item_id).values(**update_data)
        await database.execute(query)

    query = items.select().where(items.c.id ==item_id)
    updated_item = await database.fetch_one(query)

    return {"message": "Item updated", "item_id": item_id, "data": dict(updated_item)}


# WISHLIST 

# GET - pobierz wszystko z wishlist
@app.get("/api/wishlist")
async def get_wishlist_all():
    query = wishlist_items.select()
    return await database.fetch_all(query)

#GET - pobierz jeden przedmiot z wishlisty
@app.get("/api/wishlist/{wishlist_item_id}")
async def get_wishlist_item(wishlist_item_id:int):
    query = wishlist_items.select().where(wishlist_items.c.id == wishlist_item_id)
    result = await database.fetch_one(query)
    if result:
        return dict(result)
    raise HTTPException(status_code=404, detail="Item not found")

#POST - dodaj przedmiot do wishlisty
@app.post("/api/wishlist")
async def create_wishlist_item(item: WishlistItem):
    query = wishlist_items.insert().values(**item.model_dump())
    last_id = await database.execute(query)
    return {"id": last_id, "data": item.model_dump()}


# DELETE - usun przedmiot z wishlisty
@app.delete("/api/wishlist/{wishlist_item_id}")
async def delete_wishlist_item(wishlist_item_id:int):
    query = wishlist_items.select().where(wishlist_items.c.id == wishlist_item_id)
    existing = await database.fetch_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    query = wishlist_items.delete().where(wishlist_items.c.id == wishlist_item_id)
    await database.execute(query)
    return {"message": f"item with id {wishlist_item_id} deleted"}
