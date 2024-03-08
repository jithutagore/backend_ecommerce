import json
from bs4 import BeautifulSoup
import re
import urllib.parse
import requests

def google_search(url, file_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(response.text)
        return response.text
    else:
        return False

def comparer(html_content):
    data = []
    soup = BeautifulSoup(html_content, "html.parser")
    buying_options_div = soup.find("div", class_="sh-pov__grid")
    # Find all img tags within the div
    img_tags = soup.find_all("img")
    whole_data={}
    img_url=""
    for img_tag in img_tags:
        # Get the src attribute value of the img tag
        src = img_tag.get('src')
        # Check if src starts with "https://encrypted"
        if src and src.startswith("https://encrypted"):
            img_url=src
            # print(src)
            break 
    whole_data["img_url"]=img_url
    # Extracting the description
    description = []
    for li in soup.find_all('li', class_='KgL16d'):
        description.append(li.span.text.strip())
    whole_data["description"]=description
    
    # Extracting the title
    title = soup.find('span', class_='BvQan').text.strip()
    whole_data["title"]=title

    # Extract the src attribute value for each img tag
    # image_urls = [img["src"] for img in img_tags]
    # print(image_urls)
    
    if buying_options_div:
        buying_options_rows = buying_options_div.find_all("tr", class_="sh-osd__offer-row")
        for row in buying_options_rows:
            seller_name = row.find("td", class_="SH30Lb").text.strip().replace('Opens in a new window', '') 
            item_price = row.find("span", class_="g9WBQb").text.strip().replace('\u20b9', '')  # Remove currency symbol
         
            anchor_tags = row.find_all("a", href=True)
            for anchor_tag in anchor_tags:
                href = anchor_tag["href"]
                href1 = urllib.parse.unquote(href.replace("/url?q=", "").replace("\\x3d", "=").replace("\\x26", "&"))
                
            data.append({
                "Seller": seller_name,
                "Item Price": item_price,
           
                "Href": href1
            })
    else:
        print("Buying options div not found in the HTML content.")
    whole_data["price_comparision"]=data
    return whole_data

result = google_search("https://www.google.com/shopping/product/1243462884014177314?q=i+phone+12&prds=eto:4374576081361121147_0,pid:18072550868136806665,rsk:PC_14074616196041694734&sa=X&ved=0ahUKEwjv_ePs4beEAxWBTWwGHetHCQUQ8gII9AsoAA", "shopping.html")
if result:
    output = comparer(result)
    with open("output.json", "w") as json_file:
        json.dump(output, json_file, indent=4)
