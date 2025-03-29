# SafeTubeBot

A bot to moderate comments on my YouTube channel using advanced moderation techniques.

## Getting Started

### Prerequisites

- Python 3.x
- `google-auth-oauthlib` library
- `google-api-python-client` library
- `requests` library

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/LazyDom/SafeTubeBot.git
   cd SafeTubeBot
   ```

2. Install the required libraries:
   ```sh
   pip install google-auth-oauthlib google-api-python-client requests
   ```

3. Set up your API keys:
   - Replace `YOUR_PERSPECTIVE_API_KEY` with your actual Perspective API key.
   - Replace `YOUR_CHANNEL_ID` with your actual YouTube channel ID.

### Usage

Run the script to moderate comments on your YouTube channel:
```sh
python youtube_moderator.py
```

### License

This project is licensed under the MIT License.