from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup as bs
import re
import json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get search query from the form
        search_query = request.form.get('search_query')
        # Construct the search URL
        url = f"https://www.youtube.com/results?search_query={search_query}"

        # Define headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Send the request and get the response
        response = requests.get(url, headers=headers)

        # Parse the response using BeautifulSoup
        soup = bs(response.content, "html.parser")

        # Extract script tag containing the JSON data
        pattern = r'<script nonce="[-\w]+">\n\s+var ytInitialData = (.+)'
        script_data = re.search(pattern=pattern, string=soup.prettify())

        # Check if script_data is found
        if script_data:
            # Extract JSON data from the script tag
            script_data = script_data.group(1).replace(';', '')
            json_data = json.loads(script_data)
            
            # Extract videos container from JSON data
            videos_container = json_data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
            
            # List to store scraped video data
            scraped_videos = []

            # Process each video in the container
            for video in videos_container:
                # Check if the item is a video
                if 'videoRenderer' in video:
                    video_data = video['videoRenderer']
                    
                    # Extract video information
                    video_title = video_data['title']['runs'][0]['text']
                    video_url = f"https://www.youtube.com/watch?v={video_data['videoId']}"
                    thumbnails = video_data['thumbnail']['thumbnails'][0]['url']
                    no_of_views = video_data.get('viewCountText', {}).get('simpleText', 'Views not available')
                    date_posted = video_data.get('publishedTimeText', {}).get('simpleText', 'Date not available')
                    
                    # Append video data to the list
                    scraped_videos.append({
                        'title': video_title,
                        'url': video_url,
                        'thumbnails': thumbnails,
                        'views': no_of_views,
                        'date_posted': date_posted
                    })

            # Connect to MongoDB
            client = MongoClient("mongodb+srv://mohitrathod723:mohit99@cluster0.9xj2jcf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            db = client['youtube_scraper']
            collection = db['scrap_data']
            # Store scraped data in MongoDB
            collection.insert_many(scraped_videos)

        return render_template('index.html', videos=scraped_videos)
    else:
        return render_template('index.html', videos=[])

if __name__ == '__main__':
    app.run(debug=True)
