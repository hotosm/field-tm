# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Logic for user routes."""


from sqlalchemy.orm import Session

from ..db import db_models
from . import user_schemas

# --------------
# ---- CRUD ----
# --------------


async def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users."""
    return db.query(db_models.DbUser).offset(skip).limit(limit).all()


async def get_user(db: Session, user_id: int):
    """Get a single user by user id."""
    return db.query(db_models.DbUser).filter(db_models.DbUser.id == user_id).first()


async def get_user_by_username(db: Session, username: str):
    """Get a single user by username."""
    return (
        db.query(db_models.DbUser).filter(db_models.DbUser.username == username).first()
    )


async def get_user_role_by_user_id(db: Session, user_id: int):
    """Return the user role for a given user ID."""
    db_user_role = (
        db.query(db_models.DbUserRoles)
        .filter(db_models.DbUserRoles.user_id == user_id)
        .first()
    )
    if db_user_role:
        return db_user_role.role.value
    return None


async def create_user_roles(user_role: user_schemas.UserRoles, db: Session):
    """Assign a user a role."""
    db_user_role = db_models.DbUserRoles(
        user_id=user_role.user_id,
        role=user_role.role,
        organization_id=user_role.organization_id,
        project_id=user_role.project_id,
    )

    db.add(db_user_role)
    db.commit()
    db.refresh(db_user_role)
    return db_user_role
