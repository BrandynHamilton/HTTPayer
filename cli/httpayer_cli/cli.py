from httpayer import HTTPayerClient
import click
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel
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
from sqlalchemy import create_engine

from .auth_manager import clear_api_key

load_dotenv()

DISCOVERY_URL = "https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources"

HTTPAYER_API_KEY = os.getenv("HTTPAYER_API_KEY")

CONFIG_DIR = Path.home() / ".httpayer"
CONFIG_PATH = CONFIG_DIR / "config.json"

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
    """Open file in browser (HTML), spreadsheet app (CSV), Markdown viewer (MD), or JSON viewer (JSON)."""
    if fmt == "html":
        webbrowser.open(f"file://{os.path.abspath(filepath)}")
    elif fmt in ["csv", "md", "json"]:
        if sys.platform.startswith("win"):
            os.startfile(filepath)  # Windows: Excel, VS Code, Notepad, etc.
        elif sys.platform == "darwin":
            subprocess.run(["open", filepath])  # macOS: Numbers/Excel, VS Code/TextEdit
        else:
            subprocess.run(["xdg-open", filepath])  # Linux: LibreOffice/Excel, VS Code, etc.

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
@click.option('--format', type=click.Choice(['json', 'csv', 'md', 'html']), default=None,
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
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
def call(method, url, headers, data, params, output, format, open_browser, stdout_only, to_db, table, replace_table, json_file, verbose):
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

    # Parse headers/params if passed as JSON strings
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
            fmt = "json"   # trust actual parse
        else:
            content_type = response.headers.get("Content-Type", "")
            if "html" in content_type.lower() or content.strip().startswith("<!DOCTYPE html"):
                fmt = "html"
            else:
                fmt = "txt"

    # Build timestamped filename
    timestamp = int(time.time())
    if output:
        out_path = Path(output)
        if out_path.is_absolute() or out_path.parent != Path('.'):
            # Treat as full path (absolute or relative with dirs)
            if not out_path.suffix:
                out_path = out_path.with_suffix(f".{fmt}")
            out_path = out_path.with_name(f"{out_path.stem}_{timestamp}{out_path.suffix}")
        else:
            # Treat as basename, save inside configured output dir
            hist_dir = load_output_dir()
            hist_dir.mkdir(parents=True, exist_ok=True)
            suffix = Path(output).suffix or f".{fmt}"
            stem = Path(output).stem
            out_path = hist_dir / f"{stem}_{timestamp}{suffix}"
    else:
        hist_dir = load_output_dir()
        hist_dir.mkdir(parents=True, exist_ok=True)
        out_path = hist_dir / f"response_{timestamp}.{fmt}"

    # Format response
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
        else:
            raise ValueError("Unrecognized or unparseable format")
    except Exception:
        out_text = content
        out_path = out_path.with_suffix(".txt")
        fmt = "txt"

    # Save unless stdout-only
    if not stdout_only and not (to_db and not output):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_text, encoding="utf-8", errors="ignore")
        click.echo(f"Response saved to {out_path}")
        if open_browser and fmt in ["html", "csv", "md", "json"]:
            open_file(out_path, fmt)

    # Always echo to console
    if fmt == "json" and parsed:
        click.echo(json.dumps(parsed, indent=4))
    else:
        click.echo(out_text[:500] + ("..." if len(out_text) > 500 else ""))

    # Save to DB if requested
    if to_db:
        save_to_db(parsed if parsed else out_text, to_db, table_name=table, fmt=fmt, replace=replace_table)
        click.echo(f"Response saved to DB {to_db}, table '{table}'")

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
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
def list_endpoints_cmd(save, open_flag, verbose):
    """List available API endpoints on x402 Bazaar (raw JSON)."""
    try:
        resp = requests.get(DISCOVERY_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise click.ClickException(f"Failed to fetch discovery resources: {e}")

    services = data.get("items", [])
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

cli.add_command(call)
cli.add_command(balance)
cli.add_command(login)
cli.add_command(logout)
cli.add_command(list_endpoints_cmd)
cli.add_command(set_dir_cmd)
cli.add_command(show_config)

SYSTEM_DRAFT = """You are a CLI helper.
Convert user requests into strict JSON of the form:
{
  "method": "GET|POST|...",
  "api_url": "...",
  "params": {...},
  "headers": {...},
  "data": {...}
}
Only return JSON, nothing else.
"""

@cli.group()
def ai():
    """AI-powered helpers (draft/run/explain)."""
    pass

@ai.command()
@click.argument("prompt", type=str)
@click.option("--save", type=click.Path(), help="Save structured call to JSON file")
@click.option("--model", default="gpt-4o-mini")
def draft(prompt, save, model):
    """Draft a call spec from a natural language prompt."""
    from .llm import OpenAIProvider
    provider = OpenAIProvider(model=model)
    raw = provider.complete(SYSTEM_DRAFT, prompt)

    # Validate JSON
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError:
        raise click.ClickException(f"LLM did not return valid JSON: {raw}")

    if save:
        Path(save).write_text(json.dumps(spec, indent=2))
        click.echo(f"Saved draft to {save}")
    else:
        click.echo(json.dumps(spec, indent=2))

@ai.command()
@click.argument("prompt", type=str)
@click.option("--model", default="gpt-4o-mini")
@click.pass_context
def run(ctx, prompt, model):
    """Draft and immediately run a call from a prompt."""
    from .llm import OpenAIProvider
    provider = OpenAIProvider(model=model)
    raw = provider.complete(SYSTEM_DRAFT, prompt)
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError:
        raise click.ClickException(f"Invalid JSON: {raw}")

    # Reuse your `call` command
    ctx.invoke(
        call,
        method=spec.get("method"),
        url=spec.get("api_url"),
        headers=json.dumps(spec.get("headers", {})),
        params=json.dumps(spec.get("params", {})),
        data=json.dumps(spec.get("data", {})) if spec.get("data") else None,
        output=None,
        format=None,
        open_browser=False,
        stdout_only=False,
        to_db=None,
        table="responses",
        replace_table=False,
        json_file=None,
        verbose=False,
    )

@ai.command()
@click.option("--json-file", type=click.Path(exists=True), required=True)
def explain(json_file):
    """Explain a structured call file in plain English."""
    spec = json.loads(Path(json_file).read_text())
    click.echo("This call will:")
    click.echo(f"- Method: {spec['method']}")
    click.echo(f"- URL: {spec['api_url']}")
    if spec.get("params"):
        click.echo(f"- Params: {spec['params']}")
    if spec.get("headers"):
        click.echo(f"- Headers: {spec['headers']}")
    if spec.get("data"):
        click.echo(f"- Data: {spec['data']}")

ai.add_command(draft)
ai.add_command(run)
ai.add_command(explain)

if __name__ == '__main__':
    cli()
