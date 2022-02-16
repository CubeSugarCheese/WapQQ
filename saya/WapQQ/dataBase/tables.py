from sqlalchemy import MetaData, Table, Column, Integer, String, Float


metadata = MetaData()
AccountTable = Table(
    "account",
    metadata,
    Column("_id", Integer, primary_key=True),
    Column("accountID", Integer),
    Column("name", String),
)

MemberTable = Table(
    "member",
    metadata,
    Column("_id", Integer, primary_key=True),
    Column("accountID", Integer),
    Column("groupID", Integer),
    Column("name", String),
)

GroupTable = Table(
    "group",
    metadata,
    Column("_id", Integer, primary_key=True),
    Column("groupID", Integer),
    Column("name", String),
)

FriendMessageTable = Table(
    "FriendMessage",
    metadata,
    Column("_id", Integer, primary_key=True),
    Column("senderID", Integer),
    Column("friendID", Integer),
    Column("timestamp", Float),
    Column("context", String)
)

GroupMessageTable = Table(
    "GroupMessage",
    metadata,
    Column("_id", Integer, primary_key=True),
    Column("senderID", Integer),
    Column("groupID", Integer),
    Column("timestamp", Float),
    Column("context", String)
)