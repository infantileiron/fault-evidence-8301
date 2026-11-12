import json,hashlib
from uuid import uuid4
from fastapi import HTTPException
from ..models.plan import ObservationPlan
from ..models.case import EvidenceCase
from ..models.revision import CptRevision
from ..models.network import BayesNetwork
from ..utils.queue import enqueue
from .network_service import nodes
from .revision_service import rows
from .network_validation import validate_evidence
from .observation_plan import observation_plan,validate_budget,validate_costs,count_states,MAX_PLAN_STATES
def _checked_rules(db,case,budget,costs_json):
 try:costs=json.loads(costs_json)
 except (ValueError,TypeError):raise HTTPException(422,'成本JSON无法解析')
 try:
  budget=validate_budget(budget)
  revision=db.get(CptRevision,case.revision_id)
  eligible=validate_evidence(nodes(db,db.get(BayesNetwork,revision.network_id)),case.evidence,case.target,case.candidates)
  costs=validate_costs(costs,eligible)
  states=count_states(eligible,costs,budget)
  if states>MAX_PLAN_STATES:raise ValueError('计划状态空间过大（'+str(states)+'＞'+str(MAX_PLAN_STATES)+'），请缩小候选集合或预算')
 except ValueError as error:raise HTTPException(422,str(error))
 return budget,costs
def create(db,body):
 case=db.get(EvidenceCase,body.case_id)
 if not case:raise HTTPException(422,'证据案例不存在')
 budget,costs=_checked_rules(db,case,body.budget,body.costs_json)
 row=ObservationPlan(id=str(uuid4()),case_id=case.id,budget=budget,costs=costs,status='queued',result={},error='');db.add(row);db.commit()
 try:enqueue('plan:'+row.id)
 except Exception:
  row.status='failed';row.error='Redis队列不可用，请重试';db.commit();raise HTTPException(503,row.error)
 return row
def compute(db,ident):
 row=db.get(ObservationPlan,ident)
 if not row or row.status not in ['queued','running']:return
 row.status='running';db.commit()
 try:
  case=db.get(EvidenceCase,row.case_id);revision=db.get(CptRevision,case.revision_id);network=db.get(BayesNetwork,revision.network_id);graph=nodes(db,network);cpt=rows(db,revision)
  snapshot={'nodes':graph,'cpt':cpt,'evidence':case.evidence,'target':case.target,'candidates':case.candidates,'costs':row.costs,'budget':row.budget,'revision_id':revision.id,'version':revision.version}
  analysis=observation_plan(graph,cpt,case.evidence,case.target,row.budget,row.costs,case.candidates)
  fingerprint=hashlib.sha256(json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  row.result={'network_name':network.name,'revision_name':revision.name,'version':revision.version,'case_name':case.name,'snapshot':snapshot,'analysis':analysis,'input_sha256':fingerprint,'assumptions':'只按给定模拟DAG/CPT与正整数成本规则安排观测；期望剩余熵最低不等于现实维修收益，不输出真实检查或维修指令。'}
  row.baseline_entropy=analysis['baseline_entropy'];row.expected_remaining_entropy=analysis['expected_remaining_entropy']
  row.status='completed';db.commit()
 except Exception as error:
  db.rollback();row=db.get(ObservationPlan,ident);row.status='failed';row.error=str(error)[:1000];db.commit()
