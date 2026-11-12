"""Budgeted adaptive observation planning via dynamic programming.

V(E,b) = min( H(Q|E),  min over affordable X of  sum_x P(X=x|E) * V(E+{X=x}, b-cost_X) )

The stop action is available at every node, so the policy may end a path
early; observed nodes leave the candidate set and costs never exceed the
remaining budget. Strict zero-probability branches are skipped; branches
with finite log probability whose weight underflows to 0 are still expanded.
"""
import math
from .network_validation import validate_evidence
from .variable_elimination import infer
from .information_gain import entropy

MAX_PLAN_STATES=6000
STOP_EPSILON=1e-12

def validate_budget(budget):
 if isinstance(budget,bool) or not isinstance(budget,int) or budget<0:raise ValueError('总预算须为非负整数')
 return budget

def validate_costs(costs,eligible):
 if not isinstance(costs,dict):raise ValueError('观测成本须为候选节点到正整数的JSON映射')
 clean={}
 for key,value in costs.items():
  if key not in eligible:raise ValueError('成本含未知或非候选节点：'+str(key))
  if isinstance(value,bool) or not isinstance(value,int) or value<1:raise ValueError('观测成本须为正整数：'+str(key))
  clean[key]=value
 missing=[node for node in eligible if node not in clean]
 if missing:raise ValueError('候选观测缺少正整数成本：'+','.join(missing))
 return clean

def count_states(eligible,costs,budget):
 memo={}
 def rec(remaining,left):
  key=(remaining,left)
  if key in memo:return memo[key]
  total=1
  for node in sorted(remaining):
   cost=costs[node]
   if cost<=left:total+=2*rec(remaining-{node},left-cost)
  memo[key]=total
  return total
 return rec(frozenset(eligible),budget)

def observation_plan(nodes,cpt,evidence,target,budget,costs,candidates=None):
 budget=validate_budget(budget)
 eligible=validate_evidence(nodes,evidence,target,candidates)
 costs=validate_costs(costs,eligible)
 states=count_states(eligible,costs,budget)
 if states>MAX_PLAN_STATES:raise ValueError('计划状态空间过大（'+str(states)+'＞'+str(MAX_PLAN_STATES)+'），请缩小候选集合或预算')
 baseline=infer(nodes,cpt,evidence,target);baseline_entropy=entropy(baseline['posterior']);baseline_entropy=0.0 if baseline_entropy==0 else baseline_entropy
 evaluated=[0]
 def solve(items,left,depth):
  evaluated[0]+=1
  current=dict(items);inference=infer(nodes,cpt,current,target);h=entropy(inference['posterior']);h=0.0 if h==0 else h  # normalize -0.0 from one-hot posteriors
  node={'evidence':current,'depth':depth,'cumulative_cost':budget-left,'remaining_budget':left,'posterior':inference['posterior'],'log_evidence':inference['log_evidence'],'evidence_probability_underflow':inference['evidence_probability_underflow'],'entropy':h,'expected_remaining_entropy':h,'decision':None,'branches':[]}
  remaining=[c for c in eligible if c not in current]
  affordable=[c for c in remaining if costs[c]<=left]
  best=h;chosen=None
  for candidate in affordable:
   cost=costs[candidate];marginal=infer(nodes,cpt,current,candidate);branches=[];terms=[]
   for p in marginal['posterior']:
    branch={'state':p['state'],'probability':p['probability'],'log_probability':p['log_probability'],'probability_underflow':p['probability_underflow'],'skipped_zero_probability':p['log_probability'] is None,'child':None}
    if p['log_probability'] is None:branches.append(branch);continue
    # A finite log probability can exponentiate to zero; the tiny positive branch is still expanded.
    child=solve(tuple(sorted(items+((candidate,p['state']),))),left-cost,depth+1)
    terms.append(p['probability']*child['expected_remaining_entropy']);branch['child']=child;branches.append(branch)
   expected=math.fsum(terms)
   if expected<best-STOP_EPSILON:best=expected;chosen={'node_id':candidate,'cost':cost,'expected_entropy':expected,'branches':branches,'marginal_log_evidence':marginal['log_evidence']}
  if chosen is None:
   reason='候选已全部观测' if not remaining else ('剩余预算不足以观测任何候选' if not affordable else '继续观测不能降低期望剩余熵，允许提前结束')
   node['decision']={'type':'stop','reason':reason}
  else:
   node['expected_remaining_entropy']=best
   node['decision']={'type':'observe','node_id':chosen['node_id'],'cost':chosen['cost'],'expected_entropy':chosen['expected_entropy'],'marginal_log_evidence':chosen['marginal_log_evidence']}
   node['branches']=chosen['branches']
  return node
 tree=solve(tuple(sorted(dict(evidence).items())),budget,0)
 tree_nodes=[0]
 def walk(node):
  tree_nodes[0]+=1
  for branch in node['branches']:
   if branch['child'] is not None:walk(branch['child'])
 walk(tree)
 return {'baseline_entropy':baseline_entropy,'expected_remaining_entropy':tree['expected_remaining_entropy'],'expected_entropy_reduction':baseline_entropy-tree['expected_remaining_entropy'],'budget':budget,'costs':costs,'candidates':eligible,'tree':tree,'tree_node_count':tree_nodes[0],'evaluated_state_count':evaluated[0],'max_evaluated_states':MAX_PLAN_STATES,'stop_epsilon':STOP_EPSILON,'entropy_base':2,'method':'finite-horizon dynamic programming over (evidence, remaining budget); stop allowed at every node','note':'V(E,b)=min(H(Q|E), Σ_x P(X=x|E)·V(E∪{X=x}, b−成本_X))，每条路径不重复观测且不超支；期望剩余熵下降不超过1e-12 bit视为无收益并提前结束。严格零概率分支跳过；log概率有限但exp下溢的极小正分支仍展开，仅浮点权重可能为0。只按给定模型与成本规则研修，不发现因果、不输出维修指令。'}
