import time as time_module
from typing import Optional, Union, List
from pathlib import Path

from databases import Database, core
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, GroupSyncMessage, FriendSyncMessage, \
    ActiveFriendMessage, ActiveGroupMessage
from graia.ariadne.model import Group, Friend, Member, Stranger
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.exception import UnknownTarget
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .tables import metadata, GroupTable, AccountTable, MemberTable, FriendMessageTable, GroupMessageTable
from .utils import MessageContainer, get_time_by_timestamp

current_path = Path(__file__).parents[0]


class DataManager:
    """数据库管理类"""
    # see https://docs.sqlalchemy.org/en/14/core/engines.html#sqlite
    DATABASE_URL: str = f"sqlite:///{current_path}/data.db"
    database: core.Database = Database(DATABASE_URL)
    engine: Engine
    app: Ariadne

    async def startup(self):
        """应在开启 bot 时调用，用于开启数据库连接"""
        await self.database.connect()
        self.engine = create_engine(self.DATABASE_URL, connect_args={"check_same_thread": False})
        metadata.create_all(self.engine)  # 自动检查是否已经创建表，若无，则创建
        self.app = Ariadne.current()

    async def shutdown(self):
        """应在关闭 bot 时调用，用于关闭数据库连接"""
        await self.database.disconnect()

    async def has_in_group_table(self, group: Group) -> bool:
        """检查数据库中是否已有该 Group """
        query = GroupTable.select().where(GroupTable.c.groupID == group.id)
        result = await self.database.fetch_val(query)
        if result is not None:
            return True
        else:
            return False

    async def has_in_account_table(self, account: Union[Friend, Stranger, Member]) -> bool:
        """检查数据库中是否已有该 Account """
        query = AccountTable.select().where(AccountTable.c.accountID == account.id)
        result = await self.database.fetch_val(query)
        if result is not None:
            return True
        else:
            return False

    async def has_in_member_table(self, account: Member) -> bool:
        """检查数据库中是否已有该 Member """
        query = AccountTable.select() \
            .where(MemberTable.c.accountID == account.id) \
            .where(MemberTable.c.groupID == account.group.id)
        result = await self.database.fetch_val(query)
        if result is not None:
            return True
        else:
            return False

    async def add_group(self, group: Group):
        """往数据库中添加新 Group """
        query = GroupTable.insert().values(groupID=group.id, name=group.name)
        await self.database.execute(query)

    async def add_account(self, account: Union[Friend, Stranger, Member]):
        """往数据库中添加新 Account """
        if isinstance(account, Member):
            profile = await account.get_profile()
            query = AccountTable.insert().values(accountID=account.id, name=profile.nickname)
        else:
            query = AccountTable.insert().values(accountID=account.id, name=account.nickname)
        await self.database.execute(query)

    async def add_member(self, account: Member):
        """往数据库中添加新 Member """
        query = MemberTable.insert().values(accountID=account.id, groupID=account.group.id, name=account.name)
        await self.database.execute(query)

    async def add_bot_account(self):
        """往数据库中添加 Bot 自身的账号信息"""
        profile = await self.app.get_bot_profile()
        query = AccountTable.insert().values(accountID=self.app.account, name=profile.nickname)
        await self.database.execute(query)

    async def add_bot_member(self, group_id: int):
        """往数据库中添加 Bot 自身在 Group 中的的成员信息"""
        group = await self.app.get_group(group_id)
        if group is None:
            return
        info = await self.app.get_member_profile(self.app.account, group)
        name = info.nickname
        query = MemberTable.select().where(
            MemberTable.c.accountID == self.app.account
        ).where(
            MemberTable.c.groupID == group_id)
        result = await self.database.fetch_val(query)
        if result is None:
            query = MemberTable.insert().values(name=name, accountID=self.app.account, groupID=group_id)
            await self.database.execute(query)

    async def update_group_name(self, group: Group):
        """自动检查 GroupName 是否变化，若变化则更新数据库"""
        query = GroupTable.update().values(name=group.name) \
            .where(GroupTable.c.groupID == group.id) \
            .where(GroupTable.c.name != group.name)
        await self.database.execute(query)

    async def update_account_name(self, account: Union[Friend, Stranger, Member]):
        """自动检查 AccountName 是否变化，若变化则更新数据库"""
        if isinstance(account, Member):
            try:
                profile = await account.get_profile()
                query = AccountTable.update().values(name=profile.nickname) \
                    .where(AccountTable.c.accountID == account.id) \
                    .where(AccountTable.c.name != profile.nickname)
            except UnknownTarget:
                query = AccountTable.update().values(name=account.name) \
                    .where(AccountTable.c.accountID == account.id) \
                    .where(AccountTable.c.name != account.name)
        else:
            query = AccountTable.update().values(name=account.nickname) \
                .where(AccountTable.c.accountID == account.id) \
                .where(AccountTable.c.name != account.nickname)
        await self.database.execute(query)

    async def update_member_name(self, account: Member):
        """自动检查 MemberName 是否变化，若变化则更新数据库"""
        query = MemberTable.update().values(name=account.name) \
            .where(MemberTable.c.accountID == account.id) \
            .where(MemberTable.c.groupID == account.group.id) \
            .where(MemberTable.c.name != account.name)
        await self.database.execute(query)

    async def update_bot_account_name(self):
        """自动检查 Bot 自身 nickname 是否变化，若变化则更新数据库"""
        profile = await self.app.get_bot_profile()
        query = AccountTable.update().values(name=profile.nickname) \
            .where(AccountTable.c.accountID == self.app.account) \
            .where(AccountTable.c.name != profile.nickname)
        await self.database.execute(query)

    async def update_bot_member_name(self, group_id: int):
        """自动检查 Bot 自身所在 Group 中的 name 是否变化，若变化则更新数据库"""
        group = await self.app.get_group(group_id)
        if group is None:
            return
        info = await self.app.get_member_profile(self.app.account, group)
        name = info.nickname
        query = MemberTable.update().values(name=name) \
            .where(MemberTable.c.accountID == self.app.account) \
            .where(MemberTable.c.name != name)
        await self.database.execute(query)

    async def add_group_message(self, message: GroupMessage):
        """往数据库中添加新 GroupMessage """
        query = GroupMessageTable.insert().values(senderID=message.sender.id,
                                                  groupID=message.sender.group.id,
                                                  timestamp=message.source.time.timestamp(),
                                                  context=message.message_chain.json())
        await self.database.execute(query)

    async def add_friend_message(self, message: FriendMessage):
        """往数据库中添加新 FriendMessage """
        query = FriendMessageTable.insert().values(senderID=message.sender.id,
                                                   friendID=message.sender.id,
                                                   timestamp=message.source.time.timestamp(),
                                                   context=message.message_chain.json())
        await self.database.execute(query)

    async def add_bot_group_message(self, message: ActiveGroupMessage, group_id: int):
        """往数据库中添加 ActiveGroupMessage """
        query = GroupMessageTable.insert().values(senderID=self.app.account,
                                                  groupID=group_id,
                                                  timestamp=time_module.time(),
                                                  context=message.message_chain.json())
        await self.database.execute(query)

    async def add_bot_friend_message(self, message: ActiveFriendMessage, friend_id: int):
        """往数据库中添加 ActiveFriendMessage """
        query = FriendMessageTable.insert().values(senderID=self.app.account,
                                                   friendID=friend_id,
                                                   timestamp=time_module.time(),
                                                   context=message.message_chain.json())
        await self.database.execute(query)

    async def add_sync_group_message(self, message: GroupSyncMessage):
        """往数据库中添加 GroupSyncMessage """
        query = GroupMessageTable.insert().values(senderID=self.app.account,
                                                  groupID=message.subject.id,
                                                  timestamp=time_module.time(),
                                                  context=message.message_chain.json())
        await self.database.execute(query)

    async def add_sync_friend_message(self, message: FriendSyncMessage):
        """往数据库中添加 FriendSyncMessage """
        query = FriendMessageTable.insert().values(senderID=self.app.account,
                                                   friendID=message.subject.id,
                                                   timestamp=time_module.time(),
                                                   context=message.message_chain.json())
        await self.database.execute(query)

    async def get_group_name_by_id(self, group_id: int) -> str:
        """通过 groupID 获取群名"""
        group = await self.app.get_group(group_id)
        name = group.name
        return name

    async def get_account_name_by_id(self, account_id: int) -> str:
        """通过 accountID 获取账号名"""
        if account_id == self.app.account:
            profile = await self.app.get_user_profile(account_id)
            name = profile.nickname
        else:
            try:
                profile = await self.app.get_user_profile(account_id)
                name = profile.nickname
            except UnknownTarget:
                name = "【无法获取的用户】"
        return name

    async def get_member_name_by_id(self, account_id: int, group_id: int) -> str:
        """通过 accountID 和 groupID 获得成员名"""
        query = MemberTable.select().where(MemberTable.c.groupID == group_id).where(
            MemberTable.c.accountID == account_id)
        result = await self.database.fetch_one(query)
        name = result[3]
        return name

    async def get_group_message(self, group: Group, limit: int = 60, page: int = 1) -> List[Optional[MessageContainer]]:
        query = GroupMessageTable.select().limit(limit) \
            .order_by(GroupMessageTable.c._id.desc()) \
            .offset((page - 1) * limit) \
            .where(GroupMessageTable.c.groupID == group.id)
        result = await self.database.fetch_all(query)
        message_list: List[Optional[MessageContainer]] = []
        for i in result:
            sender_id = i[1]
            group_id = i[2]
            try:
                sender_name = await self.get_member_name_by_id(account_id=sender_id, group_id=group_id)
            except UnknownTarget:
                sender_name = await self.get_account_name_by_id(account_id=sender_id)
            group_name = await self.get_group_name_by_id(group_id=group_id)
            timestamp = i[3]
            time = get_time_by_timestamp(timestamp)
            message = MessageChain.parse_raw(i[4])
            message_list.append(MessageContainer(time=time, timestamp=timestamp,
                                                 message=message, sender_id=sender_id, sender_name=sender_name,
                                                 group_id=group_id, group_name=group_name))
        return message_list

    async def get_friend_message(self, friend: Friend, limit: int = 60) -> List[Optional[MessageContainer]]:
        query = FriendMessageTable.select().limit(limit) \
            .order_by(FriendMessageTable.c._id.desc()) \
            .where(FriendMessageTable.c.friendID == friend.id)
        result = await self.database.fetch_all(query)
        message_list: List[Optional[MessageContainer]] = []
        for i in result:
            sender_id = i[1]
            sender_name = await self.get_account_name_by_id(account_id=sender_id)
            timestamp = i[3]
            time_ = get_time_by_timestamp(timestamp)
            message = MessageChain.parse_raw(i[4])
            message_list.append(MessageContainer(time=time_, timestamp=timestamp,
                                                 message=message, sender_id=sender_id, sender_name=sender_name,
                                                 group_id=None, group_name=None))
        return message_list

    async def count_group_message(self, group_id: int) -> int:
        query = "select COUNT(*) from GroupMessage where groupID = :group_id"
        values = {"group_id": group_id}
        result = await self.database.fetch_val(query, values)
        return result

    async def count_friend_message(self, friend_id: int) -> int:
        query = "select COUNT(*) from FriendMessage where friendID = :friend_id"
        values = {"friend_id": friend_id}
        result = await self.database.fetch_val(query, values)
        return result


data_manager = DataManager()
