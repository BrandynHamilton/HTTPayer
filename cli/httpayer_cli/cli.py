from httpayer import HTTPayerClient
import click
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Any, Optional, List, Dict
from pathlib import Path
import pandas as pd
import webbrowser
import time
import subprocess
import sys
import asyncio
import requests
import sqlite3
import io
import hashlib
import tempfile
from sqlalchemy import create_engine

from .auth_manager import clear_api_key

try:
    import yaml  
except Exception:
    yaml = None

from .ai_provider import OpenAIProvider
from .ai_cache import bazaar_hash, make_key, get_cache, put_cache
from .schemas import DraftCall
from .plan_runner import run_plan

load_dotenv()

DISCOVERY_URL = "https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources"

HTTPAYER_API_KEY = os.getenv("HTTPAYER_API_KEY")

CONFIG_DIR = Path.home() / ".httpayer"
CONFIG_PATH = CONFIG_DIR / "config.json"

network_map = {
    "mainnet":"base",
    "testnet":"base-sepolia",
}

def _endpoints_path() -> Path:
    out_root = get_output_root()
    ep_dir = out_root / "endpoints"
    ep_dir.mkdir(parents=True, exist_ok=True)
    return ep_dir / "endpoints.json"


def _load_bazaar_or_fetch() -> dict:
    """Load endpoints/endpoints.json; if missing, fetch from DISCOVERY_URL."""
    ep_path = _endpoints_path()
    if ep_path.exists():
        try:
            return json.loads(ep_path.read_text())
        except Exception:
            pass
    # fetch fresh
    resp = requests.get(DISCOVERY_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    ep_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def _filter_services(data: dict, max_price: Optional[int]) -> List[dict]:
    items = data.get("items", [])
    res = []
    for it in items:
        accepts = it.get("accepts", [])
        if not accepts:
            continue
        a0 = accepts[0]
    
        if max_price is not None:
            raw = a0.get("maxAmountRequired")
            try:
                if raw is None:
                    continue
                if int(str(raw)) > int(max_price):
                    continue
            except Exception:
                continue
        res.append(it)
    # cheap first
    res.sort(key=lambda s: int(s["accepts"][0].get("maxAmountRequired") or 1_000_000_000))
    return res[:50]  # keep prompt small


def _compact_services_for_prompt(svcs: List[dict]) -> List[dict]:
    out = []
    for s in svcs:
        a = s.get("accepts", [{}])[0]
        # Method may live in outputSchema.input.method
        method = (a.get("outputSchema", {}) or {}).get("input", {}).get("method") or "GET"
        out.append({
            "url": s.get("resource"),
            "network": a.get("network"),
            "method": method,
            "maxAmountRequired": a.get("maxAmountRequired"),
            "mimeType": a.get("mimeType") or "",
            "description": a.get("description") or s.get("metadata", {}).get("description", "")
        })
    return out


STRICT_DRAFT_SYSTEM = """You translate natural tasks into STRICT JSON for one HTTP call.

Return ONLY valid JSON matching exactly:
{
  "method": "GET|POST|PUT|DELETE",
  "api_url": "https://...",
  "headers": { ... },
  "params": { ... },
  "data": null | object | string
}

Rules:
- Prefer services from the provided x402 list (cheap first).
- If service exposes input schema (query/body), propose reasonable defaults.
- Never add commentary, markdown, or extra keys. JSON only.
- Use uppercase HTTP method.
- If unsure about headers, return {}.
- If no body, set "data": null.
"""

def _draft_prompt(user_prompt: str, services_snippet: List[dict]) -> str:
    return (
        "Task:\n"
        f"{user_prompt}\n\n"
        "Candidate x402 endpoints (cheap-first):\n"
        f"{json.dumps(services_snippet, indent=2)}\n\n"
        "Return the STRICT JSON now."
    )


def _validate_draft(text: str) -> DraftCall:
    # Extract JSON (some models wrap in code blocks)
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # remove leading 'json' in triple backticks if present
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            maybe_lang = cleaned[:first_newline].lower()
            if "json" in maybe_lang:
                cleaned = cleaned[first_newline+1:]
    payload = json.loads(cleaned)
    return DraftCall(**payload)


def _post_ops(op: Optional[str], json_data: Optional[Any], raw_text: str) -> Dict[str, Any]:
    """
    op syntax:
      - 'summary'
      - 'extract:key1,key2'
      - 'table'  (returns markdown table)
      - 'html'   (table to HTML)
      - None     (pass-through)
    """
    if not op:
        return {"kind": "raw", "text": raw_text, "json": json_data}

    if op == "summary":
        if isinstance(json_data, dict):
            keys = list(json_data.keys())
            return {"kind": "summary", "text": f"Object with keys: {keys}", "json": json_data}
        elif isinstance(json_data, list):
            return {"kind": "summary", "text": f"List with {len(json_data)} rows", "json": json_data}
        return {"kind": "summary", "text": f"Text length: {len(raw_text)}", "json": None}

    if op.startswith("extract:"):
        fields = [p.strip() for p in op.split(":", 1)[1].split(",") if p.strip()]
        rows = []
        if isinstance(json_data, list):
            for r in json_data:
                rows.append({k: r.get(k) for k in fields})
        elif isinstance(json_data, dict):
            rows.append({k: json_data.get(k) for k in fields})
        else:
            rows.append({"text": raw_text})
        return {"kind": "extract", "rows": rows}

    if op == "table":
        if isinstance(json_data, list):
            df = pd.json_normalize(json_data)
        elif isinstance(json_data, dict):
            df = pd.json_normalize([json_data])
        else:
            df = pd.DataFrame([{"text": raw_text}])
        return {"kind": "table", "markdown": df.to_markdown(index=False)}

    if op == "html":
        if isinstance(json_data, list):
            df = pd.json_normalize(json_data)
        elif isinstance(json_data, dict):
            df = pd.json_normalize([json_data])
        else:
            df = pd.DataFrame([{"text": raw_text}])
        return {"kind": "html", "html": df.to_html(index=False)}

    return {"kind": "raw", "text": raw_text, "json": json_data}

def filter_endpoints(endpoints, config):
    env = config.get("network_env", "testnet")
    target = network_map.get(env, "base-sepolia")

    # Only keep endpoints whose network matches the target
    return [e for e in endpoints if any(
        acc.get("network") == target for acc in e.get("accepts", [])
    )]

def get_databases_root():
    """Load configured databases dir from ~/.httpayer/config.json, fallback to ~/.httpayer/databases"""
    cfg = load_config()
    dbdir = cfg.get("databases_dir")
    if not dbdir:
        dbdir = Path.home() / ".httpayer" / "databases"
    return Path(dbdir).expanduser().resolve()

def save_databases_dir(path: str):
    config = load_config()
    config["databases_dir"] = str(Path(path).expanduser().resolve())
    save_config(config)

def normalize_db_url(to_db: str) -> str:
    """Detect if `to_db` is a file path or already a DB URL."""
    if "://" in to_db and not to_db.endswith((".db", ".sqlite")):
        # Looks like a DB URL (postgres, mysql, etc.)
        return to_db
    
    db_path = Path(to_db)

    # Absolute or contains directory → respect it
    if db_path.is_absolute() or db_path.parent != Path('.'):
        return f"sqlite:///{db_path.expanduser().resolve()}"

    # Otherwise, drop into databases_dir
    db_root = get_databases_root()
    db_root.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(db_root / db_path).resolve()}"

