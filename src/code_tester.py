"""
Advanced Code Testing System
Safely executes and validates generated code with comprehensive error detection
"""

import ast
import asyncio
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import psutil
import signal

from .logger import get_logger
from .config_manager import get_config

logger = get_logger("CodeTester")


class TestResult(Enum):
    """Test result types"""
    SUCCESS = "success"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"
    SECURITY_ERROR = "security_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class TestReport:
    """Comprehensive test report"""
    result: TestResult
    success: bool
    execution_time: float
    memory_usage: float
    output: str
    errors: List[str]
    warnings: List[str]
    syntax_issues: List[str]
    runtime_issues: List[str]
    security_issues: List[str]
    suggestions: List[str]
    exit_code: Optional[int] = None


@dataclass
class SecurityCheck:
    """Security check result"""
    is_safe: bool
    issues: List[str]
    blocked_operations: List[str]


class CodeTester:
    """Advanced code testing system with security and performance monitoring"""
    
    def __init__(self):
        self.config = get_config()
        self.temp_dir = Path(self.config.get_temp_dir())
        self.temp_dir.mkdir(exist_ok=True)
        
        # Security patterns to block
        self.dangerous_patterns = [
            r'import\s+os\s*\.\s*system',
            r'subprocess\s*\.\s*call',
            r'subprocess\s*\.\s*run',
            r'subprocess\s*\.\s*Popen',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'open\s*\([^)]*["\'][rwa]',
            r'file\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
            r'socket\s*\.',
            r'urllib\s*\.',
            r'requests\s*\.',
            r'http\s*\.',
            r'ftplib\s*\.',
            r'smtplib\s*\.',
            r'pickle\s*\.',
            r'marshal\s*\.',
            r'ctypes\s*\.',
            r'sys\s*\.\s*exit',
            r'os\s*\.\s*_exit',
            r'quit\s*\(',
            r'exit\s*\(',
        ]
        
        logger.info("Code tester initialized")
    
    async def test_project(self, project_files: Dict[str, str], project_name: str) -> TestReport:
        """Test entire project with comprehensive analysis"""
        start_time = time.time()
        
        try:
            # Create temporary project directory
            project_dir = self.temp_dir / f"test_{project_name}_{int(time.time())}"
            project_dir.mkdir(exist_ok=True)
            
            logger.info(f"Testing project: {project_name} in {project_dir}")
            
            # Security check first
            security_check = self._perform_security_check(project_files)
            if not security_check.is_safe:
                return TestReport(
                    result=TestResult.SECURITY_ERROR,
                    success=False,
                    execution_time=time.time() - start_time,
                    memory_usage=0,
                    output="",
                    errors=security_check.issues,
                    warnings=[],
                    syntax_issues=[],
                    runtime_issues=[],
                    security_issues=security_check.issues,
                    suggestions=["Remove dangerous operations", "Use safer alternatives"]
                )
            
            # Write files to disk
            written_files = []
            for filename, content in project_files.items():
                file_path = project_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    written_files.append(file_path)
                    logger.debug(f"Written file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to write file {filename}: {e}")
            
            # Perform comprehensive testing
            test_report = await self._comprehensive_test(project_dir, written_files, project_name)
            
            # Cleanup
            self._cleanup_directory(project_dir)
            
            test_report.execution_time = time.time() - start_time
            logger.log_code_test(project_name, {
                "success": test_report.success,
                "errors": len(test_report.errors),
                "result": test_report.result.value
            })
            
            return test_report
            
        except Exception as e:
            logger.error(f"Project testing failed: {e}")
            return TestReport(
                result=TestResult.UNKNOWN_ERROR,
                success=False,
                execution_time=time.time() - start_time,
                memory_usage=0,
                output="",
                errors=[f"Testing failed: {str(e)}"],
                warnings=[],
                syntax_issues=[],
                runtime_issues=[],
                security_issues=[],
                suggestions=["Check project structure", "Verify file contents"]
            )
    
    async def test_single_file(self, filename: str, content: str) -> TestReport:
        """Test a single file"""
        return await self.test_project({filename: content}, f"single_file_{filename}")
    
    def _perform_security_check(self, project_files: Dict[str, str]) -> SecurityCheck:
        """Perform security analysis on project files"""
        issues = []
        blocked_operations = []
        
        for filename, content in project_files.items():
            # Check for dangerous patterns
            for pattern in self.dangerous_patterns:
                import re
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    issue = f"Dangerous operation in {filename}: {pattern}"
                    issues.append(issue)
                    blocked_operations.extend(matches)
            
            # Check for suspicious imports
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if self._is_dangerous_import(alias.name):
                                issues.append(f"Dangerous import in {filename}: {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and self._is_dangerous_import(node.module):
                            issues.append(f"Dangerous import in {filename}: {node.module}")
            except SyntaxError:
                # Will be caught in syntax check
                pass
            except Exception as e:
                logger.warning(f"Security check failed for {filename}: {e}")
        
        is_safe = len(issues) == 0
        
        if not is_safe:
            logger.warning(f"Security issues found: {len(issues)} issues")
        
        return SecurityCheck(
            is_safe=is_safe,
            issues=issues,
            blocked_operations=blocked_operations
        )
    
    def _is_dangerous_import(self, module_name: str) -> bool:
        """Check if import is potentially dangerous"""
        dangerous_modules = {
            'os', 'subprocess', 'sys', 'socket', 'urllib', 'urllib2', 'urllib3',
            'requests', 'http', 'ftplib', 'smtplib', 'pickle', 'marshal',
            'ctypes', 'importlib', '__builtin__', 'builtins'
        }
        
        return module_name in dangerous_modules
    
    async def _comprehensive_test(self, project_dir: Path, files: List[Path], project_name: str) -> TestReport:
        """Perform comprehensive testing of the project"""
        errors = []
        warnings = []
        syntax_issues = []
        runtime_issues = []
        security_issues = []
        suggestions = []
        
        output = ""
        max_memory = 0
        exit_code = None
        
        # 1. Syntax Analysis
        logger.info("Performing syntax analysis...")
        for file_path in files:
            if file_path.suffix == '.py':
                syntax_result = self._check_python_syntax(file_path)
                if syntax_result['errors']:
                    syntax_issues.extend(syntax_result['errors'])
                if syntax_result['warnings']:
                    warnings.extend(syntax_result['warnings'])
        
        # 2. Static Analysis
        logger.info("Performing static analysis...")
        static_analysis = self._perform_static_analysis(files)
        warnings.extend(static_analysis.get('warnings', []))
        suggestions.extend(static_analysis.get('suggestions', []))
        
        # 3. Runtime Testing (if no syntax errors)
        if not syntax_issues:
            logger.info("Performing runtime testing...")
            runtime_result = await self._run_project_safely(project_dir, project_name)
            
            output = runtime_result['output']
            exit_code = runtime_result['exit_code']
            max_memory = runtime_result['memory_usage']
            
            if runtime_result['errors']:
                runtime_issues.extend(runtime_result['errors'])
            
            if runtime_result['timeout']:
                return TestReport(
                    result=TestResult.TIMEOUT,
                    success=False,
                    execution_time=0,
                    memory_usage=max_memory,
                    output=output,
                    errors=["Execution timeout"],
                    warnings=warnings,
                    syntax_issues=syntax_issues,
                    runtime_issues=runtime_issues,
                    security_issues=security_issues,
                    suggestions=suggestions + ["Optimize performance", "Check for infinite loops"],
                    exit_code=exit_code
                )
        
        # Determine overall result
        all_errors = syntax_issues + runtime_issues + security_issues
        
        if security_issues:
            result = TestResult.SECURITY_ERROR
        elif syntax_issues:
            result = TestResult.SYNTAX_ERROR
        elif runtime_issues:
            result = TestResult.RUNTIME_ERROR
        elif all_errors:
            result = TestResult.UNKNOWN_ERROR
        else:
            result = TestResult.SUCCESS
        
        success = len(all_errors) == 0
        
        return TestReport(
            result=result,
            success=success,
            execution_time=0,  # Will be set by caller
            memory_usage=max_memory,
            output=output,
            errors=all_errors,
            warnings=warnings,
            syntax_issues=syntax_issues,
            runtime_issues=runtime_issues,
            security_issues=security_issues,
            suggestions=suggestions,
            exit_code=exit_code
        )
    
    def _check_python_syntax(self, file_path: Path) -> Dict[str, List[str]]:
        """Check Python file syntax"""
        errors = []
        warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
                
                # Check for common issues
                for node in ast.walk(tree):
                    # Check for unused imports (basic check)
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            # This is a simplified check
                            if alias.name not in content:
                                warnings.append(f"Potentially unused import: {alias.name}")
                
            except SyntaxError as e:
                errors.append(f"Syntax error in {file_path.name}: {e.msg} at line {e.lineno}")
            except Exception as e:
                errors.append(f"Parse error in {file_path.name}: {str(e)}")
                
        except Exception as e:
            errors.append(f"Failed to read {file_path.name}: {str(e)}")
        
        return {"errors": errors, "warnings": warnings}
    
    def _perform_static_analysis(self, files: List[Path]) -> Dict[str, List[str]]:
        """Perform static code analysis"""
        warnings = []
        suggestions = []
        
        for file_path in files:
            if file_path.suffix == '.py':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Basic static checks
                    lines = content.split('\n')
                    
                    # Check for long lines
                    for i, line in enumerate(lines, 1):
                        if len(line) > 120:
                            warnings.append(f"Long line in {file_path.name}:{i} ({len(line)} chars)")
                    
                    # Check for missing docstrings
                    if 'def ' in content and '"""' not in content and "'''" not in content:
                        suggestions.append(f"Consider adding docstrings to {file_path.name}")
                    
                    # Check for print statements (might be debug code)
                    if 'print(' in content:
                        suggestions.append(f"Consider using logging instead of print in {file_path.name}")
                    
                except Exception as e:
                    warnings.append(f"Static analysis failed for {file_path.name}: {str(e)}")
        
        return {"warnings": warnings, "suggestions": suggestions}
    
    async def _run_project_safely(self, project_dir: Path, project_name: str) -> Dict[str, Any]:
        """Safely execute the project with monitoring"""
        output = ""
        errors = []
        timeout = False
        exit_code = None
        max_memory = 0
        
        # Find main file to execute
        main_file = self._find_main_file(project_dir)
        if not main_file:
            return {
                "output": "",
                "errors": ["No executable main file found"],
                "timeout": False,
                "exit_code": -1,
                "memory_usage": 0
            }
        
        try:
            # Prepare execution command
            if main_file.suffix == '.py':
                cmd = [sys.executable, str(main_file)]
            else:
                return {
                    "output": "",
                    "errors": [f"Unsupported file type: {main_file.suffix}"],
                    "timeout": False,
                    "exit_code": -1,
                    "memory_usage": 0
                }
            
            # Execute with timeout and monitoring
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024*1024  # 1MB buffer limit
            )
            
            try:
                # Wait with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.testing.max_execution_time
                )
                
                output = stdout.decode('utf-8', errors='ignore')
                error_output = stderr.decode('utf-8', errors='ignore')
                
                if error_output:
                    errors.append(f"Runtime error: {error_output}")
                
                exit_code = process.returncode
                
                # Monitor memory usage (basic)
                try:
                    if process.pid:
                        proc = psutil.Process(process.pid)
                        max_memory = proc.memory_info().rss / 1024 / 1024  # MB
                except:
                    pass
                
            except asyncio.TimeoutError:
                timeout = True
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                errors.append("Execution timeout")
            
        except Exception as e:
            errors.append(f"Execution failed: {str(e)}")
        
        return {
            "output": output,
            "errors": errors,
            "timeout": timeout,
            "exit_code": exit_code,
            "memory_usage": max_memory
        }
    
    def _find_main_file(self, project_dir: Path) -> Optional[Path]:
        """Find the main executable file in the project"""
        # Priority order for main files
        main_candidates = [
            "main.py", "app.py", "run.py", "start.py", "__main__.py",
            "index.py", "server.py", "bot.py", "client.py"
        ]
        
        # Check for specific main files first
        for candidate in main_candidates:
            main_file = project_dir / candidate
            if main_file.exists():
                return main_file
        
        # Find any Python file with main guard
        for py_file in project_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'if __name__ == "__main__"' in content:
                    return py_file
            except:
                continue
        
        # Return first Python file as fallback
        py_files = list(project_dir.rglob("*.py"))
        if py_files:
            return py_files[0]
        
        return None
    
    def _cleanup_directory(self, directory: Path):
        """Safely cleanup temporary directory"""
        try:
            import shutil
            if directory.exists():
                shutil.rmtree(directory)
                logger.debug(f"Cleaned up directory: {directory}")
        except Exception as e:
            logger.warning(f"Failed to cleanup directory {directory}: {e}")


# Global code tester instance
code_tester = None


def get_code_tester() -> CodeTester:
    """Get global code tester instance"""
    global code_tester
    if code_tester is None:
        code_tester = CodeTester()
    return code_tester