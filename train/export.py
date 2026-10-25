"""Export a trained adapter from Tinker in Hugging Face format to results/train/adapters/<name>/.

Loads the checkpoint's saved state into a training client, asks Tinker to write the weights in
external (Hugging Face) format, then downloads every file through the signed URLs. The adapter
directory is gitignored (binary weights); a manifest with file sizes and hashes is written next to it.
"""

from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import httpx
import typer

warnings.filterwarnings("ignore", message=r'Field "model_')

from harness.db import ROOT  # noqa: E402
from train.sft_tinker import CHECKPOINTS_PATH, RESULTS_DIR, load_tinker_key  # noqa: E402

ADAPTERS_DIR = RESULTS_DIR / "adapters"

app = typer.Typer(add_completion=False)


@app.callback()
def _cli() -> None:
    """Subcommands below."""


def resolve_state(run_id: str, checkpoint: str | None) -> tuple[dict, str]:
    from train.rl_cookbook import checkpoint_record

    rec = checkpoint_record(run_id)  # a run name or a run_id
    if checkpoint:
        c = next((c for c in rec.get("checkpoints", []) if c.get("name") == checkpoint), None)
        if c is None or not c.get("state_path"):
            raise typer.BadParameter(f"run {run_id} has no state checkpoint named {checkpoint}")
        return rec, c["state_path"]
    return rec, rec["state_path"]


@app.command()
def main(run_id: str = typer.Option(...), checkpoint: str = typer.Option(None, help="Checkpoint name within the run (default: final)."),
         name: str = typer.Option(None, help="Output directory name under results/train/adapters/.")) -> None:
    rec, state_path = resolve_state(run_id, checkpoint)
    name = name or f"{rec.get('name', rec['run_id'])}" + (f"-{checkpoint}" if checkpoint else "")
    out_dir = ADAPTERS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    load_tinker_key()
    import tinker

    service = tinker.ServiceClient()
    client = service.create_training_client_from_state(state_path)
    typer.echo(f"loaded {state_path}; exporting in Hugging Face format")
    saved = client.save_weights_external("hf_export").result()
    external_path = saved.path
    rest = service.create_rest_client()
    urls = rest.get_external_weights_urls(external_path).result().urls
    manifest = {"run_id": run_id, "checkpoint": checkpoint or "final", "model": rec["model"], "renderer": rec["renderer"],
                "state_path": state_path, "external_path": external_path, "files": {}}
    with httpx.Client(timeout=600, follow_redirects=True) as http:
        for rel, url in sorted(urls.items()):
            dest = out_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with http.stream("GET", url) as r:
                r.raise_for_status()
                h = hashlib.sha256()
                with dest.open("wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
                        h.update(chunk)
            manifest["files"][rel] = {"bytes": dest.stat().st_size, "sha256": h.hexdigest()}
            typer.echo(f"  {rel}: {dest.stat().st_size / 1e6:.1f} MB")
    cfg_path = out_dir / "adapter_config.json"
    if cfg_path.exists():  # Tinker leaves the base model empty; fill it so `peft` can load the adapter directly
        cfg = json.loads(cfg_path.read_text())
        if not cfg.get("base_model_name_or_path"):
            cfg["base_model_name_or_path"] = rec["model"]
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (RESULTS_DIR / f"adapter_manifest_{name}.json").write_text(json.dumps(manifest, indent=2) + "\n")
    typer.echo(f"wrote {out_dir.relative_to(ROOT)} ({len(urls)} files)")


if __name__ == "__main__":
    app()