def save_to_db(data, to_db, table_name="responses", fmt="json", replace=False):
    db_url = normalize_db_url(to_db)
    engine = create_engine(db_url)

    if fmt == "json":
        if isinstance(data, dict):
            df = pd.json_normalize([data])
        elif isinstance(data, list):
            df = pd.json_normalize(data)
        else:
            df = pd.DataFrame([{"content": str(data)}])
    elif fmt == "csv":
        df = pd.read_csv(io.StringIO(data))
    else:
        df = pd.DataFrame([{"content": str(data)}])

    with engine.begin() as conn:
        try:
            df.to_sql(
                table_name,
                conn,
                if_exists="replace" if replace else "append",
                index=False
            )
        except Exception as e:
            # Auto-fallback if append fails due to schema mismatch
            if not replace and "has no column" in str(e):
                df.to_sql(table_name, conn, if_exists="replace", index=False)
            else:
                raise

def load_json_file(path):
    with open(path, "r") as f:
        return json.load(f)

def open_file(filepath, fmt):
    """Open file in browser (HTML), spreadsheet app (CSV), Markdown viewer (MD), JSON viewer, or text editor."""
    if fmt == "html":
        webbrowser.open(f"file://{os.path.abspath(filepath)}")
    elif fmt in ["csv", "md", "json", "txt"]:
        if sys.platform.startswith("win"):
            os.startfile(filepath)  # Windows: Excel, Notepad, VS Code, etc.
        elif sys.platform == "darwin":
            subprocess.run(["open", filepath])  # macOS: TextEdit, VS Code
        else:
            subprocess.run(["xdg-open", filepath])  # Linux: gedit, VS Code

