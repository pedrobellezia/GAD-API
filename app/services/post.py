from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import CustomAppError, CustomErrorType
from app.models import Client, Media, Post, PostMedia, PostStatus, User, UserType
from app.schemas import PostCreate, PostFilter, PostStatusUpdate, PostUpdate


async def get_posts(
    db: AsyncSession,
    user: User,
    filters: PostFilter,
) -> list[Post]:
    query = select(Post).options(
        selectinload(Post.medias).selectinload(PostMedia.media),
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
        query = query.where(Post.client_id == user.id)

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
        )
        .where(Post.id == post_id)
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
        elif user.type == UserType.client and post.client_id != user.id:
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
        # RN-10: Verificar se as mídias existem e pertencem à agência
        for media_item in post_data.medias:
            media = await db.scalar(
                select(Media).where(Media.id == media_item.media_id)
            )
            if not media or media.agency_id != agency_id:
                raise CustomAppError(
                    message=f"Mídia {media_item.media_id} é inválida ou não pertence à agência",
                    error_type=CustomErrorType.bad_request,
                )

            post_media = PostMedia(
                post_id=new_post.id,
                media_id=media_item.media_id,
                position=media_item.position,
            )
            db.add(post_media)

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

    # Se estiver alterando o cliente, validar pertencimento à agência
    if post_data.client_id and post_data.client_id != post.client_id:
        client = await db.scalar(select(Client).where(Client.id == post_data.client_id))
        if not client or client.agency_id != post.agency_id:
            raise CustomAppError(
                message="Cliente informado é inválido ou não pertence à agência",
                error_type=CustomErrorType.bad_request,
            )
        post.client_id = post_data.client_id

    if post_data.title is not None:
        post.title = post_data.title
    if post_data.content is not None:
        post.content = post_data.content

    if post_data.medias is not None:
        # Remover mídias antigas do post
        for existing_media in list(post.medias):
            await db.delete(existing_media)

        # Adicionar novas mídias validadas
        for media_item in post_data.medias:
            media = await db.scalar(
                select(Media).where(Media.id == media_item.media_id)
            )
            if not media or media.agency_id != post.agency_id:
                raise CustomAppError(
                    message=f"Mídia {media_item.media_id} é inválida ou não pertence à agência",
                    error_type=CustomErrorType.bad_request,
                )
            post_media = PostMedia(
                post_id=post.id,
                media_id=media_item.media_id,
                position=media_item.position,
            )
            db.add(post_media)

    await db.commit()
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

    if next_status == PostStatus.review and not post.medias:
        raise CustomAppError(
            message="O post precisa ter pelo menos uma mídia para entrar em revisão",
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

    await db.delete(post)
    await db.commit()
