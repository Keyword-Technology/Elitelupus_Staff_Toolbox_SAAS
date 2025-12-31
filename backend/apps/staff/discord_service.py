"""Discord bot service for monitoring staff member presence and status."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import discord
from django.conf import settings
from django.utils import timezone

from .models import StaffRoster

logger = logging.getLogger(__name__)


class DiscordStatusBot:
    """Discord bot for tracking staff member presence and status."""
    
    def __init__(self):
        """Initialize the Discord bot."""
        self.bot = None
        self.guild_id = None
        self.is_running = False
        self.loop = None
        
    async def start_bot(self, token: str, guild_id: int):
        """Start the Discord bot.
        
        Args:
            token: Discord bot token
            guild_id: Discord server (guild) ID to monitor
        """
        if self.is_running:
            logger.warning("Bot is already running")
            return
            
        self.guild_id = guild_id
        
        # Set up intents
        intents = discord.Intents.default()
        intents.presences = True  # Required for presence updates
        intents.members = True    # Required for member information
        intents.guilds = True     # Required for guild information
        
        # Create bot client
        client = discord.Client(intents=intents)
        self.bot = client
        
        @client.event
        async def on_ready():
            """Bot is ready and logged in."""
            logger.info(f"Discord bot logged in as {client.user}")
            self.is_running = True
            
            # Initial sync of all member statuses
            await self.sync_all_member_statuses()
        
        @client.event
        async def on_presence_update(before, after):
            """Handle presence updates for members."""
            # Only track members in our staff roster
            if after.guild.id == self.guild_id:
                await self.update_member_status(after)
        
        # Start the bot
        try:
            await client.start(token)
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}")
            self.is_running = False
            raise
    
    async def stop_bot(self):
        """Stop the Discord bot."""
        if self.bot and self.is_running:
            await self.bot.close()
            self.is_running = False
            logger.info("Discord bot stopped")
    
    async def sync_all_member_statuses(self):
        """Sync status for all staff members in the guild."""
        if not self.bot or not self.is_running:
            logger.warning("Bot is not running, cannot sync statuses")
            return
        
        try:
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                logger.error(f"Guild {self.guild_id} not found")
                return
            
            # Get all staff members with Discord IDs
            staff_members = StaffRoster.objects.filter(
                discord_id__isnull=False,
                is_active=True
            ).exclude(discord_id='')
            
            updated_count = 0
            for staff in staff_members:
                try:
                    # Find member in guild
                    member = guild.get_member(int(staff.discord_id))
                    if member:
                        await self.update_member_status(member, staff)
                        updated_count += 1
                    else:
                        # Member not found, set offline
                        staff.discord_status = 'offline'
                        staff.discord_activity = None
                        staff.discord_custom_status = None
                        staff.discord_status_updated = timezone.now()
                        staff.save()
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error processing staff member {staff.name}: {e}")
            
            logger.info(f"Synced status for {updated_count} staff members")
            
        except Exception as e:
            logger.error(f"Error syncing member statuses: {e}")
    
    async def update_member_status(self, member: discord.Member, staff: Optional[StaffRoster] = None):
        """Update status for a specific member.
        
        Args:
            member: Discord member object
            staff: StaffRoster object (if None, will be looked up)
        """
        try:
            # Find staff member if not provided
            if not staff:
                staff = StaffRoster.objects.filter(
                    discord_id=str(member.id),
                    is_active=True
                ).first()
            
            if not staff:
                return  # Not a tracked staff member
            
            # Get status
            status = str(member.status) if member.status else 'offline'
            
            # Get activity information
            activity_name = None
            custom_status = None
            
            if member.activities:
                for activity in member.activities:
                    if isinstance(activity, discord.CustomActivity):
                        custom_status = activity.name
                    elif activity.name:
                        activity_name = activity.name
            
            # Update staff record
            staff.discord_status = status
            staff.discord_activity = activity_name
            staff.discord_custom_status = custom_status
            staff.discord_status_updated = timezone.now()
            staff.save()
            
            logger.debug(f"Updated status for {staff.name}: {status}")
            
        except Exception as e:
            logger.error(f"Error updating member status: {e}")
    
    async def get_member_status(self, discord_id: str) -> Optional[Dict]:
        """Get current status for a specific Discord user.
        
        Args:
            discord_id: Discord user ID
            
        Returns:
            Dict with status information or None if not found
        """
        if not self.bot or not self.is_running:
            return None
        
        try:
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                return None
            
            member = guild.get_member(int(discord_id))
            if not member:
                return None
            
            # Get activity information
            activity_name = None
            custom_status = None
            
            if member.activities:
                for activity in member.activities:
                    if isinstance(activity, discord.CustomActivity):
                        custom_status = activity.name
                    elif activity.name:
                        activity_name = activity.name
            
            return {
                'status': str(member.status),
                'activity': activity_name,
                'custom_status': custom_status,
            }
            
        except Exception as e:
            logger.error(f"Error getting member status: {e}")
            return None


# Global bot instance
_bot_instance = None
_bot_task = None


def get_bot_instance() -> DiscordStatusBot:
    """Get the global bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = DiscordStatusBot()
    return _bot_instance


async def start_discord_bot():
    """Start the Discord bot in the background."""
    global _bot_task
    
    # Get bot token and guild ID from settings
    bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', None)
    guild_id = getattr(settings, 'DISCORD_GUILD_ID', None)
    
    if not bot_token or not guild_id:
        logger.warning("Discord bot token or guild ID not configured")
        return
    
    bot = get_bot_instance()
    
    # Run bot in background
    _bot_task = asyncio.create_task(bot.start_bot(bot_token, int(guild_id)))
    logger.info("Discord bot started in background")


async def stop_discord_bot():
    """Stop the Discord bot."""
    global _bot_task
    
    bot = get_bot_instance()
    await bot.stop_bot()
    
    if _bot_task:
        _bot_task.cancel()
        try:
            await _bot_task
        except asyncio.CancelledError:
            pass
        _bot_task = None
    
    logger.info("Discord bot stopped")


async def sync_discord_statuses():
    """Sync all Discord statuses."""
    bot = get_bot_instance()
    if bot.is_running:
        await bot.sync_all_member_statuses()
    else:
        logger.warning("Discord bot is not running, cannot sync statuses")
