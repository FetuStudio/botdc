import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

intents = discord.Intents.default()
intents.members = True
intents.messages = True  # Habilitar la lectura de contenido de mensajes
intents.message_content = True  # Habilitar la intención de contenido de mensajes
bot = commands.Bot(command_prefix="!", intents=intents)

CATEGORY_ID = 123456789012345678  # Reemplaza con la ID de la categoría "REGISTROS"
LOG_CHANNEL_ID = 1323612398392840212  # Canal donde se registran cierres de tickets
WELCOME_CHANNEL_ID = 1338539073857392745  # Canal de bienvenida
FAREWELL_CHANNEL_ID = 1340259901552726026  # Canal de despedida
NOTIFY_CHANNEL_ID = 1340071432163688550  # Canal de notificaciones de niveles
MUTE_ROLE_ID = 1340329426944135238  # Reemplaza con la ID del rol de muteo
PREV_ROLE_ID = 1312710261819572286  # Reemplaza con la ID del rol previo


# Roles por nivel (con los IDs proporcionados)
LEVEL_ROLES = {
    10: (1337105639570276422, "LVL 1", "🐱"),  # LVL 1 ID
    50: (1337105773402128424, "LVL 5", "🐶"),  # LVL 5 ID
    150: (1337105945213534298, "LVL 15", "🐢"),  # LVL 15 ID
    250: (1337106168023089162, "LVL 25", "🐖"),  # LVL 25 ID
    500: (1337106274223128577, "LVL 50", "🦣"),  # LVL 50 ID
    750: (1337106695679115277, "LVL 75", "🦦"),  # LVL 75 ID
    1000: (1337106842517639228, "LVL 100", "🦖"),  # LVL 100 ID
    1500: (1337107046239178782, "LVL 150", "🦏"),  # LVL 150 ID
    2000: (1337107171128901757, "LVL 200", "🐉"),  # LVL 200 ID
}

# Diccionario para almacenar los niveles de los jugadores (en memoria)
user_levels = {}

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title=f"Bienvenido jugador {member.display_name} a los Fetu Games 2!",
            description=("Hace frío, ¿no? Normalmente no hace tanto. Supongo que tendremos que correr al ascensor "
                         "para que no nos congelemos de frío. Te veo en la línea de meta y espero que disfrutes del evento."),
            color=discord.Color.blue()
        )
        embed.set_image(url="https://i.ibb.co/bjZD22Nb/Screenshot-2025-02-14-21-28-55-875-com-android-chrome-edit.webp")
        embed.set_footer(text=f"Ahora somos {len(member.guild.members)} jugadores.")
        await channel.send(embed=embed)
        
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(FAREWELL_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title=f"Jopilinines {member.display_name} se ha ido del evento.",
            description=("Me parece increíble que tengas una segunda oportunidad y la falles, podrías haberte muerto de frío, "
                         "podías haberte muerto luchando hasta el final pero no... Esto hiciste y esto quedó, "
                         "suerte en los siguientes Fetu Games 3."),
            color=discord.Color.red()
        )
        embed.set_image(url="https://i.ibb.co/21KMJW2G/Sin-t-tulo-2.jpg")
        embed.set_footer(text=f"Ahora somos {len(member.guild.members)} jugadores.")
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignorar los mensajes del bot

    # Actualizar la cantidad de mensajes del usuario
    user_id = message.author.id
    if user_id not in user_levels:
        user_levels[user_id] = 0
    user_levels[user_id] += 1

    # Comprobar si el usuario ha alcanzado algún nivel
    for messages_needed, (role_id, role_name, role_emoji) in LEVEL_ROLES.items():
        if user_levels[user_id] >= messages_needed and not any(role.id == role_id for role in message.author.roles):
            role = message.guild.get_role(role_id)
            await message.author.add_roles(role)
            
            # Notificar en el canal correspondiente
            notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
            if notify_channel:
                await notify_channel.send(f"{message.author.mention} ha llegado al nivel {role_name} {role_emoji}! 🎉")

    await bot.process_commands(message)

