from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import BigInteger, Enum as SQLEnum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class MediaType(str, Enum):
    image = "IMAGE"
    video = "VIDEO"


class StorageProvider(str, Enum):
    local = "local"
    s3 = "s3"
    gcs = "gcs"
    azure = "azure"


class Media(Base):
    __tablename__ = "medias"

    # Identificador único do arquivo de mídia.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    # Tipo do arquivo armazenado: imagem ou vídeo.
    media_type: Mapped[MediaType] = mapped_column(
        SQLEnum(MediaType, name="mediatype"),
        nullable=False,
        index=True,
    )

    # Onde o arquivo está salvo: local, S3, GCS, Azure etc.
    storage_provider: Mapped[StorageProvider] = mapped_column(
        SQLEnum(StorageProvider, name="storageprovider"),
        default=StorageProvider.local,
        nullable=False,
        index=True,
    )

    # Chave/caminho lógico do arquivo no storage.
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)

    # Nome original do arquivo enviado pelo usuário.
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Tipo MIME do arquivo, ex.: image/jpeg, video/mp4.
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Tamanho do arquivo em bytes.
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Hash/checksum para validação de integridade e deduplicação.
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    post_medias = relationship("PostMedia", back_populates="media")
