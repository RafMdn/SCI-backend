from fastapi import FastAPI , HTTPException , Depends , status
from pydantic import BaseModel
from typing import Annotated , Optional
import models 
from database import engine, SessionLocal 
from sqlalchemy.orm import Session

from datetime import datetime

from fastapi_mqtt.fastmqtt import FastMQTT
from fastapi import FastAPI
from fastapi_mqtt.config import MQTTConfig


app = FastAPI()


mqtt_config = MQTTConfig()

fast_mqtt = FastMQTT(config=mqtt_config)

fast_mqtt.init_app(app)

@mqtt.on_connect()
def connect(client, flags, rc, properties):
    mqtt.client.subscribe("/mqtt") #subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)

@mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print("Received message: ",topic, payload.decode(), qos, properties)
    return 0

@mqtt.subscribe("my/mqtt/topic/#")
async def message_to_topic(client, topic, payload, qos, properties):
    print("Received message to specific topic: ", topic, payload.decode(), qos, properties)

@mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print("Disconnected")

@mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print("subscribed", client, mid, qos, properties)


@app.get("/")
async def func():
    fast_mqtt.publish("/mqtt", "Hello from Fastapi") #publishing mqtt topic

    return {"result": True,"message":"Published" }


models.Base.metadata.create_all(bind = engine) 

class WorkerBase(BaseModel): 
    # id : Optional[int]
    first_name : str
    last_name : str
    rfid_code : Optional[str]
    access_status : bool

class Worker(WorkerBase):
    id: int

    class Config:
        orm_mode = True      

class AccessHistoryBase(BaseModel):
    # id : Optional[int]
    accessDate : datetime
    rfid_code : str

class AccessHistory(AccessHistoryBase):
    id: int

    class Config:
        orm_mode = True  


class SensorsBase(BaseModel):
    # id :  int
    heat : int
    gaz : bool
    fire : bool
    forcedEntry : bool
    measureTime : datetime

class Sensors(SensorsBase):
    id: int

    class Config:
        orm_mode = True  



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()   

db_dependency = Annotated [Session, Depends(get_db)]

@app.post("/addworker/" , response_model= Worker )
def addworker(worker : WorkerBase , db : db_dependency):    
    db_worker = models.Worker(
        first_name = worker.first_name,
        last_name = worker.last_name, 
        rfid_code = worker.rfid_code,
        access_status = worker.access_status,
        
        )
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return  db_worker


@app.post("/addworker/{access_id}" , response_model= Worker )
def addworkerFromAccess(access_id : int, worker : WorkerBase , db : db_dependency):    
    rfid_code = db.query(models.AccessHistory).filter(models.AccessHistory.id == access_id).first().rfid_code

    db_worker = models.Worker(
        first_name = worker.first_name,
        last_name = worker.last_name, 
        rfid_code = rfid_code,
        access_status = worker.access_status,
        
        )
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return  db_worker


@app.post("/addaccess/")
def addaccess(acces : AccessHistoryBase , db : db_dependency):    
   
    worker= db.query(models.Worker).filter(models.Worker.rfid_code == acces.rfid_code).first()
    access_status = False

    if worker is None:
        worker_id = None        
    else :
        worker_id = worker.id
        if worker.access_status == True : 
            access_status = True

    db_acces = models.AccessHistory(
        accessDate = acces.accessDate,
        rfid_code = acces.rfid_code, 
        worker_id = worker_id,
        access_status = access_status
        )
    db.add(db_acces)
    db.commit()
    db.refresh(db_acces)
    return  {"access" : "denied"} if worker_id  == None or worker.access_status == False else  {"access" : "allowed"} 





@app.get("/accesshistory/" )
def accesshistory(db : Session = Depends(get_db)):    
    access_history = db.query(models.AccessHistory).order_by(models.AccessHistory.accessDate.desc()).all()

    return  access_history



@app.get("/workers/")
def workers(db : Session = Depends(get_db)):    
    workers_list = db.query(models.Worker).all()
    return  workers_list

@app.get("/workers/{worker_id}")
def workerByID(worker_id : int , db : Session = Depends(get_db)):    
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
   
    return  worker

@app.get("/workers/accesshistory/{worker_id}/")
def workerHistoryByID(worker_id : int , db : Session = Depends(get_db)):    
    worker_history = db.query(models.AccessHistory).filter(models.AccessHistory.worker_id == worker_id).first()
    return  worker_history

@app.get("/workers/accesshistoryunknown/")
def workerHistoryByID(db : Session = Depends(get_db)):    
    unknown_workers_history = db.query(models.AccessHistory).filter(models.AccessHistory.worker_id == None ).all()
    print(unknown_workers_history)
    return  unknown_workers_history