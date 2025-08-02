"""
Unit tests for main.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import MultiStepLLMApp, WorkflowStep


class TestWorkflowStep:
    """Test WorkflowStep dataclass"""
    
    def test_workflow_step_creation(self):
        """Test creating a WorkflowStep"""
        step = WorkflowStep(
            name="Test Step",
            system_prompt="You are a test assistant",
            user_prompt="Do something",
            max_tokens=1000,
            temperature=0.7
        )
        
        assert step.name == "Test Step"
        assert step.system_prompt == "You are a test assistant"
        assert step.user_prompt == "Do something"
        assert step.max_tokens == 1000
        assert step.temperature == 0.7
    
    def test_workflow_step_defaults(self):
        """Test WorkflowStep default values"""
        step = WorkflowStep(
            name="Test",
            system_prompt="System",
            user_prompt="User"
        )
        
        assert step.max_tokens == 1000
        assert step.temperature == 0.7


class TestMultiStepLLMApp:
    """Test suite for MultiStepLLMApp"""
    
    def test_init_with_api_key(self, mock_anthropic_client):
        """Test initialization with provided API key"""
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            assert app.api_key == "test-key"
            assert app.model == "claude-3-5-sonnet-20241022"
    
    def test_init_with_env_key(self, mock_anthropic_client):
        """Test initialization with environment variable"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env-test-key'}):
            with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
                app = MultiStepLLMApp()
                assert app.api_key == 'env-test-key'
    
    def test_init_without_key(self):
        """Test initialization fails without API key"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            with pytest.raises(SystemExit):
                MultiStepLLMApp()
    
    def test_create_workflow_steps(self, mock_anthropic_client):
        """Test workflow steps creation"""
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            steps = app.create_workflow_steps()
            
            assert len(steps) == 5
            assert steps[0].name == "Story Ideation"
            assert steps[1].name == "Character Development"
            assert steps[2].name == "Plot Outline"
            assert steps[3].name == "Opening Scene"
            assert steps[4].name == "Story Analysis"
            
            # Check all steps have required fields
            for step in steps:
                assert step.system_prompt
                assert step.user_prompt
                assert step.max_tokens > 0
                assert 0 <= step.temperature <= 1
    
    def test_execute_step_success(self, mock_anthropic_client):
        """Test successful step execution"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="Test response")
        ]
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            
            step = WorkflowStep(
                name="Test Step",
                system_prompt="Test system",
                user_prompt="Test prompt"
            )
            
            result = app.execute_step(step)
            assert result == "Test response"
            
            # Verify API was called correctly
            mock_anthropic_client.messages.create.assert_called_once()
            call_args = mock_anthropic_client.messages.create.call_args
            assert call_args.kwargs['model'] == "claude-3-5-sonnet-20241022"
            assert call_args.kwargs['max_tokens'] == 1000
            assert call_args.kwargs['temperature'] == 0.7
            assert call_args.kwargs['system'] == "Test system"
    
    def test_execute_step_with_context(self, mock_anthropic_client):
        """Test step execution with context from previous steps"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="Response with context")
        ]
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            
            step = WorkflowStep(
                name="Test Step",
                system_prompt="System",
                user_prompt="Current task"
            )
            
            context = "Previous step output"
            result = app.execute_step(step, context)
            
            # Check that context was included in prompt
            call_args = mock_anthropic_client.messages.create.call_args
            user_message = call_args.kwargs['messages'][0]['content']
            assert "Previous context:" in user_message
            assert context in user_message
            assert "Current task:" in user_message
    
    def test_execute_step_rate_limit(self, mock_anthropic_client):
        """Test handling of rate limit errors"""
        import anthropic
        mock_anthropic_client.messages.create.side_effect = anthropic.RateLimitError(
            "Rate limit exceeded",
            response=Mock(status_code=429),
            body={"error": {"message": "Rate limit exceeded"}}
        )
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            
            step = WorkflowStep(
                name="Test Step",
                system_prompt="System",
                user_prompt="Prompt"
            )
            
            with pytest.raises(SystemExit):
                app.execute_step(step)
    
    def test_execute_step_api_error(self, mock_anthropic_client):
        """Test handling of API errors"""
        import anthropic
        mock_anthropic_client.messages.create.side_effect = anthropic.APIError(
            "API Error",
            response=Mock(status_code=500),
            body={"error": {"message": "Internal error"}}
        )
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            
            step = WorkflowStep(
                name="Test Step",
                system_prompt="System",
                user_prompt="Prompt"
            )
            
            with pytest.raises(SystemExit):
                app.execute_step(step)
    
    def test_test_api_connection_success(self, mock_anthropic_client):
        """Test successful API connection test"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="API connection successful!")
        ]
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            app.test_api_connection()
            
            # Should not raise any exceptions
            mock_anthropic_client.messages.create.assert_called_once()
    
    def test_test_api_connection_failure(self, mock_anthropic_client):
        """Test failed API connection test"""
        mock_anthropic_client.messages.create.side_effect = Exception("Connection failed")
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            
            # Should handle exception gracefully
            app.test_api_connection()
            mock_anthropic_client.messages.create.assert_called_once()
    
    @patch('builtins.input')
    def test_run_interactive_quit(self, mock_input, mock_anthropic_client):
        """Test quitting interactive mode"""
        mock_input.return_value = 'q'
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            results = app.run_interactive()
            
            assert results == {}
            mock_anthropic_client.messages.create.assert_not_called()
    
    @patch('builtins.input')
    def test_run_interactive_single_step(self, mock_input, mock_anthropic_client):
        """Test running a single step in interactive mode"""
        mock_input.side_effect = ['', 'q']  # Continue once, then quit
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="Step 1 result")
        ]
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            results = app.run_interactive()
            
            assert len(results) == 1
            assert "Story Ideation" in results
            assert results["Story Ideation"] == "Step 1 result"
    
    def test_run_headless(self, mock_anthropic_client):
        """Test headless mode execution"""
        responses = [
            MagicMock(text=f"Step {i} result") for i in range(1, 6)
        ]
        mock_anthropic_client.messages.create.side_effect = [
            MagicMock(content=[resp]) for resp in responses
        ]
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            results = app.run_headless()
            
            assert len(results) == 5
            assert results["Story Ideation"] == "Step 1 result"
            assert results["Character Development"] == "Step 2 result"
            assert results["Plot Outline"] == "Step 3 result"
            assert results["Opening Scene"] == "Step 4 result"
            assert results["Story Analysis"] == "Step 5 result"
            
            # Verify all API calls were made
            assert mock_anthropic_client.messages.create.call_count == 5
    
    def test_run_headless_with_context_accumulation(self, mock_anthropic_client):
        """Test that context accumulates in headless mode"""
        mock_anthropic_client.messages.create.return_value.content = [
            MagicMock(text="Generic response")
        ]
        
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            app.run_headless()
            
            # Check that later calls included context from earlier ones
            calls = mock_anthropic_client.messages.create.call_args_list
            
            # First call should have no context
            first_call_content = calls[0].kwargs['messages'][0]['content']
            assert "Previous context:" not in first_call_content
            
            # Later calls should have context
            for i in range(1, 5):
                call_content = calls[i].kwargs['messages'][0]['content']
                assert "Previous context:" in call_content
    
    def test_save_results(self, tmp_path, mock_anthropic_client):
        """Test saving results to file"""
        with patch('main.anthropic.Anthropic', return_value=mock_anthropic_client):
            app = MultiStepLLMApp(api_key="test-key")
            
            results = {
                "Step 1": "Result 1",
                "Step 2": "Result 2"
            }
            
            output_file = tmp_path / "test_results.md"
            app.save_results(results, str(output_file))
            
            assert output_file.exists()
            content = output_file.read_text()
            
            assert "# Multi-Step LLM Workflow Results" in content
            assert "## Step 1" in content
            assert "Result 1" in content
            assert "## Step 2" in content
            assert "Result 2" in content
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('main.MultiStepLLMApp')
    def test_main_test_mode(self, mock_app_class, mock_args):
        """Test main function in test mode"""
        mock_args.return_value = Mock(test=True, headless=False)
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        from main import main
        main()
        
        mock_app.test_api_connection.assert_called_once()
        mock_app.run_interactive.assert_not_called()
        mock_app.run_headless.assert_not_called()
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('main.MultiStepLLMApp')
    def test_main_interactive_mode(self, mock_app_class, mock_args):
        """Test main function in interactive mode"""
        mock_args.return_value = Mock(test=False, headless=False)
        mock_app = Mock()
        mock_app.run_interactive.return_value = {"Step": "Result"}
        mock_app_class.return_value = mock_app
        
        from main import main
        main()
        
        mock_app.run_interactive.assert_called_once()
        mock_app.save_results.assert_called_once()
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('main.MultiStepLLMApp')
    def test_main_headless_mode(self, mock_app_class, mock_args):
        """Test main function in headless mode"""
        mock_args.return_value = Mock(test=False, headless=True)
        mock_app = Mock()
        mock_app.run_headless.return_value = {"Step": "Result"}
        mock_app_class.return_value = mock_app
        
        from main import main
        main()
        
        mock_app.run_headless.assert_called_once()
        mock_app.save_results.assert_called_once()