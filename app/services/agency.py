from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from app.core import pswd_hasher
from app.models import Agency, User, UserType, Client, Writer, Designer, InviteToken
from app.schemas import AgencyCreate, AgencyFilter
from app.services.invite_token import create_invite_tokens
from app.services.user import get_profile


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
        .options(selectinload(Client.user))
        .where(Client.agency_id == agency_id)
    )
    return list(result.scalars().all())


async def get_my_writers(db: AsyncSession, agency_id) -> list[Writer]:
    if not agency_id:
        return []
    result = await db.execute(
        select(Writer)
        .options(selectinload(Writer.user))
        .where(Writer.agency_id == agency_id)
    )
    return list(result.scalars().all())


async def get_my_designers(db: AsyncSession, agency_id) -> list[Designer]:
    if not agency_id:
        return []
    result = await db.execute(
        select(Designer)
        .options(selectinload(Designer.user))
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
    await db.delete(token)
    await db.commit()


async def unlink_member_self(db: AsyncSession, member) -> None:
    if not member.agency_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário nao possui agencia",
        )

    member.agency_id = None
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


async def unlink_member_by_agency(db: AsyncSession, agency_user_id, member_id) -> None:
    profile = await get_profile(db=db, user_id=member_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado"
        )
    if not profile.agency_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario nao esta vinculado a nenhuma agencia",
        )
    if profile.agency_id != agency_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao esta vinculado a sua agencia",
        )
    profile.agency_id = None
    await db.commit()
