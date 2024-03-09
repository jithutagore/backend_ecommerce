from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pymysql
from services.query_scrapper import google_search,html_parser,comparer,google_search_morzilla,extract_reviews_from_url,run_insert_tracker_data
from services.models_api import UserCreate,Login,CartItem
from datetime  import datetime,timedelta
import jwt
from typing import List
import threading
import time

# Your JWT secret key
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# Create and start a new thread to run the insert_tracker_data function
insert_tracker_thread = threading.Thread(target=run_insert_tracker_data)
insert_tracker_thread.start()





# Function to create JWT token
def create_jwt_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {"sub": email, "exp": expire}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# Function to decode JWT token
def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Signature has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Your other functions...

# Your database connection
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='admin123',
    database='ecommerce',
    cursorclass=pymysql.cursors.DictCursor
)

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST","DELETE"],
    allow_headers=["*"],
)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE"],
#     allow_headers=["*"],
# )


cursor = conn.cursor()

# API endpoints
@app.post("/auth/signup")
async def create_user(user: UserCreate):
    # Check if email already exists
    cursor.execute("SELECT email FROM users_data WHERE email = %s", (user.email,))
    existing_email = cursor.fetchone()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Insert the new user
    sql = "INSERT INTO users_data (username, email, password) VALUES (%s, %s, %s)"
    val = (user.username, user.email, user.password)
    cursor.execute(sql, val)
    conn.commit()
    token = create_jwt_token(user.email)  # Create JWT token for the user
    return {"success": True, "token": token}

@app.get("/search/")
async def search(query: str):
    try:
        html_content = google_search(query)
        results = html_parser(html_content)
        return {"results": results}
    except HTTPException as e:
        return {"error": str(e.detail)}
    except ConnectionResetError as e:
        return {"error": "Connection reset by peer"}  # Handle connection reset error gracefully


@app.post("/login/")
async def user_login(login: Login):
    sql = "SELECT * FROM users_data WHERE email = %s AND password = %s"
    val = (login.email, login.password)
    cursor.execute(sql, val)
    user = cursor.fetchone()
    if user:
        token = create_jwt_token(user['email'])  # Create JWT token for the user
        return {"success": True, "token": token}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")


# Insert data into the cart table
@app.post("/insert_cart_item/")
async def add_to_cart(item: CartItem):
    try:
        query = "INSERT INTO cart (email, product_id, product_url, image_url, product_description, price, product_title,google_product_url) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)"
        values = (item.email, item.product_id, item.product_url, item.image_url, item.product_description, item.price, item.product_title,item.google_product_url)
        cursor.execute(query, values)
        conn.commit()
        return {"message": "Item added to cart successfully"}
    except Exception as e:
        return {"error": str(e)}

# Delete cart data by product_id
@app.delete("/cart/")
async def delete_cart(product_id: str):
    try:
        query = "DELETE FROM cart WHERE product_id = %s"
        cursor.execute(query, (product_id,))
        conn.commit()
        return {"message": f"Cart data with product ID {product_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/get_product_info/")
async def get_product_info(url: str):
    html_content = google_search_morzilla(url)
    if html_content:
        product_info = comparer(html_content,url)
        return product_info
    else:
        return {"error": "Failed to fetch HTML content."}
    

# Define endpoint to retrieve cart by email
@app.get("/cart/{email}")
async def get_cart(email: str):
    try:
        # Create cursor
        cursor = conn.cursor()

        # Execute SQL query to retrieve cart for the given email
        sql = f"SELECT * FROM cart WHERE email = '{email}'"
        cursor.execute(sql)
        cart_data = cursor.fetchall()

        # Close cursor
        cursor.close()

        # Check if cart is empty
        if not cart_data:
            raise HTTPException(status_code=404, detail="Cart not found")

        return cart_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# API endpoint to fetch tracker data
@app.get("/tracker_data")
async def get_tracker_data(product_id: str):
    try:
        # Create a cursor
        cursor = conn.cursor()

        # Execute SQL query to retrieve tracker data for the given product ID
        sql = "SELECT price, timestamp FROM tracker WHERE product_id = %s"
        cursor.execute(sql, (product_id,))
        tracker_data = cursor.fetchall()

        # Close cursor
        cursor.close()

        # Check if tracker data is empty
        if not tracker_data:
            raise HTTPException(status_code=404, detail="Tracker data not found")

        return tracker_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
# Define a route to extract reviews from a URL
@app.post("/extract_reviews/")
async def extract_reviews(url: str):
    reviews = extract_reviews_from_url(url)
    return reviews or []

# Run the application with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8500)
