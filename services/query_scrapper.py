from bs4 import BeautifulSoup
import urllib.parse
import requests
import re
import pymysql
import random
import string


import pymysql
from bs4 import BeautifulSoup
import urllib.parse
import requests
import time

def get_database_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='admin123',
        database='ecommerce',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_lowest_price_tracker(html_content, email, product_id, product_url, image_url):
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
def google_search_mozilla_tracker(url):
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
    if len(cart_data)>0:
        for each_item in cart_data:
            product_url = each_item["google_product_url"]
            email = each_item["email"]
            product_id = each_item["product_id"]
            image_url = each_item["image_url"]

            # Fetch HTML content from the product URL
            html_content = google_search_mozilla_tracker(product_url)
            # print(html_content,".is it getinng data")

            # Get lowest price data
            lowest_price_data = get_lowest_price_tracker(html_content, email, product_id, product_url, image_url)

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
    
  
    while True:
        # Run the function to insert tracker data
        conn = get_database_connection()
        insert_tracker_data(conn)
        
        # Sleep for 15 minutes
        time.sleep(5)  # 15 minutes in seconds






def google_search(query):
    try:
        formatted_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={formatted_query}&tbm=shop"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for 4XX or 5XX status codes
        return response.text
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def generate_product_id():
    # Generate a random string of characters
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # Combine the username and random string
    product_id = random_string
    return product_id

def html_parser(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    sh_dgr_contents = soup.find_all(class_="sh-dgr__content")
    
    for sh_dgr_content in sh_dgr_contents:
        product_title = sh_dgr_content.find(class_="tAxDx").get_text()
        original_price = sh_dgr_content.find(class_="a8Pemb OFFNJ").get_text()
        
        
        additional_info_element = sh_dgr_content.find(class_="vEjMR")
        additional_info = additional_info_element.get_text() if additional_info_element else None
        
        url_anchor = sh_dgr_content.find('a', class_='xCpuod')
        product_url = "https://www.google.com" + url_anchor['href'] if url_anchor else None
        
        img_tag = sh_dgr_content.find('img')
        img_id = img_tag.get('id') if img_tag else None
        if img_id:
            script_tag = soup.find('script', string=re.compile(f"var _i\s*=\s*'({img_id})'"))
            if script_tag:
                u_pattern = r"var _u\s*=\s*'([^']*)';"
                match = re.search(u_pattern, script_tag.string)
                if match:
                    img_url = urllib.parse.unquote(match.group(1).replace("\\x3d", "=").replace("\\x26", "&"))
                else:
                    img_url = None
            else:
                img_url = None
        else:
            img_url = None
        id=generate_product_id()
        
        result = {
            "id":id,
            "product_title": product_title,
            "original_price": original_price,
            "additional_info": additional_info,
            "product_url": product_url,
            "img_url": img_url
        }
        
        results.append(result)
    results_sorted = sorted(results, key=lambda x: float(x['original_price'].replace('₹', '').replace(',', '').replace('+ tax', '').strip()))
    return results_sorted

def extract_reviews_from_url(url):
    # Fetch HTML content
    html_content = google_search_morzilla(url)
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    reviews = []

    if soup.find(class_='bqCdTe'):
        # Get the link to all reviews
        all_reviews_link = soup.find('a', class_='internal-link')['href']
        product_url = "https://www.google.com" + all_reviews_link if all_reviews_link else None

        if product_url:
            html_content = google_search_morzilla(product_url)
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract each review
            review_divs = soup.find_all("div", class_="z6XoBf fade-in-animate")
            for review_div in review_divs:
                review = {}
                date_element = review_div.find("span", class_="less-spaced ff3bE nMkOOb")
                if date_element:
                    review["date"] = date_element.text.strip()
                else:
                    review["date"] = "Date not available"

                rating_element = review_div.find("div", class_="UzThIf")
                if rating_element:
                    review["rating"] = rating_element["aria-label"].split()[0]
                else:
                    review["rating"] = "Rating not available"

                content_element = review_div.find("div", class_="g1lvWe")
                if content_element:
                    content_text = content_element.text.strip().replace("TranslateShow in original", "")
                    review["content"] = content_text
                else:
                    review["content"] = "Content not available"

                # Extract the shop name
                shop_name = review_div.find("div", class_="sPPcBf").text.strip()
                dot_index = shop_name.find(" Review provided by")
                if dot_index != -1:
                    shop_name=shop_name[dot_index + 1:]
                
                review["shop_name"] = shop_name

                reviews.append(review)

            return reviews
        else:
            print("Product URL not found")
            return None
    else:
        print("Class 'bqCdTe' not found")
        return None




def google_search_morzilla(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return None

def comparer(html_content,url):
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
    unique_data = {}
    cnt=0
    for item in data:
        seller = item["Seller"]
        if seller not in unique_data:
            unique_data[cnt] = item
            print(unique_data)
            cnt+=1

    else:
        print("Buying options div not found in the HTML content.")
    return {
        "img_url": img_url,
        "description": description,
        "title": title,
        "price_comparison": unique_data,
        "product_url":url
    }