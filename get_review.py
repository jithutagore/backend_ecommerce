from bs4 import BeautifulSoup
from services.query_scrapper import google_search_morzilla

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

# Example usage:
url = "https://www.google.com/shopping/product/13991748537158060772?q=phones&prds=eto:12264521196707514861_0,pid:14169174980791836783,rsk:PC_7227856489616844083&sa=X&ved=0ahUKEwj1iJCH5-KEAxUCbmwGHVBkDC0Q8gII9w0oAA"
reviews = extract_reviews_from_url(url)
# if reviews:
#     for review in reviews:
#         print(review)
