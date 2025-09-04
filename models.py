import sqlalchemy
from sqlalchemy import Column, Integer, String, Table, MetaData


metadata = MetaData()


items = Table(
    "items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("type", String),
    Column("name", String),
    Column("year", Integer),
)