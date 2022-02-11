from sqlalchemy import MetaData, Table, Column, Integer, String
import databases

DATABASE_URL = "sqlite:///./data.db"
database = databases.Database(DATABASE_URL)
metadata = MetaData()

AccountTable = Table(
    "account",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
)

GroupTable = Table(
    "group",
    metadata,
    Column("groupID", Integer, primary_key=True),
    Column("groupName", String),
)

