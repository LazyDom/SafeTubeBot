import os
import googleapiclient.discovery
import googleapiclient.errors
import google_auth_oauthlib.flow
import google.auth.transport.requests
import requests
import re
from google.cloud import language_v1
import json
import pickle
import logging

# Load secrets from secrets file
with open('secrets.json') as secrets_file:
    secrets = json.load(secrets_file)
    YOUTUBE_CLIENT_SECRET_FILE = secrets["YOUTUBE_CLIENT_SECRET_FILE"]
    PERSPECTIVE_API_KEY = secrets["PERSPECTIVE_API_KEY"]
    GOOGLE_CLOUD_CREDENTIALS_FILE = secrets["GOOGLE_CLOUD_CREDENTIALS_FILE"]
    CHANNEL_ID = secrets["CHANNEL_ID"]

# Set the environment variable for Google Cloud credentials using the path from secrets.json
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_CREDENTIALS_FILE

# File to store processed comment IDs
PROCESSED_COMMENTS_FILE = "processed_comments.json"
# File to store OAuth 2.0 token
TOKEN_FILE = "token.pickle"

# Setup logging to output to both the terminal and a file
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("youtube_moderator.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

def load_processed_comments():
    logger.info("Loading processed comments")
    if os.path.exists(PROCESSED_COMMENTS_FILE):
        with open(PROCESSED_COMMENTS_FILE, "r") as file:
            return json.load(file)
    return {}

def save_processed_comments(processed_comments):
    logger.info("Saving processed comments")
    with open(PROCESSED_COMMENTS_FILE, "w") as file:
        json.dump(processed_comments, file)

def get_authenticated_service():
    logger.info("Getting authenticated YouTube service")
    # Load OAuth 2.0 credentials
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRET_FILE, scopes)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds, cache_discovery=False)
    return youtube

def get_all_video_ids(youtube, channel_id):
    logger.info(f"Fetching all video IDs for channel: {channel_id}")
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

def moderate_comments(youtube, video_id, processed_comments):
    logger.info(f"Moderating comments for video: {video_id}")
    # Fetch comments from the video
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        textFormat="plainText",
        maxResults=100  # Adjust maxResults as needed
    )
    response = request.execute()

    while response:
        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comment_id = item["snippet"]["topLevelComment"]["id"]

            # Check if the comment is new
            if comment_id not in processed_comments:
                logger.info(f"Processing comment ID: {comment_id}")
                # Implement moderation logic
                if contains_inappropriate_content(comment):
                    delete_comment(youtube, comment_id)
                # Mark the comment as processed after moderation check
                processed_comments[comment_id] = True

        if "nextPageToken" in response:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                maxResults=100,
                pageToken=response["nextPageToken"]
            )
            response = request.execute()
        else:
            break

def contains_inappropriate_content(comment):
    logger.info("Checking if comment contains inappropriate content")
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
    try:
        language = detect_language(comment)
        if language == 'en' and analyze_sentiment(comment) < sentiment_threshold:
            return True
    except google.api_core.exceptions.InvalidArgument:
        # Skip sentiment analysis for unsupported languages
        pass

    # Check Perspective API for toxicity
    if is_toxic(comment):
        return True

    return False

def detect_language(text):
    logger.info("Detecting language of the comment")
    # Call Google Cloud Natural Language API for language detection
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = client.analyze_sentiment(request={'document': document})
    return response.language

def analyze_sentiment(comment):
    logger.info("Analyzing sentiment of the comment")
    # Call Google Cloud Natural Language API for sentiment analysis
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=comment, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = client.analyze_sentiment(request={'document': document})
    sentiment_score = response.document_sentiment.score
    return sentiment_score

def is_toxic(comment):
    logger.info(f"Making Perspective API request for comment: {comment}")
    # Call Perspective API
    url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={PERSPECTIVE_API_KEY}"
    data = {
        "comment": {"text": comment},
        "requestedAttributes": {"TOXICITY": {}}
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        toxicity_score = response.json().get("attributeScores", {}).get("TOXICITY", {}).get("summaryScore", {}).get("value", 0.0)
        logger.info(f"Perspective API response: {response.json()}")
        return toxicity_score >= 0.8  # Example threshold for toxicity
    else:
        logger.error(f"Error in Perspective API request: {response.status_code}, {response.text}")
        return False

def delete_comment(youtube, comment_id):
    logger.info(f"Deleting comment ID: {comment_id}")
    # Delete the comment
    youtube.comments().setModerationStatus(
        id=comment_id,
        moderationStatus="rejected"
    ).execute()

if __name__ == "__main__":
    logger.info("Starting YouTube comment moderation script")
    youtube = get_authenticated_service()
    processed_comments = load_processed_comments()
    video_ids = get_all_video_ids(youtube, CHANNEL_ID)
    for video_id in video_ids:
        moderate_comments(youtube, video_id, processed_comments)
    save_processed_comments(processed_comments)
    logger.info("YouTube comment moderation script completed")