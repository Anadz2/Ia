"""
Intelligent Code Correction System
Automatically fixes code issues using multiple strategies and AI personas
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import hashlib

from .logger import get_logger
from .config_manager import get_config
from .gemini_ai import get_gemini_ai, PersonaType, GeneratedProject
from .code_tester import get_code_tester, TestReport, TestResult

logger = get_logger("CodeCorrector")


class CorrectionStrategy(Enum):
    """Different correction strategies"""
    CONSERVATIVE = "conservative"  # Minimal changes
    STANDARD = "standard"         # Normal fixes
    AGGRESSIVE = "aggressive"     # Major improvements
    REWRITE = "rewrite"          # Complete rewrite
    HYBRID = "hybrid"            # Mix of strategies
    PERSONA_SWITCH = "persona_switch"  # Try different AI personas


@dataclass
class CorrectionAttempt:
    """Record of a correction attempt"""
    attempt_number: int
    strategy: CorrectionStrategy
    persona: PersonaType
    original_errors: List[str]
    fixed_files: Dict[str, str]
    test_result: TestReport
    success: bool
    improvement_score: float
    code_hash: str
    timestamp: float


@dataclass
class CorrectionSession:
    """Complete correction session data"""
    project_name: str
    original_files: Dict[str, str]
    attempts: List[CorrectionAttempt]
    final_files: Dict[str, str]
    total_time: float
    success: bool
    final_score: float


class CodeCorrector:
    """Intelligent code correction system with multiple strategies"""
    
    def __init__(self):
        self.config = get_config()
        self.gemini_ai = get_gemini_ai()
        self.code_tester = get_code_tester()
        
        # Strategy progression for different error types
        self.strategy_progression = {
            TestResult.SYNTAX_ERROR: [
                CorrectionStrategy.CONSERVATIVE,
                CorrectionStrategy.STANDARD,
                CorrectionStrategy.AGGRESSIVE,
                CorrectionStrategy.REWRITE
            ],
            TestResult.RUNTIME_ERROR: [
                CorrectionStrategy.STANDARD,
                CorrectionStrategy.AGGRESSIVE,
                CorrectionStrategy.PERSONA_SWITCH,
                CorrectionStrategy.REWRITE
            ],
            TestResult.SECURITY_ERROR: [
                CorrectionStrategy.AGGRESSIVE,
                CorrectionStrategy.REWRITE
            ],
            TestResult.TIMEOUT: [
                CorrectionStrategy.AGGRESSIVE,
                CorrectionStrategy.PERSONA_SWITCH,
                CorrectionStrategy.REWRITE
            ]
        }
        
        # Persona progression for different strategies
        self.persona_progression = [
            PersonaType.DEBUGGER,
            PersonaType.SENIOR_DEVELOPER,
            PersonaType.OPTIMIZER,
            PersonaType.ARCHITECT,
            PersonaType.SECURITY_EXPERT
        ]
        
        logger.info("Code corrector initialized")
    
    async def correct_project(self, project: GeneratedProject, initial_test: TestReport) -> CorrectionSession:
        """Correct project issues using intelligent strategies"""
        start_time = time.time()
        session = CorrectionSession(
            project_name=project.name,
            original_files=project.files.copy(),
            attempts=[],
            final_files=project.files.copy(),
            total_time=0,
            success=False,
            final_score=0
        )
        
        logger.info(f"Starting correction session for project: {project.name}")
        
        if initial_test.success:
            logger.info("Project already passes all tests, no correction needed")
            session.success = True
            session.final_score = 100.0
            session.total_time = time.time() - start_time
            return session
        
        current_files = project.files.copy()
        current_test = initial_test
        seen_hashes: Set[str] = set()
        
        max_attempts = self.config.testing.max_correction_attempts
        
        for attempt_num in range(1, max_attempts + 1):
            logger.log_correction_attempt(project.name, attempt_num, "determining_strategy")
            
            # Prevent infinite loops by checking code hash
            code_hash = self._calculate_code_hash(current_files)
            if code_hash in seen_hashes:
                logger.warning(f"Code hash already seen, switching to drastic strategy")
                strategy = CorrectionStrategy.REWRITE
            else:
                seen_hashes.add(code_hash)
                strategy = self._select_strategy(current_test, attempt_num, max_attempts)
            
            # Select persona based on strategy and attempt
            persona = self._select_persona(strategy, attempt_num, current_test.result)
            
            logger.info(f"Attempt {attempt_num}/{max_attempts}: Strategy={strategy.value}, Persona={persona.value}")
            
            try:
                # Apply correction strategy
                corrected_files = await self._apply_correction_strategy(
                    current_files, current_test, strategy, persona
                )
                
                # Test corrected code
                test_result = await self.code_tester.test_project(corrected_files, f"{project.name}_attempt_{attempt_num}")
                
                # Calculate improvement score
                improvement_score = self._calculate_improvement_score(current_test, test_result)
                
                # Record attempt
                attempt = CorrectionAttempt(
                    attempt_number=attempt_num,
                    strategy=strategy,
                    persona=persona,
                    original_errors=current_test.errors.copy(),
                    fixed_files=corrected_files.copy(),
                    test_result=test_result,
                    success=test_result.success,
                    improvement_score=improvement_score,
                    code_hash=self._calculate_code_hash(corrected_files),
                    timestamp=time.time()
                )
                
                session.attempts.append(attempt)
                
                logger.info(f"Attempt {attempt_num} result: Success={test_result.success}, "
                           f"Improvement={improvement_score:.1f}%, Errors={len(test_result.errors)}")
                
                # Check if we should accept this attempt
                if test_result.success:
                    logger.info(f"✅ Project corrected successfully in {attempt_num} attempts!")
                    session.final_files = corrected_files
                    session.success = True
                    session.final_score = 100.0
                    break
                elif improvement_score > 0:
                    logger.info(f"📈 Improvement detected, continuing with corrected code")
                    current_files = corrected_files
                    current_test = test_result
                else:
                    logger.warning(f"❌ No improvement, trying different strategy")
                    # Don't update current_files, try different approach
                
            except Exception as e:
                logger.error(f"Correction attempt {attempt_num} failed: {e}")
                # Continue with next attempt
                continue
        
        # Final assessment
        if not session.success:
            # Use best attempt if available
            best_attempt = self._find_best_attempt(session.attempts)
            if best_attempt and best_attempt.improvement_score > 0:
                session.final_files = best_attempt.fixed_files
                session.final_score = best_attempt.improvement_score
                logger.info(f"Using best attempt with {best_attempt.improvement_score:.1f}% improvement")
            else:
                logger.warning("No successful correction found, returning original files")
        
        session.total_time = time.time() - start_time
        
        logger.info(f"Correction session completed: Success={session.success}, "
                   f"Time={session.total_time:.1f}s, Attempts={len(session.attempts)}")
        
        return session
    
    def _select_strategy(self, test_result: TestReport, attempt_num: int, max_attempts: int) -> CorrectionStrategy:
        """Select correction strategy based on test results and attempt number"""
        
        # Get strategy progression for the main error type
        main_error_type = test_result.result
        strategies = self.strategy_progression.get(main_error_type, [
            CorrectionStrategy.STANDARD,
            CorrectionStrategy.AGGRESSIVE,
            CorrectionStrategy.REWRITE
        ])
        
        # Progress through strategies based on attempt number
        if attempt_num <= len(strategies):
            return strategies[attempt_num - 1]
        
        # For later attempts, use more aggressive strategies
        if attempt_num > max_attempts * 0.7:
            return CorrectionStrategy.REWRITE
        elif attempt_num > max_attempts * 0.5:
            return CorrectionStrategy.PERSONA_SWITCH
        else:
            return CorrectionStrategy.AGGRESSIVE
    
    def _select_persona(self, strategy: CorrectionStrategy, attempt_num: int, error_type: TestResult) -> PersonaType:
        """Select AI persona based on strategy and error type"""
        
        if strategy == CorrectionStrategy.PERSONA_SWITCH:
            # Cycle through different personas
            persona_index = (attempt_num - 1) % len(self.persona_progression)
            return self.persona_progression[persona_index]
        
        # Select persona based on error type
        persona_map = {
            TestResult.SYNTAX_ERROR: PersonaType.DEBUGGER,
            TestResult.RUNTIME_ERROR: PersonaType.DEBUGGER,
            TestResult.SECURITY_ERROR: PersonaType.SECURITY_EXPERT,
            TestResult.TIMEOUT: PersonaType.OPTIMIZER,
            TestResult.MEMORY_ERROR: PersonaType.OPTIMIZER
        }
        
        return persona_map.get(error_type, PersonaType.SENIOR_DEVELOPER)
    
    async def _apply_correction_strategy(
        self, 
        files: Dict[str, str], 
        test_result: TestReport, 
        strategy: CorrectionStrategy,
        persona: PersonaType
    ) -> Dict[str, str]:
        """Apply specific correction strategy"""
        
        logger.info(f"Applying {strategy.value} strategy with {persona.value} persona")
        
        # Set AI persona
        self.gemini_ai.set_persona(persona)
        
        corrected_files = files.copy()
        
        if strategy == CorrectionStrategy.CONSERVATIVE:
            # Fix only critical errors with minimal changes
            corrected_files = await self._conservative_fix(files, test_result)
            
        elif strategy == CorrectionStrategy.STANDARD:
            # Standard error fixing
            corrected_files = await self._standard_fix(files, test_result)
            
        elif strategy == CorrectionStrategy.AGGRESSIVE:
            # Aggressive fixing with major improvements
            corrected_files = await self._aggressive_fix(files, test_result)
            
        elif strategy == CorrectionStrategy.REWRITE:
            # Complete rewrite of problematic files
            corrected_files = await self._rewrite_fix(files, test_result)
            
        elif strategy == CorrectionStrategy.HYBRID:
            # Mix of different strategies
            corrected_files = await self._hybrid_fix(files, test_result)
            
        elif strategy == CorrectionStrategy.PERSONA_SWITCH:
            # Use different persona with standard approach
            corrected_files = await self._standard_fix(files, test_result)
        
        return corrected_files
    
    async def _conservative_fix(self, files: Dict[str, str], test_result: TestReport) -> Dict[str, str]:
        """Apply conservative fixes - minimal changes only"""
        corrected_files = files.copy()
        
        # Focus only on syntax errors and critical runtime errors
        critical_errors = test_result.syntax_issues + [
            error for error in test_result.runtime_issues 
            if any(keyword in error.lower() for keyword in ['syntax', 'indentation', 'import', 'undefined'])
        ]
        
        if not critical_errors:
            return corrected_files
        
        # Fix files one by one
        for filename, content in files.items():
            if any(filename in error for error in critical_errors):
                try:
                    fixed_content = await self.gemini_ai.fix_code(
                        content, filename, critical_errors, "conservative"
                    )
                    corrected_files[filename] = fixed_content
                    logger.debug(f"Conservative fix applied to {filename}")
                except Exception as e:
                    logger.error(f"Conservative fix failed for {filename}: {e}")
        
        return corrected_files
    
    async def _standard_fix(self, files: Dict[str, str], test_result: TestReport) -> Dict[str, str]:
        """Apply standard fixes"""
        corrected_files = files.copy()
        
        all_errors = test_result.errors
        if not all_errors:
            return corrected_files
        
        # Fix files with errors
        for filename, content in files.items():
            relevant_errors = [error for error in all_errors if filename in error or not any(fname in error for fname in files.keys())]
            
            if relevant_errors:
                try:
                    fixed_content = await self.gemini_ai.fix_code(
                        content, filename, relevant_errors, "standard"
                    )
                    corrected_files[filename] = fixed_content
                    logger.debug(f"Standard fix applied to {filename}")
                except Exception as e:
                    logger.error(f"Standard fix failed for {filename}: {e}")
        
        return corrected_files
    
    async def _aggressive_fix(self, files: Dict[str, str], test_result: TestReport) -> Dict[str, str]:
        """Apply aggressive fixes with major improvements"""
        corrected_files = files.copy()
        
        all_issues = test_result.errors + test_result.warnings + test_result.suggestions
        
        # Fix all files aggressively
        for filename, content in files.items():
            try:
                fixed_content = await self.gemini_ai.fix_code(
                    content, filename, all_issues, "aggressive"
                )
                corrected_files[filename] = fixed_content
                logger.debug(f"Aggressive fix applied to {filename}")
            except Exception as e:
                logger.error(f"Aggressive fix failed for {filename}: {e}")
        
        return corrected_files
    
    async def _rewrite_fix(self, files: Dict[str, str], test_result: TestReport) -> Dict[str, str]:
        """Completely rewrite problematic files"""
        corrected_files = files.copy()
        
        # Identify most problematic files
        problematic_files = self._identify_problematic_files(files, test_result)
        
        for filename in problematic_files:
            if filename in files:
                try:
                    # Create a rewrite prompt
                    original_content = files[filename]
                    rewrite_prompt = f"""
                    The following file has multiple issues and needs to be completely rewritten:
                    
                    Original file: {filename}
                    Issues found: {', '.join(test_result.errors)}
                    
                    Please rewrite this file completely to fix all issues while maintaining the same functionality:
                    
                    ```
                    {original_content}
                    ```
                    
                    Requirements:
                    1. Fix all syntax and runtime errors
                    2. Improve code structure and readability
                    3. Add proper error handling
                    4. Follow best practices
                    5. Maintain original functionality
                    """
                    
                    # Use senior developer persona for rewriting
                    self.gemini_ai.set_persona(PersonaType.SENIOR_DEVELOPER)
                    response = await self.gemini_ai._generate_with_persona(rewrite_prompt, PersonaType.SENIOR_DEVELOPER)
                    
                    # Extract rewritten code
                    rewritten_content = self.gemini_ai._extract_code_from_response(response)
                    corrected_files[filename] = rewritten_content
                    
                    logger.info(f"File {filename} completely rewritten")
                    
                except Exception as e:
                    logger.error(f"Rewrite failed for {filename}: {e}")
        
        return corrected_files
    
    async def _hybrid_fix(self, files: Dict[str, str], test_result: TestReport) -> Dict[str, str]:
        """Apply hybrid approach - mix of strategies"""
        corrected_files = files.copy()
        
        # Apply conservative fix first
        corrected_files = await self._conservative_fix(corrected_files, test_result)
        
        # Test intermediate result
        intermediate_test = await self.code_tester.test_project(corrected_files, "hybrid_intermediate")
        
        # If still has issues, apply aggressive fix to remaining problems
        if not intermediate_test.success:
            corrected_files = await self._aggressive_fix(corrected_files, intermediate_test)
        
        return corrected_files
    
    def _identify_problematic_files(self, files: Dict[str, str], test_result: TestReport) -> List[str]:
        """Identify files that are causing the most issues"""
        file_error_count = {}
        
        # Count errors per file
        for error in test_result.errors:
            for filename in files.keys():
                if filename in error:
                    file_error_count[filename] = file_error_count.get(filename, 0) + 1
        
        # Sort by error count
        sorted_files = sorted(file_error_count.items(), key=lambda x: x[1], reverse=True)
        
        # Return top problematic files (up to 3)
        return [filename for filename, count in sorted_files[:3]]
    
    def _calculate_improvement_score(self, old_test: TestReport, new_test: TestReport) -> float:
        """Calculate improvement score between two test results"""
        if new_test.success:
            return 100.0
        
        old_error_count = len(old_test.errors)
        new_error_count = len(new_test.errors)
        
        if old_error_count == 0:
            return 0.0 if new_error_count > 0 else 100.0
        
        # Calculate error reduction percentage
        error_reduction = max(0, (old_error_count - new_error_count) / old_error_count * 100)
        
        # Bonus for fixing specific error types
        bonus = 0
        if len(new_test.syntax_issues) < len(old_test.syntax_issues):
            bonus += 10
        if len(new_test.security_issues) < len(old_test.security_issues):
            bonus += 20
        
        return min(100.0, error_reduction + bonus)
    
    def _find_best_attempt(self, attempts: List[CorrectionAttempt]) -> Optional[CorrectionAttempt]:
        """Find the best correction attempt"""
        if not attempts:
            return None
        
        # Prioritize successful attempts
        successful_attempts = [attempt for attempt in attempts if attempt.success]
        if successful_attempts:
            return successful_attempts[0]  # First successful attempt
        
        # Otherwise, return attempt with highest improvement score
        return max(attempts, key=lambda x: x.improvement_score)
    
    def _calculate_code_hash(self, files: Dict[str, str]) -> str:
        """Calculate hash of all files to detect loops"""
        combined_content = ""
        for filename in sorted(files.keys()):
            combined_content += f"{filename}:{files[filename]}\n"
        
        return hashlib.md5(combined_content.encode()).hexdigest()


# Global code corrector instance
code_corrector = None


def get_code_corrector() -> CodeCorrector:
    """Get global code corrector instance"""
    global code_corrector
    if code_corrector is None:
        code_corrector = CodeCorrector()
    return code_corrector