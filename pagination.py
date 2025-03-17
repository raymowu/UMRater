import discord
from typing import Callable, Optional


class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, tiers_indexes, get_page: Callable):
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 1
        self.tiers_indexes = tiers_indexes
        self.tiers_index = 0
        super().__init__(timeout=100)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navegate(self):
        emb, self.total_pages = await self.get_page(self.index)
        if self.total_pages == 1:
            await self.interaction.response.send_message(embed=emb)
        elif self.total_pages > 1:
            self.update_buttons()
            await self.interaction.response.send_message(embed=emb, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == 1
        self.children[2].label = f"{self.index}/{self.total_pages}"
        self.children[3].disabled = self.index == self.total_pages
        self.children[4].disabled = self.index == self.total_pages

    @discord.ui.button(label="◀◀", style=discord.ButtonStyle.blurple)
    async def previous_tier(self, interaction: discord.Interaction, button: discord.Button):
        if self.tiers_index != 0:
            self.tiers_index -= 1
        self.index = self.tiers_indexes[self.tiers_index]
        await self.edit_page(interaction)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        if self.tiers_index != 0 and self.index == self.tiers_indexes[self.tiers_index - 1]:
            self.tiers_index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(style=discord.ButtonStyle.gray, disabled=True)
    async def page_count(self, interaction: discord.Interaction, button: discord.Button):
        return

    @discord.ui.button(label="▶", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        if self.tiers_index != len(self.tiers_indexes) - 1 and self.index == self.tiers_indexes[self.tiers_index + 1]:
            self.tiers_index += 1
        await self.edit_page(interaction)

    @discord.ui.button(label="▶▶", style=discord.ButtonStyle.blurple)
    async def end(self, interaction: discord.Interaction, button: discord.Button):
        if self.tiers_index != len(self.tiers_indexes) - 1:
            self.tiers_index += 1
            self.index = self.tiers_indexes[self.tiers_index]
        else:
            self.index = self.total_pages
        await self.edit_page(interaction)

    async def on_timeout(self):
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(total_results: int, results_per_page: int) -> int:
        return ((total_results - 1) // results_per_page) + 1