"""Miniaturas das mídias (imagens e vídeos), usadas nas listagens e nos posts.

A miniatura fica em ``LOCAL_STORAGE/thumbs/<nome do arquivo>.webp`` e é gerada sob
demanda no primeiro acesso, o que também cobre as mídias enviadas antes deste recurso.
"""

import asyncio
import logging
import os
from pathlib import Path
from uuid import uuid4

import av
from PIL import Image, ImageOps, ImageStat

from app.core.config import LOCAL_STORAGE_PATH
from app.exceptions import CustomAppError, CustomErrorType
from app.models import Media, MediaType

logger = logging.getLogger(__name__)

THUMBNAIL_DIR = LOCAL_STORAGE_PATH / "thumbs"
# Lado maior em pixels: nítido nos cards (~350px de largura em telas 2x) e leve nas grades
THUMBNAIL_MAX_SIDE = 640
THUMBNAIL_QUALITY = 80
# Quadro usado como capa do vídeo: evita o primeiro quadro, muitas vezes preto (fade-in)
VIDEO_FRAME_SECONDS = 1.0
VIDEO_FRAME_FRACTION = 0.1
# Limite de quadros decodificados após o seek, para não varrer o vídeo inteiro
VIDEO_MAX_DECODED_FRAMES = 240
# Brilho médio (0-255) abaixo do qual o quadro é considerado "preto" e é pulado
VIDEO_DARK_THRESHOLD = 16


def get_thumbnail_path(filename: str) -> Path:
    root = THUMBNAIL_DIR.resolve()
    path = (root / f"{Path(filename).stem}.webp").resolve()
    if path.parent != root:
        raise CustomAppError(
            message="Caminho de miniatura inválido",
            error_type=CustomErrorType.internal_server_error,
        )
    return path


def _video_frame(source: Path) -> Image.Image:
    with av.open(str(source)) as container:
        stream = next(s for s in container.streams if s.type == "video")
        duration = None
        if stream.duration is not None and stream.time_base is not None:
            duration = float(stream.duration * stream.time_base)
        elif container.duration is not None:
            duration = container.duration / av.time_base

        target_seconds = VIDEO_FRAME_SECONDS
        if duration:
            target_seconds = min(VIDEO_FRAME_SECONDS, duration * VIDEO_FRAME_FRACTION)
        if target_seconds > 0 and stream.time_base:
            # O seek cai no quadro-chave anterior; decodifica até chegar ao alvo
            container.seek(int(target_seconds / stream.time_base), stream=stream)

        # A partir do alvo, usa o primeiro quadro que não seja escuro demais (fade-in).
        # Se todos forem escuros até o limite, fica com o último decodificado.
        chosen = None
        last = None
        for index, frame in enumerate(container.decode(stream)):
            if index >= VIDEO_MAX_DECODED_FRAMES:
                break
            last = frame
            if (frame.time or 0) < target_seconds:
                continue
            chosen = frame.to_image()
            if ImageStat.Stat(chosen.convert("L")).mean[0] >= VIDEO_DARK_THRESHOLD:
                break
        if chosen is None:
            # Sem timestamps confiáveis: usa o último quadro decodificado
            if last is None:
                raise ValueError("Vídeo sem quadros decodificáveis")
            chosen = last.to_image()
        return chosen


def _open_image(source: Path, media_type: MediaType) -> Image.Image:
    if media_type == MediaType.video:
        return _video_frame(source)
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        image.load()
        return image


def _render_thumbnail(source: Path, target: Path, media_type: MediaType) -> None:
    # Grava num arquivo temporário e renomeia: requisições simultâneas nunca leem
    # uma miniatura pela metade.
    tmp = target.with_name(f".{target.stem}.{uuid4().hex}.tmp")
    try:
        image = _open_image(source, media_type)
        image.thumbnail(
            (THUMBNAIL_MAX_SIDE, THUMBNAIL_MAX_SIDE), Image.Resampling.LANCZOS
        )
        if image.mode not in ("RGB", "RGBA"):
            has_alpha = image.mode in ("LA", "PA") or "transparency" in image.info
            image = image.convert("RGBA" if has_alpha else "RGB")
        image.save(tmp, "WEBP", quality=THUMBNAIL_QUALITY, method=4)
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)


async def ensure_thumbnail(media: Media) -> Path | None:
    """Retorna o caminho da miniatura, gerando-a se preciso.

    Retorna ``None`` se o arquivo original não existir ou a geração falhar; quem
    chama decide o fallback (ex.: servir o original da imagem).
    """
    target = get_thumbnail_path(media.filename)
    if target.is_file():
        return target

    # Import local: media.py importa este módulo para remover a miniatura na exclusão
    from app.services.media import get_media_path

    source = get_media_path(media.filename)
    if not source.is_file():
        return None

    try:
        await asyncio.to_thread(THUMBNAIL_DIR.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(_render_thumbnail, source, target, media.media_type)
    except Exception:
        logger.warning("Falha ao gerar miniatura da mídia %s", media.id, exc_info=True)
        return None
    return target


async def remove_thumbnail(filename: str) -> None:
    try:
        path = get_thumbnail_path(filename)
        await asyncio.to_thread(path.unlink, missing_ok=True)
    except Exception:
        # A mídia já foi removida; uma miniatura órfã não deve falhar a exclusão
        logger.warning("Falha ao remover miniatura de %s", filename, exc_info=True)
