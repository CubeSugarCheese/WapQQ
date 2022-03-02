from graia.ariadne.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.ariadne.event.message import GroupMessage, FriendMessage, GroupSyncMessage, FriendSyncMessage
from graia.ariadne.app import Ariadne

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from .dataBase import dataManager

from .web import launch_webserver, stop_webserver

channel = Channel.current()

channel.name("WapQQ")
channel.description("简单的WebQQ实现")
channel.author("Cubesugarcheese")


app: Ariadne


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def launch():
    await dataManager.startup()
    await launch_webserver()


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def stop():
    await dataManager.shutdown()
    await stop_webserver()


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


@channel.use(ListenerSchema(listening_events=[GroupSyncMessage]))
async def handleGroupSyncMessage(message: GroupSyncMessage):
    group_id = message.subject.id
    await dataManager.addSyncGroupMessage(message)
    await dataManager.addBotMember(group_id)
    await dataManager.updateBotMemberName(group_id)
    await dataManager.addBotAccount()
    await dataManager.updateBotAccountName()


@channel.use(ListenerSchema(listening_events=[FriendSyncMessage]))
async def handleFriendSyncMessage(message: FriendSyncMessage):
    await dataManager.addSyncFriendMessage(message)
    await dataManager.addBotAccount()
    await dataManager.updateBotAccountName()