def save_api_key(api_key: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": api_key}, f)
    os.chmod(CONFIG_PATH, 0o600)  # user read/write only

def load_api_key() -> str | None:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f).get("api_key")
    return os.getenv("HTTPAYER_API_KEY")

def get_client() -> HTTPayerClient:
    api_key = load_api_key()
    if not api_key:
        raise click.ClickException("No API key found. Run `httpayer auth` first.")
    return HTTPayerClient(api_key=api_key)

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_PATH, 0o600)

def get_output_root():
    """Load configured output dir from ~/.httpayer/config.json, fallback to history dir."""
    cfg = load_config()
    outdir = cfg.get("output_dir")
    if not outdir:
        outdir = Path.home() / ".httpayer" / "history"
    return Path(outdir).expanduser().resolve()

def save_output_dir(path: str):
    config = load_config()
    config["output_dir"] = str(Path(path).expanduser().resolve())
    save_config(config)

def load_output_dir() -> Path:
    config = load_config()
    if "output_dir" in config:
        return Path(config["output_dir"])
    return Path.home() / ".httpayer" / "history"

def apply_post_transform(op: str, parsed: Any, raw_text: str):
    import pandas as pd
    if not op:
        return raw_text, parsed, None

    if op == "summary":
        if isinstance(parsed, dict):
            return f"Object with keys: {list(parsed.keys())}", parsed, "summary"
        elif isinstance(parsed, list):
            return f"List with {len(parsed)} items", parsed, "summary"
        else:
            return f"Text length: {len(raw_text)}", None, "summary"

    if op.startswith("extract:"):
        fields = [f.strip() for f in op.split(":", 1)[1].split(",")]
        rows = []
        if isinstance(parsed, list):
            for r in parsed:
                rows.append({k: r.get(k) for k in fields})
        elif isinstance(parsed, dict):
            rows.append({k: parsed.get(k) for k in fields})
        return json.dumps(rows, indent=2), rows, "extract"

    if op == "table":
        if isinstance(parsed, list):
            df = pd.json_normalize(parsed)
        elif isinstance(parsed, dict):
            df = pd.json_normalize([parsed])
        else:
            df = pd.DataFrame([{"text": raw_text}])
        return df.to_markdown(index=False), parsed, "table"

    if op == "html":
        if isinstance(parsed, list):
            df = pd.json_normalize(parsed)
        elif isinstance(parsed, dict):
            df = pd.json_normalize([parsed])
        else:
            df = pd.DataFrame([{"text": raw_text}])
        return df.to_html(index=False), parsed, "html"

    return raw_text, parsed, None

@click.group(name="httpayer", invoke_without_command=True)
def cli():
    """HTTPayer CLI tool for making HTTP requests with payment handling."""
    pass

@cli.command()
@click.argument('method', type=str, required=False)
@click.argument('url', type=str, required=False)
@click.option('--headers', type=str, default='{}', help='JSON string of headers')
@click.option('--data', type=str, default=None, help='Request body data')
@click.option('--params', type=str, default='{}', help='JSON string of query parameters')
@click.option('--output', type=str, default=None,
              help='Output file name or path (timestamp auto-appended)')
@click.option('--format', type=click.Choice(['json', 'csv', 'md', 'html', 'txt']), default=None,
              help='Force output format (default: auto-detect or JSON)')
@click.option('--open', 'open_browser', is_flag=True,
              help='Open output automatically (HTML/CSV/MD/JSON)')
@click.option('--stdout-only', is_flag=True,
              help='Print to console only, do not save to disk')
@click.option("--to-db", type=str,
              help="Save response into DB. Pass a SQLite filename (data.db) or a DB URL (postgresql://user:pass@host/db)")