class CloseTicketModal(Modal):
    def __init__(self, ticket_channel: discord.TextChannel, author: discord.Member):
        super().__init__(title="Cerrar Ticket")
        self.ticket_channel = ticket_channel
        self.author = author
        self.reason = TextInput(label="Razón de cierre", required=False)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        reason = self.reason.value if self.reason.value else "No se ha proporcionado una razón."
        
        embed = discord.Embed(title="• Ticket", color=discord.Color.red())
        embed.add_field(name="Ticket cerrado por", value=f"{self.author.display_name}")
        embed.add_field(name="➦ Ticket", value=f"{self.ticket_channel.name} ({self.ticket_channel.id})")
        embed.add_field(name="➦ Panel", value="Inscripción")
        embed.add_field(name="➦ Propietario", value=f"{self.author.display_name} ({self.author.id})")
        embed.add_field(name="➦ Razón de cierre", value=reason)
        
        if log_channel:
            await log_channel.send(embed=embed)
        await self.ticket_channel.delete()

class CloseTicketButton(Button):
    def __init__(self, ticket_channel: discord.TextChannel, author: discord.Member):
        super().__init__(label="Cerrar Ticket", style=discord.ButtonStyle.danger)
        self.ticket_channel = ticket_channel
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CloseTicketModal(self.ticket_channel, interaction.user))

class TicketButton(Button):
    def __init__(self):
        super().__init__(label="Inscríbete", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Crear el canal de tickets privado
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),  # No visible para todos
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),  # Visible solo para el creador
        }

        # Crear el canal de texto en la categoría (puedes omitir la categoría si no la necesitas)
        ticket_channel = await guild.create_text_channel(
            name=f"inscripciones-{interaction.user.display_name}",
            overwrites=overwrites
        )
        
        # Agregar el botón de cerrar ticket
        view = View()
        view.add_item(CloseTicketButton(ticket_channel, interaction.user))
        
        embed = discord.Embed(title="Inscripción a Fetu Games 2", description="Por favor, proporciona la información necesaria.", color=discord.Color.blue())
        await ticket_channel.send(embed=embed, view=view)

        # Confirmar creación del canal
        await interaction.response.send_message(f"Tu inscripción ha sido creada: {ticket_channel.mention}", ephemeral=True)

@bot.command()
async def ins(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="¡Inscríbete a Fetu Games 2!", description="Haz clic en el botón para inscribirte en el evento.", color=discord.Color.green())
    view = View()
    view.add_item(TicketButton())
    await ctx.send(embed=embed, view=view)

@bot.command()
async def muteall(ctx):
    guild = ctx.guild
    role_to_remove = guild.get_role(1312710261819572286)
    muted_role = guild.get_role(1333454344200392746)

    print(f"Rol a eliminar: {role_to_remove}")  # Depuración
    print(f"Rol de muted: {muted_role}")  # Depuración

    if not role_to_remove or not muted_role:
        await ctx.send("No se encontraron los roles especificados.")
        return

@bot.command()
async def unmuteall(ctx):
    guild = ctx.guild
    role_to_add = guild.get_role(1312710261819572286)  # Rol a devolver
    muted_role = guild.get_role(1333454344200392746)  # Reemplaza con la ID del rol "Muted"

    if not role_to_add or not muted_role:
        await ctx.send("No se encontraron los roles especificados.")
        return

    count = 0
    for member in guild.members:
        if muted_role in member.roles:
            try:
                await member.remove_roles(muted_role)
                await member.add_roles(role_to_add)
                count += 1
            except discord.Forbidden:
                await ctx.send(f"No tengo permisos para modificar los roles de {member.mention}.")
            except discord.HTTPException:
                await ctx.send(f"Ocurrió un error al modificar los roles de {member.mention}.")
    
    await ctx.send(f"🔊 {count} miembros han sido desmuteados.")

@bot.command()
async def ruserol(ctx):
    # ID del rol a eliminar
    rol_id = 1312710261819572286
    rol = discord.utils.get(ctx.guild.roles, id=rol_id)

    if not rol:
        await ctx.send("No se ha encontrado el rol con el ID proporcionado.")
        return

    # Iterar sobre todos los miembros del servidor
    for member in ctx.guild.members:
        # Verificar si el miembro tiene el rol
        if rol in member.roles:
            try:
                # Eliminar el rol
                await member.remove_roles(rol)
                print(f'Rol eliminado a {member.name}')
            except discord.Forbidden:
                print(f'No tengo permisos para remover el rol de {member.name}')
            except discord.HTTPException as e:
                print(f'Error al intentar remover rol de {member.name}: {e}')
    await ctx.send("Rol eliminado a todos los miembros que lo tenían.")
  
token = os.getenv("DISCORD_TOKEN")
bot.run(token)
