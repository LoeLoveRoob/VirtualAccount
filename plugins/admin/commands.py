from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from pyromod.helpers import ikb, array_chunk

import os
from zipfile import ZipFile

import plugins.config as config
import plugins.models as models
import plugins.user.commands as UserCommands



@Client.on_message(filters.user(config.ADMIN) & filters.command("panel"))
async def panel_handler(client: Client, message: Message):
    question: Message = await message.chat.ask(
        "سلام ادمین گرامی به پنل مدیریت خوش آمدید!",
        reply_markup = ReplyKeyboardMarkup([
            ["افزودن اکانت", "تنظیمات کشورها"],
            ["کاربران"],
            ["بازگشت به منوی اصلی"],
        ], resize_keyboard=True)
    )

    match question.text:
        case "تنظیمات کشورها":
            return await country_handler(client, message)
        
        case "افزودن اکانت":
            return await choose_country_handler(client, message)
        
        case "کاربران":
            return await users_handler(client, message)
        
        case "بازگشت به منوی اصلی":
            return await UserCommands.start_handler(client, message)
        
        case _ :
            await question.reply("لطفا از کیبورد ها استفاده کنید !")
            return await panel_handler(client, message)

async def country_handler(client: Client, message: Message):

    countries = await models.Countries.objects.all()
    keyboards = [(country.name, f"country:{country.id}") for country in countries]
    keyboards = array_chunk(keyboards, 2)
    keyboards.append([("افزودن کشور", "addcountry")])
    keyboards.append([("بازگشت به پنل مدیریت", "panel_handler")])
    keyboards = ikb(keyboards)

    keydel    = await message.reply("Loading!", reply_markup=ReplyKeyboardRemove())
    await keydel.delete()

    await client.send_message(
        message.chat.id,
        "به بخش تنظیمات کشور ها خوش آمدید!",
        reply_markup = keyboards,
    )


async def choose_country_handler(client: Client, message: Message):

    countries = await models.Countries.objects.all()
    keyboards = [(country.name, f"choosed:{country.id}") for country in countries]
    keyboards = array_chunk(keyboards, 2)
    keyboards.append([("بازگشت به پنل مدیریت", "panel_handler")])
    keyboards = ikb(keyboards)

    keydel    = await message.reply("Loading!", reply_markup=ReplyKeyboardRemove())
    await keydel.delete()

    await client.send_message(
        message.chat.id,
        "لطفا کشور اکانت ها را مشخص کنید: ",
        reply_markup = keyboards,
    )


async def get_pass_handler(client: Client, message: Message, country_id):
    await message.reply(
        "اکانت ها دارای پسورد هستند؟",
        reply_markup=ikb([
            [("✅", f"password:{country_id}:yes"),("❌", f"password:{country_id}:no")]
        ])
    )


async def add_account_handler(client: Client, message: Message, country_id, password: str = None):

    question: Message = await message.chat.ask(
        "لطفا فایل zip حاوی سشن اکانت ها رو ارسال کنید",
        reply_markup = ReplyKeyboardMarkup([
            ["بازگشت به پنل مدیریت"]
        ], resize_keyboard=True)
    )
    if question.text == "بازگشت به پنل مدیریت":
        return await panel_handler(client, message)
    
    elif question.document and question.document.file_name.endswith(".zip"):
        await question.download(question.document.file_name)

        with ZipFile("downloads/"+question.document.file_name, "r") as zip:
            zip.extractall("accounts")

            load_message  = await client.send_message(message.chat.id, "Loading...")

            counter = 0
            for session_file in zip.filelist:
                # session_file.filename format = 1.+12831231321.session
                number         = "+"+session_file.filename.split("+")[1].split(".")[0]
                null           = await models.Users.objects.get(user_id = 0)
                country        = await models.Countries.objects.get(id = country_id)
                session_string = await models.export_session_string("accounts/"+session_file.filename)

                await models.Accounts.objects.create(
                    user     = null,
                    country  = country,
                    number   = number,
                    password = password,
                    session_string = session_string,
                )
                print("accounts/"+session_file.filename)
                os.remove("accounts/"+session_file.filename)

                counter += 1
                await load_message.edit(f"تعداد {counter} اکانت با موفقیت اضافه شد")
            else:
                await client.send_message(message.chat.id, "عملیات با موفقیت به پایان رسید! ✅")

            os.remove("downloads/"+question.document.file_name)
            return await panel_handler(client, message)
        


async def users_handler(client: Client, message: Message):
    users = await models.Users.objects.all()
    
    question: Message = await message.chat.ask(
        f"به بخش کاربران خوش امدید!\nتعداد کاربران ربات:‌ {len(users)}",
        reply_markup = ReplyKeyboardMarkup([
            ["دریافت اطلاعات کاربر"],
            ["مسدود کردن کاربر", "حذف مسدودیت"],
            ["کاهش موجودی کاربر", "افزایش موجودی کاربر"],
        ], resize_keyboard=True)
    )
    while True:
        next: Message = await message.chat.ask(
            "لطفا ایدی عددی کاربر را ارسال کنید‌:‌",
            reply_markup = ReplyKeyboardMarkup([
                ["انصراف"]
            ], resize_keyboard=True)
        )
        if next.text == "انصراف":
            return await panel_handler(client, message)
            
        user_id = next.text
        try:
            user = await models.Users.objects.get(user_id=user_id)
            break
        except:
            await next.reply("این کاربر در دیتابیس یافت نشد !لطفا دوباره امتحان کنید!")

    match question.text:
        case "دریافت اطلاعات کاربر":
            keyboards = [[(f"{field}", "None"), (f"{getattr(user, field)}", "None")] for field in user.fields]
            keyboards.append([("بازگشت به پنل مدیریت", "panel_handler")])
            await question.reply(
                "اطلاعات کاربر یه شرح زیر است:",
                reply_markup=ikb(keyboards)
            )

        case "حذف مسدودیت":
            await user.update(is_banned = False)
            await client.send_message(message.chat.id, "کاربر از لیست مسدود ها خارج شد ✅")
            return await panel_handler(client, message)
        
        case "مسدود کردن کاربر":
            await user.update(is_banned = True)
            await client.send_message(message.chat.id, "کاربر به لیست مسدود ها اضافه شد ✅")
            return await panel_handler(client, message)
        
        case "افزایش موجودی کاربر":
            while True:
                balance_: Message = await message.chat.ask(
                    "مقداری که میخاهید به موجودی کاربر اضافه شود را وارد کنید (فقط عدد!)"
                )
                try:
                    balance = int(balance_.text)
                    break
                except :
                    await balance_.reply("فقط مقدار عددی قابل قبول است لطفا دوباره امتحان کنید!")

            print(balance, user.balance)
            await user.update(balance = user.balance + balance)
            await balance_.reply(f"موجودی کاربر به موفقیت به {user.balance} تغییر یافت!")

            return await panel_handler(client, message)

        case "کاهش موجودی کاربر":
            while True:
                balance_: Message = await message.chat.ask(
                    "مقداری که میخاهید از موجودی کاربر کسر شود را وارد کنید (فقط عدد!)"
                )
                try:
                    balance = int(balance_.text)
                    break
                except :
                    await balance_.reply("فقط مقدار عددی قابل قبول است لطفا دوباره امتحان کنید!")

            await user.update(balance = user.balance - balance if user.balance - balance > 0 else 0)
            await balance_.reply(f"موجودی کاربر به موفقیت به {user.balance} تغییر یافت!")

            return await panel_handler(client, message)
    
    