"""HTTP API. `mode` is optional for backward compatible SFX requests."""

from typing import Optional
from urllib.parse import quote

import anyio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import store, translate
from app.config import settings
from app.presets import PRESETS, PRESETS_BY_ID
from app.sfx_model import sfx_model

router = APIRouter(prefix="/api")


class GenerateRequest(BaseModel):
    mode: str = "sfx"
    prompt: Optional[str] = None
    preset_id: Optional[str] = None
    duration: Optional[float] = None
    name: Optional[str] = None
    seed: Optional[int] = None
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None
    negative_prompt: Optional[str] = None


class RenameRequest(BaseModel):
    name: str


class CutRequest(BaseModel):
    start_s: float
    end_s: float


class GainRequest(BaseModel):
    gain_db: Optional[float] = None
    normalize: bool = False


@router.get("/status")
async def get_status():
    state = sfx_model.status()
    return {
        "model_loaded": state["loaded"],
        "model_loading": state["loading"],
        "model_error": state["error"],
        "models": state["models"],
        "active_mode": state["active_mode"],
        "translator_ok": await translate.check_translator_ok(),
        "translator_url": settings.llm_url,
        "device": settings.device,
    }


@router.get("/presets")
async def get_presets():
    return PRESETS


@router.post("/generate")
async def generate_sound(body: GenerateRequest):
    mode = body.mode.lower()
    if mode not in settings.model_names:
        raise HTTPException(422, "mode must be 'sfx' or 'music'")
    if not body.prompt and not body.preset_id:
        raise HTTPException(400, "prompt or preset_id is required")
    preset = PRESETS_BY_ID.get(body.preset_id) if body.preset_id else None
    if body.preset_id and preset is None and not body.prompt:
        raise HTTPException(400, f"unknown preset_id: {body.preset_id}")
    prompt_original = body.prompt if body.prompt else preset["prompt"]
    source = "custom" if body.prompt else preset["id"]
    duration = (
        body.duration
        if body.duration is not None
        else (preset.get("duration") if preset else settings.default_durations[mode])
    )
    if duration is None:
        duration = settings.default_durations[mode]
    max_duration = 30 if mode == "sfx" else 120
    if not 0.5 <= duration <= max_duration:
        raise HTTPException(
            422, f"duration must be between 0.5 and {max_duration} for {mode}"
        )
    if body.steps is not None and not 1 <= body.steps <= 100:
        raise HTTPException(422, "steps must be between 1 and 100")
    if body.cfg_scale is not None and not 0.1 <= body.cfg_scale <= 10:
        raise HTTPException(422, "cfg_scale must be between 0.1 and 10")

    async def english(text: str) -> str:
        if not translate.needs_translation(text):
            return text
        try:
            return await translate.translate_to_english(text)
        except Exception as exc:
            raise HTTPException(
                503,
                "日本語翻訳サーバーに接続できません。英語で入力するか、"
                f"OpenAI互換サーバーを {settings.llm_url} に起動してください。詳細: {type(exc).__name__}",
            )

    prompt_en = await english(prompt_original)
    negative_prompt_en = (
        await english(body.negative_prompt) if body.negative_prompt else None
    )
    try:
        audio, sample_rate, seed_used = await anyio.to_thread.run_sync(
            lambda: sfx_model.generate(
                mode,
                prompt_en,
                duration,
                seed=body.seed,
                steps=body.steps,
                cfg_scale=body.cfg_scale,
                negative_prompt=negative_prompt_en,
            )
        )
    except RuntimeError:
        raise HTTPException(
            503,
            "モデルを読み込めませんでした。Hugging Faceでモデルのライセンスを承認し、"
            "`huggingface-cli login` を実行後、GPU/空きメモリを確認して再試行してください。",
        )
    return store.create_sound(
        prompt_original=prompt_original,
        prompt_en=prompt_en,
        source=source,
        mode=mode,
        duration_s=audio.shape[0] / sample_rate,
        sample_rate=sample_rate,
        audio=audio,
        name=body.name,
        preset_label=preset["label"] if preset else None,
        seed=seed_used,
        steps=body.steps or 8,
        cfg_scale=body.cfg_scale or 1.0,
        negative_prompt=negative_prompt_en,
    )


@router.get("/sounds")
async def list_sounds():
    return store.list_sounds()


@router.get("/sounds/{sound_id}")
async def get_sound(sound_id: str):
    sound = store.get_sound(sound_id)
    if not sound:
        raise HTTPException(404, "sound not found")
    return sound


@router.get("/sounds/{sound_id}/audio")
async def get_audio(sound_id: str, download: int = Query(0)):
    sound = store.get_sound(sound_id)
    if not sound or not store.wav_path(sound_id).exists():
        raise HTTPException(404, "audio file not found")
    headers = (
        {
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(sound['name'] + '.wav')}"
        }
        if download
        else None
    )
    return FileResponse(
        store.wav_path(sound_id), media_type="audio/wav", headers=headers
    )


@router.patch("/sounds/{sound_id}")
async def rename_sound(sound_id: str, body: RenameRequest):
    sound = store.rename_sound(sound_id, body.name)
    if not sound:
        raise HTTPException(404, "sound not found")
    return sound


@router.delete("/sounds/{sound_id}", status_code=204)
async def delete_sound(sound_id: str):
    if not store.delete_sound(sound_id):
        raise HTTPException(404, "sound not found")


@router.post("/sounds/{sound_id}/cut")
async def cut_sound(sound_id: str, body: CutRequest):
    try:
        sound = store.cut_sound(sound_id, body.start_s, body.end_s)
    except store.CutError as exc:
        raise HTTPException(400, str(exc))
    if not sound:
        raise HTTPException(404, "sound not found")
    return sound


@router.post("/sounds/{sound_id}/gain")
async def gain_sound(sound_id: str, body: GainRequest):
    try:
        sound = store.gain_sound(sound_id, body.gain_db, body.normalize)
    except store.GainError as exc:
        raise HTTPException(400, str(exc))
    if not sound:
        raise HTTPException(404, "sound not found")
    return sound


@router.post("/sounds/{sound_id}/undo")
async def undo_sound(sound_id: str):
    try:
        sound = store.undo_sound(sound_id)
    except FileNotFoundError:
        raise HTTPException(404, "no backup available")
    if not sound:
        raise HTTPException(404, "sound not found")
    return sound
