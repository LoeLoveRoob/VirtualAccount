import asyncio
import databases
import orm
import struct
import base64

import plugins.config as config

database = databases.Database("sqlite+aiosqlite:///database/database.sqlite")
models = orm.ModelRegistry(database)


class Users(orm.Model):
    tablename = "Users"
    registry = models
    fields = {
        "id":        orm.Integer(primary_key=True),
        "user_id":   orm.Integer(unique=True),
        "balance":   orm.Integer(default=0),
        "is_banned": orm.Boolean(default=False),
        "is_admin":  orm.Boolean(default=False),
    }

class Countries(orm.Model):
    tablename = "Countries"
    registry = models
    fields = {
        "id":     orm.Integer(primary_key=True),
        "name":   orm.String(max_length=20),
        "code":   orm.Integer(),
        "price":  orm.Integer(),
    }

class Accounts(orm.Model):
    tablename = "Accounts"
    registry = models
    fields = {
        "id":             orm.Integer(primary_key=True),
        "user":           orm.ForeignKey(Users),
        "country":        orm.ForeignKey(Countries),
        "number":         orm.Integer(unique=True),
        "password":       orm.String(max_length=256, allow_null=True),
        "session_string": orm.Text(),
    }

class Channels(orm.Model):
    tablename = "Channels"
    registry  = models
    fields = {
        "id": orm.Integer(primary_key=True),
        "channel_id": orm.Integer(unique=True),
    }

async def export_session_string(session_file):
    database = databases.Database(f"sqlite+aiosqlite:///{session_file}")
    models = orm.ModelRegistry(database)

    class Sessions(orm.Model):
        tablename = "sessions"
        registry  = models
        fields    = {
            "dc_id":     orm.Integer(primary_key=True),
            "api_id":    orm.Integer(),
            "test_mode": orm.Boolean(default=False),
            "auth_key":  orm.String(max_length=256),
            "date":      orm.Integer(),
            "user_id":   orm.Integer(),
            "is_bot":    orm.Boolean(),
            }
        
    await models.create_all()
    sessions = await Sessions.objects.all()
    session  = sessions[0]

    SESSION_STRING_FORMAT = ">BI?256sQ?"
    packed = struct.pack(
        SESSION_STRING_FORMAT,
        session.dc_id,
        session.api_id,
        session.test_mode,
        session.auth_key,
        session.user_id,
        session.is_bot,
    )

    return base64.urlsafe_b64encode(packed).decode().rstrip("=")


async def main():
    await models.create_all()

    await Countries.objects.create(
        name = "امریکا",
        code = 1,
        price = 5_000,
    )
    await Countries.objects.create(
        name = "کانادا",
        code = 1,
        price = 5_000,
    )
    await Users.objects.create(
        user_id = config.ADMIN,
        is_admin = True,
    )
    await Users.objects.create(
        user_id = 0,
    )

async def cmd():
    process = await Countries.objects.all()
    print(process[0].name)
    await Accounts.objects.create(
        user = await Users.objects.get(user_id = 799041666),
        country = process[0],
        number = +1933203433448,
        password = None,
        session_string = "sssssssssssssssssssssssssss",
    )

if __name__ == "__main__":
    asyncio.run(main())

    
    