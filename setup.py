#!/usr/bin/env python3
"""
Setup script for VibeCode Bot
Handles installation and initial configuration
"""

import os
import subprocess
import sys
from pathlib import Path
import shutil

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_step(step, text):
    """Print formatted step"""
    print(f"\n[{step}] {text}")

def run_command(cmd, description=""):
    """Run command with error handling"""
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error {description}: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False

def check_python_version():
    """Check Python version"""
    print_step("1", "Checking Python version...")
    
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_step("2", "Installing dependencies...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    # Upgrade pip first
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "upgrading pip"):
        print("⚠️ Failed to upgrade pip, continuing anyway...")
    
    # Install requirements
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], "installing dependencies"):
        return False
    
    print("✅ Dependencies installed successfully")
    return True

def setup_directories():
    """Create necessary directories"""
    print_step("3", "Setting up directories...")
    
    directories = ["logs", "temp", "projects", "config"]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Directory created/verified: {dir_name}")
        except Exception as e:
            print(f"❌ Failed to create directory {dir_name}: {e}")
            return False
    
    return True

def setup_environment():
    """Setup environment file"""
    print_step("4", "Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        try:
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your actual API keys:")
            print("   - DISCORD_TOKEN: Get from Discord Developer Portal")
            print("   - GEMINI_API_KEY: Get from Google AI Studio")
            return True
        except Exception as e:
            print(f"❌ Failed to copy .env template: {e}")
            return False
    else:
        print("⚠️ .env.example not found, creating basic .env file")
        
        basic_env = """# VibeCode Bot Environment Variables
DISCORD_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(basic_env)
            print("✅ Created basic .env file")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False

def verify_configuration():
    """Verify configuration"""
    print_step("5", "Verifying configuration...")
    
    try:
        # Try to import and load config
        sys.path.insert(0, str(Path("src")))
        from src.config_manager import get_config
        
        config = get_config()
        print("✅ Configuration loaded successfully")
        
        # Check critical settings
        if config.discord.token.startswith("your_"):
            print("⚠️ Discord token not configured")
            return False
        
        if config.gemini.api_key.startswith("your_"):
            print("⚠️ Gemini API key not configured")
            return False
        
        print("✅ Configuration verified")
        return True
        
    except Exception as e:
        print(f"❌ Configuration verification failed: {e}")
        return False

def run_tests():
    """Run basic tests"""
    print_step("6", "Running basic tests...")
    
    try:
        # Test imports
        sys.path.insert(0, str(Path("src")))
        
        from src.logger import get_logger
        from src.config_manager import get_config
        from src.gemini_ai import get_gemini_ai
        from src.code_tester import get_code_tester
        from src.code_corrector import get_code_corrector
        from src.project_manager import get_project_manager
        
        print("✅ All modules imported successfully")
        
        # Test logger
        logger = get_logger("SetupTest")
        logger.info("Setup test log message")
        print("✅ Logger working")
        
        print("✅ Basic tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        return False

def print_final_instructions():
    """Print final setup instructions"""
    print_header("Setup Complete!")
    
    print("""
🎉 VibeCode Bot setup completed successfully!

📋 Next Steps:

1. Configure your API keys in .env file:
   - Get Discord token: https://discord.com/developers/applications
   - Get Gemini API key: https://makersuite.google.com/app/apikey

2. Invite your bot to Discord:
   - Go to Discord Developer Portal
   - Select your application
   - Go to OAuth2 > URL Generator
   - Select 'bot' scope and necessary permissions
   - Use the generated URL to invite your bot

3. Start the bot:
   python main.py
   
   Or use the quick run script:
   python run.py

🔧 Configuration:
   - Edit config/config.yaml for advanced settings
   - Check logs/ directory for detailed logs
   - Projects will be saved in projects/ directory

📚 Commands:
   - !code <description> - Generate code
   - !help - Show help
   - !stats - Show statistics
   - !status - Check bot status

🆘 Need Help?
   - Check the logs for detailed error information
   - Make sure all API keys are correctly configured
   - Verify bot permissions in Discord

Happy coding! 🚀
""")

def main():
    """Main setup function"""
    print_header("VibeCode Bot Setup")
    
    print("""
🤖 Welcome to VibeCode Bot Setup!

This script will:
• Check Python version
• Install dependencies
• Create necessary directories
• Setup configuration files
• Verify installation

Let's get started!
""")
    
    # Run setup steps
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Setup Directories", setup_directories),
        ("Setup Environment", setup_environment),
        ("Verify Configuration", verify_configuration),
        ("Run Tests", run_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Unexpected error in {step_name}: {e}")
            failed_steps.append(step_name)
    
    # Report results
    if failed_steps:
        print_header("Setup Issues")
        print("❌ The following steps failed:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease fix these issues and run setup again.")
        sys.exit(1)
    else:
        print_final_instructions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup failed with unexpected error: {e}")
        sys.exit(1)