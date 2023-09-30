from pyrogram import Client, idle
from pyromod import listen

import plugins.models as models
import plugins.config as config

import sys
import os
# setting path
sys.path.append('plugins')

plugins = dict(root="plugins/")

app = Client(
    name      = "session",
    api_id    = config.API_ID,
    api_hash  = config.API_HASH,
    proxy     = config.PROXY["Phone"],
    bot_token = config.API_TOKEN,
    plugins   = plugins,
    )

with app:
    if not os.path.exists("database/database.sqlite"):
        app.loop.run_until_complete(models.main())
        
    print("running...")
    idle()