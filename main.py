import discord
from discord.ext import commands
from discord import app_commands
import csv
import os
from pathlib import Path
from datetime import datetime

# ============ Configuracion Inicial del Bot (Importante) ============

TOKEN = ("DISCORD_TOKEN")  # export DISCORD_TOKEN="tu_token"

# Canal & roles (sustituye si cambian en tu servidor)
Apertura_Canal = 921656304488046645
Rol_Ciudadano = 1352343946755313801
ROL_MODERACION_ID = 1375219535073902623
Rol_AM = 1383635952840478821 
ROL_CIUDADANO_WHITE_ID = 1379202226395807744
ROL_RAYA1_ID = 1379202248240005200
ROL_RAYA2_ID = 1379202250320384201

CALIFICACIONES_CSV = Path("estrellas_staff.csv")
SANCIONES_CSV = Path("sanciones.csv")

# ============ UTILS ============
def ensure_csv_file(path, headers):
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

def append_csv(path, row):
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ============ BOT SETUP ============
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Sesión iniciada como {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()

# ============ COMANDOS DE CALIFICACIÓN ============
@bot.tree.command(name="calificar_staff", description="Califica a un miembro del staff")
@app_commands.describe(staff="Menciona a un miembro del staff", opinion="Tu opinión sobre el staff", estrellas="Calificación del 0 al 10")
@app_commands.choices(estrellas=[app_commands.Choice(name=f"{i} ⭐", value=i) for i in range(11)])
async def calificar_staff(interaction: discord.Interaction, staff: discord.Member, opinion: str, estrellas: int):
    if ROL_MODERACION_ID not in [role.id for role in staff.roles]:
        await interaction.response.send_message(f"❌ {staff.mention} no pertenece al Equipo de Moderación.", ephemeral=True)
        return

    ensure_csv_file(CALIFICACIONES_CSV, ["staff_id", "staff_nombre", "usuario_discord", "opinion", "estrellas"])
    append_csv(CALIFICACIONES_CSV, [staff.id, staff.display_name, interaction.user.id, opinion, estrellas])

    ratings = [int(r["estrellas"]) for r in read_csv(CALIFICACIONES_CSV) if int(r["staff_id"]) == staff.id]
    promedio = sum(ratings) / len(ratings) if ratings else 0

    embed = discord.Embed(title="✅ Calificación Registrada", description=f"📩 Calificación sobre **{staff.mention}** guardada.", color=discord.Color.green())
    embed.add_field(name="👤 Usuario", value=interaction.user.mention)
    embed.add_field(name="🏅 Staff", value=staff.mention)
    embed.add_field(name="⭐ Calificación", value=f"**{estrellas}/10**")
    embed.add_field(name="🗨️ Opinión", value=f"```{opinion}```", inline=False)
    embed.add_field(name="📊 Promedio actual", value=f"**{promedio:.2f}/10**")
    embed.set_thumbnail(url=staff.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="ver_calificacion", description="Muestra la calificación de un staff")
async def ver_calificacion(interaction: discord.Interaction, staff: discord.Member):
    ensure_csv_file(CALIFICACIONES_CSV, ["staff_id", "staff_nombre", "usuario_discord", "opinion", "estrellas"])
    ratings = [int(r["estrellas"]) for r in read_csv(CALIFICACIONES_CSV) if int(r["staff_id"]) == staff.id]
    if not ratings:
        await interaction.response.send_message(f"🔍 {staff.mention} no tiene calificaciones.", ephemeral=True)
        return

    promedio = sum(ratings) / len(ratings)
    embed = discord.Embed(title="📊 Calificación del Staff", description=f"Calificaciones de {staff.mention}", color=discord.Color.teal())
    embed.add_field(name="⭐ Total de Estrellas", value=str(sum(ratings)))
    embed.add_field(name="📊 Promedio", value=f"**{promedio:.2f}/10**")
    embed.add_field(name="📈 Total de Calificaciones", value=str(len(ratings)))
    embed.set_thumbnail(url=staff.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=False)

# ============ COMANDOS DE SANCIONES ============
@bot.tree.command(name="sancionar", description="Aplica una sanción a un usuario")
@app_commands.describe(usuario="Usuario sancionado", motivo="Motivo de la sanción")
async def sancionar(interaction: discord.Interaction, usuario: discord.User, motivo: str):
    if ROL_MODERACION_ID not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("🚫 No tienes permisos para usar este comando.", ephemeral=True)
        return

    ensure_csv_file(SANCIONES_CSV, ["usuario_discord", "motivo", "numero_sancion", "fecha_sancion", "staff_id", "apelada", "apelo_staff_id"])
    sanciones = [row for row in read_csv(SANCIONES_CSV) if int(row["usuario_discord"]) == usuario.id and row["apelada"] == "False"]

    if len(sanciones) >= 3:
        await interaction.response.send_message(f"🚫 {usuario.mention} ya tiene 3 sanciones activas.", ephemeral=True)
        return

    numero = len(sanciones) + 1
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    append_csv(SANCIONES_CSV, [usuario.id, motivo, numero, fecha, interaction.user.id, "False", ""])

    embed = discord.Embed(title="🚨 Nueva Sanción", description=f"🔒 {usuario.mention} sancionado.", color=discord.Color.dark_red())
    embed.add_field(name="📄 Motivo", value=f"```{motivo}```")
    embed.add_field(name="📌 Número", value=f"**{numero}/3**")
    embed.add_field(name="🕒 Fecha", value=f"<t:{int(datetime.now().timestamp())}>")
    embed.add_field(name="👮‍♂️ Staff", value=interaction.user.mention)
    embed.set_thumbnail(url=usuario.avatar.url if usuario.avatar else usuario.default_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sanciones_historial", description="Muestra historial de sanciones activas")
@app_commands.describe(usuario="Usuario")
async def sanciones_historial(interaction: discord.Interaction, usuario: discord.User):
    if ROL_MODERACION_ID not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("🚫 No tienes permisos.", ephemeral=True)
        return

    ensure_csv_file(SANCIONES_CSV, ["usuario_discord", "motivo", "numero_sancion", "fecha_sancion", "staff_id", "apelada", "apelo_staff_id"])
    sanciones = [s for s in read_csv(SANCIONES_CSV) if int(s["usuario_discord"]) == usuario.id and s["apelada"] == "False"]

    if not sanciones:
        await interaction.response.send_message(f"{usuario.mention} no tiene sanciones activas.", ephemeral=True)
        return

    embed = discord.Embed(title=f"📜 Sanciones Activas - {usuario.display_name}", color=discord.Color.orange())
    for sancion in sanciones:
        embed.add_field(name=f"🔹 Sanción #{sancion['numero_sancion']} - 📅 {sancion['fecha_sancion']}", value=f"**Motivo**: {sancion['motivo']}\n👮 Staff: <@{sancion['staff_id']}>", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="apelar_sancion", description="Apela la última sanción de un usuario")
@app_commands.describe(usuario="Usuario")
async def apelar_sancion(interaction: discord.Interaction, usuario: discord.User):
    if ROL_MODERACION_ID not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("🚫 Solo moderadores.", ephemeral=True)
        return

    sanciones = read_csv(SANCIONES_CSV)
    for i in reversed(range(len(sanciones))):
        if int(sanciones[i]["usuario_discord"]) == usuario.id and sanciones[i]["apelada"] == "False":
            sanciones[i]["apelada"] = "True"
            sanciones[i]["apelo_staff_id"] = str(interaction.user.id)
            break
    else:
        await interaction.response.send_message(f"⚠️ {usuario.mention} no tiene sanciones activas.", ephemeral=True)
        return

    with open(SANCIONES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["usuario_discord", "motivo", "numero_sancion", "fecha_sancion", "staff_id", "apelada", "apelo_staff_id"])
        writer.writeheader()
        writer.writerows(sanciones)

    embed = discord.Embed(title="🙋 Sanción Apelada", description=f"Última sanción de {usuario.mention} marcada como apelada.", color=discord.Color.green())
    embed.add_field(name="🙋 Apelada por", value=interaction.user.mention)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vaciar-sanciones", description="Elimina todas las sanciones")
async def vaciar_sanciones(interaction: discord.Interaction):
    if Rol_AM not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("🚫 Solo altos mandos.", ephemeral=True)
        return

    ensure_csv_file(SANCIONES_CSV, ["usuario_discord", "motivo", "numero_sancion", "fecha_sancion", "staff_id", "apelada", "apelo_staff_id"])
    with open(SANCIONES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["usuario_discord", "motivo", "numero_sancion", "fecha_sancion", "staff_id", "apelada", "apelo_staff_id"])

    embed = discord.Embed(title="🗑️ Sanciones Eliminadas", description="Todas las sanciones han sido eliminadas.", color=discord.Color.orange())
    await interaction.response.send_message(embed=embed)

# ============ COMANDO DE WHITELIST ============
@bot.tree.command(name="whitelist", description="Aprueba o rechaza la solicitud de whitelist de un usuario.")
@app_commands.describe(
    usuario="Usuario que aplicó a la whitelist",
    estado="Estado de la whitelist: Aceptado o Rechazado"
)
@app_commands.choices(estado=[
    app_commands.Choice(name="✅ Aceptado", value="aceptado"),
    app_commands.Choice(name="❌ Rechazado", value="rechazado")
])
async def whitelist(interaction: discord.Interaction, usuario: discord.Member, estado: app_commands.Choice[str]):
    await interaction.response.defer(thinking=True, ephemeral=False)

    if ROL_MODERACION_ID not in [role.id for role in interaction.user.roles]:
        await interaction.followup.send("🚫 Solo el equipo de moderación puede usar este comando.", ephemeral=True)
        return

    if estado.value == "aceptado":
        try:
            await usuario.edit(roles=[])
            await usuario.add_roles(
                interaction.guild.get_role(ROL_CIUDADANO_WHITE_ID),
                interaction.guild.get_role(Rol_Ciudadano),
                interaction.guild.get_role(ROL_RAYA1_ID),
                interaction.guild.get_role(ROL_RAYA2_ID)
            )
        except Exception as e:
            await interaction.followup.send(f"⚠️ Error al asignar roles: {e}", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ ¡Whitelist Aprobada!",
            description=(
                f"🎉 ¡Felicidades {usuario.mention}!\n"
                "Tu solicitud ha sido **aceptada**. Bienvenido a **Los Santos Horizons**.\n"
                f"🛡️ Aprobado por: {interaction.user.mention}"
            ),
            color=discord.Color.green()
        )
        embed.set_image(url="https://media.discordapp.net/attachments/921656304488046645/1383633389847969853/image.png?ex=684f8082&is=684e2f02&hm=24ce6b0e8a26640b06e0f826c7caad512a7ebc808c3b8d73227731be20d84f5c&=&format=webp&quality=lossless")
        embed.set_footer(text="Los Santos Horizons | Bienvenido al rol")
        embed.timestamp = discord.utils.utcnow()
    else:
        embed = discord.Embed(
            title="❌ Whitelist Rechazada",
            description=(
                f"{usuario.mention}, tu solicitud de whitelist fue **rechazada**.\n"
                "📖 Lee el reglamento 📜│reglamento y vuelve a intentarlo.\n"
                f"👮 Evaluado por: {interaction.user.mention}"
            ),
            color=discord.Color.red()
        )
        embed.set_image(url="https://media.discordapp.net/attachments/921656304488046645/1383633433414205562/image.png?ex=684f808d&is=684e2f0d&hm=fbe4c86f3b13db61e5e9ae56acbf4e9f0a76d352f13f54e2ba3be4692b3990f8&=&format=webp&quality=lossless")
        embed.set_footer(text="Los Santos Horizons | Normativa en el canal 📜│reglamento")
        embed.timestamp = discord.utils.utcnow()

    await interaction.followup.send(content=usuario.mention, embed=embed)
    
# ============ COMANDO DE MENSAJE A CIUDADANOS ============
@bot.tree.command(name="anuncios", description="Envía un mensaje en embed a todos los ciudadanos.")
@app_commands.describe(
    titulo="Título del mensaje",
    contenido="Contenido del mensaje",
    mencionar="¿Deseas mencionar al rol de Ciudadanos?"
)
@app_commands.choices(mencionar=[
    app_commands.Choice(name="Sí", value="si"),
    app_commands.Choice(name="No", value="no")
])
async def mensaje_ciudadanos(interaction: discord.Interaction, titulo: str, contenido: str, mencionar: app_commands.Choice[str]):
    if ROL_MODERACION_ID not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message("🚫 No tienes permisos para usar este comando.", ephemeral=True)
        return

    embed = discord.Embed(
        title=titulo,
        description=f"```{contenido}```",
        color=discord.Color.dark_blue()
    )
    embed.set_footer(text=f"Mensaje enviado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1382957452810649600/1383637261333168128/Logo_los_santos_Horizon.png?ex=684f841d&is=684e329d&hm=de30785a96afda70eaa62818e5afcf1d72424790308ecfad67c943009cd748e4&=&format=webp&quality=lossless&width=960&height=960")
    embed.timestamp = discord.utils.utcnow()

    if mencionar.value == "si":
        canal = bot.get_channel(Apertura_Canal)
        if canal:
            await canal.send(content=f"<@&{Rol_Ciudadano}>", embed=embed)
            await interaction.response.send_message("✅ Mensaje enviado correctamente.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ No se encontró el canal de apertura.", ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed)


# ============ EJECUTAR EL BOT ============
if __name__ == "__main__":
    ensure_csv_file(CALIFICACIONES_CSV, ["staff_id", "staff_nombre", "usuario_discord", "opinion", "estrellas"])
    ensure_csv_file(SANCIONES_CSV, ["usuario_discord", "motivo", "numero_sancion", "fecha_sancion", "staff_id", "apelada", "apelo_staff_id"])
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN no definido")
    bot.run(TOKEN)
