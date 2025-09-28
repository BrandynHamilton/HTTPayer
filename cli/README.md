uv pip install -e .

✅ Option A: Use uv run

Since you’re already using uv, the quickest is:

uv run httpayer call GET https://demo.httpayer.com/base-weather


That works because uv run exposes scripts from the local environment.

✅ Option B: Activate the venv

If you activate the .venv, Scripts/ will be added to PATH automatically:

.\.venv\Scripts\activate
httpayer call GET https://demo.httpayer.com/base-weather

✅ Option C: Add to PATH permanently

If you want httpayer always available without uv run or activating:

Find the .venv\Scripts directory for your project (probably C:\Users\brand\projects\httpayer\cli\.venv\Scripts).

Add that folder to your Windows PATH environment variable.

Start Menu → “Environment Variables” → edit PATH → add the directory.

Restart PowerShell.

Now httpayer should work globally.

---
uv pip install -e ".[ai]" (editable)

uv pip install ".[ai]" (non-editable)

--

httpayer ai draft "Get current weather for Austin using a cheap x402 endpoint" \
  --max-price 10000 --network base --save calls/call_austin.json

httpayer call --json-file calls/call_austin.json --open --format csv

httpayer ai run "Scrape the Coinbase x402 docs and summarize key limits" \
  --post summary --out results/docs_summary.md

httpayer ai run "Scrape the Coinbase x402 docs and summarize key limits" \
  --post summary --out results/docs_summary.md
