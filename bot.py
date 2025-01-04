### MIT License

### Copyright (c) 2025 xDVoidGG99

### Permission is hereby granted, free of charge, to any person obtaining a copy
### of this software and associated documentation files (the "Software"), to deal
### in the Software without restriction, including without limitation the rights
### to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
### copies of the Software, and to permit persons to whom the Software is
### furnished to do so, subject to the following conditions:

### The above copyright notice and this permission notice shall be included in all
### copies or substantial portions of the Software.

### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
### IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
### FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
### AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
### LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
### OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
### SOFTWARE.

import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=';', intents=intents)
CATEGORY_ID = YOUR_TICKET_CATEGORY  # Replace with your category ID
GUILD_ID = YOUR_GUILD_ID  # Replace it with your GUID ID
TICKET_ROLE_ID = YOUR_TICKET_ROLE_ID  # TEAM ROLE ID

active_tickets = {}


closed_tickets = set()

typing_messages = {}

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    # Set the status on idle with your custom status
    activity = discord.Activity(
        type=discord.ActivityType.competing,  # Type: watching, playing, listening, etc.
        name="YOUR_STATUS"
    )
    await bot.change_presence(status=discord.Status.idle, activity=activity) # dnd, idle, online, invisible


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        if message.author.id in closed_tickets:
            await message.author.send("Your ticket has been closed. Please open a new ticket if needed.")
            return

        if message.author.id not in active_tickets:
            if message.content.lower() == "openticket":
                embed = discord.Embed(
                    title="🎫 Open a Ticket",
                    description=(
                        "Choose one of the following options to open a ticket:\n\n"
                        "**💰 Buy** - For purchase inquiries\n"
                        "**🛠️ Support** - For help or issues\n"
                        "**🤝 Partner** - For partnership inquiries"
                    ),
                    color=discord.Color.blue()
                )
                embed.set_footer(text="Click a button below to create a ticket.")

                class TicketView(View):
                    def __init__(self):
                        super().__init__()
                        self.add_item(Button(label="💰 Buy", style=discord.ButtonStyle.green, custom_id="ticket_buy"))
                        self.add_item(Button(label="🛠️ Support", style=discord.ButtonStyle.blurple, custom_id="ticket_support"))
                        self.add_item(Button(label="🤝 Partner", style=discord.ButtonStyle.grey, custom_id="ticket_partner"))

                        for button in self.children:
                            button.callback = self.create_ticket(button.label)

                    def create_ticket(self, ticket_type):
                        async def callback(interaction: discord.Interaction):
                            guild = bot.get_guild(GUILD_ID)
                            if not guild:
                                await interaction.response.send_message(
                                    "There was an error accessing the server. Please contact an admin.",
                                    ephemeral=True
                                )
                                return

                            ticket_category = discord.utils.get(guild.categories, name="Tickets")
                            if not ticket_category:
                                ticket_category = await guild.create_category("Tickets")

                            overwrites = {
                                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                                guild.get_role(TICKET_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
                            }
                            ticket_channel = await ticket_category.create_text_channel(
                                name=f"ticket-{interaction.user.name.lower()}-{ticket_type.lower().strip('🤝🛠️💰 ')}",
                                overwrites=overwrites
                            )

                            # Ticket saving
                            active_tickets[interaction.user.id] = ticket_channel.id

                            ticket_embed = discord.Embed(
                                title=f"🎫 Ticket Opened - {ticket_type}",
                                description=(
                                    f"Hello {interaction.user.mention}, your ticket has been created.\n\n"
                                    f"**Category:** {ticket_type}\n"
                                    f"**Opened by:** {interaction.user.mention}\n\n"
                                    "Please describe your issue or inquiry, and a staff member will assist you shortly."
                                ),
                                color=discord.Color.dark_gray()
                            )
                            ticket_embed.set_footer(text="Thank you for reaching out!")
                            await ticket_channel.send(embed=ticket_embed)

                            await interaction.response.send_message(
                                f"Your ticket has been created in **{ticket_category.name}**: {ticket_channel.mention}",
                                ephemeral=True
                            )

                            # Buttons disable
                            for child in self.children:
                                if isinstance(child, Button):
                                    child.disabled = True

                            await interaction.message.edit(view=self)

                        return callback

                await message.author.send(embed=embed, view=TicketView())
            else:
                await message.author.send("You currently do not have an open ticket. Use `openticket` to create one.")
        else:
            ticket_channel_id = active_tickets[message.author.id]
            guild = bot.get_guild(GUILD_ID)
            ticket_channel = guild.get_channel(ticket_channel_id)

            if ticket_channel:
                await ticket_channel.send(f"**{message.author}:** {message.content}")
                if message.attachments:
                    for attachment in message.attachments:
                        await ticket_channel.send(file=await attachment.to_file())

    if isinstance(message.channel, discord.TextChannel) and message.channel.id in active_tickets.values():
        user_id = next(key for key, value in active_tickets.items() if value == message.channel.id)
        user = await bot.fetch_user(user_id)

        await user.send(f"**{message.author}:** {message.content}")
        if message.attachments:
            for attachment in message.attachments:
                await user.send(file=await attachment.to_file())

    await bot.process_commands(message)

@bot.event
async def create_ticket(interaction, ticket_type):
    if interaction.user.id in active_tickets:
        await interaction.response.send_message(
            f"You already have an open ticket. Please wait until it is resolved or close it before creating a new one.",
            ephemeral=True
        )
        return

    guild = bot.get_guild(GUILD_ID)
    category = discord.utils.get(guild.categories, id=CATEGORY_ID)
    ticket_channel = await category.create_text_channel(f"ticket-{ticket_type}-{interaction.user.name}")

    role = discord.utils.get(guild.roles, id=TICKET_ROLE_ID)
    overwrite = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),  
        interaction.user: discord.PermissionOverwrite(view_channel=False),  
        guild.me: discord.PermissionOverwrite(view_channel=True),  
        role: discord.PermissionOverwrite(view_channel=True)
    }
    await ticket_channel.edit(overwrites=overwrite)

    active_tickets[interaction.user.id] = ticket_channel.id

    # Privat message to the user
    embed = discord.Embed(
        title="Ticket Created",
        description=(
            f"Your ticket has been created successfully!\n\n"
            f"Please describe your issue here if you haven't already."
        ),
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

    # Ticket Message in the server (Only staff member can see)
    ticket_embed = discord.Embed(
        title="New Ticket Created",
        description=f"A new ticket has been opened by {interaction.user.mention} ({interaction.user.id}).\n\nCategory: {ticket_type.capitalize()}",
        color=discord.Color.dark_magenta()
    )
    await ticket_channel.send(embed=ticket_embed)

@bot.command()
async def close(ctx):
    if ctx.channel.id in active_tickets.values():
        user_id = next(key for key, value in active_tickets.items() if value == ctx.channel.id)

        del active_tickets[user_id]
        closed_tickets.add(user_id)

        embed = discord.Embed(
            title="Ticket Closed",
            description="This ticket has been closed. Thank you!",
            color=discord.Color.red()
        )

        user = await bot.fetch_user(user_id)
        if user:
            try:
                await user.send("Your ticket has been closed. If you need further assistance, please open a new ticket.")
            except discord.Forbidden:
                pass

        await ctx.send(embed=embed)
        await ctx.channel.delete()

@bot.event
async def on_message_edit(before, after):
    if before.author == bot.user:
        return

    if isinstance(before.channel, discord.DMChannel):
        if before.author.id in active_tickets:
            ticket_channel_id = active_tickets[before.author.id]
            guild = bot.get_guild(GUILD_ID)
            ticket_channel = guild.get_channel(ticket_channel_id)

            if ticket_channel:
                async for msg in ticket_channel.history(limit=500):
                    if msg.content.startswith(f"**{before.author}:**") and msg.content.endswith(before.clean_content):
                        await msg.edit(content=f"**{before.author}:** {after.clean_content}")
                        break

    elif before.channel.id in active_tickets.values():
        user_id = next(key for key, value in active_tickets.items() if value == before.channel.id)
        user = await bot.fetch_user(user_id)

        if user:

            async for msg in user.history(limit=500):
                if msg.content.startswith(f"**{before.author}:**") and msg.content.endswith(before.clean_content):
                    await msg.edit(content=f"**{before.author}:** {after.clean_content}")
                    break


bot.run("YOUR_BOT_TOKEN")
