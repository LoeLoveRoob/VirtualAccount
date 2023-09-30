from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from pyromod.helpers import ikb

import plugins.models as models
import plugins.admin.commands as commands



@Client.on_callback_query(filters.regex(r"^country"))
async def countries_callback(client: Client, query: CallbackQuery):

    data       = query.data
    country_id = data.split(":")[1]
    message    = query.message
    country    = await models.Countries.objects.get(id = country_id )

    keyboards = [[(field, f"{country.id}:{field}"), (str(getattr(country, field)), "None")] for field in country.fields]
    keyboards.append([("حذف کشور ❌", f"delete:{country.id}")])
    keyboards.append([("بازگشت به پنل مدیریت", "panel_handler")])
    
    await message.edit(
        "برای تغییر هر مقدار روی اسم ان کلیک کنید (دکمه سمت چپ)",
        reply_markup=ikb(keyboards)
    )


@Client.on_callback_query(filters.regex(r"^delete"))
async def delete_country_callback(client: Client, query: CallbackQuery):
    data       = query.data
    message    = query.message
    country_id = data.split(":")[1]
    country    = await models.Countries.objects.get(id=country_id)

    await country.delete()
    await query.answer(f"کشور {country.name} با موفقیت حذف شد ✅")
    await message.delete()
    return await commands.country_handler(client, message)


@Client.on_callback_query(filters.regex(r"id|name|code|price"))
async def change_country_callback(client: Client, query: CallbackQuery):
        data       = data.split(":")
        message    = query.message
        country_id = data[0]
        field      = data[1]

        country = await models.Countries.objects.get(id = country_id)
        if field == "id":
            await query.answer("این مقدار قابل تغییر نیست!")
        else:
            await message.delete()
            question: Message = await message.chat.ask(
                f"مقداری که میخواهید جایگزین {getattr(country, field)} در فیلد {field} شود را وارد کنید:",
                reply_markup = ReplyKeyboardMarkup([
                    ["انصراف"]
                ], resize_keyboard=True)
            )
            value = question.text
            try:
                await country.update(**{field: value})
                await question.reply(f"مقدار فیلد {field} با موفقیت به {value} تغییر یافت ✅")
            except:
                try:
                    value = int(value)
                    await country.update(**{field: value})
                    await question.reply(f"مقدار فیلد {field} با موفقیت به {value} تغییر یافت ✅")
                except ValueError:
                    await question.reply(f"❌ مقدار فیلد {field} باید از نوع عددی باشد! ")
            return await commands.panel_handler(client, message)


@Client.on_callback_query(filters.regex(r"^addcountry"))
async def add_country_callback(client: Client, query: CallbackQuery):
    data    = query.data
    message = query.message

    country_fields  = models.Countries.fields
    fields  = {}
    for field in country_fields:
        if field == "id":
            continue

        value: Message = await message.chat.ask(
            f"لطفا {field} کشور را وارد کنید: ",
        )
        fields[field] = value.text
    try:
        country = await models.Countries.objects.create(**fields)
        await client.send_message(
            message.chat.id,
            f"کشور {country.name} با موفقیت اضافه شد ✅"
        )
        return await commands.panel_handler(client, message)
    except:
        await client.send_message(
            message.chat.id,
            f"کشور اضافه نشد! ❌"
        )
        return await commands.panel_handler(client, message)

@Client.on_callback_query(filters.regex(r"^choosed"))
async def choose_country_callback(client: Client, query: CallbackQuery):
    country_id = query.data.split(":")[1]
    country = await models.Countries.objects.get(id = country_id)

    await query.message.delete()
    await query.answer(f"کشور {country.name} با موفقیت انتخاب شد!")
    return await commands.get_pass_handler(client, query.message, country_id)



@Client.on_callback_query(filters.regex(r"^password"))
async def check_pass_callback(client: Client, query: CallbackQuery):
    country_id = query.data.split(":")[1]
    has_pass = query.data.split(":")[2]
    has_pass = True if has_pass == "yes" else False
    message  = query.message

    await query.message.delete()

    if has_pass:
        question: Message = await message.chat.ask(
            "پسورد را وارد کنید:",
            reply_markup = ReplyKeyboardMarkup([
                ["انصراف"]
            ], resize_keyboard=True)
        )
        if question.text == "انصراف":
            return await commands.add_account_handler(client, message, country_id = country_id)
        
        await question.reply(f"پسورد `{question.text}` با موفقیت ست شد ✅")
        return await commands.add_account_handler(client, message, password = question.text, country_id = country_id)
    else:
        return await commands.add_account_handler(client, message, country_id = country_id)


@Client.on_callback_query(filters.regex(r"^panel_handler"))
async def go_to_panel_handler(client: Client, query: CallbackQuery):
        await query.message.delete()
        return await commands.panel_handler(client, query.message)
    