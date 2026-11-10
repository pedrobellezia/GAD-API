from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import CustomAppError, CustomErrorType
from app.models import (
    Client,
    Media,
    Post,
    PostMedia,
    PostStatus,
    User,
    UserType,
    Writer,
)
from app.schemas import (
    PostCreate,
    PostFilter,
    PostMediaCreate,
    PostStatusUpdate,
    PostUpdate,
    PostWriterUpdate,
)
from app.services.audit_log import record_audit


async def _validate_post_medias(
    db: AsyncSession,
    agency_id: UUID | None,
    media_items: list[PostMediaCreate],
) -> list[tuple[Media, int]]:
    seen_media_ids: set[UUID] = set()
    seen_positions: set[int] = set()
    validated: list[tuple[Media, int]] = []

    for media_item in media_items:
        if media_item.position < 0:
            raise CustomAppError(
                message="A posição da mídia deve ser maior ou igual a zero",
                error_type=CustomErrorType.bad_request,
            )
        if media_item.media_id in seen_media_ids:
            raise CustomAppError(
                message="Não é permitido repetir a mesma mídia no post",
                error_type=CustomErrorType.bad_request,
            )
        if media_item.position in seen_positions:
            raise CustomAppError(
                message="Não é permitido repetir a mesma posição de mídia no post",
                error_type=CustomErrorType.bad_request,
            )
        seen_media_ids.add(media_item.media_id)
        seen_positions.add(media_item.position)

        media = await db.scalar(select(Media).where(Media.id == media_item.media_id))
        if not media or media.agency_id != agency_id:
            raise CustomAppError(
                message=f"Mídia {media_item.media_id} é inválida ou não pertence à agência",
                error_type=CustomErrorType.bad_request,
            )
        validated.append((media, media_item.position))

    return validated


async def get_posts(
    db: AsyncSession,
    user: User,
    filters: PostFilter,
) -> list[Post]:
    query = select(Post).options(
        selectinload(Post.medias).selectinload(PostMedia.media),
        selectinload(Post.comments),
    )

    # Permissões de Visibilidade (RN-16, RN-17)
    if user.type == UserType.agency:
        query = query.where(Post.agency_id == user.id)

    elif user.type == UserType.writer:
        if not user.writer or not user.writer.agency_id:
            return []
        query = query.where(Post.agency_id == user.writer.agency_id)

    elif user.type == UserType.designer:
        if not user.designer or not user.designer.agency_id:
            return []
        query = query.where(Post.agency_id == user.designer.agency_id)

    elif user.type == UserType.client:
        query = query.where(
            Post.client_id == user.id,
            Post.status != PostStatus.draft,
        )

    else:
        return []

    query = filters.apply_filters(query)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def get_post_by_id(
    db: AsyncSession,
    post_id: UUID,
    user: User | None = None,
) -> Post:
    post = await db.scalar(
        select(Post)
        .options(
            selectinload(Post.medias).selectinload(PostMedia.media),
            selectinload(Post.comments),
        )
        .where(Post.id == post_id)
        .execution_options(populate_existing=True)
    )

    if not post:
        raise CustomAppError(
            message="Post não encontrado",
            error_type=CustomErrorType.not_found,
        )

    # Validar visibilidade para o usuário atual
    if user:
        if user.type == UserType.agency and post.agency_id != user.id:
            raise CustomAppError(
                message="Post não encontrado",
                error_type=CustomErrorType.not_found,
            )
        elif user.type == UserType.writer:
            if not user.writer or post.agency_id != user.writer.agency_id:
                raise CustomAppError(
                    message="Post não encontrado",
                    error_type=CustomErrorType.not_found,
                )
        elif user.type == UserType.designer:
            if not user.designer or post.agency_id != user.designer.agency_id:
                raise CustomAppError(
                    message="Post não encontrado",
                    error_type=CustomErrorType.not_found,
                )
        elif user.type == UserType.client and (
            post.client_id != user.id or post.status == PostStatus.draft
        ):
            raise CustomAppError(
                message="Post não encontrado",
                error_type=CustomErrorType.not_found,
            )

    return post


