from fastapi import APIRouter,Depends,Response
from ..config.database import get_db
from ..utils.auth import current,write_user,admin
from ..schemas.plan import PlanCreate
from ..controllers import plan_controller as controller
router=APIRouter(prefix='/plans',tags=['plans'])
@router.get('')
def listing(db=Depends(get_db),user=Depends(current)):return controller.list_all(db)
@router.get('/{ident}')
def detail(ident:str,db=Depends(get_db),user=Depends(current)):return controller.detail(db,ident)
@router.post('',status_code=201)
def create(body:PlanCreate,db=Depends(get_db),user=Depends(write_user)):return controller.create(db,body)
