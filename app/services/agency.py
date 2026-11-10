from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from app.core import pswd_hasher
from app.models import (
    Agency,
    Client,
    Designer,
    InviteToken,
    Media,
    Post,
    PostStatus,
    User,
    UserType,
    Writer,
)
from app.schemas import AgencyCreate, AgencyFilter
from app.services.audit_log import record_audit


async def get_agencies(db: AsyncSession, filters: AgencyFilter) -> list[Agency]:
    query = select(Agency).join(Agency.user).options(contains_eager(Agency.user))
    query = filters.apply_filters(query)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def create_agency(db: AsyncSession, agency_data: AgencyCreate) -> None:
    new_user = User(**agency_data.user.model_dump(exclude={"pswd"}))
    new_user.pswd = pswd_hasher.hash(agency_data.user.pswd)
    new_user.type = UserType.agency
    db.add(new_user)
    await db.flush()
    new_agency = Agency(id=new_user.id, cnpj=agency_data.cnpj)
    db.add(new_agency)
    await db.flush()


async def get_agency_me(db: AsyncSession, user_id) -> Agency:
    agency = await db.scalar(
        select(Agency).options(selectinload(Agency.user)).where(Agency.id == user_id)
    )
    return agency


async def get_my_clients(db: AsyncSession, agency_id) -> list[Client]:
    if not agency_id:
        return []
    result = await db.execute(
        select(Client)
        .options(
            selectinload(Client.user),
            selectinload(Client.agency).selectinload(Agency.user),
        )
        .where(Client.agency_id == agency_id)
    )
    return list(result.scalars().all())


async def get_my_writers(db: AsyncSession, agency_id) -> list[Writer]:
    if not agency_id:
        return []
    result = await db.execute(
        select(Writer)
        .options(
            selectinload(Writer.user),
            selectinload(Writer.agency).selectinload(Agency.user),
        )
        .where(Writer.agency_id == agency_id)
    )
    return list(result.scalars().all())


async def get_my_designers(db: AsyncSession, agency_id) -> list[Designer]:
    if not agency_id:
        return []
    result = await db.execute(
        select(Designer)
        .options(
            selectinload(Designer.user),
            selectinload(Designer.agency).selectinload(Agency.user),
        )
        .where(Designer.agency_id == agency_id)
    )
    return list(result.scalars().all())


async def link_member_by_token(db: AsyncSession, member, token_str: str) -> None:
    if member.agency_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuário ja vinculado a uma agencia",
        )

    token: InviteToken | None = await db.scalar(
        select(InviteToken).where(InviteToken.token == token_str).with_for_update()
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de convite invalido",
        )

    member.agency_id = token.agency_id
    await record_audit(
        db,
        user=member.user,
        action="member_link",
        resource_type="user",
        resource_id=member.id,
        resource_name=member.user.name,
        agency_id=token.agency_id,
        message=f"{member.user.name} vinculou-se à agência.",
    )
    await db.delete(token)
    await db.commit()


async def unlink_member(
    db: AsyncSession,
    member: Client | Writer | Designer,
    *,
    actor: User,
    requesting_agency_id=None,
    commit: bool = True,
) -> None:
    is_self_unlink = requesting_agency_id is None

    if not member.agency_id:
        if is_self_unlink:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não possui agencia",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario nao esta vinculado a nenhuma agencia",
        )

    if not is_self_unlink and member.agency_id != requesting_agency_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario não esta vinculado a sua agencia",
        )

    agency_id = member.agency_id
    member_name = member.user.name

    if isinstance(member, Writer):
        posts = list(
            (
                await db.scalars(
                    select(Post).where(
                        Post.writer_id == member.id,
                        Post.agency_id == agency_id,
                    )
                )
            ).all()
        )
        for post in posts:
            post.writer_id = None
            await record_audit(
                db,
                user=actor,
                action="author_remove",
                resource_type="post",
                resource_id=post.id,
                resource_name=post.title,
                agency_id=agency_id,
                message=(
                    f"{actor.name} retirou a autoria do redator "
                    f"'{member_name}' do post '{post.title}'."
                ),
            )
    elif isinstance(member, Designer):
        medias = list(
            (
                await db.scalars(
                    select(Media).where(
                        Media.designer_id == member.id,
                        Media.agency_id == agency_id,
                    )
                )
            ).all()
        )
        for media in medias:
            media.designer_id = None
            await record_audit(
                db,
                user=actor,
                action="author_remove",
                resource_type="media",
                resource_id=media.id,
                resource_name=media.alias,
                agency_id=agency_id,
                message=(
                    f"{actor.name} retirou a autoria do designer "
                    f"'{member_name}' da mídia '{media.alias}'."
                ),
            )
    elif isinstance(member, Client):
        posts = list(
            (
                await db.scalars(
                    select(Post).where(
                        Post.client_id == member.id,
                        Post.agency_id == agency_id,
                    )
                )
            ).all()
        )
        for post in posts:
            previous_status = post.status
            if post.status != PostStatus.published:
                post.client_id = None
                await record_audit(
                    db,
                    user=actor,
                    action="recipient_remove",
                    resource_type="post",
                    resource_id=post.id,
                    resource_name=post.title,
                    agency_id=agency_id,
                    message=(
                        f"{actor.name} retirou o cliente '{member_name}' "
                        f"do post '{post.title}'."
                    ),
                )
            if post.status in (PostStatus.review, PostStatus.approved):
                post.status = PostStatus.draft
                await record_audit(
                    db,
                    user=actor,
                    action="status_change",
                    resource_type="post",
                    resource_id=post.id,
                    resource_name=post.title,
                    agency_id=agency_id,
                    message=(
                        f"{actor.name} alterou o status do post '{post.title}' "
                        f"de '{previous_status}' para '{post.status}'."
                    ),
                )

    member.agency_id = None
    await record_audit(
        db,
        user=actor,
        action="member_unlink",
        resource_type="user",
        resource_id=member.id,
        resource_name=member_name,
        agency_id=agency_id,
        message=f"{actor.name} desvinculou '{member_name}' da agência.",
    )
    if commit:
        await db.commit()


async def get_member_agency(db: AsyncSession, member) -> Agency:
    agency_id = member.agency_id

    if not agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário nao possui agencia",
        )

    agency = await db.scalar(
        select(Agency).options(selectinload(Agency.user)).where(Agency.id == agency_id)
    )

    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Não foi possível encontrar a agência do usuário",
        )

    return agency
