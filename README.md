# mistral-web-assistant

A scheduled GitHub Actions job that runs the **Open WebUI** chat interface on top of
**Google Gemini** (via its OpenAI-compatible endpoint), with **live web search**, exposed
through an **ngrok** tunnel and announced over **ntfy**.

- Runs automatically **every 5 hours** (`cron: 0 */5 * * *`, UTC), and can be started
  manually from the Actions tab with **Run workflow**.
- **Open WebUI** (Docker) is the front end: chat history, markdown, streaming, and
  built-in web search (Tavily). It auto-creates an admin account on first start.
- **Gemini** is the model backend (free tier). No local model, no download, no CPU
  inference — the model list comes straight from Google.
- **ngrok** exposes it on your account's free static dev domain, so the URL is stable.
- **ntfy** sends a start notification with the URL and the login.

## Read this first

A GitHub Actions job is **ephemeral**. It is not a permanent server:

- It lives for at most **6 hours**, then the VM — and the tunnel — are destroyed.
- The ngrok URL is **stable** (your dev domain); it just stops responding between runs.

## Security warning

The tunnel is **public**, and the admin login is a **weak, known password**. Anyone who
learns the URL can log in as admin. The ntfy topic is also public on ntfy.sh — anyone who
knows the topic name can read the notification (which contains the password). Keep the
topic name secret, and treat this as a personal demo.

## Setup (one time)

Add these repository secrets (**Settings -> Secrets and variables -> Actions**):

1. `GEMINI_API_KEY` — from https://aistudio.google.com/apikey (free, no card needed).
2. `TAVILY_API_KEY` — your search key. (Set `SEARCH_PROVIDER`/`WEB_SEARCH_ENGINE` to
   match if you use a different engine.)
3. `NGROK_AUTHTOKEN` — from https://dashboard.ngrok.com/get-started/your-authtoken.

Subscribe to your ntfy topic in the ntfy app or at https://ntfy.sh/<NTFY_TOPIC>.

## Using it

Open the URL from the latest run's Summary (or the ntfy notification) and log in with the
admin account shown there. Pick a Gemini model (e.g. a Flash model) and toggle web search
in a chat.

## Notes and limits

- **Free only while the repo is public.** Private repos bill Actions minutes, and a
  ~6-hour job every 5 hours is far past the 2,000 free minutes/month.
- Gemini's free tier has no credit card and no expiry, but Google may use free-tier
  prompts to improve its models, and the exact rate limits are shown per project in AI
  Studio. Gemini is also safety-filtered.
- Gemini's OpenAI-compatible layer breaks native tool-calling; if a turn returns blank,
  set the model's Function Calling to **Legacy** in Advanced Params.
- Scheduled workflows run from the **default branch** and are auto-disabled after
  **60 days of repository inactivity**; push any commit to re-enable.
