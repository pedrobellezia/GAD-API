from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import pswd_hasher
from app.models import Agency, User, UserType, Designer
from app.schemas.designer import DesignerCreate


async def get_designer_me(db: AsyncSession, user_id) -> Designer:
    designer = await db.scalar(
        select(Designer)
        .options(
            selectinload(Designer.user),
            selectinload(Designer.agency).selectinload(Agency.user),
        )
        .where(Designer.id == user_id)
    )

    return designer


async def create_designer(db: AsyncSession, designer_data: DesignerCreate) -> None:
    async with db.begin():
        new_user = User(**designer_data.user.model_dump(exclude={"pswd"}))
        new_user.pswd = pswd_hasher.hash(designer_data.user.pswd)
        new_user.type = UserType.designer
        db.add(new_user)
        await db.flush()

        new_designer = Designer(id=new_user.id, agency_id=designer_data.agency_id)
        db.add(new_designer)
