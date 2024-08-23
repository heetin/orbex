import discord
from discord.ext import commands, tasks
import asyncio
import time

intents = discord.Intents.default()
intents.message_content = True  # Habilitar esto si necesitas acceder al contenido de los mensajes

bot = commands.Bot(command_prefix="!", intents=intents)

orbe_holders = {}  # Dictionary to keep track of orb holders and their expiration times

notification_channel_id = 1276126478656081971  # ID del canal donde se enviarán las notificaciones
default_map_name = "Quaent-Viesom"  # Nombre predeterminado para "hq"

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    send_reminders.start()  # Iniciar la tarea de enviar recordatorios cuando el bot esté listo

def get_expiry_time(color):
    if color == "verde":
        return 5 * 60  # 5 minutos
    elif color == "azul":
        return 20 * 60  # 20 minutos
    elif color == "morada":
        return 30 * 60  # 30 minutos
    elif color == "dorada":
        return 40 * 60  # 40 minutos
    return None

@bot.command()
async def orbe(ctx, color: str = None, *, map_name: str = None):
    if color is None:
        await ctx.send("Uso correcto: !orbe <color> <nombre del mapa>\nEjemplo: !orbe verde Qient-Sus")
        return

    color = color.lower()
    if color not in ["verde", "azul", "morada", "dorada"]:
        await ctx.send("Color de orbe no válido. Usa: verde, azul, morada, dorada.")
        return

    # Reemplazar "hq" por el nombre predeterminado
    if map_name.lower() == "hq":
        map_name = default_map_name

    if map_name is None:
        await ctx.send("Debes proporcionar un nombre de mapa.\nUso correcto: !orbe <color> <nombre del mapa>\nEjemplo: !orbe verde Qient-Sus")
        return

    current_time = time.time()
    if color in orbe_holders and map_name in orbe_holders[color]:
        holder, expiry_timestamp = orbe_holders[color][map_name]
        remaining_time = expiry_timestamp - current_time
        if remaining_time > 0:
            minutes, seconds = divmod(int(remaining_time), 60)
            await ctx.send(f"La orbe {color} en el mapa {map_name} ya está activa y la tiene {holder.display_name}. Tiempo restante: {minutes} minutos y {seconds} segundos.")
            return

    expiry_time = get_expiry_time(color)
    if expiry_time:
        if color not in orbe_holders:
            orbe_holders[color] = {}
        expiry_timestamp = current_time + expiry_time
        orbe_holders[color][map_name] = (ctx.author, expiry_timestamp)
        await ctx.send(f"{ctx.author.display_name} reclamó la orbe {color} en el mapa {map_name} por {expiry_time // 60} minutos.")
        await notify_claim(ctx.author, color, map_name, expiry_time)
        await expire_orbe(color, map_name, expiry_time, ctx.channel)
    else:
        await ctx.send("Color de orbe no válido.")

@bot.command()
async def orbes_activas(ctx):
    current_time = time.time()
    active_orbes = []
    for color, maps in orbe_holders.items():
        for map_name, (holder, expiry_timestamp) in maps.items():
            remaining_time = expiry_timestamp - current_time
            if remaining_time > 0:
                minutes, seconds = divmod(int(remaining_time), 60)
                active_orbes.append(f"{color.capitalize()} en {map_name}: {holder.display_name} - Tiempo restante: {minutes} minutos y {seconds} segundos")
    
    if active_orbes:
        await ctx.send("Orbes activas:\n" + "\n".join(active_orbes))
    else:
        await ctx.send("No hay orbes activas en este momento.")

async def notify_claim(user, color, map_name, expiry_time):
    channel = bot.get_channel(notification_channel_id)
    if channel:
        minutes = expiry_time // 60
        await channel.send(f"{user.display_name} reclamó la orbe {color} en el mapa {map_name} por {minutes} minutos.")

async def expire_orbe(color, map_name, delay, channel):
    await asyncio.sleep(delay)
    del orbe_holders[color][map_name]
    await channel.send(f"La orbe {color} en el mapa {map_name} ha expirado.")

# Tarea para enviar recordatorios cada 10 minutos
@tasks.loop(minutes=10)
async def send_reminders():
    channel = bot.get_channel(notification_channel_id)
    if channel:
        message = (
            "**Recordatorio de Comandos:**\n"
            "`!orbe (COLOR) (MAPA)` - Usa este comando para reclamar un orbe del color especificado, aclarando el mapa donde está el orbe.\n\n`!orbe azul hq` < Para claimear un orbe dentro de nuestro mapa."
            "\n\n`!orbes_activas` - Muestra las orbes actualmente activasy reclamadas por algun compañero de la alianza."
        )
        await channel.send(message)

bot.run('')
