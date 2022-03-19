import asyncio
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
from numpy import ndarray
from PIL import Image, ImageSequence, UnidentifiedImageError
from graia.ariadne import get_running
from graia.ariadne.message.chain import MessageChain
from httpx import AsyncClient
from httpx import RequestError
from sanic import Sanic, Request, html, HTTPResponse
from sanic.response import redirect, raw

from .config import use_image_proxy, max_height, max_width, chat_limit
from .utils import render_template
from ..dataBase import dataManager

current_path = Path(__file__).parents[0]
sanic = Sanic("WapQQ")


@sanic.get("/qq")
async def show_main_page(request: Request) -> HTTPResponse:
    application = get_running()
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
    application = get_running()
    page = int(request.args.get("page")) if request.args.get("page") is not None else 1
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
    message_container_list = await dataManager.getGroupMessage(current_group, limit=chat_limit, page=page)
    max_page = ((await dataManager.countGroupMessage(group_id)) // chat_limit) + 1
    template = await render_template("message_page.jinja2", messageContainer_list=message_container_list,
                                     group_name=current_group.name, id=group_id, type='group',
                                     status=status, account=application.account,
                                     use_image_proxy=use_image_proxy, page=page, max_page=max_page)
    return html(template)


@sanic.get("/qq/friend/<friend_id:int>")
async def show_friend_page(request: Request, friend_id: int) -> HTTPResponse:
    application = get_running()
    page = int(request.args.get("page")) if request.args.get("page") is not None else 1
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
    max_page = ((await dataManager.countGroupMessage(friend_id)) // chat_limit) + 1
    template = await render_template("message_page.jinja2", messageContainer_list=message_container_list,
                                     friend_name=current_friend.nickname, id=friend_id, type='friend',
                                     status=status, account=application.account,
                                     use_image_proxy=use_image_proxy, page=page, max_page=max_page)
    return html(template)


@sanic.post("/qq/send_group_message/<group_id:int>")
async def send_group_message(request: Request, group_id: int):
    application = get_running()
    try:
        message: str = request.form["message"]
    except KeyError:
        return redirect("/qq/send_error")
    bot_message = await application.sendGroupMessage(group_id, MessageChain.create(message))
    await dataManager.addBotGroupMessage(bot_message, group_id)
    await dataManager.addBotMember(group_id)
    await dataManager.updateBotMemberName(group_id)
    return redirect(f"/qq/group/{group_id}", status=303)


@sanic.post("/qq/send_friend_message/<friend_id:int>")
async def send_friend_message(request: Request, friend_id: int):
    application = get_running()
    try:
        message: str = request.form["message"]
    except KeyError:
        return redirect("/qq/send_error")
    bot_message = await application.sendFriendMessage(friend_id, MessageChain.create(message))
    await dataManager.addBotFriendMessage(bot_message, friend_id)
    await dataManager.addBotAccount()
    await dataManager.updateBotAccountName()
    return redirect(f"/qq/friend/{friend_id}", status=303)


@sanic.get(r"/qq/image_proxy")
async def image_proxy(request: Request):
    url = request.args.get("url")
    try:
        async with AsyncClient() as client:
            r = await client.get(url)
        image = Image.open(BytesIO(r.content))
    except RequestError:
        return HTTPResponse("invalid url", status=403)
    except UnidentifiedImageError:
        return HTTPResponse("content not support, must image", status=403)
    img_bytes = await asyncio.to_thread(lambda: thumbnail_image(image))
    return raw(img_bytes.getvalue())


def thumbnail_dynamic_image(image: Image.Image, img_format: str = "GIF") -> BytesIO:
    imgs: List[Image.Image] = [frame.copy() for frame in ImageSequence.Iterator(image)]
    img_frames: List[Image.Image] = []
    for i in imgs:
        i.thumbnail((max_width, max_height), Image.ANTIALIAS)
        img_frames.append(i)
    after_image = BytesIO()
    img_frames[0].save(
        after_image,
        format=img_format,
        append_images=img_frames[1:],
        save_all=True,
        duration=60,
        loop=0,
        optimize=False,
        quality=100
    )
    return after_image


def thumbnail_image(image: Image.Image) -> BytesIO:
    after_image = BytesIO()
    if image.mode == "P":  # ['1', 'L', 'I', 'F', 'P', 'RGB', 'RGBA', 'CMYK', 'YCbCr' ]
        # Gif
        after_image = thumbnail_dynamic_image(image, "GIF")
    elif image.mode == "RGBA":
        if image.get_format_mimetype() == "image/apng":
            # APNG
            after_image = thumbnail_dynamic_image(image, "PNG")
        elif image.format == "WEBP":
            # WEBP
            after_image = thumbnail_dynamic_image(image, "WEBP")
        else:
            # normal PNG
            image.thumbnail((max_width, max_height), Image.ANTIALIAS)
            image.save(after_image, format="PNG")
    else:
        image.thumbnail((max_width, max_height), Image.ANTIALIAS)
        image.save(after_image, format="JPEG")
    return after_image
