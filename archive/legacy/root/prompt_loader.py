#!/usr/bin/env python3
"""
Prompt Loader Utility
Loads prompts from the prompts directory for use in the pipeline
"""

import os
from typing import Dict, Optional
from pathlib import Path


class PromptLoader:
    """Load and manage prompts from files"""

    def __init__(self, prompts_dir: str = "prompts"):
        """Initialize with prompts directory path"""
        self.prompts_dir = Path(prompts_dir)
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")

        # Cache for loaded prompts
        self._cache: Dict[str, str] = {}

    def load_prompt(
        self, filename: str, variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Load a prompt from file and substitute variables

        Args:
            filename: Name of the prompt file (e.g., "1-research-analyzer-verticals.txt")
            variables: Dictionary of variables to substitute in the prompt

        Returns:
            Processed prompt text
        """
        # Check cache first
        if filename not in self._cache:
            filepath = self.prompts_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Prompt file not found: {filepath}")

            with open(filepath, "r", encoding="utf-8") as f:
                self._cache[filename] = f.read()

        prompt = self._cache[filename]

        # Substitute variables
        if variables:
            for key, value in variables.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt

    def extract_system_and_user(self, prompt_text: str) -> tuple[str, str]:
        """
        Extract system and user prompts from loaded text

        Args:
            prompt_text: Full prompt text with SYSTEM: and USER: sections

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = ""
        user_prompt = ""

        if "SYSTEM:" in prompt_text and "USER:" in prompt_text:
            parts = prompt_text.split("USER:")
            system_part = parts[0].replace("SYSTEM:", "").strip()
            user_part = "USER:".join(parts[1:]).strip()

            system_prompt = system_part
            user_prompt = user_part
        else:
            # If no SYSTEM/USER markers, treat entire text as user prompt
            user_prompt = prompt_text.strip()

        return system_prompt, user_prompt

    def load_and_parse(
        self, filename: str, variables: Optional[Dict[str, str]] = None
    ) -> tuple[str, str]:
        """
        Load prompt and parse into system and user components

        Args:
            filename: Name of the prompt file
            variables: Dictionary of variables to substitute

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        prompt_text = self.load_prompt(filename, variables)
        return self.extract_system_and_user(prompt_text)

    def list_prompts(self) -> list[str]:
        """List all available prompt files"""
        return sorted([f.name for f in self.prompts_dir.glob("*.txt")])

    def get_prompt_info(self, filename: str) -> Dict[str, str]:
        """Get information about a prompt file"""
        filepath = self.prompts_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Prompt file not found: {filepath}")

        # Extract first line as description
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        return {
            "filename": filename,
            "path": str(filepath),
            "description": first_line
            if first_line.startswith("SYSTEM:")
            else "No description",
            "size": filepath.stat().st_size,
        }


# Global instance for convenience
prompt_loader = PromptLoader()


def load_prompt(filename: str, **variables) -> str:
    """Convenience function to load a prompt with variables"""
    return prompt_loader.load_prompt(filename, variables)


def load_system_user(filename: str, **variables) -> tuple[str, str]:
    """Convenience function to load and parse system/user prompts"""
    return prompt_loader.load_and_parse(filename, variables)
