from fastapi import FastAPI, BackgroundTasks, HTTPException
import requests
import schedule
import time
import threading
from bs4 import BeautifulSoup
import urllib.parse
import re

# Dictionary to map URLs to their corresponding thread objects
url_threads = {}
global scheduler_running
scheduler_running = True  # Set scheduler_running to True to start the scheduler

def get_lowest_price(html_content,email,product_id):
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

    if data:
        # Find the seller with the lowest price
        lowest_price = float('inf')  # Set to positive infinity initially
        lowest_price_seller = None
        for item in data['price_comparison']:
            item_price = float(item['Item Price'])
            if item_price < lowest_price:
                lowest_price = item_price
                lowest_price_seller = item['Seller']
        print("Lowest Price Seller:", lowest_price_seller)
    else:
        print("No data found.")
    return {
        "product_id":product_id,
        "email":email,
        "img_url": img_url,
        "description": description,
        "title": title,
        "lowest_price": lowest_price,
        "lowest_price_seller":lowest_price_seller

    }

# Function to fetch price from a given URL
def google_search_mozilla(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return None

url="https://www.google.com/shopping/product/9729766800518872077?q=shirt&prds=eto:8451140432829201964_0,pid:10467222731450053961&sa=X&ved=0ahUKEwidj4f5g9-EAxXOK7kGHWmBDMkQ8gIIhQkoAA"

# Function to update prices for a given product URL
def update_price_for_url(url):
    while scheduler_running:  # Check the flag before running
        html_content = google_search_mozilla(url)
        if html_content:
            data = get_lowest_price(html_content)
            print(data)
        else:
            print(f"Failed to fetch HTML content from {url}")
        time.sleep(3)  # Wait for 3 seconds before fetching data again

# Define background task to update prices
def update_prices_background(url):
    thread = threading.Thread(target=update_price_for_url, args=(url,))
    url_threads[url] = thread
    thread.start()

# Schedule the background task to run every three seconds
schedule.every(15).minutes.do(update_prices_background, url)

# Run the scheduler in a separate thread
def run_scheduler():
    while scheduler_running:  # Check the flag before running
        schedule.run_pending()
        time.sleep(1)

# Start the scheduler thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()
