# mistral-web-assistant

A scheduled GitHub Actions job that serves an **uncensored Mistral 7B** (GGUF, Q4_K_M)
behind the **Open WebUI** chat interface, with **live web search**, exposed through an
**ngrok** tunnel and announced over **ntfy**.

- Runs automatically **every 5 hours** (`cron: 0 */5 * * *`, UTC), and can be started
  manually from the Actions tab with **Run workflow**.
- Downloads `bartowski/dolphin-2.9.3-mistral-7B-32k-GGUF` (`...Q4_K_M.gguf`, ~4.4 GB) —
  an uncensored Dolphin fine-tune of Mistral 7B — and serves it on CPU via `llama.cpp`.
- **Open WebUI** (Docker) is the front end: chat history, markdown, streaming, and
  built-in web search (Tavily). It auto-creates an admin account on first start.
- **ngrok** exposes it on your account's free static dev domain, so the URL is stable.
- **ntfy** sends a start notification with the URL and the login.

## Read this first

A GitHub Actions job is **ephemeral**. It is not a permanent server:

- It lives for at most **6 hours**, then the VM — and the tunnel — are destroyed.
- The ngrok URL is **stable** (your dev domain); it just stops responding between runs.

## Security warning

The tunnel is **public**, and the admin login is a **weak, known password**. Anyone who
learns the URL can log in as admin. Treat this as a personal demo, not anything holding
real data. The ntfy topic is also public on ntfy.sh — anyone who knows the topic name can
read the notification (which contains the password), so keep the topic name secret.

## Setup (one time)

Add these repository secrets (**Settings -> Secrets and variables -> Actions**):

1. `TAVILY_API_KEY` — your search key. (Set `SEARCH_PROVIDER` in the workflow to match:
   `tavily`, `brave`, or `serper`.)
2. `NGROK_AUTHTOKEN` — from https://dashboard.ngrok.com/get-started/your-authtoken.
   If ngrok fails with `ERR_NGROK_15013`, claim your free dev domain at
   https://dashboard.ngrok.com/domains.

Subscribe to your ntfy topic in the ntfy app or at https://ntfy.sh/<NTFY_TOPIC>
(set by `NTFY_TOPIC` in the workflow).

## Using it

Open the URL from the latest run's Summary (or from the ntfy notification) and log in
with the admin account shown there. Turn on the web-search toggle in a chat to let the
model search the web.

## Notes and limits

- **Free only while the repo is public.** Private repos bill Actions minutes, and a
  ~6-hour job every 5 hours is far past the 2,000 free minutes/month.
- The runner is 4 vCPU / 16 GB RAM; Mistral 7B at Q4_K_M (~4.4 GB) fits comfortably.
  Expect a few tokens per second on CPU — Open WebUI and the model share the same cores.
- Scheduled workflows run from the **default branch** and are auto-disabled after
  **60 days of repository inactivity**; push any commit to re-enable.
- Uncensored fine-tunes also give up some instruction-following and reasoning quality
  along with the refusals. That is the trade.

## Swapping the model

Edit `MODEL_REPO` / `MODEL_FILE` in `.github/workflows/mistral.yml`. Any
llama.cpp-compatible GGUF works; a 7B at Q4_K_M is the sweet spot for this runner.
