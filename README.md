# SafeTubeBot

A bot to moderate comments on my YouTube channel using advanced moderation techniques.

## Getting Started

### Prerequisites

- Python 3.x
- `google-auth-oauthlib` library
- `google-api-python-client` library
- `requests` library
- `google-cloud-language` library

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/LazyDom/SafeTubeBot.git
   cd SafeTubeBot
   ```

2. Install the required libraries:
   ```sh
   pip install google-auth-oauthlib google-api-python-client requests google-cloud-language
   ```

3. Set up your `secrets.json` file with the following structure:
   ```json
   {
     "YOUTUBE_CLIENT_SECRET_FILE": "path/to/your/client_secret.json",
     "PERSPECTIVE_API_KEY": "YOUR_PERSPECTIVE_API_KEY",
     "GOOGLE_CLOUD_CREDENTIALS_FILE": "path/to/your/google-cloud-credentials.json",
     "CHANNEL_ID": "YOUR_CHANNEL_ID"
   }
   ```
   - Replace `path/to/your/client_secret.json` with the path to your YouTube client secret file.
   - Replace `YOUR_PERSPECTIVE_API_KEY` with your actual Perspective API key.
   - Replace `path/to/your/google-cloud-credentials.json` with the path to your Google Cloud credentials file.
   - Replace `YOUR_CHANNEL_ID` with your actual YouTube channel ID.

4. Enable the necessary APIs:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **Google Cloud Natural Language API**.
   - Enable the **Perspective API** through the [Perspective API Console](https://console.cloud.google.com/apis/library/commentanalyzer.googleapis.com).

### $${\textbf{\color{red}WARNING}}$$
If you don't know how to manage OAuth 2.0 and API keys, please don't proceed. Improper handling of these credentials can lead to security risks and unauthorized access.

### Usage

Run the script to moderate comments on your YouTube channel:
```sh
python youtube_moderator.py
```

### License

This project is licensed under the MIT License.