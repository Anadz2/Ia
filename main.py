#!/usr/bin/env python3
"""
VibeCode Bot - Advanced Discord AI Code Generator
Main entry point for the bot application
"""

import asyncio
import os
import sys
import signal
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.logger import get_logger
from src.config_manager import get_config
from src.discord_bot import run_bot

logger = get_logger("Main")


class BotManager:
    """Bot manager with graceful shutdown handling"""

    def __init__(self):
        self.running = False
        self.bot_task = None

    async def start(self):
        """Start the bot with error handling and restart capability"""
        self.running = True

        # Setup signal handlers for graceful shutdown
        if sys.platform != 'win32':
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("🚀 Starting VibeCode Bot Manager...")

        retry_count = 0
        max_retries = 5

        while self.running and retry_count < max_retries:
            try:
                logger.info(f"Bot startup attempt {retry_count + 1}/{max_retries}")

                # Start bot
                self.bot_task = asyncio.create_task(run_bot())
                await self.bot_task

                # If we reach here, bot stopped normally
                logger.info("Bot stopped normally")
                break

            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break

            except Exception as e:
                retry_count += 1
                logger.error(f"Bot crashed: {e}")

                if retry_count < max_retries:
                    wait_time = min(60, 10 * retry_count)  # Exponential backoff, max 60s
                    logger.info(f"Restarting in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max retries reached, giving up")
                    break

        logger.info("Bot manager shutting down")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False

        if self.bot_task and not self.bot_task.done():
            self.bot_task.cancel()

    async def stop(self):
        """Stop the bot gracefully"""
        self.running = False

        if self.bot_task and not self.bot_task.done():
            self.bot_task.cancel()
            try:
                await self.bot_task
            except asyncio.CancelledError:
                pass


def check_environment():
    """Check if environment is properly configured"""
    logger.info("🔍 Checking environment configuration...")

    errors = []
    warnings = []

    # Check Python version
    if sys.version_info < (3, 7):
        errors.append("Python 3.7 or higher is required")
    else:
        logger.info(f"✅ Python version: {sys.version}")

    # Check if config.py exists
    config_file = Path("config.py")
    if not config_file.exists():
        errors.append("config.py file not found! Please create and configure config.py")
    else:
        logger.info("✅ config.py file found")
        
        # Try to import and validate config
        try:
            sys.path.insert(0, str(Path.cwd()))
            import config as bot_config
            
            # Validate configuration
            config_errors = bot_config.validate_config()
            if config_errors:
                errors.extend(config_errors)
            else:
                logger.info("✅ Configuration validation passed")
                
        except ImportError as e:
            errors.append(f"Cannot import config.py: {e}")
        except Exception as e:
            errors.append(f"Error validating config.py: {e}")

    # Check directories
    required_dirs = ["logs", "temp", "projects"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created directory: {dir_name}")
            except Exception as e:
                errors.append(f"Cannot create directory {dir_name}: {e}")
        else:
            logger.info(f"✅ Directory exists: {dir_name}")

    # Detect Termux
    is_termux = os.path.exists('/data/data/com.termux') or 'com.termux' in os.environ.get('PREFIX', '')
    if is_termux:
        logger.info("✅ Termux environment detected")
    else:
        logger.info("✅ Standard Linux/Unix environment")

    # Report results
    if errors:
        logger.error("❌ Environment check failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    if warnings:
        logger.warning("⚠️ Environment warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    logger.info("✅ Environment check passed")
    return True


def setup_environment():
    """Setup environment if needed"""
    logger.info("🔧 Setting up environment...")

    # Create config.py template if it doesn't exist
    config_file = Path("config.py")
    if not config_file.exists():
        logger.info("📝 Creating config.py template...")
        logger.info("⚠️  Please edit config.py with your actual API keys!")
        logger.info("📖 Instructions:")
        logger.info("   1. Edit config.py")
        logger.info("   2. Replace 'your_discord_bot_token_here' with your Discord bot token")
        logger.info("   3. Replace 'your_gemini_api_key_here' with your Gemini API key")
        logger.info("   4. Save the file and run the bot again")


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  ██╗   ██╗██╗██████╗ ███████╗ ██████╗ ██████╗ ██████╗ ███████╗║
║  ██║   ██║██║██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝║
║  ██║   ██║██║██████╔╝█████╗  ██║     ██║   ██║██║  ██║█████╗  ║
║  ╚██╗ ██╔╝██║██╔══██╗██╔══╝  ██║     ██║   ██║██║  ██║██╔══╝  ║
║   ╚████╔╝ ██║██████╔╝███████╗╚██████╗╚██████╔╝██████╔╝███████╗║
║    ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝║
║                                                              ║
║              Advanced AI-Powered Discord Code Bot           ║
║                     Version 1.0.0                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🤖 Features:
   • AI-powered code generation with Google Gemini
   • Automatic code testing and error correction
   • Multiple AI personas for specialized tasks
   • Intelligent project packaging and delivery
   • Comprehensive logging and monitoring
   • Termux compatibility

🚀 Starting up...
"""
    print(banner)


async def main():
    """Main entry point"""
    try:
        # Print banner
        print_banner()

        # Setup environment
        setup_environment()

        # Check environment
        if not check_environment():
            logger.error("❌ Environment check failed. Please fix the issues and try again.")
            logger.error("💡 Make sure to:")
            logger.error("   1. Create and configure config.py with your API keys")
            logger.error("   2. Install all required dependencies")
            logger.error("   3. Ensure Python 3.7+ is installed")
            sys.exit(1)

        # Load configuration
        try:
            config = get_config()
            logger.info("✅ Configuration loaded successfully")
            
            # Show Termux status
            if config.is_termux():
                logger.info("🤖 Running in Termux environment")
                termux_config = config.get_termux_config()
                if termux_config:
                    logger.info(f"📱 Termux prefix: {termux_config.get('prefix', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            logger.error("💡 Please check your config.py file for errors")
            sys.exit(1)

        # Start bot manager
        bot_manager = BotManager()
        await bot_manager.start()

    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)