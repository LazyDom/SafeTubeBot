import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import re

# Set up YouTube API credentials and scopes
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

PERSPECTIVE_API_KEY = "YOUR_PERSPECTIVE_API_KEY"  # Replace with your Perspective API key
SENTIMENT_API_URL = "https://api.yoursentimentanalysis.com/analyze"  # Replace with your sentiment analysis API URL

def get_authenticated_service():
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret.json"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    return youtube

def get_all_video_ids(youtube, channel_id):
    video_ids = []
    request = youtube.search().list(
        part="id",
        channelId=channel_id,
        maxResults=50,
        order="date"
    )
    response = request.execute()
    while response:
        for item in response.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                video_ids.append(item["id"]["videoId"])
        if "nextPageToken" in response:
            request = youtube.search().list(
                part="id",
                channelId=channel_id,
                maxResults=50,
                order="date",
                pageToken=response["nextPageToken"]
            )
            response = request.execute()
        else:
            break
    return video_ids

def moderate_comments(youtube, video_id):
    # Fetch comments from the video
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        textFormat="plainText"
    )
    response = request.execute()

    for item in response.get("items", []):
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comment_id = item["snippet"]["topLevelComment"]["id"]

        # Implement moderation logic
        if contains_inappropriate_content(comment):
            delete_comment(youtube, comment_id)

def contains_inappropriate_content(comment):
    # Define inappropriate content criteria
    inappropriate_words = ["spam", "hate", "inappropriate"]
    pattern = re.compile(r"(http|www|\.com|\.net|\.org)")
    sentiment_threshold = -0.5  # Example threshold for sentiment analysis

    # Check for inappropriate words
    for word in inappropriate_words:
        if word in comment.lower():
            return True

    # Check for spam patterns
    if pattern.search(comment):
        return True

    # Check sentiment analysis
    if analyze_sentiment(comment) < sentiment_threshold:
        return True

    # Check Perspective API for toxicity
    if is_toxic(comment):
        return True

    return False

def analyze_sentiment(comment):
    # Call sentiment analysis API
    response = requests.post(SENTIMENT_API_URL, json={"text": comment})
    if response.status_code == 200:
        sentiment_score = response.json().get("sentiment_score", 0.0)
        return sentiment_score
    return 0.0

def is_toxic(comment):
    # Call Perspective API
    url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={PERSPECTIVE_API_KEY}"
    data = {
        "comment": {"text": comment},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        scores = response.json().get("attributeScores", {}).get("TOXICITY", {}).get("summaryScore", {})
        if scores.get("value", 0.0) >= 0.7:  # Example threshold for toxicity
            return True
    return False

def delete_comment(youtube, comment_id):
    request = youtube.comments().delete(id=comment_id)
    request.execute()

if __name__ == "__main__":
    youtube = get_authenticated_service()
    channel_id = "YOUR_CHANNEL_ID"  # Replace with your YouTube channel ID
    video_ids = get_all_video_ids(youtube, channel_id)
    for video_id in video_ids:
        moderate_comments(youtube, video_id)