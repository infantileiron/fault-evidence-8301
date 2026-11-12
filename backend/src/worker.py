import time,logging
from pathlib import Path
from .config.database import Session
from .utils.queue import client,QUEUE
from .services import run_service,plan_service
heartbeat=Path("/artifacts/worker-heartbeat")
while True:
 try:
  heartbeat.touch()
  item=client().blpop(QUEUE,timeout=2)
  if item:
   message=item[1]
   with Session() as db:
    if message.startswith('plan:'):plan_service.compute(db,message[5:])
    else:run_service.compute(db,message)
 except Exception:logging.exception("Worker error");time.sleep(2)