@click.option("--table", type=str, default="responses", help="Table name when saving to DB")
@click.option("--replace-table", is_flag=True, help="Replace table instead of appending", default=False)
@click.option('--json-file', type=click.Path(exists=True), help='Path to JSON file', default=None)
@click.option(
    "--post",
    type=str,
    help="Transform response before saving: summary | extract:key1,key2 | table | html"
)
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
def call(method, url, headers, data, params, output, format, open_browser,
         stdout_only, to_db, table, replace_table, json_file, post, verbose):
    """Make an HTTP request with payment handling and flexible output."""

    # Load from JSON file if provided
    if json_file:
        with open(json_file, "r") as f:
            config = json.load(f)
        method = config.get("method", method)
        url = config.get("api_url", url)
        headers = config.get("headers", headers)
        params = config.get("params", params)
        data = config.get("data", data)

    if not method or not url:
        raise click.UsageError("You must provide METHOD and URL, either as arguments or in --json-file")

    headers = json.loads(headers) if isinstance(headers, str) else headers or {}
    params = json.loads(params) if isinstance(params, str) else params or {}

    client = get_client()
    response = client.request(method, url, headers=headers, data=data, params=params)
    response.raise_for_status()

    if verbose:
        click.echo(f"Status Code: {response.status_code}")
        click.echo(f"Headers: {response.headers}")

    content = response.text
    parsed = None
    try:
        parsed = response.json()
    except Exception:
        pass

    # Detect format
    fmt = format
    if not fmt and output:
        ext = Path(output).suffix.lower().lstrip(".")
        if ext in ["json", "csv", "md", "html"]:
            fmt = ext

    if not fmt:
        if parsed is not None:
            fmt = "json"
        else:
            content_type = response.headers.get("Content-Type", "")
            body = content.strip()

            # 🔹 Prefer .txt if it's "html" header but not actual HTML markup
            if "html" in content_type.lower() or body.lower().startswith("<!doctype html"):
                if body.startswith("<") and not body[:200].strip().startswith(("Vegetarians", "Hello", "Error", "Warning")):
                    fmt = "html"
                elif body.lower().startswith("<html") or body.lower().startswith("<!doctype"):
                    fmt = "html"
                else:
                    fmt = "txt"
            else:
                fmt = "txt"

    # 🔹 Apply post transform if requested
    if post:
        out_text, parsed, kind = apply_post_transform(post, parsed, content)
        if kind == "table":
            fmt = "md"
        elif kind == "html":
            fmt = "html"
        elif kind in ("summary", "extract"):
            fmt = "json"
    else:
        out_text = None

    # Format response if no transform already produced it
    if out_text is None:
        try:
            if fmt == "json" and parsed:
                out_text = json.dumps(parsed, indent=4)
            elif fmt == "csv" and parsed:
                df = pd.json_normalize(parsed)
                out_text = df.to_csv(index=False)
            elif fmt == "md" and parsed:
                df = pd.json_normalize(parsed)
                out_text = df.to_markdown(index=False)
            elif fmt == "html":
                out_text = content
            elif fmt == "txt":
                out_text = content.strip() or content
            else:
                raise ValueError("Unrecognized or unparseable format")
        except Exception as e:
            out_text = content
            fmt = "txt"   # 🔹 fallback to plain text
            click.echo(
                f"⚠️  Warning: response could not be parsed as {format or 'auto-detected'} "
                f"(error: {e}). Saved as plain text instead.",
                err=True
            )

    # Build timestamped filename
    timestamp = int(time.time())
    if output:
        out_path = Path(output)
        if out_path.is_absolute() or out_path.parent != Path('.'):
            if not out_path.suffix:
                out_path = out_path.with_suffix(f".{fmt}")
            out_path = out_path.with_name(f"{out_path.stem}_{timestamp}{out_path.suffix}")
        else:
            hist_dir = load_output_dir()
            hist_dir.mkdir(parents=True, exist_ok=True)
            suffix = Path(output).suffix or f".{fmt}"
            stem = Path(output).stem
            out_path = hist_dir / f"{stem}_{timestamp}{suffix}"
    else:
        hist_dir = load_output_dir()
        hist_dir.mkdir(parents=True, exist_ok=True)
        out_path = hist_dir / f"response_{timestamp}.{fmt}"

    # Save unless stdout-only
    if not stdout_only and not (to_db and not output):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_text, encoding="utf-8", errors="ignore")
        click.echo(f"Response saved to {out_path}")
        if open_browser and fmt in ["html", "csv", "md", "json", "txt"]:
            open_file(out_path, fmt)

    # Always echo to console
    if fmt == "json" and parsed:
        click.echo(json.dumps(parsed, indent=4))
    else:
        click.echo(out_text[:500] + ("..." if len(out_text) > 500 else ""))

    # Save to DB if requested
    if to_db:
        save_to_db(parsed if parsed else out_text, to_db,
                   table_name=table, fmt=fmt, replace=replace_table)
        click.echo(f"Response saved to DB {to_db}, table '{table}'")

    return str(out_path)

