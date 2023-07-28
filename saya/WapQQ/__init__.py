from graia.ariadne.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.ariadne.event.message import GroupMessage, FriendMessage, GroupSyncMessage, FriendSyncMessage

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from .dataBase import data_manager

from .web import launch_webserver, stop_webserver

channel = Channel.current()

channel.name("WapQQ")
channel.description("简单的WebQQ实现")
channel.author("Cubesugarcheese")


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def launch():
    await data_manager.startup()
    await launch_webserver()


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def stop():
    await data_manager.shutdown()
    await stop_webserver()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def handle_group_message(message: GroupMessage):
    group = message.sender.group
    member = message.sender
    await data_manager.add_group_message(message)
    if not await data_manager.has_in_group_table(group):
        await data_manager.add_group(group)
    if not await data_manager.has_in_account_table(member):
        await data_manager.add_account(member)
    if not await data_manager.has_in_member_table(member):
        await data_manager.add_member(member)
    await data_manager.update_group_name(group)
    await data_manager.update_account_name(member)
    await data_manager.update_member_name(member)


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def handle_friend_message(message: FriendMessage):
    friend = message.sender
    await data_manager.add_friend_message(message)
    if not await data_manager.has_in_accountTable(friend):
        await data_manager.add_account(friend)
    await data_manager.update_account_name(friend)


@channel.use(ListenerSchema(listening_events=[GroupSyncMessage]))
async def handle_group_sync_message(message: GroupSyncMessage):
    group_id = message.subject.id
    await data_manager.add_sync_group_message(message)
    await data_manager.add_bot_member(group_id)
    await data_manager.update_bot_member_name(group_id)
    await data_manager.add_bot_account()
    await data_manager.update_bot_account_name()


@channel.use(ListenerSchema(listening_events=[FriendSyncMessage]))
async def handle_friend_sync_message(message: FriendSyncMessage):
    await data_manager.add_sync_friend_message(message)
    await data_manager.add_bot_account()
    await data_manager.update_bot_account_name()
