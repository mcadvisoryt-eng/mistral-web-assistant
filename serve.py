#!/usr/bin/env python3
"""
Web-search-enabled chat wrapper around a local llama.cpp (llama-server) instance.

  user message -> web search (Tavily | Brave | Serper) -> results folded into the
  prompt -> the local Mistral answers from them -> answer + sources returned.

Env:
  LLAMA_URL        base URL of llama-server          (default http://127.0.0.1:8080)
  SEARCH_PROVIDER  tavily | brave | serper           (default tavily)
  TAVILY_API_KEY / BRAVE_API_KEY / SERPER_API_KEY    (whichever provider you pick)
  TOP_K            number of search results to fetch (default 5)
  APP_PORT         port to listen on                 (default 8000)
"""
import os

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

LLAMA_URL = os.environ.get("LLAMA_URL", "http://127.0.0.1:8080").rstrip("/")
SEARCH_PROVIDER = os.environ.get("SEARCH_PROVIDER", "tavily").lower()
TOP_K = int(os.environ.get("TOP_K", "5"))

SYSTEM_PROMPT = (
    "You are a helpful, direct assistant running locally. When web-search results "
    "are supplied, ground your answer in them and cite them as [n]. If the results "
    "do not contain the answer, say so plainly rather than guessing."
)

app = FastAPI(title="Mistral web assistant")


class ChatIn(BaseModel):
    message: str


def _fmt(i, title, url, body):
    return f"[{i}] {title}\n{url}\n{body}"


def web_search(query):
    """Return (context, sources). context is '' when search is unavailable."""
    try:
        if SEARCH_PROVIDER == "tavily":
            key = os.environ.get("TAVILY_API_KEY", "")
            if not key:
                return "", []
            r = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": key,
                    "query": query,
                    "max_results": TOP_K,
                    "include_answer": False,
                    "search_depth": "basic",
                },
                timeout=30,
            )
            r.raise_for_status()
            items = r.json().get("results", [])
            ctx = "\n\n".join(
                _fmt(i + 1, x.get("title", ""), x.get("url", ""), x.get("content", ""))
                for i, x in enumerate(items)
            )
            src = [{"title": x.get("title", ""), "url": x.get("url", "")} for x in items]

        elif SEARCH_PROVIDER == "brave":
            key = os.environ.get("BRAVE_API_KEY", "")
            if not key:
                return "", []
            r = httpx.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": TOP_K},
                headers={"X-Subscription-Token": key, "Accept": "application/json"},
                timeout=30,
            )
            r.raise_for_status()
            items = (r.json().get("web") or {}).get("results", [])
            ctx = "\n\n".join(
                _fmt(i + 1, x.get("title", ""), x.get("url", ""), x.get("description", ""))
                for i, x in enumerate(items)
            )
            src = [{"title": x.get("title", ""), "url": x.get("url", "")} for x in items]

        elif SEARCH_PROVIDER == "serper":
            key = os.environ.get("SERPER_API_KEY", "")
            if not key:
                return "", []
            r = httpx.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": TOP_K},
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                timeout=30,
            )
            r.raise_for_status()
            items = r.json().get("organic", [])
            ctx = "\n\n".join(
                _fmt(i + 1, x.get("title", ""), x.get("link", ""), x.get("snippet", ""))
                for i, x in enumerate(items)
            )
            src = [{"title": x.get("title", ""), "url": x.get("link", "")} for x in items]

        else:
            return "", []

        return ctx, src
    except Exception as exc:  # a search failure must never break the chat
        return f"(web search failed: {exc})", []


@app.post("/chat")
def chat(inp: ChatIn):
    ctx, sources = web_search(inp.message)
    if ctx:
        user = (
            "Web search results:\n\n"
            f"{ctx}\n\n"
            f"Question: {inp.message}\n\n"
            "Answer the question using the results above and cite them as [n]."
        )
    else:
        user = inp.message

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": False,
    }
    r = httpx.post(f"{LLAMA_URL}/v1/chat/completions", json=payload, timeout=900)
    r.raise_for_status()
    answer = r.json()["choices"][0]["message"]["content"]
    return {"answer": answer, "sources": sources}


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mistral web assistant</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font: 15px/1.5 system-ui, sans-serif; background: #0d1117; color: #e6edf3; }
  header { padding: 14px 18px; border-bottom: 1px solid #21262d; font-weight: 600; }
  #log { max-width: 820px; margin: 0 auto; padding: 18px 18px 90px; }
  .msg { margin: 0 0 14px; padding: 12px 14px; border-radius: 10px; white-space: pre-wrap; }
  .user { background: #1f6feb22; border: 1px solid #1f6feb55; }
  .bot  { background: #161b22; border: 1px solid #21262d; }
  .src  { font-size: 13px; color: #8b949e; margin-top: 8px; }
  .src a { color: #58a6ff; }
  form { position: fixed; bottom: 0; left: 0; right: 0; background: #0d1117;
         padding: 14px; display: flex; gap: 8px; border-top: 1px solid #21262d; }
  input { flex: 1; padding: 11px 12px; border-radius: 8px; border: 1px solid #30363d;
          background: #010409; color: inherit; }
  button { padding: 11px 18px; border-radius: 8px; border: 0; background: #238636;
           color: #fff; font-weight: 600; cursor: pointer; }
  button:disabled { opacity: .6; cursor: default; }
</style>
</head>
<body>
<header>Mistral 7B - web search enabled - local</header>
<div id="log"></div>
<form id="f">
  <input id="q" placeholder="Ask anything..." autocomplete="off" autofocus>
  <button id="b" type="submit">Send</button>
</form>
<script>
const log = document.getElementById('log'), f = document.getElementById('f'),
      q = document.getElementById('q'), b = document.getElementById('b');
function add(cls, text, sources) {
  const d = document.createElement('div');
  d.className = 'msg ' + cls;
  d.textContent = text;
  if (sources && sources.length) {
    const s = document.createElement('div');
    s.className = 'src';
    s.innerHTML = 'Sources: ' + sources.map((x, i) =>
      '<a href="' + x.url + '" target="_blank" rel="noopener">[' + (i + 1) + '] ' +
      (x.title || x.url) + '</a>').join(' - ');
    d.appendChild(s);
  }
  log.appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
  return d;
}
f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = q.value.trim();
  if (!text) return;
  add('user', text);
  q.value = ''; b.disabled = true;
  const out = add('bot', 'thinking...');
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text}),
    });
    const data = await res.json();
    out.remove();
    add('bot', data.answer || '(no answer)', data.sources);
  } catch (err) {
    out.textContent = 'Error: ' + err;
  } finally {
    b.disabled = false; q.focus();
  }
});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("APP_PORT", "8000")))
