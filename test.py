import pymysql
from bs4 import BeautifulSoup
import urllib.parse
import requests
import threading
import time

def get_database_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='admin123',
        database='ecommerce',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_lowest_price(html_content, email, product_id, product_url, image_url):
    data = []
    soup = BeautifulSoup(html_content, "html.parser")
    buying_options_div = soup.find("div", class_="sh-pov__grid")
    product_description = ""
    title = ""
    lowest_price = None
    lowest_price_seller = None
    lowest_price_seller_url = None
    if buying_options_div:
        for row in buying_options_div.find_all("tr", class_="sh-osd__offer-row"):
            seller_name = row.find("td", class_="SH30Lb").text.strip().replace('Opens in a new window', '') 
            item_price = row.find("span", class_="g9WBQb").text.strip().replace('\u20b9', '')  # Remove currency symbol
            for anchor_tag in row.find_all("a", href=True):
                href = anchor_tag["href"]
                href1 = urllib.parse.unquote(href.replace("/url?q=", "").replace("\\x3d", "=").replace("\\x26", "&"))
                data.append({
                    "Seller": seller_name,
                    "Item Price": item_price,
                    "Href": href1
                })
    else:
        print("Buying options div not found in the HTML content.")

    if data:
        # Find the seller with the lowest price
        lowest_price = float('inf')  # Set to positive infinity initially
        for item in data:
            item_price = float(item['Item Price'].replace(",", ""))
            if item_price < lowest_price:
                lowest_price = item_price
                lowest_price_seller = item['Seller']
                lowest_price_seller_url = item["Href"]

    # Get product description and title
    description_tag = soup.find('span', class_='BvQan')
    if description_tag:
        title = description_tag.text.strip()

    description_tags = soup.find_all('li', class_='KgL16d')
    if description_tags:
        product_description = "\n".join([tag.span.text.strip() for tag in description_tags])
    else:
        description_tag = soup.find('span', class_='sh-ds__trunc-txt')
        if description_tag:
            product_description = description_tag.text.strip()

    return {
        "email": email,
        "product_id": product_id,
        "product_url": product_url,
        "image_url": image_url,
        "product_description": product_description,
        "title": title,
        "lowest_price": lowest_price,
        "lowest_price_seller": lowest_price_seller,
        "lowest_price_seller_url": lowest_price_seller_url
    }

# Function to fetch HTML content from a given URL
def google_search_mozilla(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return None

def insert_tracker_data(conn):
    cursor = conn.cursor()
    sql = "SELECT * FROM cart"
    cursor.execute(sql)
    cart_data = cursor.fetchall()

    for each_item in cart_data:
        product_url = each_item["product_url"]
        email = each_item["email"]
        product_id = each_item["product_id"]
        image_url = each_item["image_url"]

        # Fetch HTML content from the product URL
        html_content = google_search_mozilla(product_url)

        # Get lowest price data
        lowest_price_data = get_lowest_price(html_content, email, product_id, product_url, image_url)

        # Insert data into the tracker table
        insert_sql = """
            INSERT INTO tracker (email, product_id, product_url, image_url, product_description, title, price, seller, seller_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            lowest_price_data["email"],
            lowest_price_data["product_id"],
            lowest_price_data["product_url"],
            lowest_price_data["image_url"],
            lowest_price_data["product_description"],
            lowest_price_data["title"],
            lowest_price_data["lowest_price"],
            lowest_price_data["lowest_price_seller"],
            lowest_price_data["lowest_price_seller_url"]
        ))
        conn.commit()

# Define a function to run the insert_tracker_data function in a separate thread
def run_insert_tracker_data():
    conn = get_database_connection()
  
    while True:
        # Run the function to insert tracker data
        insert_tracker_data(conn)
        
        # Sleep for 15 minutes
        time.sleep(60*15)  # 15 minutes in seconds
print("start thread")
# Create and start a new thread to run the insert_tracker_data function
insert_tracker_thread = threading.Thread(target=run_insert_tracker_data)
insert_tracker_thread.start()
print("next step")