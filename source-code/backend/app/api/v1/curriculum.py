from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.curriculum import CatalogResponse
from app.security import Principal, get_principal
from app.services.curriculum import get_catalog


router = APIRouter(tags=["curriculum"])


@router.get("/catalog", response_model=CatalogResponse)
def catalog(
    _principal: Annotated[Principal, Depends(get_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> CatalogResponse:
    return get_catalog(db)
