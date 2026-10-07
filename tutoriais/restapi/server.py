from fastapi import FastAPI
from pydantic import BaseModel

#TUTORIAL = https://www.geeksforgeeks.org/python/creating-first-rest-api-with-fastapi/

app = FastAPI()

# Define Item model
class Item(BaseModel):
    name: str
    price: float

# Temporary in-memory storage
items = {}

# CREATE
@app.post("/items/")
async def create_item(item: Item):
    item_id = len(items) + 1
    items[item_id] = item
    return {"id": item_id, "item": item}

# READ
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return items.get(item_id, {"error": "Item not found"})

# UPDATE
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    if item_id in items:
        items[item_id] = item
        return {"message": "Item updated", "item": item}
    return {"error": "Item not found"}

# DELETE
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if item_id in items:
        deleted_item = items.pop(item_id)
        return {"message": "Item deleted", "item": deleted_item}
    return {"error": "Item not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)