from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from pyromod.helpers import ikb, array_chunk

import plugins.config as config
import plugins.models as models
import plugins.user.commands as commands
from orm.exceptions import NoMatch

@Client.on_callback_query()
async def check_ban(client, query: CallbackQuery):
    try:
        user = await models.Users.objects.get(user_id = query.message.chat.id)
    except NoMatch:
        await models.Users.objects.create(user_id = query.message.chat.id)
        return query.continue_propagation()
    
    if user.is_banned:
        return query.stop_propagation()
    else:
        return query.continue_propagation()


@Client.on_callback_query(filters.regex(r"^addbalance"))
async def addbalance_callback(client: Client, query: CallbackQuery):
    await query.message.edit(
        "برای افزایش موجودی به پیوی ادمین مراجعه کنید!",
        reply_markup=ikb([
            [("پیوی ادمین", f"t.me/{config.ADMIN_USERNAME}", "url")],
        ])
    )
    return await commands.start_handler(client, query.message)


@Client.on_callback_query(filters.regex(r"^showaccounts"))
async def show_accounts_callback(client: Client, query: CallbackQuery):
    message  = query.message
    user     = await models.Users.objects.get(user_id = message.chat.id)
    accounts = await models.Accounts.objects.all(user = user.id)
    print(accounts)
    if accounts:
        await message.edit(
            "اکانت هایی که شما خریداری کردید:",
            reply_markup = ikb(array_chunk([(f"+{account.number}", f"number:{account.id}") for account in accounts], 2))
        )
    else:
        await query.answer("شما هنوز هیچ اکانتی خریداری نکرده اید!")



@Client.on_callback_query(filters.regex(r"^mainmenu"))
async def goto_mainmenu(client: Client, query: CallbackQuery):
    return await commands.start_handler(client, query.message)