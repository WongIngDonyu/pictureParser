from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///pictures.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    pictures = relationship("Picture", back_populates="category")

class Picture(Base):
    __tablename__ = 'picture'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    tags = Column(String)
    height = Column(Integer)
    width = Column(Integer)
    url = Column(String)
    fileName = Column(String)
    category = relationship("Category", back_populates="pictures")

def init_db():
    Base.metadata.create_all(engine)