async def create_post(
    db: AsyncSession,
    user: User,
    post_data: PostCreate,
) -> Post:
    # RN-14: Apenas Redatores vinculados a uma agência podem criar posts
    if user.type != UserType.writer or not user.writer or not user.writer.agency_id:
        raise CustomAppError(
            message="Apenas redatores vinculados a uma agência podem criar posts",
            error_type=CustomErrorType.forbidden,
        )

    agency_id = user.writer.agency_id

    # Verificar se o cliente existe e pertence à mesma agência
    client = await db.scalar(select(Client).where(Client.id == post_data.client_id))
    if not client or client.agency_id != agency_id:
        raise CustomAppError(
            message="Cliente informado é inválido ou não pertence à agência",
            error_type=CustomErrorType.bad_request,
        )

    new_post = Post(
        title=post_data.title,
        content=post_data.content,
        client_id=post_data.client_id,
        agency_id=agency_id,
        writer_id=user.id,
    )
    db.add(new_post)
    await db.flush()

    if post_data.medias:
        # RN-10: Verificar se as mídias existem, pertencem à agência e não possuem duplicatas
        validated_medias = await _validate_post_medias(db, agency_id, post_data.medias)
        for media, position in validated_medias:
            post_media = PostMedia(
                post_id=new_post.id,
                media_id=media.id,
                position=position,
            )
            db.add(post_media)

    await record_audit(
        db,
        user=user,
        action="create",
        resource_type="post",
        resource_id=new_post.id,
        resource_name=new_post.title,
        message=f"{user.name} criou o post '{new_post.title}'.",
        agency_id=agency_id,
    )
    await db.commit()
    return await get_post_by_id(db, new_post.id)


async def update_post(
    db: AsyncSession,
    user: User,
    post_id: UUID,
    post_data: PostUpdate,
) -> Post:
    post = await get_post_by_id(db, post_id, user=user)

    # RN-15: Apenas a agência responsável ou o redator autor podem manipular o post
    if user.type == UserType.writer and post.writer_id != user.id:
        raise CustomAppError(
            message="Você não tem permissão para alterar este post",
            error_type=CustomErrorType.forbidden,
        )
    elif user.type == UserType.agency and post.agency_id != user.id:
        raise CustomAppError(
            message="Você não tem permissão para alterar este post",
            error_type=CustomErrorType.forbidden,
        )
    elif user.type not in (UserType.writer, UserType.agency):
        raise CustomAppError(
            message="Você não tem permissão para alterar este post",
            error_type=CustomErrorType.forbidden,
        )

    # RN-21 / RNF-05: Controle de Concorrência
    if post.version != post_data.version:
        raise CustomAppError(
            message="O post foi modificado por outro usuário. Recarregue e tente novamente.",
            error_type=CustomErrorType.conflict,
        )

    # RN-20: Imutabilidade de posts em estados finais
    if post.status in (PostStatus.denied, PostStatus.published):
        raise CustomAppError(
            message="Posts negados ou publicados não podem ser alterados",
            error_type=CustomErrorType.bad_request,
        )

    previous_title = post.title
    previous_content = post.content
    previous_client_id = post.client_id
    previous_status = post.status
    target_title = (
        post_data.title if post_data.title is not None else previous_title
    )
    audit_events: list[tuple[str, str]] = []

    new_client = None
    previous_client_name: str | None = None
    if "client_id" in post_data.model_fields_set:
        if user.type != UserType.agency:
            raise CustomAppError(
                message="Apenas a agência pode alterar o destinatário do post",
                error_type=CustomErrorType.forbidden,
            )

        if post_data.client_id is not None:
            new_client = await db.scalar(
                select(Client)
                .options(selectinload(Client.user))
                .where(Client.id == post_data.client_id)
            )
            if not new_client or new_client.agency_id != post.agency_id:
                raise CustomAppError(
                    message="Cliente informado é inválido ou não pertence à agência",
                    error_type=CustomErrorType.bad_request,
                )

        if post_data.client_id != previous_client_id and previous_client_id is not None:
            previous_client_user = await db.scalar(
                select(User).where(User.id == previous_client_id)
            )
            previous_client_name = (
                previous_client_user.name
                if previous_client_user
                else str(previous_client_id)
            )

    medias_changed = False
    if post_data.medias is not None:
        old_medias_list = list(post.medias)
        old_aliases = {
            pm.media_id: pm.media.alias for pm in old_medias_list if pm.media
        }
        old_positions = {pm.media_id: pm.position for pm in old_medias_list}

        validated_medias = await _validate_post_medias(
            db, post.agency_id, post_data.medias
        )
        new_aliases: dict[UUID, str] = {
            media.id: media.alias for media, _ in validated_medias
        }
        new_positions: dict[UUID, int] = {
            media.id: position for media, position in validated_medias
        }
        medias_changed = old_positions != new_positions

        if medias_changed:
            # Remover mídias antigas do post e efetivar DELETE antes de inserir as novas
            for existing_media in old_medias_list:
                await db.delete(existing_media)
            await db.flush()

            for media, position in validated_medias:
                post_media = PostMedia(
                    post_id=post.id,
                    media_id=media.id,
                    position=position,
                )
                db.add(post_media)

    if "client_id" in post_data.model_fields_set:
        post.client_id = post_data.client_id
        if post_data.client_id != previous_client_id:
            if previous_client_id is not None:
                audit_events.append(
                    (
                        "recipient_remove",
                        f"{user.name} retirou o cliente '{previous_client_name}' "
                        f"do post '{target_title}'.",
                    )
                )
            if new_client is not None:
                audit_events.append(
                    (
                        "recipient_add",
                        f"{user.name} adicionou o cliente '{new_client.user.name}' "
                        f"no post '{target_title}'.",
                    )
                )

    if post_data.title is not None:
        post.title = post_data.title
        if post.title != previous_title:
            audit_events.append(
                (
                    "title_change",
                    f"{user.name} alterou o título do post de "
                    f"'{previous_title}' para '{post.title}'.",
                )
            )
    if post_data.content is not None:
        post.content = post_data.content
        if post.content != previous_content:
            audit_events.append(
                (
                    "content_change",
                    f"{user.name} alterou o conteúdo do post '{post.title}'.",
                )
            )

    if post_data.medias is not None:
        if medias_changed:
            post.updated_at = datetime.now(UTC)

        for media_id, alias in old_aliases.items():
            if media_id not in new_aliases:
                audit_events.append(
                    (
                        "media_remove",
                        f"{user.name} retirou a mídia '{alias}' do post '{post.title}'.",
                    )
                )

        for media_id, alias in new_aliases.items():
            if media_id not in old_aliases:
                audit_events.append(
                    (
                        "media_add",
                        f"{user.name} incluiu a mídia '{alias}' no post '{post.title}'.",
                    )
                )

        if (
            set(old_aliases.keys()) == set(new_aliases.keys())
            and old_positions != new_positions
        ):
            audit_events.append(
                (
                    "media_reorder",
                    f"{user.name} reordenou as mídias do post '{post.title}'.",
                )
            )

    removed_client = (
        "client_id" in post_data.model_fields_set and post_data.client_id is None
    )
    removed_all_medias = post_data.medias is not None and not post_data.medias

    if removed_client or removed_all_medias:
        if post.status in (PostStatus.review, PostStatus.approved):
            post.status = PostStatus.draft
    elif previous_status == PostStatus.approved and audit_events:
        post.status = PostStatus.review

    for action_name, event_message in audit_events:
        await record_audit(
            db,
            user=user,
            action=action_name,
            resource_type="post",
            resource_id=post.id,
            resource_name=post.title,
            message=event_message,
        )

    if post.status != previous_status:
        await record_audit(
            db,
            user=user,
            action="status_change",
            resource_type="post",
            resource_id=post.id,
            resource_name=post.title,
            message=(
                f"{user.name} alterou o status do post '{post.title}' "
                f"de '{previous_status}' para '{post.status}'."
            ),
        )

    await db.commit()
    await db.refresh(post, ["medias", "comments"])
    return await get_post_by_id(db, post.id)


