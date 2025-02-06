from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging

logging.basicConfig(filename="scrapper.log", level=logging.INFO)
import pymongo

app = Flask(__name__)
CORS(app)  # Enabling CORS for API requests

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = f"https://www.flipkart.com/search?q={searchString}"
            
            # Fetch Flipkart Search Page
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "cPHDOP col-12-12"})
            
            if not bigboxes or len(bigboxes) < 4:
                return "No results found. Please try a different query."

            box = bigboxes[3]  # Selecting the first product after ads
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            
            # Fetch Product Page
            prodRes = requests.get(productLink)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")

            commentboxes = prod_html.find_all('div', {'class': "RcXBOT"})

            reviews = []
            for commentbox in commentboxes:
                try:
                    name = commentbox.find('p', {'class': '_2NsDsF AwS1CA'}).get_text(strip=True)
                except AttributeError:
                    name = "Anonymous"

                try:
                    rating = commentbox.find('div', {'class': 'XQDdHH Ga3i8K'}).get_text(strip=True)
                except AttributeError:
                    rating = "No Rating"

                try:
                    commentHead = commentbox.find('p', {'class': 'z9E0IG'}).get_text(strip=True)
                except AttributeError:
                    commentHead = "No Comment Heading"

                try:
                    custComment = commentbox.find('div', {'class': 'ZmyHeo'}).get_text(strip=True)
                except AttributeError:
                    custComment = "No Comment"

                mydict = {
                    "Product": searchString,
                    "Name": name,
                    "Rating": rating,
                    "CommentHead": commentHead,
                    "Comment": custComment
                }
                reviews.append(mydict)

            logging.info(f"Scraped {len(reviews)} reviews for {searchString}")
            client = pymongo.MongoClient("mongodb+srv://payalsahoo931:payal123@cluster0.bh0o2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            db = client['Review_Scrap']
            review_col = db['Review_Scrap_data']
            review_col.insert_many(reviews)
            
            return render_template('result.html', reviews=reviews)

        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return 'Something went wrong. Please try again later.'
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
