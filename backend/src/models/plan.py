from sqlalchemy import String,Text,JSON,ForeignKey,Double,Integer
from sqlalchemy.orm import Mapped,mapped_column
from .common import RecordMixin
from ..config.database import Base
class ObservationPlan(RecordMixin,Base):
 __tablename__="plans"
 case_id:Mapped[str]=mapped_column(ForeignKey("cases.id"))
 budget:Mapped[int]=mapped_column(Integer)
 costs:Mapped[dict]=mapped_column(JSON)
 status:Mapped[str]=mapped_column(String(20),default="queued")
 result:Mapped[dict]=mapped_column(JSON,default=dict)
 error:Mapped[str]=mapped_column(Text,default="")
 baseline_entropy:Mapped[float|None]=mapped_column(Double,nullable=True)
 expected_remaining_entropy:Mapped[float|None]=mapped_column(Double,nullable=True)
