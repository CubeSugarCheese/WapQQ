from asyncio import AbstractEventLoop
from typing import Union

from databases import Database, core
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.element import Source
from graia.ariadne.model import Group, Friend, Member, Stranger
from sqlalchemy import create_engine
from sqlalchemy.engine.mock import MockConnection

from .tables import metadata, GroupTable, AccountTable, MemberTable, FriendMessageTable, GroupMessageTable


class DataManager:
    """数据库管理类"""
    loop: AbstractEventLoop
    DATABASE_URL: str = "sqlite:///saya/WapQQ/dataBase/data.db"
    database: core.Database = Database(DATABASE_URL)
    engine: MockConnection

    def __init__(self, loop: AbstractEventLoop):
        self.loop = loop

    async def startup(self):
        """应在开启 bot 时调用，用于开启数据库连接"""
        await self.database.connect()
        self.engine = create_engine(self.DATABASE_URL, connect_args={"check_same_thread": False})
        metadata.create_all(self.engine)  # 自动检查是否已经创建表，若无，则创建

    async def shutdown(self):
        """应在关闭 bot 时调用，用于关闭数据库连接"""
        await self.database.disconnect()

    async def has_in_groupTable(self, group: Group) -> bool:
        """检查数据库中是否已有该 Group """
        query = GroupTable.select().where(GroupTable.c.groupID == group.id)
        result = await self.database.fetch_val(query)
        if result:
            return True
        else:
            return False

    async def has_in_accountTable(self, account: Union[Friend, Stranger, Member]) -> bool:
        """检查数据库中是否已有该 Account """
        query = AccountTable.select().where(AccountTable.c.accountID == account.id)
        result = await self.database.fetch_val(query)
        if result:
            return True
        else:
            return False

    async def has_in_memberTable(self, account: Member) -> bool:
        """检查数据库中是否已有该 Member """
        query = AccountTable.select().where(MemberTable.c.accountID == account.id
                                            and MemberTable.c.groupID == account.group.id)
        result = await self.database.fetch_val(query)
        if result:
            return True
        else:
            return False

    async def addGroup(self, group: Group):
        """往数据库中添加新 Group """
        query = GroupTable.insert().values(groupID=group.id, name=group.name)
        await self.database.execute(query)

    async def addAccount(self, account: Union[Friend, Stranger, Member]):
        """往数据库中添加新 Account """
        if isinstance(account, Member):
            profile = await account.getProfile()
            query = AccountTable.insert().values(accountID=account.id, name=profile.nickname)
        else:
            query = AccountTable.insert().values(accountID=account.id, name=account.nickname)
        await self.database.execute(query)

    async def addMember(self, account: Member):
        """往数据库中添加新 Member """
        query = MemberTable.insert().values(accountID=account.id, groupID=account.group.id, name=account.name)
        await self.database.execute(query)

    async def updateGroupName(self, group: Group):
        """自动检查 GroupName 是否变化，若变化则更新数据库"""
        query = GroupTable.update().values(name=group.name).where(GroupTable.c.groupID == group.id and
                                                                  GroupTable.c.name != group.name)
        await self.database.execute(query)

    async def updateAccountName(self, account: Union[Friend, Stranger, Member]):
        """自动检查 AccountName 是否变化，若变化则更新数据库"""
        if isinstance(account, Member):
            profile = await account.getProfile()
            query = AccountTable.update().values(name=profile.nickname).where(AccountTable.c.accountID == account.id and
                                                                              AccountTable.c.name != profile.nickname)
        else:
            query = AccountTable.update().values(name=account.nickname).where(AccountTable.c.accountID == account.id and
                                                                              AccountTable.c.name != account.nickname)
        await self.database.execute(query)

    async def updateMemberName(self, account: Member):
        """自动检查 MemberName 是否变化，若变化则更新数据库"""
        query = MemberTable.update().values(name=account.name).where(MemberTable.c.accountID == account.id and
                                                                     MemberTable.c.groupID == account.group.id and
                                                                     MemberTable.c.name != account.name)
        await self.database.execute(query)

    async def addGroupMessage(self, message: GroupMessage):
        """往数据库中添加新 GroupMessage """
        query = GroupMessageTable.insert().values(senderID=message.sender.id,
                                                  groupID=message.sender.group.id,
                                                  timestamp=message.messageChain.get(Source)[0].time.timestamp(),
                                                  context=message.messageChain.asPersistentString())
        await self.database.execute(query)

    async def addFriendMessage(self, message: FriendMessage):
        """往数据库中添加新 FriendMessage """
        query = GroupMessageTable.insert().values(senderID=message.sender.id,
                                                  timestamp=message.messageChain.get(Source)[0].time.timestamp(),
                                                  context=message.messageChain.asPersistentString())
        await self.database.execute(query)
