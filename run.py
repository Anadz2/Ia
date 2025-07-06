#!/usr/bin/env python3
"""
Quick run script for VibeCode Bot
Simple wrapper to start the bot
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the bot"""
    try:
        # Change to bot directory
        bot_dir = Path(__file__).parent
        
        # Run main.py
        result = subprocess.run([
            sys.executable, 
            str(bot_dir / "main.py")
        ], cwd=bot_dir)
        
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()