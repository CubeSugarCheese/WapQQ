import asyncio
from io import BytesIO
from pathlib import Path
from typing import List

from PIL.ImageFile import ImageFile
from PIL import Image, ImageSequence, UnidentifiedImageError
from graia.ariadne import Ariadne
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
sanic.static("/face", current_path / "resources" / "qq-face", name="qq_face")
sanic.static("/css", current_path / "resources" / "css", name="css")


@sanic.get("/")
async def show_main_page(request: Request) -> HTTPResponse:
    application: Ariadne = Ariadne.current()
    account = application.account
    group_list = await application.get_group_list()
    friend_list = await application.get_friend_list()
    template = await render_template("main_page.jinja2",
                                     account=account, group_list=group_list, friend_list=friend_list)
    return HTTPResponse(template, content_type='text/html')


@sanic.get("/send_error")
async def show_send_error_page(request: Request):
    template = await render_template("send_error.jinja2")
    return html(template)


@sanic.get("/group/<group_id:int>")
async def show_group_page(request: Request, group_id: int) -> HTTPResponse:
    application: Ariadne = Ariadne.current()
    page = int(request.args.get("page")) if request.args.get("page") is not None else 1
    group_list = await application.get_group_list()
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


@sanic.get("/friend/<friend_id:int>")
async def show_friend_page(request: Request, friend_id: int) -> HTTPResponse:
    application: Ariadne = Ariadne.current()
    page = int(request.args.get("page")) if request.args.get("page") is not None else 1
    friend_list = await application.get_friend_list()
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


@sanic.post("/send_group_message/<group_id:int>")
async def send_group_message(request: Request, group_id: int):
    application: Ariadne = Ariadne.current()
    try:
        message: str = request.form["message"]
    except KeyError:
        return redirect("/send_error")
    bot_message = await application.send_group_message(group_id, MessageChain(message))
    await dataManager.addBotGroupMessage(bot_message, group_id)
    await dataManager.addBotMember(group_id)
    await dataManager.updateBotMemberName(group_id)
    return redirect(f"/group/{group_id}")


@sanic.post("/send_friend_message/<friend_id:int>")
async def send_friend_message(request: Request, friend_id: int):
    application: Ariadne = Ariadne.current()
    try:
        message: str = request.form["message"]
    except KeyError:
        return redirect("/send_error")
    bot_message = await application.send_friend_message(friend_id, MessageChain(message))
    await dataManager.addBotFriendMessage(bot_message, friend_id)
    await dataManager.addBotAccount()
    await dataManager.updateBotAccountName()
    return redirect(f"/friend/{friend_id}")


@sanic.get("/image_proxy")
async def image_proxy(request: Request):
    url = request.args.get("url")
    try:
        async with AsyncClient() as client:
            r = await client.get(url)
        image: ImageFile = Image.open(BytesIO(r.content))
        mimetype = image.get_format_mimetype()
    except RequestError:
        return HTTPResponse("invalid url", status=403)
    except UnidentifiedImageError:
        return HTTPResponse("content not support, must image", status=403)
    img_bytes = await asyncio.to_thread(lambda: thumbnail_image(image))
    return raw(img_bytes.getvalue(), content_type=mimetype)


@sanic.get("/market_face/<face_id:int>")
async def market_face_proxy(request: Request, face_id: int):
    name = request.args.get("name")
    if name is None:
        return HTTPResponse("illegal param", status=403)
    async with AsyncClient() as client:
        meta = (await client.get(f"https://i.gtimg.cn/club/item/parcel/{face_id % 10}/{face_id}_android.json")).json()
        for i in meta["imgs"]:
            if i["name"] == name:
                height: int = i["wHeightInPhone"]
                width: int = i["wWidthInPhone"]
                item_id: str = i["item_id"]
                face_url = f"https://i.gtimg.cn/club/item/parcel/item/{item_id[:2]}/{item_id}/{height}x{width}.png"
                return redirect(face_url)


def thumbnail_dynamic_image(image: ImageFile, img_format: str = "GIF") -> BytesIO:
    imgs: List[ImageFile] = [frame.copy() for frame in ImageSequence.Iterator(image)]
    img_frames: List[ImageFile] = []
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


def thumbnail_image(image: ImageFile) -> BytesIO:
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
