from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = 'postgresql+psycopg2://fmtm:fmtm@db:5432' #TODO don't hardcode this

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
FmtmMetadata = Base.metadata

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()