async def transition_post_status(
    db: AsyncSession,
    user: User,
    post_id: UUID,
    status_data: PostStatusUpdate,
) -> Post:
    post = await get_post_by_id(db, post_id, user=user)

    if post.version != status_data.version:
        raise CustomAppError(
            message="O post foi modificado por outro usuário. Recarregue e tente novamente.",
            error_type=CustomErrorType.conflict,
        )

    current_status = post.status
    next_status = status_data.status

    if current_status in (PostStatus.denied, PostStatus.published):
        raise CustomAppError(
            message="Posts negados ou publicados não podem ter o status alterado",
            error_type=CustomErrorType.bad_request,
        )

    allowed_transitions = {
        PostStatus.draft: {PostStatus.review},
        PostStatus.review: {PostStatus.approved, PostStatus.denied, PostStatus.draft},
        PostStatus.approved: {PostStatus.published, PostStatus.draft},
    }
    if next_status not in allowed_transitions.get(current_status, set()):
        raise CustomAppError(
            message=f"Transição de {current_status} para {next_status} não permitida",
            error_type=CustomErrorType.bad_request,
        )

    if next_status != PostStatus.draft and not post.medias:
        raise CustomAppError(
            message="O post precisa ter pelo menos uma mídia para entrar em revisão",
            error_type=CustomErrorType.bad_request,
        )

    if next_status != PostStatus.draft and post.client_id is None:
        raise CustomAppError(
            message="O post precisa ter um cliente destinatário para entrar em revisão",
            error_type=CustomErrorType.bad_request,
        )

    if next_status in (PostStatus.approved, PostStatus.denied):
        if user.type != UserType.client or post.client_id != user.id:
            raise CustomAppError(
                message="Apenas o cliente do post pode aprovar ou reprovar",
                error_type=CustomErrorType.forbidden,
            )
    elif user.type not in (UserType.agency, UserType.writer):
        raise CustomAppError(
            message="Apenas a agência ou o redator podem alterar este status",
            error_type=CustomErrorType.forbidden,
        )
    elif user.type == UserType.writer and post.writer_id != user.id:
        raise CustomAppError(
            message="Apenas o redator autor pode alterar este status",
            error_type=CustomErrorType.forbidden,
        )
    elif user.type == UserType.agency and post.agency_id != user.id:
        raise CustomAppError(
            message="Apenas a agência responsável pode alterar este status",
            error_type=CustomErrorType.forbidden,
        )

    post.status = next_status
    await record_audit(
        db,
        user=user,
        action="status_change",
        resource_type="post",
        resource_id=post.id,
        resource_name=post.title,
        message=(
            f"{user.name} alterou o status do post '{post.title}' "
            f"de '{current_status}' para '{next_status}'."
        ),
    )
    await db.commit()
    return await get_post_by_id(db, post.id)


