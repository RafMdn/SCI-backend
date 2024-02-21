from sqlalchemy import Boolean, Column , Integer , String , Text , DateTime ,ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Worker(Base) :
    __tablename__ = "workers"
    id = Column(Integer , primary_key= True ,autoincrement=True)
    first_name = Column(Text)
    last_name = Column(Text)
    rfid_code = Column(String(100) , unique=True)
    access_status = Column(Boolean)

    access_history = relationship("AccessHistory", back_populates="worker")


class AccessHistory(Base):
    __tablename__ = "accesshistory"
    id = Column(Integer , primary_key=True , autoincrement= True)
    accessDate = Column(DateTime)
    rfid_code = Column(Text)
    worker_id = Column(Integer , ForeignKey("workers.id") , nullable=True)
    access_status = Column(Boolean)

    worker = relationship("Worker" , back_populates= "access_history")

class Sensors(Base) :
    __tablename__ = "sensors"
    id =  Column(Integer , primary_key= True ,autoincrement=True)
    heat = Column(Integer)
    gaz = Column(Integer)
    fire = Column(Boolean)
    forcedEntry = Column(Boolean)
    measureTime = Column(DateTime)

    
