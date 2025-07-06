import asyncio
import os
import time
import traceback
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import discord
from discord.ext import commands, tasks

from .logger import get_logger
from .config_manager import get_config
from .gemini_ai import get_gemini_ai, CodeGenerationRequest, PersonaType
from .code_tester import get_code_tester
from .code_corrector import get_code_corrector
from .project_manager import get_project_manager

logger = get_logger("DiscordBot")

# Bot statistics
bot_stats = {
    'requests_total': 0,
    'requests_success': 0,
    'requests_failed': 0,
    'active_sessions': 0,
    'uptime_start': time.time()
}

class VibeCodeBot(commands.Bot):
    """Advanced Discord bot for AI-powered code generation"""

    def __init__(self):
        self.config = get_config()

        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True

        # Initialize bot
        super().__init__(
            command_prefix=self.config.bot.command_prefix,
            intents=intents,
            description=self.config.bot.description,
            help_command=None  # Custom help command
        )

        # Initialize components
        self.gemini_ai = get_gemini_ai()
        self.code_tester = get_code_tester()
        self.code_corrector = get_code_corrector()
        self.project_manager = get_project_manager()

        # Bot state
        self.active_generations: Dict[int, Dict] = {}
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_corrections": 0,
            "uptime_start": time.time()
        }

        logger.info("VibeCode Bot initialized")

    async def setup_hook(self):
        """Setup hook called when bot is ready"""
        # Add commands
        await self.add_cog(BotCommands(self))

        # Start background tasks
        self.cleanup_task.start()
        self.stats_task.start()

        logger.info("Bot setup completed")

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"🤖 {self.user} is online and ready!")
        logger.info(f"📊 Connected to {len(self.guilds)} guilds")
        logger.info(f"👥 Serving {sum(guild.member_count for guild in self.guilds)} users")

        # Set bot activity
        try:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"for {self.config.bot.command_prefix}code commands"
            )
            await self.change_presence(activity=activity)
        except Exception as e:
            logger.warning(f"Failed to set bot presence: {e}")

        # Send startup message to log channel if configured
        await self._send_startup_notification()

    async def on_message(self, message):
        """Handle incoming messages"""
        # Ignore bot messages
        if message.author.bot:
            return

        # Log user commands
        if message.content.startswith(self.config.bot.command_prefix):
            logger.info(f"COMMAND | User: {message.author.display_name} ({message.author.id}) | "
                       f"Guild: {message.guild.id if message.guild else 'DM'} | "
                       f"Command: {message.content[:100]}")

        # Process commands
        await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        logger.error(f"Command error in {ctx.command}: {error}")

        if isinstance(error, commands.CommandNotFound):
            # Send help message for unknown commands
            await ctx.send(f"❌ Command not found. Use `{self.config.bot.command_prefix}help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f} seconds.")
        else:
            await ctx.send("❌ An error occurred while processing your command.")

    async def _process_code_generation(self, user_id: int, prompt: str, ctx, status_message):
        """Process code generation in background"""
        try:
            # Update stats
            self.generation_stats["total_requests"] += 1

            # Parse request and determine parameters
            generation_params = await self._parse_generation_request(prompt)

            # Update status
            await self._update_status(status_message, "🧠 Generating code with AI...", 0x0099ff)

            # Create generation request
            request = CodeGenerationRequest(
                prompt=prompt,
                language=generation_params["language"],
                project_type=generation_params["project_type"],
                complexity=generation_params["complexity"],
                additional_requirements=generation_params["requirements"],
                user_id=str(user_id)
            )

            # Generate code
            response = await self.gemini_ai.generate_code(request)

            if response.success:
                # Update status
                await self._update_status(status_message, "✅ Code generated successfully!", 0x00ff00)

                # Send the code response
                await self._send_code_response(ctx, response)

                self.generation_stats["successful_generations"] += 1
            else:
                # Error occurred
                embed = discord.Embed(
                    title="❌ Code Generation Failed",
                    description=response.error_message or "Unknown error occurred",
                    color=0xff0000
                )
                await status_message.edit(embed=embed)
                self.generation_stats["failed_generations"] += 1

        except Exception as e:
            logger.error(f"Code generation failed for user {user_id}: {e}")
            await self._send_generation_error(ctx, str(e))
            self.generation_stats["failed_generations"] += 1

        finally:
            # Clean up
            if user_id in self.active_generations:
                del self.active_generations[user_id]

    async def _parse_generation_request(self, prompt: str) -> Dict:
        """Parse generation request to determine parameters"""
        prompt_lower = prompt.lower()

        # Detect language
        language_keywords = {
            "python": ["python", "py", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "react", "vue", "express"],
            "java": ["java", "spring", "maven"],
            "cpp": ["c++", "cpp", "c plus plus"],
            "go": ["go", "golang"],
            "rust": ["rust"],
            "html": ["html", "web page", "website"],
            "css": ["css", "styling", "styles"]
        }

        detected_language = "python"  # default
        for lang, keywords in language_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_language = lang
                break

        # Detect project type
        project_type = "application"
        if any(word in prompt_lower for word in ["bot", "discord", "telegram"]):
            project_type = "bot"
        elif any(word in prompt_lower for word in ["web", "website", "api", "server"]):
            project_type = "web"
        elif any(word in prompt_lower for word in ["game", "pygame", "unity"]):
            project_type = "game"
        elif any(word in prompt_lower for word in ["cli", "command line", "terminal"]):
            project_type = "cli"

        # Detect complexity
        complexity = "medium"
        if any(word in prompt_lower for word in ["simple", "basic", "easy", "beginner"]):
            complexity = "simple"
        elif any(word in prompt_lower for word in ["advanced", "complex", "professional", "enterprise"]):
            complexity = "advanced"

        # Extract additional requirements
        requirements = []
        if "database" in prompt_lower:
            requirements.append("database integration")
        if "gui" in prompt_lower or "interface" in prompt_lower:
            requirements.append("graphical interface")
        if "test" in prompt_lower:
            requirements.append("unit tests")
        if "docker" in prompt_lower:
            requirements.append("docker support")

        return {
            "language": detected_language,
            "project_type": project_type,
            "complexity": complexity,
            "requirements": requirements
        }

    async def _update_status(self, message, status: str, color: int):
        """Update status message"""
        try:
            embed = message.embeds[0]
            embed.color = color

            # Update status field
            for i, field in enumerate(embed.fields):
                if field.name == "Status":
                    embed.set_field_at(i, name="Status", value=status, inline=False)
                    break

            await message.edit(embed=embed)
        except:
            pass  # Ignore edit failures

    async def _send_code_response(self, ctx, response):
        """Send code response to Discord"""
        try:
            # Create main embed
            embed = discord.Embed(
                title="✅ Code Generated Successfully!",
                description=f"**Language:** {response.language}",
                color=0x00ff00
            )

            embed.set_footer(text=f"Generated in {response.generation_time:.1f}s")

            await ctx.send(embed=embed)

            # Send code in code blocks
            code_content = f"```{response.language}\n{response.code}\n```"

            if len(code_content) <= 2000:
                await ctx.send(code_content)
            else:
                # Code is too long, send as file
                file_ext = self._get_file_extension(response.language)
                filename = f"generated_code.{file_ext}"

                # Ensure temp directory exists
                os.makedirs("temp", exist_ok=True)

                with open(f"temp/{filename}", 'w', encoding='utf-8') as f:
                    f.write(response.code)

                with open(f"temp/{filename}", 'rb') as f:
                    file = discord.File(f, filename=filename)
                    await ctx.send(file=file)

                # Clean up temp file
                try:
                    os.remove(f"temp/{filename}")
                except:
                    pass

            # Send explanation if available
            if hasattr(response, 'explanation') and response.explanation:
                explanation = response.explanation[:1900]
                embed = discord.Embed(
                    title="📖 Code Explanation",
                    description=explanation,
                    color=0x0099ff
                )
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending code response: {e}")

    def _get_file_extension(self, language):
        """Get file extension for programming language"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'cpp': 'cpp',
            'c++': 'cpp',
            'c': 'c',
            'go': 'go',
            'rust': 'rs',
            'php': 'php',
            'ruby': 'rb',
            'html': 'html',
            'css': 'css',
            'sql': 'sql',
            'bash': 'sh',
            'shell': 'sh'
        }
        return extensions.get(language.lower(), 'txt')

    async def _send_generation_error(self, ctx, error_msg: str):
        """Send generation error message"""
        error_lower = error_msg.lower()
        
        if "blocked by safety filters" in error_lower or "safety" in error_lower:
            # Safety filter error
            embed = discord.Embed(
                title="⚠️ Content Blocked",
                description="Your request was blocked by content safety filters.",
                color=0xff9900
            )
            embed.add_field(
                name="💡 Try These Solutions",
                value="• Make your request more general and technical\n"
                      "• Focus on educational programming concepts\n"
                      "• Avoid mentioning specific tools or platforms that might be flagged\n"
                      "• Use technical terminology instead of casual language",
                inline=False
            )
            embed.add_field(
                name="✅ Example",
                value=f"Instead of: `create a music bot`\n"
                      f"Try: `create a Python audio processing application`",
                inline=False
            )
        else:
            # Generic error
            embed = discord.Embed(
                title="❌ Code Generation Failed",
                description="Sorry, I couldn't generate your code due to an error.",
                color=0xff0000
            )
            embed.add_field(name="Error", value=f"```{error_msg[:500]}```", inline=False)
            embed.add_field(
                name="What to try",
                value="• Make your request more specific\n"
                      "• Try a different programming language\n"
                      "• Simplify your request\n"
                      "• Try again in a few moments",
                inline=False
            )

        await ctx.send(embed=embed)

    @tasks.loop(hours=24)
    async def cleanup_task(self):
        """Daily cleanup task"""
        try:
            self.project_manager.cleanup_old_projects(days_old=7)
            logger.info("Daily cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")

    @tasks.loop(hours=1)
    async def stats_task(self):
        """Hourly stats logging"""
        try:
            logger.info(f"Hourly stats - Requests: {self.generation_stats['total_requests']}, "
                       f"Success: {self.generation_stats['successful_generations']}, "
                       f"Active: {len(self.active_generations)}")
        except Exception as e:
            logger.error(f"Stats task failed: {e}")

    async def _send_startup_notification(self):
        """Send startup notification"""
        try:
            # This could be enhanced to send to a specific log channel
            logger.info("Bot startup notification sent")
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")


class BotCommands(commands.Cog):
    """Command cog for the bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="code", aliases=["generate", "create"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def generate_code(self, ctx, *, prompt: str):
        """
        Generate code using AI

        Usage: !code <your request>
        Example: !code create a discord bot in python
        """
        user_id = ctx.author.id

        # Check if user already has active generation
        if user_id in self.bot.active_generations:
            await ctx.send("⚠️ You already have an active code generation. Please wait for it to complete.")
            return

        # Validate prompt
        if len(prompt) < 10:
            await ctx.send("❌ Please provide a more detailed description (at least 10 characters).")
            return

        if len(prompt) > 2000:
            await ctx.send("❌ Description too long. Please keep it under 2000 characters.")
            return

        # Start generation process
        self.bot.active_generations[user_id] = {
            "start_time": time.time(),
            "prompt": prompt,
            "status": "starting"
        }

        try:
            # Send initial response
            embed = discord.Embed(
                title="🤖 AI Code Generation Started",
                description=f"**Request:** {prompt[:500]}{'...' if len(prompt) > 500 else ''}",
                color=0x00ff00
            )
            embed.add_field(name="Status", value="🔄 Analyzing request...", inline=False)
            embed.add_field(name="User", value=ctx.author.mention, inline=True)
            embed.add_field(name="Estimated Time", value="30-120 seconds", inline=True)

            status_message = await ctx.send(embed=embed)

            # Update generation info
            self.bot.active_generations[user_id].update({
                "status_message": status_message,
                "ctx": ctx
            })

            # Process generation in background
            asyncio.create_task(self.bot._process_code_generation(user_id, prompt, ctx, status_message))

        except Exception as e:
            logger.error(f"Failed to start code generation for user {user_id}: {e}")
            if user_id in self.bot.active_generations:
                del self.bot.active_generations[user_id]
            await ctx.send("❌ Failed to start code generation. Please try again.")

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Show help information"""
        embed = discord.Embed(
            title="🤖 VibeCode Bot - Help",
            description="Advanced AI-powered code generation bot",
            color=0x0099ff
        )

        embed.add_field(
            name="📝 Main Commands",
            value=f"`{self.bot.config.bot.command_prefix}code <description>` - Generate code from description\n"
                  f"`{self.bot.config.bot.command_prefix}help` - Show this help message\n"
                  f"`{self.bot.config.bot.command_prefix}stats` - Show bot statistics\n"
                  f"`{self.bot.config.bot.command_prefix}status` - Check bot status",
            inline=False
        )

        embed.add_field(
            name="💡 Example Usage",
            value=f"`{self.bot.config.bot.command_prefix}code create a discord bot in python`\n"
                  f"`{self.bot.config.bot.command_prefix}code make a web scraper with requests`\n"
                  f"`{self.bot.config.bot.command_prefix}code build a simple calculator in javascript`",
            inline=False
        )

        embed.add_field(
            name="🎯 Supported Languages",
            value="Python, JavaScript, Java, C++, Go, Rust, HTML/CSS",
            inline=True
        )

        embed.add_field(
            name="⚡ Features",
            value="• AI-powered generation\n• Automatic testing\n• Error correction\n• ZIP packaging",
            inline=True
        )

        embed.set_footer(text="VibeCode Bot - Making coding easier with AI")

        await ctx.send(embed=embed)

    @commands.command(name="stats")
    async def stats_command(self, ctx):
        """Show bot statistics"""
        uptime = time.time() - self.bot.generation_stats["uptime_start"]
        uptime_hours = uptime / 3600

        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=0x00ff00
        )

        embed.add_field(
            name="🎯 Generation Stats",
            value=f"**Total Requests:** {self.bot.generation_stats['total_requests']}\n"
                  f"**Successful:** {self.bot.generation_stats['successful_generations']}\n"
                  f"**Failed:** {self.bot.generation_stats['failed_generations']}\n"
                  f"**Success Rate:** {(self.bot.generation_stats['successful_generations'] / max(1, self.bot.generation_stats['total_requests']) * 100):.1f}%",
            inline=True
        )

        embed.add_field(
            name="🔧 Correction Stats",
            value=f"**Total Corrections:** {self.bot.generation_stats['total_corrections']}\n"
                  f"**Active Generations:** {len(self.bot.active_generations)}\n"
                  f"**Uptime:** {uptime_hours:.1f} hours",
            inline=True
        )

        embed.add_field(
            name="🌐 Server Stats",
            value=f"**Guilds:** {len(self.bot.guilds)}\n"
                  f"**Users:** {sum(guild.member_count for guild in self.bot.guilds)}\n"
                  f"**Latency:** {self.bot.latency * 1000:.1f}ms",
            inline=True
        )

        await ctx.send(embed=embed)

    @commands.command(name="status")
    async def status_command(self, ctx):
        """Check bot status"""
        embed = discord.Embed(
            title="🟢 Bot Status - Online",
            color=0x00ff00
        )

        embed.add_field(name="Version", value=self.bot.config.bot.version, inline=True)
        embed.add_field(name="Latency", value=f"{self.bot.latency * 1000:.1f}ms", inline=True)
        embed.add_field(name="Active Tasks", value=str(len(self.bot.active_generations)), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping_command(self, ctx):
        """Check bot latency"""
        try:
            latency = self.bot.latency * 1000

            if latency < 100:
                color = 0x00ff00  # Green
                status = "Excellent"
            elif latency < 200:
                color = 0xffff00  # Yellow
                status = "Good"
            else:
                color = 0xff0000  # Red
                status = "Poor"

            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Latency: {latency:.1f}ms ({status})",
                color=color
            )

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await ctx.send("❌ Error checking ping.")


async def run_bot():
    """Run the Discord bot"""
    try:
        config = get_config()
        bot = VibeCodeBot()

        logger.info("Starting VibeCode Bot...")
        await bot.start(config.discord.token)

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_bot())
