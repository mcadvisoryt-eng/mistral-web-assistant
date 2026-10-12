# mistral-web-assistant

A scheduled GitHub Actions job that runs the **Open WebUI** chat interface on top of
**Google Gemini** (via its OpenAI-compatible endpoint), with **live web search**, exposed
through an **ngrok** tunnel, announced over **ntfy**, and tracked in a GitHub issue.

- Runs automatically **every 5 hours** (`cron: 0 */5 * * *`, UTC), and can be started
  manually from the Actions tab with **Run workflow**.
- **Open WebUI** (Docker) is the front end: chat history, markdown, streaming, and
  built-in web search (Tavily). It auto-creates an admin account on first start.
- **Gemini** is the model backend (free tier). No local model, no download, no CPU
  inference — the model list comes straight from Google.
- **ngrok** exposes it on your account's free static dev domain, so the URL is stable.
- **ntfy** sends a start notification (URL + login) and a failure alert if a run breaks.
- A **"Current endpoint"** issue is kept up to date with the live URL.

## Where to find the URL

**Stable link (bookmark this):** https://mcadvisoryt-eng.github.io/mistral-web-assistant/
- it always redirects to whichever endpoint is live at the time.

The live endpoint itself also appears in:

1. The **"Current endpoint"** issue in this repo (auto-updated each run).
2. The run's **Summary** page.
3. The **ntfy** notification on your phone.

## Read this first

A GitHub Actions job is **ephemeral**. It is not a permanent server:

- It lives for at most **6 hours**, then the VM — and the tunnel — are destroyed.
- The ngrok URL is **stable** (your dev domain); it just stops responding between runs.

## Security warning

The tunnel is **public**, and the admin login is a **weak, known password**. Anyone who
learns the URL can log in as admin. The ntfy topic is also public on ntfy.sh — anyone who
knows the topic name can read the notification (which contains the password). Keep the
topic name secret, and treat this as a personal demo, not anything holding real data.

## Setup (one time)

Add these repository secrets (**Settings -> Secrets and variables -> Actions**):

| Secret | Where to get it |
| --- | --- |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey (free, no card) |
| `TAVILY_API_KEY` | https://tavily.com (search key) |
| `NGROK_AUTHTOKEN` | https://dashboard.ngrok.com/get-started/your-authtoken |

Subscribe to your ntfy topic in the ntfy app, or at https://ntfy.sh/<NTFY_TOPIC>.

If ngrok fails with `ERR_NGROK_15013`, claim your free dev domain at
https://dashboard.ngrok.com/domains and update `PUBLIC_URL` in the workflow.

## Using it

Open the URL and log in with the admin account from the endpoint issue. The model is
pre-selected (a Gemini Flash model) and web search is enabled, so you can start chatting
immediately.

## Configuration

Everything is set as environment variables in `.github/workflows/mistral.yml`:

- `DEFAULT_MODEL` — the Gemini model pre-selected in the UI. Also settable per-run via the
  **Run workflow** input.
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` — the admin account created on startup.
  The password defaults to `joshi`, but you can override it by adding a repo secret named
  `ADMIN_PASSWORD` (recommended, since this repo is public).
- `NTFY_TOPIC` — the ntfy channel for notifications.
- `WEB_SEARCH_ENGINE` — `tavily` by default; other engines are supported by Open WebUI.

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

## Troubleshooting

- **"No models available" in the UI** — the `GEMINI_API_KEY` is missing/invalid. The
  workflow's *Verify Gemini API key* step fails loudly on this; check the run log.
- **No ntfy notification** — confirm the topic name matches, and that the runner could
  reach ntfy.sh (the step logs a line either way).
- **Blank replies** — set Function Calling to Legacy for the model (Gemini quirk above).
