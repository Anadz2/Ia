"""
Configuration Manager for VibeCode Bot
Handles loading and managing all bot configurations
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Adicionar o diretório pai ao path para importar config.py
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import config as bot_config
except ImportError:
    raise ImportError("Arquivo config.py não encontrado! Por favor, configure o arquivo config.py na raiz do projeto.")

from .logger import get_logger

logger = get_logger("ConfigManager")


@dataclass
class BotConfig:
    """Bot configuration dataclass"""
    name: str
    version: str
    description: str
    command_prefix: str
    max_message_length: int
    max_file_size_mb: int


@dataclass
class DiscordConfig:
    """Discord configuration dataclass"""
    token: str
    intents: list
    activity: dict


@dataclass
class GeminiConfig:
    """Gemini AI configuration dataclass"""
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int


@dataclass
class CodeGenConfig:
    """Code generation configuration dataclass"""
    max_files: int
    max_project_size_mb: int
    supported_languages: list


@dataclass
class TestingConfig:
    """Testing configuration dataclass"""
    max_execution_time: int
    max_memory_mb: int
    max_correction_attempts: int
    sandbox_enabled: bool


@dataclass
class LoggingConfig:
    """Logging configuration dataclass"""
    level: str
    format: str
    file_rotation: bool
    max_file_size_mb: int
    backup_count: int


@dataclass
class PathsConfig:
    """Paths configuration dataclass"""
    temp_dir: str
    projects_dir: str
    logs_dir: str
    templates_dir: str


class ConfigManager:
    """Manages all bot configurations"""

    def __init__(self):
        self._raw_config: Dict[str, Any] = {}

        # Configuration objects
        self.bot: Optional[BotConfig] = None
        self.discord: Optional[DiscordConfig] = None
        self.gemini: Optional[GeminiConfig] = None
        self.code_generation: Optional[CodeGenConfig] = None
        self.testing: Optional[TestingConfig] = None
        self.logging: Optional[LoggingConfig] = None
        self.paths: Optional[PathsConfig] = None

        # Load configurations
        self._load_config_from_py()
        self._parse_configurations()
        self._validate_configurations()

        logger.info("Configuration loaded successfully")

    def _load_config_from_py(self):
        """Load configuration from config.py file"""
        try:
            # Validar configurações do config.py
            validation_errors = bot_config.validate_config()
            if validation_errors:
                error_msg = "Erros de configuração encontrados:\n" + "\n".join(f"- {error}" for error in validation_errors)
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Carregar todas as configurações
            self._raw_config = bot_config.get_all_config()
            logger.info("Configuration loaded from config.py")

        except Exception as e:
            logger.error(f"Failed to load configuration from config.py: {e}")
            raise

    def _parse_configurations(self):
        """Parse raw configuration into dataclass objects"""
        try:
            # Parse bot configuration
            bot_config_data = self._raw_config.get('bot', {})
            self.bot = BotConfig(**bot_config_data)

            # Parse discord configuration
            discord_config_data = self._raw_config.get('discord', {})
            self.discord = DiscordConfig(**discord_config_data)

            # Parse gemini configuration
            gemini_config_data = self._raw_config.get('gemini', {})
            self.gemini = GeminiConfig(**gemini_config_data)

            # Parse code generation configuration
            codegen_config_data = self._raw_config.get('code_generation', {})
            self.code_generation = CodeGenConfig(**codegen_config_data)

            # Parse testing configuration
            testing_config_data = self._raw_config.get('testing', {})
            self.testing = TestingConfig(**testing_config_data)

            # Parse logging configuration
            logging_config_data = self._raw_config.get('logging', {})
            self.logging = LoggingConfig(**logging_config_data)

            # Parse paths configuration
            paths_config_data = self._raw_config.get('paths', {})
            self.paths = PathsConfig(**paths_config_data)

            logger.info("All configurations parsed successfully")

        except Exception as e:
            logger.error(f"Failed to parse configurations: {e}")
            raise

    def _validate_configurations(self):
        """Validate critical configurations"""
        errors = []

        # Validate Discord token
        if not self.discord.token or self.discord.token == "your_discord_bot_token_here":
            errors.append("Discord token is missing or not configured")

        # Validate Gemini API key
        if not self.gemini.api_key or self.gemini.api_key == "your_gemini_api_key_here":
            errors.append("Gemini API key is missing or not configured")

        # Validate paths
        for path_name, path_value in [
            ("temp_dir", self.paths.temp_dir),
            ("projects_dir", self.paths.projects_dir),
            ("logs_dir", self.paths.logs_dir)
        ]:
            path_obj = Path(path_value)
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create {path_name} directory '{path_value}': {e}")

        # Validate numeric values
        if self.testing.max_correction_attempts <= 0:
            errors.append("max_correction_attempts must be greater than 0")

        if self.gemini.temperature < 0 or self.gemini.temperature > 2:
            errors.append("Gemini temperature must be between 0 and 2")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Configuration validation passed")

    def get_supported_languages(self) -> list:
        """Get list of supported programming languages"""
        return self.code_generation.supported_languages.copy()

    def is_language_supported(self, language: str) -> bool:
        """Check if a programming language is supported"""
        return language.lower() in [lang.lower() for lang in self.code_generation.supported_languages]

    def get_temp_dir(self) -> Path:
        """Get temporary directory path"""
        return Path(self.paths.temp_dir)

    def get_projects_dir(self) -> Path:
        """Get projects directory path"""
        return Path(self.paths.projects_dir)

    def get_logs_dir(self) -> Path:
        """Get logs directory path"""
        return Path(self.paths.logs_dir)

    def reload(self):
        """Reload configuration from config.py"""
        logger.info("Reloading configuration...")

        # Recarregar o módulo config.py
        import importlib
        importlib.reload(bot_config)

        self._load_config_from_py()
        self._parse_configurations()
        self._validate_configurations()
        logger.info("Configuration reloaded successfully")

    def is_termux(self) -> bool:
        """Check if running on Termux"""
        return self._raw_config.get('is_termux', False)

    def get_termux_config(self) -> dict:
        """Get Termux-specific configuration"""
        return self._raw_config.get('termux', {})


# Global configuration instance
config = None


def get_config() -> ConfigManager:
    """Get global configuration instance"""
    global config
    if config is None:
        config = ConfigManager()
    return config


def reload_config():
    """Reload global configuration"""
    global config
    if config:
        config.reload()
    else:
        config = ConfigManager()