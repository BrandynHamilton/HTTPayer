# httpayer_cli/plan_runner.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
import yaml
import tempfile
import click
from click import Context

from .cli import get_output_root

# Only used to know which args to forward
CALL_KW = (
    "headers", "data", "params", "output", "format", "open_browser",
    "stdout_only", "to_db", "table", "replace_table", "json_file", "verbose"
)


def _write_tmp_json(payload: dict) -> Path:
    fp = Path(tempfile.mkstemp(prefix="httpayer_step_", suffix=".json")[1])
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return fp


def _expand_prompt(ai_cfg: dict, results: Dict[str, Any]) -> str:
    """Expand {{ step.output }} placeholders with actual file contents, with debug prints."""
    prompt = ai_cfg["prompt"]
    use = ai_cfg.get("use", [])

    print(f"🔍 Expanding prompt: {prompt}")
    for ref in use:
        ref_info = results.get(ref, {})
        ref_out = ref_info.get("out") or ref_info.get("json_file")

        print(f"   • Reference '{ref}': out={ref_out}")

        if ref_out and Path(ref_out).exists():
            try:
                data = Path(ref_out).read_text(encoding="utf-8")
                print(f"     ↳ Loaded {len(data)} chars from {ref_out}")
            except Exception as e:
                data = f"[Error reading {ref_out}: {e}]"
                print(f"     ⚠️ Error reading {ref_out}: {e}")
            placeholder = f"{{{{ {ref}.output }}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, data)
                print(f"     ✅ Replaced placeholder {placeholder}")
            else:
                print(f"     ⚠️ Placeholder {placeholder} not found in prompt")
        else:
            print(f"     ⚠️ Missing or invalid file for '{ref}', leaving placeholder unchanged")

    print(f"✅ Final expanded prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
    return prompt


def run_plan(ctx: Context, plan_file: str) -> Dict[str, Any]:
    from .ai_provider import OpenAIProvider
    """
    Execute a small DAG defined in YAML:

    steps:
      - name: fetch
        call: { method: GET, url: https://..., params: {...}, output: joke.txt }
      - name: summarize
        ai:
          prompt: "Summarize: {{ fetch.output }}"
          use: [fetch]
          out: summary.md
      - name: story
        ai:
          prompt: "Write a 500 word story based on {{ fetch.output }}"
          mode: text          # 👈 new field
          model: gpt-4o-mini
          out: story.md
    """
    plan_path = Path(plan_file)
    spec = yaml.safe_load(plan_path.read_text())
    if not spec or "steps" not in spec:
        raise ValueError("Invalid plan file: missing 'steps'.")

    results: Dict[str, Any] = {}
    root = ctx.find_root().command  # top-level cli

    for step in spec["steps"]:
        name = step["name"]

        if "call" in step:
            call_cfg = step["call"]
            payload = {
                "method": call_cfg["method"],
                "api_url": call_cfg["url"],
                "headers": call_cfg.get("headers", {}),
                "params": call_cfg.get("params", {}),
                "data": call_cfg.get("data"),
            }
            tmp_json = _write_tmp_json(payload)

            call_cmd = root.commands.get("call")
            if not call_cmd:
                raise click.ClickException("Plan failed: `call` command not found")

            saved_path = ctx.invoke(
                call_cmd,
                method=None,
                url=None,
                headers="{}",
                data=None,
                params="{}",
                output=call_cfg.get("output"),
                format=call_cfg.get("format"),
                open_browser=bool(call_cfg.get("open", False)),
                stdout_only=bool(call_cfg.get("stdout_only", False)),
                to_db=call_cfg.get("to_db"),
                table=call_cfg.get("table", "responses"),
                replace_table=bool(call_cfg.get("replace_table", False)),
                json_file=str(tmp_json),
                verbose=bool(call_cfg.get("verbose", False)),
                post=None,
            )

            if not saved_path or not Path(saved_path).exists():
                saved_path = None

            results[name] = {
                "type": "call",
                "json_file": str(tmp_json),
                "out": saved_path,
            }

        elif "ai" in step:
            ai_cfg = step["ai"]
            prompt = _expand_prompt(ai_cfg, results)
            out = ai_cfg.get("out")

            # --- NEW: support ai.mode === text
            if ai_cfg.get("mode") == "text":
                provider = OpenAIProvider(api_key=ai_cfg.get("ai_key"))
                res = provider.complete(
                    system="",
                    user=prompt,
                    model=ai_cfg.get("model", "gpt-4o-mini"),
                    max_tokens=1000,
                    temperature=0.7,
                )
                if out:
                    out_path = Path(out)
                    if not out_path.is_absolute():
                        outdir = get_output_root()
                        outdir.mkdir(parents=True, exist_ok=True)
                        out_path = outdir / out_path
                    out_path.write_text(res.text, encoding="utf-8")
                    click.echo(f"AI text saved to {out_path}")
                else:
                    click.echo(res.text)
                results[name] = {"type": "ai-text", "out": out}

            else:
                ai_cmd = root.commands.get("agent").commands.get("run")
                if not ai_cmd:
                    raise click.ClickException("Plan failed: `agent run` command not found")

                ctx.invoke(
                    ai_cmd,
                    prompt=prompt,
                    save=None,
                    max_price=None,
                    post=None,
                    ai_key=ai_cfg.get("ai_key"),
                    out=out,
                    **({"model": ai_cfg["model"]} if "model" in ai_cfg else {}),
                )
                results[name] = {"type": "ai", "out": out}

        else:
            raise ValueError(f"Step '{name}' must define either 'call' or 'ai'.")

    return results