@cli.command()
def balance():
    """Check account balance."""
    client = get_client()
    # balance_info = client.get_balance(chain=chain)
    # click.echo(f"Balance: {balance_info['balance']} {balance_info['currency']}")
    pass  # Placeholder for balance functionality

@cli.command()
@click.option(
    "--api-key",
    envvar="HTTPAYER_API_KEY",
    prompt="Enter your API key",
    hide_input=True,
    help="API key for the user account"
)
@click.option('--ephemeral', is_flag=True, help="Use API key only for this session (don't save).")
def login(api_key, ephemeral):
    """Authenticate the user and persist API key."""
    if ephemeral:
        os.environ["HTTPAYER_API_KEY"] = api_key
        click.echo("Ephemeral API key set for this session.")
    else:
        save_api_key(api_key)
        click.echo("API key saved to ~/.httpayer/config.json")

@cli.command()
def logout():
    """Log out the user and clear API key."""
    clear_api_key()
    click.echo("API key cleared.")

@cli.command(name="list")
@click.option(
    "--save/--no-save",
    default=True,
    help="Save full discovery response to endpoints/endpoints.json (default: save)"
)
@click.option(
    "--open",
    "open_flag",
    is_flag=True,
    help="Open the saved endpoints.json file in the default viewer"
)
@click.option('--filter', type=str, help="Filter services by name or tag")
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
def list_endpoints_cmd(save, open_flag, filter, verbose):
    """List available API endpoints on x402 Bazaar (raw JSON)."""
    try:
        resp = requests.get(DISCOVERY_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise click.ClickException(f"Failed to fetch discovery resources: {e}")

    services = data.get("items", [])
    services = filter_endpoints(services, load_config())
    click.echo(f"Found {len(services)} services")

    if verbose:

        for i, svc in enumerate(services, 1):
            accepts = svc.get("accepts", [])
            method = "?"
            max_amt = "(unspecified)"
            network = "?"

            if accepts:
                method = (
                    accepts[0].get("outputSchema", {})
                            .get("input", {})
                            .get("method", "?")
                )
                raw_val = accepts[0].get("maxAmountRequired")
                max_amt = raw_val if raw_val else "(unspecified)"
                network = accepts[0].get("network", "?")

            click.echo(f"{i}. {method} {svc.get('resource')} "
                    f"(max: {max_amt}, network: {network})")
    if save:
        out_root = get_output_root()
        out_dir = out_root / "endpoints"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "endpoints.json"
        out_path.write_text(json.dumps(data, indent=2))
        click.echo(f"Full discovery JSON saved to {out_path}")

        if open_flag:
            open_file(out_path, "json")

@cli.command(name="set-dir")
@click.argument("path", type=click.Path())
@click.option("--target", type=click.Choice(["output", "databases"]), default="output",
              help="Which directory to set (output or databases)")
def set_dir_cmd(path, target):
    """Override default directories for responses or databases."""
    config = load_config()
    key = f"{target}_dir"
    config[key] = str(Path(path).expanduser().resolve())
    save_config(config)
    click.echo(f"{target.capitalize()} directory set to {path}")

@cli.command(name="set-network")
@click.argument("env", type=click.Choice(["testnet"]))
def set_network_cmd(env):
    """Set network environment (mainnet or testnet)."""
    config = load_config()
    config["network_env"] = env
    save_config(config)
    click.echo(f"Network environment set to {env}")

@click.command()
def show_config():
    """Show current HTTPayer config (API key path, output dir, etc.)."""
    config = load_config()
    click.echo("HTTPayer Configuration:")
    click.echo(f"- Config file: {CONFIG_PATH}")
    api_key = config.get("api_key", None)
    click.echo(f"- API key set: {'yes' if api_key else 'no'}")
    click.echo(f"- Output directory: {config.get('output_dir', Path.home() / '.httpayer' / 'history')}")
    click.echo(f"- Databases directory: {config.get('databases_dir', Path.home() / '.httpayer' / 'databases')}")
    click.echo(f"- Network environment: {config.get('network_env', 'testnet')}")

@cli.command(name="list-files")
def list_files():
    """List files in the output directory."""
    out_dir = load_output_dir()
    if not out_dir.exists():
        click.echo(f"Output directory {out_dir} does not exist.")
        return
    files = list(out_dir.glob("*"))
    if not files:
        click.echo(f"No files found in output directory {out_dir}.")
        return
    click.echo(f"Files in output directory {out_dir}:")
    for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
        mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(f.stat().st_mtime))
        size = f.stat().st_size
        click.echo(f"- {f.name} (size: {size} bytes, modified: {mtime})")

