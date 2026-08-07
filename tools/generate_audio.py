"""Generate through the local app API and download a verified WAV for agent use."""
from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "generated" / "agent"


def verify_wav(path: Path) -> dict[str, float | int]:
    if not path.is_file() or path.stat().st_size <= 44:
        raise RuntimeError(f"Generated WAV is missing or empty: {path}")
    with wave.open(str(path), "rb") as wav:
        frames = wav.getnframes()
        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
    if frames <= 0 or sample_rate <= 0:
        raise RuntimeError(f"Generated WAV has no audio frames: {path}")
    return {
        "duration": frames / sample_rate,
        "sample_rate": sample_rate,
        "channels": channels,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sfx", "music"], default="sfx")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--name")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--url", default="http://127.0.0.1:8600")
    args = parser.parse_args()

    try:
        with httpx.Client(timeout=600) as client:
            response = client.post(
                args.url + "/api/generate",
                json={
                    "mode": args.mode,
                    "prompt": args.prompt,
                    "duration": args.duration,
                    "name": args.name,
                    "seed": args.seed,
                },
            )
            response.raise_for_status()
            sound = response.json()
            output = args.output.resolve() if args.output else (DEFAULT_OUTPUT_DIR / f"{sound['id']}.wav").resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            audio = client.get(args.url + sound["url"], timeout=120)
            audio.raise_for_status()
            output.write_bytes(audio.content)
    except httpx.ConnectError:
        print("Local sound-effect service is not running. Start start.bat and retry.", file=sys.stderr)
        return 2
    except httpx.HTTPError as exc:
        detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
        print(f"Generation failed: {detail}", file=sys.stderr)
        return 1

    verified = verify_wav(output)
    result = {
        "path": str(output),
        "model": "small-" + args.mode,
        "duration": verified["duration"],
        "sample_rate": verified["sample_rate"],
        "channels": verified["channels"],
        "prompt": sound["prompt_en"],
        "id": sound["id"],
    }
    print(json.dumps(result, ensure_ascii=False) if args.json else result["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
