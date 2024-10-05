import nextcord
import time
import os
from dotenv import load_dotenv
from nextcord.ext import commands
intents = nextcord.Intents.all() # we don't need all intents but this helps save dev time
bot = commands.Bot(command_prefix='bm!', intents=intents)
load_dotenv()

data = {}

recent_data = {}

@bot.event
async def on_ready():
    print(f'BridgeMark logged in as {bot.user.name}')

@bot.command()
async def source(ctx, name, *, channel):
    channel = int(channel.replace('<#', '').replace('>', ''))
    if not name in data.keys():
        data.update({name: {}})
        recent_data.update({name: {'source': None, 'target': []}})

    data[name].update({'source': channel})
    await ctx.send(f'Listening to <#{channel}> as message source for {name}')

@bot.command()
async def target(ctx, name, *, channel):
    channel = int(channel.replace('<#', '').replace('>', ''))
    if not name in data.keys():
        return await ctx.send('Source must be set for this name first')

    if not 'target' in data[name].keys():
        data[name].update({'target': []})

    data[name]['target'].append(channel)
    await ctx.send(f'Listening to <#{channel}> as message target for {name}')

@bot.command(name='data')
async def resultdata(ctx, name):
    data = recent_data[name]

    if not data['source']:
        return await ctx.send('No tests have been ran yet')

    starttime = data['source']
    omitted = []
    results = []

    for index in range(len(data['target'])):
        entry = data['target'][index]
        if entry < starttime:
            omitted.append(index+1)

        results.append(round((entry - starttime)*1000,2)) # measure in ms

    appendices = ''
    if omitted:
        appendices = f'\nResults {", ".join([str(x) for x in omitted])} were omitted'

    average = sum(results) / len(results)
    worst = max(results)
    best = min(results)
    uncertainty = (worst - best) / 2

    await ctx.send(f'Average: {average}ms\nWorst: {worst}ms\nBest: {best}ms\nUncertainty: {uncertainty}ms{appendices}')


@bot.event
async def on_message(message):
    t = time.time()

    if message.content.startswith(bot.command_prefix) and not message.author.bot:
        await bot.process_commands(message)

    for name in data.keys():
        if message.channel.id == data[name]['source']:
            recent_data[name].update({'source': t})
            break
        elif message.channel.id in data[name]['target']:
            if len(recent_data[name]['target']) >= len(data[name]['target']):
                recent_data[name]['target'] = []

            recent_data[name]['target'].append(t)

# unlike Unifier, BridgeMark is not meant to be used by the public
# so we will not be providing token encryption for this bot
bot.run(os.environ.get('TOKEN'))