@cli.group()
def agent():
    """AI-powered helpers (draft/run/explain)."""
    pass

@agent.command("draft")
@click.argument("prompt", type=str, required=True)
@click.option("--save", type=click.Path(), help="Save draft JSON to file")
@click.option("--max-price", type=int, help="Max atomic units (e.g., USDC 6dp)")
@click.option("--model", type=str, default="gpt-4o-mini", help="LLM model")
@click.option("--ai-key", type=str, default=None, help="Override OPENAI_API_KEY")
def ai_draft(prompt, save, max_price, model, ai_key):
    """Produce a strict call JSON from a natural language prompt (no call executed)."""
    bazaar = _load_bazaar_or_fetch()
    bazaar["items"] = filter_endpoints(bazaar.get("items", []), load_config())

    svcs = _filter_services(bazaar, max_price=max_price)
    snippet = _compact_services_for_prompt(svcs)

    # Cache lookup
    root = CONFIG_DIR
    bh = bazaar_hash(bazaar)
    user = _draft_prompt(prompt, snippet)
    cache_key = make_key(model, user, bh, mode="draft")
    cached = get_cache(root, cache_key)
    if cached:
        text = cached
    else:
        provider = OpenAIProvider(api_key=ai_key)
        res = provider.complete(system=STRICT_DRAFT_SYSTEM, user=user, model=model, max_tokens=600, temperature=0)
        text = res.text
        put_cache(root, cache_key, model, bh, user, text)

    # Validate
    draft = _validate_draft(text)

    # Save or print
    payload = draft.model_dump(mode="json")
    if save:
        Path(save).parent.mkdir(parents=True, exist_ok=True)
        Path(save).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        click.echo(f"Draft saved → {save}")
    else:
        click.echo(json.dumps(payload, indent=2))


@agent.command("run")
@click.argument("prompt", type=str, required=True)
@click.option("--save", type=click.Path(), help="Save draft JSON before running")
@click.option("--max-price", type=int, help="Max atomic units")
@click.option("--post", type=str, help="Post-op: summary | extract:key1,key2 | table | html")
@click.option("--model", type=str, default="gpt-4o-mini", help="LLM model")
@click.option("--ai-key", type=str, default=None, help="Override OPENAI_API_KEY")
@click.option("--out", type=click.Path(), default=None, help="Optional output filename/path (httpayer call)")
@click.pass_context
def ai_run(ctx, prompt, save, max_price, post, model, ai_key, out):
    """Draft from prompt, then execute the call; optional post-processing."""
    # 1) draft
    bazaar = _load_bazaar_or_fetch()
    bazaar["items"] = filter_endpoints(bazaar.get("items", []), load_config())

    svcs = _filter_services(bazaar, max_price=max_price)
    snippet = _compact_services_for_prompt(svcs)

    root = CONFIG_DIR
    bh = bazaar_hash(bazaar)
    user = _draft_prompt(prompt, snippet)
    cache_key = make_key(model, user, bh, mode="draft")
    cached = get_cache(root, cache_key)
    if cached:
        text = cached
    else:
        provider = OpenAIProvider(api_key=ai_key)
        res = provider.complete(system=STRICT_DRAFT_SYSTEM, user=user, model=model, max_tokens=600, temperature=0)
        text = res.text
        put_cache(root, cache_key, model, bh, user, text)

    draft = _validate_draft(text)
    payload = draft.model_dump(mode="json")

    if save:
        Path(save).parent.mkdir(parents=True, exist_ok=True)
        Path(save).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        click.echo(f"Draft saved → {save}")

    # 2) run via existing `call`
    tmp = Path(tempfile.mkstemp(prefix="httpayer_draft_", suffix=".json")[1])
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # We can pass through your call flags. Here we re-use only a subset for simplicity.
    # If you want to expose more, add matching options on this command and forward them.
    ctx.invoke(
        cli.commands["call"],
        method=None,
        url=None,
        headers="{}",
        data=None,
        params="{}",
        output=out,
        format=None,
        open_browser=False,
        stdout_only=False,
        to_db=None,
        table="responses",
        replace_table=False,
        json_file=str(tmp),
        verbose=False,
        post=(post or None)
    )

    # 3) Optional post-ops (read the just-executed response from stdout is tricky;
    # instead, we re-fetch using the same draft and run it ad-hoc here to shape in-memory)
    # If you want post-ops to shape the saved file, wire them inside your `call()` path.
    if post:
        # simple roundtrip re-call using requests (read-only; no payment interceptor here)
        try:
            import requests as _r
            _m = payload["method"].upper()
            _u = payload["api_url"]
            _h = payload.get("headers") or {}
            _p = payload.get("params") or {}
            _d = payload.get("data")
            r = _r.request(_m, _u, headers=_h, params=_p, json=_d, timeout=20)
            txt = r.text
            try:
                js = r.json()
            except Exception:
                js = None
            shaped = _post_ops(post, js, txt)
            if shaped.get("markdown"):
                click.echo(shaped["markdown"])
            elif shaped.get("html"):
                click.echo(shaped["html"])
            elif shaped.get("rows"):
                click.echo(json.dumps(shaped["rows"], indent=2))
            else:
                click.echo(shaped.get("text") or json.dumps(shaped.get("json"), indent=2))
        except Exception as e:
            click.echo(f"[post] failed: {e}", err=True)