async def update_post_writer(
    db: AsyncSession,
    user: User,
    post_id: UUID,
    writer_data: PostWriterUpdate,
) -> Post:
    post = await get_post_by_id(db, post_id, user=user)
    previous_writer_id = post.writer_id

    if user.type != UserType.agency or post.agency_id != user.id:
        raise CustomAppError(
            message="Apenas a agência responsável pode alterar a autoria do post",
            error_type=CustomErrorType.forbidden,
        )

    if post.version != writer_data.version:
        raise CustomAppError(
            message="O post foi modificado por outro usuário. Recarregue e tente novamente.",
            error_type=CustomErrorType.conflict,
        )

    if post.status in (PostStatus.denied, PostStatus.published):
        raise CustomAppError(
            message="Posts negados ou publicados não podem ser alterados",
            error_type=CustomErrorType.bad_request,
        )

    previous_writer_user = (
        await db.scalar(select(User).where(User.id == previous_writer_id))
        if previous_writer_id is not None
        else None
    )
    previous_writer_name = (
        previous_writer_user.name if previous_writer_user else str(previous_writer_id)
    )

    writer = None
    if writer_data.writer_id is None:
        post.writer_id = None
    else:
        writer = await db.scalar(
            select(Writer)
            .options(selectinload(Writer.user))
            .where(
                Writer.id == writer_data.writer_id,
                Writer.agency_id == post.agency_id,
            )
        )
        if not writer:
            raise CustomAppError(
                message="Redator inválido ou não vinculado à agência do post",
                error_type=CustomErrorType.bad_request,
            )
        post.writer_id = writer.id

    if post.writer_id != previous_writer_id:
        if previous_writer_id is not None:
            await record_audit(
                db,
                user=user,
                action="author_remove",
                resource_type="post",
                resource_id=post.id,
                resource_name=post.title,
                message=(
                    f"{user.name} retirou a autoria do redator '{previous_writer_name}' "
                    f"do post '{post.title}'."
                ),
            )
        if writer is not None:
            await record_audit(
                db,
                user=user,
                action="author_add",
                resource_type="post",
                resource_id=post.id,
                resource_name=post.title,
                message=(
                    f"{user.name} adicionou a autoria do redator '{writer.user.name}' "
                    f"no post '{post.title}'."
                ),
            )
    await db.commit()
    return await get_post_by_id(db, post.id)


async def delete_post(
    db: AsyncSession,
    user: User,
    post_id: UUID,
) -> None:
    post = await get_post_by_id(db, post_id, user=user)

    # RN-15: Permissões de manipulação
    if user.type == UserType.writer and post.writer_id != user.id:
        raise CustomAppError(
            message="Você não tem permissão para excluir este post",
            error_type=CustomErrorType.forbidden,
        )
    elif user.type == UserType.agency and post.agency_id != user.id:
        raise CustomAppError(
            message="Você não tem permissão para excluir este post",
            error_type=CustomErrorType.forbidden,
        )
    elif user.type not in (UserType.writer, UserType.agency):
        raise CustomAppError(
            message="Você não tem permissão para excluir este post",
            error_type=CustomErrorType.forbidden,
        )

    if post.status in (PostStatus.denied, PostStatus.published):
        raise CustomAppError(
            message="Posts negados ou publicados não podem ser excluídos",
            error_type=CustomErrorType.bad_request,
        )

    await record_audit(
        db,
        user=user,
        action="delete",
        resource_type="post",
        resource_id=post.id,
        resource_name=post.title,
        message=f"{user.name} excluiu o post '{post.title}'.",
        agency_id=post.agency_id,
    )
    await db.delete(post)
    await db.commit()
