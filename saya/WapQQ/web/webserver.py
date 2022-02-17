from pathlib import Path
from io import BytesIO
from typing import List
from PIL import Image, ImageSequence

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from sanic import Sanic, Request, html, HTTPResponse
from sanic.response import redirect, raw
from httpx import AsyncClient

from .utils import render_template
from .config import use_image_proxy
from ..dataBase import dataManager

current_path = Path(__file__).parents[0]
sanic = Sanic("WapQQ")
application: Ariadne


async def setApplication(app: Ariadne):
    global application
    application = app


@sanic.get("/qq")
async def show_main_page(request: Request) -> HTTPResponse:
    global application
    account = application.account
    group_list = await application.getGroupList()
    friend_list = await application.getFriendList()
    template = await render_template("main_page.jinja2",
                                     account=account, group_list=group_list, friend_list=friend_list)
    return HTTPResponse(template, content_type='text/html')


@sanic.get("/qq/send_error")
async def show_send_error_page(request: Request):
    template = await render_template("send_error.jinja2")
    return html(template)


@sanic.get("/qq/group/<group_id:int>")
async def show_group_page(request: Request, group_id: int) -> HTTPResponse:
    global application
    group_list = await application.getGroupList()
    status = "error"
    current_group = None
    for group in group_list:
        if group_id == group.id:
            current_group = group
            status = "ok"
            break
    if status == "error":
        return html(await render_template("message_page.jinja2", status=status))
    message_container_list = await dataManager.getGroupMessage(current_group)
    template = await render_template("message_page.jinja2", messageContainer_list=message_container_list,
                                     group_name=current_group.name, group_id=group_id, type='group',
                                     status=status, account=application.account,
                                     use_image_proxy=use_image_proxy)
    return html(template)


@sanic.get("/qq/friend/<friend_id:int>")
async def show_friend_page(request: Request, friend_id: int) -> HTTPResponse:
    global application
    friend_list = await application.getFriendList()
    status = "error"
    current_friend = None
    for friend in friend_list:
        if friend_id == friend.id:
            current_friend = friend
            status = "ok"
            break
    if status == "error":
        return html(await render_template("message_page.jinja2", status=status))
    message_container_list = await dataManager.getFriendMessage(current_friend)
    template = await render_template("message_page.jinja2", messageContainer_list=message_container_list,
                                     friend_name=current_friend.nickname, friend_id=friend_id, type='friend',
                                     status=status, account=application.account,
                                     use_image_proxy=use_image_proxy)
    return html(template)


@sanic.post("/qq/send_group_message/<group_id:int>")
async def send_group_message(request: Request, group_id: int):
    global application
    try:
        message: str = request.form["message"]
    except KeyError:
        return redirect("/qq/send_error")
    bot_message = await application.sendGroupMessage(group_id, MessageChain.create(message))
    await dataManager.addBotGroupMessage(bot_message, group_id)
    await dataManager.updateBotMemberName(group_id)
    return redirect(f"/qq/group/{group_id}")


@sanic.post("/qq/send_friend_message/<friend_id:int>")
async def send_friend_message(request: Request, friend_id: int):
    global application
    try:
        message: str = request.form["message"]
    except KeyError:
        return redirect("/qq/send_error")
    bot_message = await application.sendFriendMessage(friend_id, MessageChain.create(message))
    await dataManager.addBotFriendMessage(bot_message, friend_id)
    await dataManager.updateBotAccountName()
    return redirect(f"/qq/friend/{friend_id}")


@sanic.get(r"/qq/image_proxy/http%3A/<url:path>")
async def image_proxy(request: Request, url: str, max_width: int = 200, max_height: int = 200):
    url = "http:/" + url
    async with AsyncClient() as client:
        r = await client.get(url)
    image = Image.open(BytesIO(r.content))
    if image.mode == "P":
        # Gif
        imgs: List[Image.Image] = [frame.copy() for frame in ImageSequence.Iterator(image)]
        gif_frames: List = []
        for i in imgs:
            i.thumbnail((max_width, max_height))
            gif_frames.append(i)
        send_image = BytesIO()
        gif_frames[0].save(
            send_image,
            format="GIF",
            append_images=gif_frames[1:],
            save_all=True,
            duration=60,
            loop=0,
            optimize=False,
        )
    else:
        image.thumbnail((max_width, max_height))
        send_image = BytesIO()
        image.save(send_image, format="JPEG")
    return raw(send_image.getvalue(), content_type="image/jpeg")
