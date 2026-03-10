# rss-for-slack

Posts curated F1 articles and YouTube videos to a Slack channel. Runs automatically via GitHub Actions twice a week.

## Setup

### 1. Slack Incoming Webhook
1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Add feature: **Incoming Webhooks** → toggle on → **Add New Webhook to Workspace**
3. Select `#formula-1` → copy the webhook URL

### 2. YouTube API Key (optional)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → **Enable APIs** → search for **YouTube Data API v3** → enable
3. Go to **Credentials** → **Create API Key** → copy it

### 3. GitHub Secrets
In your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret name | Value |
|---|---|
| `SLACK_WEBHOOK_URL` | Your Slack webhook URL |
| `YOUTUBE_API_KEY` | Your YouTube API key (skip if not using YouTube) |

### 4. Configure sources & keywords
Edit `config.yaml`:
- **keywords**: allowlist — articles must match at least one to be posted
- **sources.rss**: list of RSS feed URLs
- **sources.youtube**: list of YouTube channel IDs

To find a YouTube channel ID: go to the channel page → view page source → search for `"channelId"`.

## Schedule
Runs every **Tuesday and Friday at 9am UTC**. You can also trigger it manually from the **Actions** tab in GitHub.

## How deduplication works
`seen.json` tracks all posted article IDs. The bot commits it back to the repo after each run so it persists across executions.
