from sqlalchemy import select
from ..models.plan import ObservationPlan
from ..models.common import serialize
from ..services import plan_service as service
from .common import require
def list_all(db):return [serialize(row) for row in db.scalars(select(ObservationPlan).order_by(ObservationPlan.created_at.desc())).all()]
def detail(db,ident):
 row=require(db,ObservationPlan,ident)
 return serialize(row)
def create(db,body):
 row=service.create(db,body)
 return serialize(row)
