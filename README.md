# mistral-web-assistant

A scheduled GitHub Actions job that serves an **uncensored Mistral 7B** (GGUF, Q4_K_M)
with **live web search**, behind a temporary `cloudflared` tunnel.

- Runs automatically **every 5 hours** (`cron: 0 */5 * * *`, UTC), and can be started
  manually from the Actions tab with **Run workflow**.
- Downloads `bartowski/dolphin-2.9.3-mistral-7B-32k-GGUF` (`...Q4_K_M.gguf`, ~4.4 GB) —
  an uncensored Dolphin fine-tune of Mistral 7B — and serves it on CPU via `llama.cpp`.
- `serve.py` wraps it: your question goes to a search API, the top results are folded
  into the prompt, and the model answers from them with citations.
- A `cloudflared` quick tunnel exposes the chat UI. **The public URL is printed to the
  run's Summary page** (and to the logs).

## Read this first

A GitHub Actions job is **ephemeral**. It is not a permanent server:

- It lives for at most **6 hours**, then the VM — and the tunnel — are destroyed.
- The `trycloudflare.com` URL is **different on every run**.
- Get the current URL from the **latest run's Summary** in the Actions tab.

If you want a permanent endpoint, this is the wrong tool; use a small VPS.

## Setup (one time)

1. Add your search API key as a repository secret:
   **Settings -> Secrets and variables -> Actions -> New repository secret**
   - Name: `TAVILY_API_KEY` (or `BRAVE_API_KEY` / `SERPER_API_KEY`)
   - Value: your key
   Then set `SEARCH_PROVIDER` in `.github/workflows/mistral.yml` to match
   (`tavily`, `brave`, or `serper`).
2. (Optional) Trigger a run now: **Actions -> mistral-web-assistant -> Run workflow**.

## Using it

Open the URL from the latest run's Summary. Type a question; the app searches the web,
feeds the results to the local model, and answers with sources.

## Notes and limits

- **Free only while the repo is public.** Private repos bill Actions minutes, and a
  ~6-hour job every 5 hours is far past the 2,000 free minutes/month.
- The runner is 4 vCPU / 16 GB RAM; Mistral 7B at Q4_K_M (~4.4 GB) fits comfortably.
  Expect a few tokens per second on CPU — this is not fast.
- Scheduled workflows run from the **default branch** and are auto-disabled after
  **60 days of repository inactivity**; push any commit to re-enable.
- GitHub can delay scheduled runs at peak times; "every 5 hours" is best-effort.
- Uncensored fine-tunes also give up some instruction-following and reasoning quality
  along with the refusals. That is the trade.

## Swapping the model

Edit `MODEL_REPO` / `MODEL_FILE` in `.github/workflows/mistral.yml`. Any
llama.cpp-compatible GGUF works; a 7B at Q4_K_M is the sweet spot for this runner.