@agent.command("explain")
@click.argument("files", type=click.Path(exists=True), nargs=-1, required=True)
@click.option("--model", type=str, default="gpt-4o-mini", help="LLM model")
@click.option("--ai-key", type=str, default=None, help="Override OPENAI_API_KEY")
@click.option("--short", is_flag=True, help="Return a one-line explanation instead of bullet points")
def ai_explain(files, model, ai_key, short):
    """Explain one or more draft/response files in plain English."""
    provider = OpenAIProvider(api_key=ai_key)

    for f in files:
        path = Path(f)
        text = path.read_text(errors="ignore")
        fmt = path.suffix.lower().lstrip(".")

        # --- try to parse smartly based on suffix
        payload = None
        mode = "text-response"
        if fmt in ("json", ""):
            try:
                payload = json.loads(text)
                if isinstance(payload, dict) and "method" in payload and "api_url" in payload:
                    mode = "draft"
                else:
                    mode = "json-response"
            except Exception:
                payload = {"response": text}
        elif fmt == "csv":
            import pandas as pd
            df = pd.read_csv(path)
            payload = df.to_dict(orient="records")
            mode = "json-response"
        elif fmt in ("md", "txt"):
            payload = {"response": text}
            mode = "text-response"
        else:
            payload = {"response": text}

        # --- build system prompt
        if mode == "draft":
            system = "Explain this HTTP request JSON " + ("in one line." if short else "in bullet points.")
            user = json.dumps(payload, indent=2)
        elif mode == "json-response":
            system = "Summarize this structured API response " + ("in one line." if short else "in bullet points.")
            user = json.dumps(payload, indent=2)
        else:
            system = "Summarize this API response text " + ("in one line." if short else "in bullet points.")
            user = text

        res = provider.complete(system=system, user=user,
                                model=model,
                                max_tokens=200 if short else 400,
                                temperature=0)
        click.echo(f"\n📄 {path.name}")
        click.echo(res.text)

# <<< NEW


# >>> NEW: PLAN COMMAND GROUP
@click.group(name="plan")
def plan_group():
    """Run small YAML plans (DAG-ish)."""
    pass


@plan_group.command("run")
@click.argument("plan_file", type=click.Path(exists=True))
@click.pass_context
def plan_run(ctx, plan_file):
    """Execute steps defined in a YAML plan."""
    if yaml is None:
        raise click.ClickException("pyyaml not installed. `pip install pyyaml`.")
    try:
        results = run_plan(ctx, plan_file)
        click.echo("Plan completed.")
    except Exception as e:
        raise click.ClickException(f"Plan failed: {e}")
# <<< NEW


# register new groups

cli.add_command(call)
cli.add_command(balance)
cli.add_command(login)
cli.add_command(logout)
cli.add_command(list_endpoints_cmd)
cli.add_command(set_dir_cmd)
cli.add_command(show_config)
cli.add_command(agent)
cli.add_command(plan_group)
cli.add_command(set_network_cmd)

if __name__ == '__main__':
    cli()
