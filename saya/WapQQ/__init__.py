from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from dataBase import dataManager

channel = Channel.current()

channel.name("WapQQ")
channel.description("简单的WebQQ实现")
channel.author("Cubesugarcheese")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def handleGroupMessage(app: Ariadne, group: Group, message: MessageChain):
    await dataManager.addGroupMessage()


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def handleFriendMessage(app: Ariadne, group: Group, message: MessageChain):
    await dataManager.addFriendMessage()
