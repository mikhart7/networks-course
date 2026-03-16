import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

products = {}
next_id = 1


class Product(BaseModel):
    id: int
    name: str
    description: str
    icon: Optional[str] = None  

class ProductCreate(BaseModel):
    name: str
    description: str


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


def to_product(product_id: int) -> Product:
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    return products[product_id]



@app.post("/product", response_model=Product)
def create_product(payload: ProductCreate) -> Product:
    global next_id
    product_id = next_id
    next_id += 1

    new_product = Product(id=product_id, **payload.model_dump())
    products[product_id] = new_product
    return new_product


@app.get("/product/{product_id}", response_model=Product)
def get_product(product_id: int) -> Product:
    return to_product(product_id)



@app.put("/product/{product_id}", response_model=Product)
def update_product(product_id: int, payload: ProductUpdate) -> Product:
    product = to_product(product_id)
    update_data = payload.model_dump(exclude_unset=True)
    updated_product = product.model_copy(update=update_data)
    products[product_id] = updated_product
    return updated_product


@app.delete("/product/{product_id}", response_model=Product)
def delete_product(product_id: int) -> Product:
    product = to_product(product_id)
    if product.icon:
        path = os.path.join(IMAGES_DIR, product.icon)
        if os.path.exists(path):
            os.remove(path)

    del products[product_id]
    return product

@app.get("/products", response_model=list[Product])
def list_products():
    return list(products.values())

@app.post("/product/{product_id}/image", response_model=Product)
def upload_product_image(product_id: int, file: UploadFile = File(...)) -> Product:
    product = to_product(product_id)

    filename = f"{product_id}_{file.filename}"
    filepath = os.path.join(IMAGES_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    updated_product = product.model_copy(update={"icon": filename})
    products[product_id] = updated_product
    return updated_product


@app.get("/product/{product_id}/image")
def get_product_image(product_id: int):
    product = to_product(product_id)

    if not product.icon:
        raise HTTPException(status_code=404, detail="Product has no icon")

    filepath = os.path.join(IMAGES_DIR, product.icon)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Icon file not found")

    return FileResponse(filepath)