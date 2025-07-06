"""
Project Management System
Handles project creation, organization, and ZIP packaging
"""

import asyncio
import os
import shutil
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .logger import get_logger
from .config_manager import get_config
from .gemini_ai import GeneratedProject

logger = get_logger("ProjectManager")


@dataclass
class ProjectMetadata:
    """Project metadata information"""
    name: str
    description: str
    language: str
    created_at: datetime
    user_id: str
    username: str
    file_count: int
    total_size: int
    dependencies: List[str]
    setup_instructions: List[str]
    run_instructions: List[str]
    test_results: Dict
    correction_attempts: int
    final_score: float


@dataclass
class PackagedProject:
    """Packaged project ready for delivery"""
    zip_path: Path
    metadata: ProjectMetadata
    file_size: int
    readme_content: str
    project_structure: str


class ProjectManager:
    """Manages project creation, organization, and packaging"""
    
    def __init__(self):
        self.config = get_config()
        self.projects_dir = Path(self.config.get_projects_dir())
        self.temp_dir = Path(self.config.get_temp_dir())
        
        # Ensure directories exist
        self.projects_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Project templates
        self.templates = self._load_templates()
        
        logger.info(f"Project manager initialized - Projects: {self.projects_dir}")
    
    def _load_templates(self) -> Dict[str, Dict]:
        """Load project templates for different languages"""
        return {
            "python": {
                "structure": {
                    "src/": "Source code directory",
                    "tests/": "Test files directory",
                    "docs/": "Documentation directory",
                    "requirements.txt": "Python dependencies",
                    "README.md": "Project documentation",
                    "setup.py": "Package setup script",
                    ".gitignore": "Git ignore file"
                },
                "gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""",
                "setup_template": """from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="1.0.0",
    description="{description}",
    packages=find_packages(),
    install_requires=[
        {dependencies}
    ],
    python_requires=">=3.7",
)
"""
            },
            "javascript": {
                "structure": {
                    "src/": "Source code directory",
                    "public/": "Public assets directory",
                    "tests/": "Test files directory",
                    "docs/": "Documentation directory",
                    "package.json": "Node.js dependencies",
                    "README.md": "Project documentation",
                    ".gitignore": "Git ignore file"
                },
                "gitignore": """# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build
dist/
build/

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""",
                "package_template": """{
    "name": "{project_name}",
    "version": "1.0.0",
    "description": "{description}",
    "main": "src/index.js",
    "scripts": {
        "start": "node src/index.js",
        "dev": "nodemon src/index.js",
        "test": "jest"
    },
    "dependencies": {
        {dependencies}
    },
    "devDependencies": {
        "nodemon": "^2.0.0",
        "jest": "^29.0.0"
    }
}
"""
            }
        }
    
    async def create_project(
        self, 
        generated_project: GeneratedProject, 
        user_id: str, 
        username: str,
        test_results: Dict = None,
        correction_attempts: int = 0,
        final_score: float = 100.0
    ) -> PackagedProject:
        """Create and package a complete project"""
        
        start_time = time.time()
        
        try:
            # Create unique project directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self._sanitize_filename(generated_project.name)
            project_dir_name = f"{safe_name}_{timestamp}_{user_id[:8]}"
            project_dir = self.projects_dir / project_dir_name
            
            logger.info(f"Creating project: {project_dir_name}")
            
            # Create project directory structure
            project_dir.mkdir(exist_ok=True)
            
            # Detect project language
            language = self._detect_language(generated_project.files)
            
            # Create enhanced project structure
            enhanced_files = await self._enhance_project_structure(
                generated_project, language, project_dir
            )
            
            # Write all files
            written_files = await self._write_project_files(enhanced_files, project_dir)
            
            # Create project metadata
            metadata = ProjectMetadata(
                name=generated_project.name,
                description=generated_project.description,
                language=language,
                created_at=datetime.now(),
                user_id=user_id,
                username=username,
                file_count=len(written_files),
                total_size=sum(os.path.getsize(f) for f in written_files),
                dependencies=generated_project.dependencies,
                setup_instructions=generated_project.setup_instructions,
                run_instructions=generated_project.run_instructions,
                test_results=test_results or {},
                correction_attempts=correction_attempts,
                final_score=final_score
            )
            
            # Generate comprehensive README
            readme_content = self._generate_readme(metadata, enhanced_files)
            readme_path = project_dir / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Generate project structure visualization
            structure_content = self._generate_project_structure(project_dir)
            
            # Create ZIP package
            zip_path = await self._create_zip_package(project_dir, project_dir_name)
            
            # Create packaged project
            packaged_project = PackagedProject(
                zip_path=zip_path,
                metadata=metadata,
                file_size=os.path.getsize(zip_path),
                readme_content=readme_content,
                project_structure=structure_content
            )
            
            # Log project creation
            duration = time.time() - start_time
            logger.log_performance("project_creation", duration, {
                "files": len(written_files),
                "size_mb": packaged_project.file_size / 1024 / 1024,
                "language": language
            })
            
            logger.info(f"✅ Project created successfully: {zip_path.name} ({packaged_project.file_size / 1024:.1f} KB)")
            
            return packaged_project
            
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            raise
    
    async def _enhance_project_structure(
        self, 
        project: GeneratedProject, 
        language: str, 
        project_dir: Path
    ) -> Dict[str, str]:
        """Enhance project with proper structure and additional files"""
        
        enhanced_files = project.files.copy()
        
        # Get template for language
        template = self.templates.get(language, {})
        
        # Add .gitignore if not present
        if ".gitignore" not in enhanced_files and "gitignore" in template:
            enhanced_files[".gitignore"] = template["gitignore"]
        
        # Add setup files based on language
        if language == "python":
            # Add requirements.txt if not present
            if "requirements.txt" not in enhanced_files and project.dependencies:
                enhanced_files["requirements.txt"] = "\n".join(project.dependencies)
            
            # Add setup.py if not present
            if "setup.py" not in enhanced_files and "setup_template" in template:
                deps_str = ",\n        ".join(f'"{dep}"' for dep in project.dependencies)
                enhanced_files["setup.py"] = template["setup_template"].format(
                    project_name=self._sanitize_filename(project.name),
                    description=project.description,
                    dependencies=deps_str
                )
        
        elif language == "javascript":
            # Add package.json if not present
            if "package.json" not in enhanced_files and "package_template" in template:
                deps_obj = ",\n        ".join(f'"{dep}": "^1.0.0"' for dep in project.dependencies)
                enhanced_files["package.json"] = template["package_template"].format(
                    project_name=self._sanitize_filename(project.name),
                    description=project.description,
                    dependencies=deps_obj
                )
        
        # Add run script if not present
        if not any(name.startswith("run") or name.startswith("start") for name in enhanced_files.keys()):
            if language == "python":
                enhanced_files["run.py"] = self._generate_python_runner(enhanced_files)
            elif language == "javascript":
                enhanced_files["run.js"] = self._generate_js_runner(enhanced_files)
        
        return enhanced_files
    
    def _generate_python_runner(self, files: Dict[str, str]) -> str:
        """Generate Python runner script"""
        main_files = [name for name in files.keys() if name.endswith('.py') and 
                     ('main' in name.lower() or 'app' in name.lower() or 'run' in name.lower())]
        
        if main_files:
            main_file = main_files[0]
            module_name = main_file.replace('.py', '').replace('/', '.')
            
            return f'''#!/usr/bin/env python3
"""
Project Runner Script
Automatically generated by VibeCode Bot
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import and run main module
    import {module_name}
    
    if hasattr({module_name}, 'main'):
        {module_name}.main()
    else:
        print("Main function not found in {module_name}")
        
except ImportError as e:
    print(f"Failed to import {module_name}: {{e}}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    
except Exception as e:
    print(f"Error running application: {{e}}")
'''
        
        return '''#!/usr/bin/env python3
"""
Project Runner Script
"""

print("No main file detected. Please run the appropriate Python file directly.")
'''
    
    def _generate_js_runner(self, files: Dict[str, str]) -> str:
        """Generate JavaScript runner script"""
        main_files = [name for name in files.keys() if name.endswith('.js') and 
                     ('main' in name.lower() or 'app' in name.lower() or 'index' in name.lower())]
        
        if main_files:
            main_file = main_files[0]
            
            return f'''#!/usr/bin/env node
/**
 * Project Runner Script
 * Automatically generated by VibeCode Bot
 */

const path = require('path');
const fs = require('fs');

try {{
    // Check if main file exists
    const mainFile = path.join(__dirname, '{main_file}');
    
    if (fs.existsSync(mainFile)) {{
        console.log('Starting application...');
        require('./{main_file}');
    }} else {{
        console.error('Main file not found: {main_file}');
    }}
    
}} catch (error) {{
    console.error('Error running application:', error.message);
    console.log('Make sure all dependencies are installed:');
    console.log('npm install');
}}
'''
        
        return '''#!/usr/bin/env node
/**
 * Project Runner Script
 */

console.log("No main file detected. Please run the appropriate JavaScript file directly.");
'''
    
    async def _write_project_files(self, files: Dict[str, str], project_dir: Path) -> List[Path]:
        """Write all project files to disk"""
        written_files = []
        
        for filename, content in files.items():
            file_path = project_dir / filename
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                written_files.append(file_path)
                logger.debug(f"Written file: {filename} ({len(content)} chars)")
                
            except Exception as e:
                logger.error(f"Failed to write file {filename}: {e}")
        
        return written_files
    
    async def _create_zip_package(self, project_dir: Path, project_name: str) -> Path:
        """Create ZIP package of the project"""
        zip_filename = f"{project_name}.zip"
        zip_path = self.temp_dir / zip_filename
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files in project directory
                for file_path in project_dir.rglob('*'):
                    if file_path.is_file():
                        # Calculate relative path for ZIP
                        arcname = file_path.relative_to(project_dir)
                        zipf.write(file_path, arcname)
                        logger.debug(f"Added to ZIP: {arcname}")
            
            logger.info(f"ZIP package created: {zip_path} ({os.path.getsize(zip_path)} bytes)")
            return zip_path
            
        except Exception as e:
            logger.error(f"Failed to create ZIP package: {e}")
            raise
    
    def _generate_readme(self, metadata: ProjectMetadata, files: Dict[str, str]) -> str:
        """Generate comprehensive README.md"""
        
        # Detect main files
        main_files = self._find_main_files(files)
        
        readme = f"""# {metadata.name}

{metadata.description}

## 📋 Project Information

- **Language**: {metadata.language.title()}
- **Created**: {metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Files**: {metadata.file_count}
- **Total Size**: {metadata.total_size / 1024:.1f} KB
- **Generated by**: VibeCode Bot 🤖

## 🚀 Quick Start

### Prerequisites

Make sure you have the following installed:
"""

        # Add language-specific prerequisites
        if metadata.language == "python":
            readme += """
- Python 3.7 or higher
- pip (Python package manager)
"""
        elif metadata.language == "javascript":
            readme += """
- Node.js 14 or higher
- npm (Node package manager)
"""

        # Add setup instructions
        if metadata.setup_instructions:
            readme += "\n### Setup Instructions\n\n"
            for i, instruction in enumerate(metadata.setup_instructions, 1):
                readme += f"{i}. {instruction}\n"
        else:
            # Add default setup instructions
            if metadata.language == "python" and metadata.dependencies:
                readme += """
### Setup Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
"""
            elif metadata.language == "javascript":
                readme += """
### Setup Instructions

1. Install dependencies:
   ```bash
   npm install
   ```
"""

        # Add run instructions
        if metadata.run_instructions:
            readme += "\n### Running the Application\n\n"
            for i, instruction in enumerate(metadata.run_instructions, 1):
                readme += f"{i}. {instruction}\n"
        else:
            # Add default run instructions
            readme += "\n### Running the Application\n\n"
            if main_files:
                if metadata.language == "python":
                    readme += f"```bash\npython {main_files[0]}\n```\n"
                elif metadata.language == "javascript":
                    readme += f"```bash\nnode {main_files[0]}\n```\n"
            else:
                readme += "Check the source files for the main entry point.\n"

        # Add dependencies section
        if metadata.dependencies:
            readme += "\n## 📦 Dependencies\n\n"
            for dep in metadata.dependencies:
                readme += f"- {dep}\n"

        # Add project structure
        readme += f"\n## 📁 Project Structure\n\n```\n{self._generate_simple_structure(files)}\n```\n"

        # Add test results if available
        if metadata.test_results:
            readme += "\n## ✅ Test Results\n\n"
            if metadata.test_results.get('success'):
                readme += "✅ All tests passed successfully!\n"
            else:
                readme += f"⚠️ Tests completed with {len(metadata.test_results.get('errors', []))} issues\n"
            
            if metadata.correction_attempts > 0:
                readme += f"\n🔧 Code was automatically corrected in {metadata.correction_attempts} attempts\n"
                readme += f"📊 Final quality score: {metadata.final_score:.1f}%\n"

        # Add usage examples if main files are detected
        if main_files:
            readme += "\n## 💡 Usage Examples\n\n"
            readme += "This project is ready to run! Check the main files for functionality:\n\n"
            for main_file in main_files[:3]:  # Show up to 3 main files
                readme += f"- `{main_file}` - Main application file\n"

        # Add footer
        readme += f"""
## 🤖 Generated by VibeCode Bot

This project was automatically generated and tested by VibeCode Bot, an advanced AI-powered coding assistant.

- **Generation Time**: {metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Quality Assurance**: Automatically tested and corrected
- **Ready to Use**: All files are complete and functional

---

*Happy coding! 🚀*
"""

        return readme
    
    def _generate_project_structure(self, project_dir: Path) -> str:
        """Generate visual project structure"""
        structure_lines = []
        
        def add_directory(path: Path, prefix: str = ""):
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                structure_lines.append(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir():
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    add_directory(item, next_prefix)
        
        structure_lines.append(project_dir.name + "/")
        add_directory(project_dir)
        
        return "\n".join(structure_lines)
    
    def _generate_simple_structure(self, files: Dict[str, str]) -> str:
        """Generate simple project structure from files dict"""
        structure_lines = []
        
        # Group files by directory
        dirs = {}
        for filename in sorted(files.keys()):
            parts = filename.split('/')
            if len(parts) > 1:
                dir_name = '/'.join(parts[:-1])
                if dir_name not in dirs:
                    dirs[dir_name] = []
                dirs[dir_name].append(parts[-1])
            else:
                if '.' not in dirs:
                    dirs['.'] = []
                dirs['.'].append(filename)
        
        # Build structure
        for dir_name in sorted(dirs.keys()):
            if dir_name != '.':
                structure_lines.append(f"{dir_name}/")
                for file in sorted(dirs[dir_name]):
                    structure_lines.append(f"  {file}")
            else:
                for file in sorted(dirs[dir_name]):
                    structure_lines.append(file)
        
        return "\n".join(structure_lines)
    
    def _find_main_files(self, files: Dict[str, str]) -> List[str]:
        """Find main executable files"""
        main_candidates = [
            "main.py", "app.py", "run.py", "start.py", "index.py",
            "main.js", "app.js", "index.js", "server.js"
        ]
        
        main_files = []
        
        # Check for specific main files
        for candidate in main_candidates:
            if candidate in files:
                main_files.append(candidate)
        
        # Check for files with main guard
        for filename, content in files.items():
            if filename.endswith('.py') and 'if __name__ == "__main__"' in content:
                if filename not in main_files:
                    main_files.append(filename)
        
        return main_files
    
    def _detect_language(self, files: Dict[str, str]) -> str:
        """Detect primary programming language"""
        extensions = {}
        
        for filename in files.keys():
            ext = Path(filename).suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Language mapping
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.html': 'html',
            '.css': 'css'
        }
        
        # Find most common extension
        if extensions:
            most_common_ext = max(extensions.items(), key=lambda x: x[1])[0]
            return lang_map.get(most_common_ext, 'unknown')
        
        return 'unknown'
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem"""
        import re
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = sanitized.strip('._')
        return sanitized[:50]  # Limit length
    
    def cleanup_old_projects(self, days_old: int = 7):
        """Clean up old project files"""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            cleaned_count = 0
            for item in self.projects_dir.iterdir():
                if item.is_dir() and item.stat().st_mtime < cutoff_time:
                    shutil.rmtree(item)
                    cleaned_count += 1
            
            for item in self.temp_dir.iterdir():
                if item.is_file() and item.stat().st_mtime < cutoff_time:
                    item.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old project files")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Global project manager instance
project_manager = None


def get_project_manager() -> ProjectManager:
    """Get global project manager instance"""
    global project_manager
    if project_manager is None:
        project_manager = ProjectManager()
    return project_manager