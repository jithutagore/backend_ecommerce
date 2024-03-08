from fastapi import FastAPI, BackgroundTasks, HTTPException
import requests
import mysql.connector
import schedule
import time
import threading
from bs4 import BeautifulSoup
import urllib.parse
import requests
import re

app = FastAPI()

# Dictionary to map URLs to their corresponding thread objects
url_threads = {}


def comparer(html_content):
    data = []
    soup = BeautifulSoup(html_content, "html.parser")
    buying_options_div = soup.find("div", class_="sh-pov__grid")
    img_url=""
    for img_tag in soup.find_all("img"):
        src = img_tag.get('src')
        if src and src.startswith("https://encrypted"):
            img_url=src
            break 
    description = [li.span.text.strip() for li in soup.find_all('li', class_='KgL16d')]
    if len(description)==0:
        description = [soup.find('span', class_='sh-ds__trunc-txt').text.strip()]
    title = soup.find('span', class_='BvQan').text.strip()

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
    return {
        "img_url": img_url,
        "description": description,
        "title": title,
        "price_comparison": data
    }

# Function to fetch price from a given URL
def fetch_price(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch price. Invalid URL or server error.")
    # Extract price from response content
    price = comparer(response.text)
    
    return price

# Function to insert price into MySQL database
def insert_price(product_id, price):
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin123",
        database="ecommerce"
    )
    cursor = connection.cursor()
    insert_query = "INSERT INTO price_data (mail_id,urlproduct_id, timestamp, price) VALUES (%s, %s, %s)"
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(insert_query, (product_id, current_time, price))
    connection.commit()
    connection.close()

# Function to update prices for a given product URL
def update_price_for_url(url):
    while scheduler_running:  # Check the flag before running
        price = fetch_price(url)
        insert_price(1, price)  # Assuming product_id is 1 for simplicity
        time.sleep(1)  # Add a small delay to avoid consuming too much CPU

# Define background task to update prices
def update_prices_background(url):
    thread = threading.Thread(target=update_price_for_url, args=(url,))
    url_threads[url] = thread
    thread.start()

# Schedule the background task to run every fifteen minutes
schedule.every(15).minutes.do(update_prices_background)

# Run the scheduler in a separate thread
def run_scheduler():
    while scheduler_running:  # Check the flag before running
        schedule.run_pending()
        time.sleep(1)

# Start the scheduler thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# Define endpoint to trigger immediate price update for a given URL
@app.get("/update_prices/")
async def trigger_update_prices(url: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(update_prices_background, url)
    return {"message": f"Price update triggered for URL: {url}"}

# Endpoint to stop the thread associated with a particular URL
@app.get("/stop_thread/")
async def stop_thread(url: str):
    if url in url_threads:
        url_threads[url].join()  # Wait for the thread to finish
        del url_threads[url]  # Remove the thread from the dictionary
        return {"message": f"Thread associated with URL {url} stopped."}
    else:
        raise HTTPException(status_code=404, detail="Thread not found for the given URL.")

# Endpoint to stop the scheduler thread
@app.get("/stop_scheduler")
async def stop_scheduler():
    global scheduler_running
    scheduler_running = False
    return {"message": "Scheduler stopped."}
