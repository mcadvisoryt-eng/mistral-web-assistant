# mistral-web-assistant

A scheduled GitHub Actions job that runs the **Open WebUI** chat interface on top of
several **free OpenAI-compatible providers** (Google Gemini by default, plus Groq,
OpenRouter and Cloudflare Workers AI if you add their keys), with **live web search**,
exposed through a **Cloudflare quick tunnel**, announced over **ntfy**, and reachable
through a **stable redirect link**.

- Runs automatically **every 5 hours** (`cron: 0 */5 * * *`, UTC), and can be started
  manually from the Actions tab with **Run workflow**.
- **Open WebUI** (Docker) is the front end: chat history, markdown, streaming, and
  built-in web search (Tavily).
- Models come from the providers you configure — no local model, no download, no CPU
  inference.
- **Cloudflare quick tunnel** exposes it. Unlike ngrok's free tier it has no browser
  interstitial, so the app loads directly. The URL is random per run.
- **ntfy** sends a start notification (URL + login) and a failure alert if a run breaks.
- A **"Current endpoint"** issue is kept up to date with the live URL.

## The stable link

Always open this — it redirects to whichever tunnel is live right now:

**https://mcadvisoryt-eng.github.io/mistral-web-assistant/**

The page reads the current URL fresh on every load (from `endpoint.txt` on the
`gh-pages` branch), so it never goes stale between runs.

## Read this first

A GitHub Actions job is **ephemeral**. It is not a permanent server:

- It lives for at most **6 hours**, then the VM — and the tunnel — are destroyed.
- Between runs the endpoint is dark; the next scheduled run brings a new URL, which the
  stable link picks up automatically.

## Security warning

The tunnel is **public**, and the admin login defaults to a **weak, known password**.
Anyone who learns the URL can log in as admin. Add a repo secret named `ADMIN_PASSWORD`
to override it (recommended). The ntfy topic is public on ntfy.sh — anyone who knows the
topic name can read the notification (which contains the password), so keep the topic
name secret. Treat this as a personal demo, not anything holding real data.

## Setup (one time)

Add these repository secrets (**Settings -> Secrets and variables -> Actions**):

| Secret | Required? | Where to get it |
| --- | --- | --- |
| `GEMINI_API_KEY` | Yes | https://aistudio.google.com/apikey (free, no card) |
| `TAVILY_API_KEY` | Yes | https://tavily.com (search key) |
| `GROQ_API_KEY` | Optional | https://console.groq.com/keys (free, no card) |
| `OPENROUTER_API_KEY` | Optional | https://openrouter.ai/keys (free models, no card) |
| `CLOUDFLARE_API_TOKEN` | Optional | Cloudflare dashboard -> My Profile -> API Tokens (Workers AI) |
| `CLOUDFLARE_ACCOUNT_ID` | Optional | Cloudflare dashboard -> Workers & Pages -> Account ID |
| `ADMIN_PASSWORD` | Optional | Any password you choose for the admin login |

Each optional provider is added only when its secret is present, so the workflow runs
fine before you add them. The connection list is printed in the *Start Open WebUI* step
log.

Subscribe to your ntfy topic in the ntfy app, or at https://ntfy.sh/<NTFY_TOPIC>.

## Using it

Open the stable link and log in with the admin account. A Gemini Flash model is
pre-selected and web search is enabled, so you can start chatting immediately. Pick any
other model from the model dropdown — every configured provider's models appear there.

## Local (uncensored) model

The job also installs **Ollama** and pulls one local model, so you get a genuinely
self-hosted option with no provider in the loop. Default:
`huihui_ai/deephermes3-abliterated:8b` — DeepHermes 3, abliterated (refusals removed).

Change it per run with **Run workflow -> `ollama_model`**. Good alternatives:

- `huihui_ai/Hermes-3-Llama-3.2-abliterated:3b` — 2GB, **much faster on CPU**
- `huihui_ai/qwen3-abliterated:8b`
- `dolphin3:8b` / `dolphin-mistral`

Set the input to blank to skip the local model entirely. Open WebUI runs with host
networking so it can reach Ollama on `127.0.0.1:11434`.

**Honest limits:** the runner has no GPU, so this is CPU inference — a few tokens per
second, and long answers can time out through the tunnel. It is also far weaker than the
hosted models. It's a no-refusals option, not a Claude replacement. The job pre-warms
the model so the first message isn't the slowest.

Uncensored models are stripped of alignment and are meant to be used responsibly — the
model cards themselves say they "require an external alignment layer for ethical use".
What you do with the output is on you.

## Configuration

Everything is set as environment variables in `.github/workflows/mistral.yml`:

- `DEFAULT_MODEL` — the model pre-selected in the UI. Also settable per-run via the
  **Run workflow** input (use the full id, e.g. `models/gemini-3.6-flash`).
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` — the admin account created on startup.
- `NTFY_TOPIC` — the ntfy channel for notifications.
- `WEB_SEARCH_ENGINE` — `tavily` by default; other engines are supported by Open WebUI.

## Notes and limits

- **Free only while the repo is public.** Private repos bill Actions minutes, and a
  ~6-hour job every 5 hours is far past the 2,000 free minutes/month.
- **Gemini free-tier limits are per model and can be very small** (e.g. some models allow
  only ~20 requests/day). A `429 ... quota exceeded` in chat is Google's limit, not a bug —
  switch to another model, or add one of the free providers above.
- **Web search** is enabled globally *and* on the default model (capability + default
  feature + native function calling), so the model can call `search_web` on its own.
- Scheduled workflows run from the **default branch** and are auto-disabled after
  **60 days of repository inactivity**; push any commit to re-enable.

## Troubleshooting

- **"No models available" in the UI** — the `GEMINI_API_KEY` is missing/invalid. The
  workflow's *Verify Gemini API key* step fails loudly on this; check the run log.
- **A provider's models don't appear** — its secret is missing, or the *Start Open WebUI*
  log shows the connection list without it.
- **`429` / "high demand"** — provider-side rate limiting. Switch models, or add another
  provider.
- **No ntfy notification** — confirm the topic name matches, and that the runner could
  reach ntfy.sh (the step logs a line either way).
