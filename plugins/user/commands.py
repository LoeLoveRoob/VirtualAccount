from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from pyromod.helpers import array_chunk, ikb

import plugins.config as config
import plugins.models as models
import plugins.admin.commands as AdminCommands
from orm.exceptions import NoMatch

@Client.on_message()
async def check_ban(client, message: Message):
    try:
        user = await models.Users.objects.get(user_id = message.chat.id)
    except NoMatch:
        await models.Users.objects.create(user_id = message.chat.id)
        return message.continue_propagation()
    
    if user.is_banned:
        return message.stop_propagation()
    else:
        return message.continue_propagation()

@Client.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):

    question: Message = await message.chat.ask(
        "با سلام به ربات خرید شماره مجازی خوش آمدید",
        reply_markup = ReplyKeyboardMarkup([
            ["حساب من", "دریافت شماره"]
        ], resize_keyboard=True)
    )

    match question.text:
        case "دریافت شماره":
            return await buy_handler(client, message)
    
        case "حساب من":
            return await dashboard_handler(client, message)

        case "/panel":
            if message.from_user.id == config.ADMIN:
                return await AdminCommands.panel_handler(client, message)

        case _ :
            await question.reply("لطفا از کیبورد ها استفاده کنید !")
            return await start_handler(client, message)


async def buy_handler(client: Client, message: Message):
    user      = await models.Users.objects.get(user_id = message.chat.id)
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
            await account.update(user = user)
            return await login_handler(client, message, user, account)
        else:
            await message.reply(
                "شما موجودی کافی برای خرید این اکانت را ندارید!\nبرای افزایش موجودی به پیوی ادمین مراجعه کنید!",
                reply_markup=ikb([["پیوی ادمین", f"t.me/{config.ADMIN_USERNAME}", "url"]])
            )
            return await start_handler(client, message)
        
    elif question.text == "انصراف ❌":
        return await start_handler(client, message)


async def login_handler(client: Client, message: Message, user, account):
    async with Client(account.number, config.API_ID, config.API_HASH, session_string=account.session_string, proxy=config.PROXY["Phone"]) as app:
        app: Client
        text = f"ربات اماده ارسال کد ورود به شماست لطفا شماره {account.number} را در تلگرام وارد کنید سپس صبرکنید تا کد ورود برای شما ارسال شود!"
        if account.password:
            text += f"\nرمز اکانت: `{account.password}`"

        question = await message.chat.ask(
            text,
            reply_markup=ReplyKeyboardMarkup([
                ["دریافت کد"]
            ], resize_keyboard=True)
        )

        match question.text:
            case "دریافت کد":
                while True:
                    async for code in app.get_chat_history(777000, 1):
                        code = code.text
                    question: Message = await question.chat.ask(
                        code,
                        reply_markup = ReplyKeyboardMarkup([
                            ["وارد شدم!"],
                            ["دریافت دوباره کد"]
                        ], resize_keyboard=True)
                    )
                    match question.text:
                        case "وارد شدم!":
                            await question.reply(
                                "ربات در حال خروج از سشن میباشد ...",
                                reply_markup = ReplyKeyboardRemove()
                            )
                            await app.log_out()
                            await client.send_message(
                                message.chat.id, "ربات با موفقیت از سشن خارج شد!"
                            )
                            return await start_handler(client, message)

        



async def dashboard_handler(client: Client, message: Message):
    user_id  = message.from_user.id
    user     = await models.Users.objects.get(user_id = user_id)
    accounts = await models.Accounts.objects.all(user = user_id)

    loading = await message.reply("Loading...", reply_markup=ReplyKeyboardRemove())
    await loading.delete()

    await client.send_message(
        message.chat.id,
        f"اطلاعات حساب شما به شکل زیر میباشید:",
        reply_markup=ikb([
            [("یوزر ایدی شما", "None"), (f"{user.user_id}", "None")],
            [("موجودی شما", "None"),(f"{user.balance}", "None")],
            [("تعداد اکانت های شما", "None"),(f"{len(accounts)}", "None")],
            [("افزایش موجودی", "addbalance")],
            [("اکانت های خریداری شده", "showaccounts")],
            [("بازگشت به منوی اصلی", "mainmenu")],
        ])
    )



        


