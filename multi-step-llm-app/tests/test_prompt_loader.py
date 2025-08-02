"""
Unit tests for prompt_loader.py
"""

import pytest
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_loader import PromptLoader, load_prompt, load_system_user


class TestPromptLoader:
    """Test suite for PromptLoader"""
    
    def test_init_with_valid_directory(self, tmp_path):
        """Test initialization with valid prompts directory"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        loader = PromptLoader(str(prompts_dir))
        assert loader.prompts_dir == prompts_dir
        assert loader._cache == {}
    
    def test_init_with_missing_directory(self):
        """Test initialization with non-existent directory"""
        with pytest.raises(FileNotFoundError, match="Prompts directory not found"):
            PromptLoader("nonexistent/prompts")
    
    def test_load_prompt_simple(self, tmp_path):
        """Test loading a simple prompt without variables"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        prompt_file = prompts_dir / "test.txt"
        prompt_file.write_text("This is a test prompt")
        
        loader = PromptLoader(str(prompts_dir))
        prompt = loader.load_prompt("test.txt")
        
        assert prompt == "This is a test prompt"
        assert "test.txt" in loader._cache
    
    def test_load_prompt_with_variables(self, tmp_path):
        """Test loading prompt with variable substitution"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        prompt_file = prompts_dir / "test.txt"
        prompt_file.write_text("Hello {name}, your score is {score}")
        
        loader = PromptLoader(str(prompts_dir))
        prompt = loader.load_prompt("test.txt", {"name": "Alice", "score": "100"})
        
        assert prompt == "Hello Alice, your score is 100"
    
    def test_load_prompt_missing_file(self, tmp_path):
        """Test loading non-existent prompt file"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        loader = PromptLoader(str(prompts_dir))
        
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            loader.load_prompt("missing.txt")
    
    def test_cache_behavior(self, tmp_path):
        """Test that prompts are cached after first load"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        prompt_file = prompts_dir / "test.txt"
        prompt_file.write_text("Original content")
        
        loader = PromptLoader(str(prompts_dir))
        
        # First load
        prompt1 = loader.load_prompt("test.txt")
        assert prompt1 == "Original content"
        
        # Modify file
        prompt_file.write_text("Modified content")
        
        # Second load should return cached version
        prompt2 = loader.load_prompt("test.txt")
        assert prompt2 == "Original content"
    
    def test_extract_system_and_user(self):
        """Test extraction of system and user prompts"""
        loader = PromptLoader(".")  # Use current dir for init
        
        # Test with both SYSTEM and USER sections
        prompt_text = """SYSTEM: You are an expert assistant.

USER: Please help me with this task."""
        
        system, user = loader.extract_system_and_user(prompt_text)
        assert system == "You are an expert assistant."
        assert user == "Please help me with this task."
    
    def test_extract_system_and_user_no_markers(self):
        """Test extraction when no SYSTEM/USER markers present"""
        loader = PromptLoader(".")
        
        prompt_text = "This is just a plain prompt"
        system, user = loader.extract_system_and_user(prompt_text)
        
        assert system == ""
        assert user == "This is just a plain prompt"
    
    def test_extract_system_and_user_complex(self):
        """Test extraction with complex formatting"""
        loader = PromptLoader(".")
        
        prompt_text = """SYSTEM: You are an expert at analysis.
You have deep knowledge.

USER: Context: {context}

Analyze the following:
- Point 1
- Point 2

Return JSON format."""
        
        system, user = loader.extract_system_and_user(prompt_text)
        assert "You are an expert at analysis" in system
        assert "deep knowledge" in system
        assert "Context: {context}" in user
        assert "Return JSON format" in user
    
    def test_load_and_parse(self, tmp_path):
        """Test combined load and parse functionality"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        prompt_file = prompts_dir / "test.txt"
        prompt_file.write_text("""SYSTEM: Expert system

USER: Hello {name}, please {action}""")
        
        loader = PromptLoader(str(prompts_dir))
        system, user = loader.load_and_parse(
            "test.txt", 
            {"name": "Bob", "action": "analyze this"}
        )
        
        assert system == "Expert system"
        assert user == "Hello Bob, please analyze this"
    
    def test_list_prompts(self, tmp_path):
        """Test listing available prompts"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        # Create test files
        (prompts_dir / "a.txt").write_text("A")
        (prompts_dir / "b.txt").write_text("B")
        (prompts_dir / "c.txt").write_text("C")
        (prompts_dir / "not_txt.json").write_text("{}")
        
        loader = PromptLoader(str(prompts_dir))
        prompts = loader.list_prompts()
        
        assert prompts == ["a.txt", "b.txt", "c.txt"]
    
    def test_get_prompt_info(self, tmp_path):
        """Test getting prompt information"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        prompt_file = prompts_dir / "test.txt"
        content = "SYSTEM: This is a test prompt\n\nUSER: Test content"
        prompt_file.write_text(content)
        
        loader = PromptLoader(str(prompts_dir))
        info = loader.get_prompt_info("test.txt")
        
        assert info["filename"] == "test.txt"
        assert str(prompts_dir / "test.txt") in info["path"]
        assert info["description"] == "SYSTEM: This is a test prompt"
        assert info["size"] == len(content)
    
    def test_get_prompt_info_missing(self, tmp_path):
        """Test getting info for non-existent prompt"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        loader = PromptLoader(str(prompts_dir))
        
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            loader.get_prompt_info("missing.txt")


class TestConvenienceFunctions:
    """Test module-level convenience functions"""
    
    def test_load_prompt_function(self, tmp_path, monkeypatch):
        """Test the load_prompt convenience function"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        prompt_file = prompts_dir / "test.txt"
        prompt_file.write_text("Hello {name}")
        
        # Monkeypatch to use our test directory
        monkeypatch.setattr('prompt_loader.prompt_loader', PromptLoader(str(prompts_dir)))
        
        result = load_prompt("test.txt", name="World")
        assert result == "Hello World"
    
    def test_load_system_user_function(self, tmp_path, monkeypatch):
        """Test the load_system_user convenience function"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        prompt_file = prompts_dir / "test.txt"
        prompt_file.write_text("""SYSTEM: Expert

USER: Task for {user}""")
        
        # Monkeypatch to use our test directory
        monkeypatch.setattr('prompt_loader.prompt_loader', PromptLoader(str(prompts_dir)))
        
        system, user = load_system_user("test.txt", user="Alice")
        assert system == "Expert"
        assert user == "Task for Alice"