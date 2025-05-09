from fastapi import FastAPI
from src.routes import user, login, FarmCRUD, ExpectationCRUD, cropCRUD, dailyCrop, getPlantMethod, harvest, expensesCRUD, CropActivity# here to include the path
from typing import Union

app = FastAPI()

# Include all the route here
app.include_router(user.router)
app.include_router(login.router)
app.include_router(FarmCRUD.router)
app.include_router(ExpectationCRUD.router)
app.include_router(cropCRUD.router)
app.include_router(dailyCrop.router)
app.include_router(getPlantMethod.router)
app.include_router(harvest.router)
app.include_router(expensesCRUD.router)
app.include_router(CropActivity.router)


@app.get("/")
def read_root():
    return {"Welcome": "!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
