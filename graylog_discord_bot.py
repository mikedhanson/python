import requests
import json
import os
import time
import datetime
import discord
import asyncio

TOKEN = 'discordBotToken'
client = discord.Client()

# Creds for graylog instance
uname = 'username'
password = 'password' #plain text passwords are bad
creds = (uname, password)

@client.event
async def on_message(message):
    guild = message.guild
    if message.content == '!info':
        await message.channel.send(f'Server Name: {guild.name}')
        await message.channel.send(f'Server Size: {len(guild.members)}')
        #await message.channel.send(f'Server Name: {guild.owner.display_name}')

headers = {
    'X-Requested-By': 'cli',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

#graylog server information
hostname = "graylogIP"
port = "9000"
interval = 10 #time between api calls in seconds

@client.event
async def parse_logs():

    await client.wait_until_ready()
    gaylog_channel = "channel_To_send_notifications"
    channel = client.get_channel(int(gaylog_channel))  # garylog channel

    print('Log Scrape Initiated')
    counter = 0

    while(True):
        
        # Validate that graylog is up
        #response = os.system("ping -c 1 " + hostname)
        #if response != 0:
        #    print(hostname, 'is down!')
        #    break

        curTime = datetime.datetime.now()
        curTime_formated = curTime.strftime("%Y-%m-%d %X")
        last_n_min = curTime - datetime.timedelta(seconds=interval)
        last_n_min_formated = last_n_min.strftime("%Y-%m-%d %X")

        params = (
            #('query', 'action:\\"tunnel\\-up\\"'),
            #('query', 'logdesc:"Admin login successful"'),
            ('query', 'logdesc:"Admin login successful" OR action:\\"tunnel\\-up\\" OR level:\"critical\"'),
            #('from', '2020-01-01 00:00:00'), #FOR TESTING ONLY
            ('from', last_n_min_formated),
            ('to', curTime_formated),
            ('decorate', 'true'),
        )

        url = "http://"+hostname + ":" + port + "/api/search/universal/absolute"
        data = requests.get(url, headers=headers, params=params, auth=creds).json()
        counter += 1

        if data["total_results"] != 0:
            logs = data["messages"]

            for log in logs:
                index = logs.index(log)

                if "login" in log['message']['action']:
                    login_msg = {
                        "What": log['message']['logdesc'],
                        "User": log['message']['user'],
                        "Time": log['message']['time'],
                        "Source IP": log['message']['srcip'],
                        "Profile": log['message']['profile'],
                        "Level": log['message']['level'],
                        "log_id": log['message']['_id'],
                        "Device": log['message']['source'],
                    }
                    format_login_msg = '\n'.join([f'{key}: {value}' for key, value in login_msg.items()]) #each item to new line as a string
                    #await channel.send(format_login_msg)
                
                    embedVar = discord.Embed(title="Login Event Found", color=0x00ff00)
                    embedVar.add_field(name="Login Event Details", value=format_login_msg, inline=False)
                    embedVar.description = "[Click here to view this log?]( http://"+ hostname + ":" + port + "/messages/graylog_1/" + login_msg.get('log_id') + ")"
                    await channel.send(embed=embedVar)

                if "tunnel-up" in log['message']['action'] :  
                    print("Tunnel established", log['message']['msg'])
                    vpn_msg = { 
                        "What"        : log['message']['logdesc'], 
                        "User"        : log['message']['user'],  
                        "Time"        : log['message']['time'],
                        "Remote IP"   : log['message']['remip'],
                        "Level"       : log['message']['level'],
                        "log_id"      : log['message']['_id'],
                        "Device"      : log['message']['source'], 
                    }
                    formated_vpn_msg = '\n'.join([f'{key}: {value}' for key, value in vpn_msg.items()]) #each item to new line as a string
                                       
                    embed_val = discord.Embed(title="VPN Tunnel Established", color=0x00ff00)
                    embed_val.add_field(name="Tunnel Details", value=formated_vpn_msg, inline=False)
                    embed_val.description = "[Click here to view this log?]( http://"+ hostname + ":" + port + "/messages/graylog_1/" + login_msg.get('log_id') + ")"
                    await channel.send(embed=embed_val)

                if "critical" in log['message']['action'] :
                    await channel.send(f" Critical Alert: { log['message']['msg'] }")

                #else:
                    #await channel.send(f" Log captured but was unable to parse { log['message']['msg'] }")
                
                print("Log numer:", index)
                print("Number of API calls:", counter)

        await asyncio.sleep(interval)

@client.event
async def on_ready():
    print(f'Bot connected as {client.user}')
    print('Logged in as:', "bot_name:", client.user.name, "User_id:", client.user.id)
    print("Bot ready")

client.loop.create_task(parse_logs())
client.run(TOKEN)
