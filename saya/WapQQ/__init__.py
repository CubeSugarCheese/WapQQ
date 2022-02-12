from asyncio import AbstractEventLoop

from graia.ariadne.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.ariadne.event.message import GroupMessage, FriendMessage

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from .dataBase import DataManager

channel = Channel.current()

channel.name("WapQQ")
channel.description("简单的WebQQ实现")
channel.author("Cubesugarcheese")

dataManager: DataManager


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def launch(loop: AbstractEventLoop):
    global dataManager
    dataManager = DataManager(loop=loop)
    await dataManager.startup()


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def stop():
    await dataManager.shutdown()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def handleGroupMessage(message: GroupMessage):
    group = message.sender.group
    member = message.sender
    await dataManager.addGroupMessage(message)
    if not await dataManager.has_in_groupTable(group):
        await dataManager.addGroup(group)
    if not await dataManager.has_in_accountTable(member):
        await dataManager.addAccount(member)
    if not await dataManager.has_in_memberTable(member):
        await dataManager.addMember(member)
    await dataManager.updateGroupName(group)
    await dataManager.updateAccountName(member)
    await dataManager.updateMemberName(member)


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def handleFriendMessage(message: FriendMessage):
    friend = message.sender
    await dataManager.addFriendMessage(message)
    if not await dataManager.has_in_accountTable(friend):
        await dataManager.addAccount(friend)
    await dataManager.updateAccountName(friend)
