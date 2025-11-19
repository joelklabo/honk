"""Execute GitHub Copilot CLI agent invocations."""
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    """Result of agent execution."""
    success: bool
    output: str
    error: str
    duration_ms: int
    exit_code: int


class AgentExecutor:
    """Executes GitHub Copilot agents via CLI."""
    
    def __init__(
        self,
        agent_name: str,
        agent_definition: dict,
        timeout: int = 300,
        log_file: Optional[Path] = None,
    ):
        self.agent_name = agent_name
        self.agent_definition = agent_definition
        self.timeout = timeout
        self.log_file = log_file
    
    def execute(
        self,
        prompt: str,
        context_files: Optional[list[Path]] = None,
    ) -> ExecutionResult:
        """
        Execute agent with prompt and context.
        
        Args:
            prompt: User instruction/question
            context_files: Optional files to include as context
        
        Returns:
            ExecutionResult with output and metadata
        
        Raises:
            TimeoutError: If execution exceeds timeout
            FileNotFoundError: If copilot CLI not found
        """
        start_time = time.time()
        
        # Build full prompt with context
        full_prompt = self._build_prompt(prompt, context_files)
        
        # Log if requested
        if self.log_file:
            self._log(f"Executing agent: {self.agent_name}")
            self._log(f"Prompt: {prompt}")
            if context_files:
                self._log(f"Context: {', '.join(str(f) for f in context_files)}")
        
        # Execute copilot CLI
        try:
            result = self._execute_copilot(full_prompt)
            duration_ms = int((time.time() - start_time) * 1000)
            
            execution_result = ExecutionResult(
                success=(result.returncode == 0),
                output=result.stdout.decode('utf-8'),
                error=result.stderr.decode('utf-8'),
                duration_ms=duration_ms,
                exit_code=result.returncode,
            )
            
            # Log result
            if self.log_file:
                self._log(f"Completed in {duration_ms}ms")
                self._log(f"Exit code: {result.returncode}")
                if execution_result.output:
                    self._log(f"Output:\n{execution_result.output}")
                if execution_result.error:
                    self._log(f"Error:\n{execution_result.error}")
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            if self.log_file:
                self._log(f"TIMEOUT after {duration_ms}ms")
            raise TimeoutError(f"Agent execution exceeded {self.timeout}s timeout")
    
    def _build_prompt(
        self,
        prompt: str,
        context_files: Optional[list[Path]] = None,
    ) -> str:
        """
        Build full prompt with context.
        
        Format:
            {prompt}
            
            Context:
            
            File: path/to/file1.py
            ```py
            [file contents]
            ```
            
            File: path/to/file2.py
            ```py
            [file contents]
            ```
        """
        full_prompt = prompt
        
        if context_files:
            full_prompt += "\n\nContext:\n"
            
            for ctx_file in context_files:
                content = ctx_file.read_text()
                ext = ctx_file.suffix.lstrip('.')
                
                full_prompt += f"\nFile: {ctx_file}\n"
                full_prompt += f"```{ext}\n{content}\n```\n"
        
        return full_prompt
    
    def _execute_copilot(self, prompt: str) -> subprocess.CompletedProcess:
        """
        Execute copilot CLI with agent.
        
        Command: copilot @agent-name --input "prompt"
        """
        # Verify copilot CLI is available
        try:
            subprocess.run(
                ["copilot", "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise FileNotFoundError(
                "GitHub Copilot CLI not found. "
                "Install: https://docs.github.com/copilot/github-copilot-in-the-cli"
            )
        
        # Execute with agent
        cmd = [
            "copilot",
            f"@{self.agent_name}",
            "--input",
            prompt,
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=self.timeout,
        )
        
        return result
    
    def _log(self, message: str) -> None:
        """Append message to log file."""
        if self.log_file:
            with open(self.log_file, 'a') as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
