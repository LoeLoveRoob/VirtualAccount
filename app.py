from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from pyromod import listen
from pyromod.helpers import array_chunk, ikb


import plugins.models as models
import plugins.config as config


app = Client("session",
             config.API_ID, config.API_HASH,
             bot_token=config.API_TOKEN,
             proxy=config.PROXY["Phone"])


@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):

    question: Message = await message.chat.ask(
        "با سلام به ربات خرید شماره مجازی خوش آمدید",
        reply_markup = ReplyKeyboardMarkup([
            ["حساب من", "دریافت شماره"]
        ], resize_keyboard=True)
    )

    if question.text == "دریافت شماره":
        return await buy_handler(client, message)
    
    elif question.text == "حساب من":
        return await me_handler(client, message)

    elif question.text == "/panel":
        return await panel_handler(client, message)


async def buy_handler(client: Client, message: Message):
    user      = await models.Users.objects.get(user_id = message.from_user.id)
    countries = await models.Countries.objects.all()
    user: models.Users.objects

    keyboards = [country.name for country in countries]
    keyboards = array_chunk(keyboards, 2)
    keyboards.append(["بازگشت به منوی اصلی"])
    keyboards = ReplyKeyboardMarkup(keyboards, resize_keyboard=True)

    question: Message = await message.chat.ask(
        "کشور مورد نظر خود را انتخاب کنید:",
        reply_markup = keyboards,
    )
    if question.text == "بازگشت به منوی اصلی":
        return await start_handler(client, message)
    
    # - If Country Is Choosed! ---------------------------------------------------------------

    country = await models.Countries.objects.get(name = question.text)
    if not country:
        await message.reply(
            "در حال حاضر ربات دارای هیچ اکانتی نمیباشد!"
        )

    accounts = await models.Accounts.objects.all(country = country.id)
    if not accounts:
        await message.reply(
            "در حال حاضر اکانتی از این کشور موجود نیست!"
        )
        return await buy_handler(client, message)

    null      = await models.Users.objects.get(user_id = 0)

    keyboards = [("+" + str(account.number)) for account in accounts if account.user.id == null.id]
    keyboards = array_chunk(keyboards, 2)
    keyboards.append(["بازگشت"])
    
    keyboards = ReplyKeyboardMarkup(keyboards, resize_keyboard=True)

    question: Message = await message.chat.ask(
        "شماره مورد نظر خود را انتخاب کنید:",
        reply_markup = keyboards,
    )
    if question.text == "بازگشت":
        return await buy_handler(client, message)
    
    #- If Number Is Choosed ----------------------------------------------------------------------------------
    account = await models.Accounts.objects.select_related("country").get(number = question.text)
    price  = account.country.price

    question: Message = await message.chat.ask(
        f"شماره: `{account.number}`\nمبلغ: `{price}`\nآیا تایید میکنید؟",
        reply_markup = ReplyKeyboardMarkup([
            ["تایید ✅"],
            ["انصراف ❌"],
        ], resize_keyboard=True)
    )
    if question.text == "تایید ✅":
        if user.balance >= price:
            await user.update(balance = (user.balance - price))
            return await login(user, account)
        else:
            await message.reply(
                "شما موجودی کافی برای خرید این اکانت را ندارید!\nبرای افزایش موجودی به پیوی ادمین مراجعه کنید!"
            )
            return await start_handler(client, message)
        
    elif question.text == "انصراف ❌":
        return await start_handler(client, message)




        


app.run()
