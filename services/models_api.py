from pydantic import BaseModel
# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

# Define a Pydantic model for the request body
class URLInput(BaseModel):
    url: str


    # CartItem model
class CartItem(BaseModel):
    email: str
    product_id: str
    product_url: str
    image_url: str
    product_description: str
    price: str
    product_title: str
    