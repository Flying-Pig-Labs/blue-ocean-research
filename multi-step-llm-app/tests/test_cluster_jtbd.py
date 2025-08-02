"""
Unit tests for cluster_jtbd.py
"""

import pytest
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cluster_jtbd import JTBDClusterer

class TestJTBDClusterer:
    """Test suite for JTBDClusterer"""
    
    def test_init_with_valid_credentials(self, mock_cohere_client, mock_openai_client):
        """Test initialization with valid credentials"""
        with patch('cluster_jtbd.cohere.Client', return_value=mock_cohere_client):
            with patch('cluster_jtbd.openai.OpenAI', return_value=mock_openai_client):
                clusterer = JTBDClusterer()
                assert clusterer.cohere_api_key == 'test-cohere-key'
                assert clusterer.openai_api_key == 'test-openai-key'
                assert clusterer.cohere_client is not None
                assert clusterer.openai_client is not None
    
    def test_init_without_cohere_key(self):
        """Test initialization fails without Cohere key"""
        with patch.dict(os.environ, {'COHERE_API_KEY': ''}):
            with pytest.raises(SystemExit):
                JTBDClusterer()
    
    def test_init_without_openai_key(self):
        """Test initialization fails without OpenAI key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with pytest.raises(SystemExit):
                JTBDClusterer()
    
    def test_load_texts_success(self, temp_files, mock_cohere_client, mock_openai_client):
        """Test loading texts from file"""
        with patch('cluster_jtbd.cohere.Client', return_value=mock_cohere_client):
            with patch('cluster_jtbd.openai.OpenAI', return_value=mock_openai_client):
                clusterer = JTBDClusterer()
                texts = clusterer.load_texts(temp_files['pain_points'])
                
                assert len(texts) == 3
                assert "I can't do X" in texts
                assert "Y is too complex" in texts
    
    def test_embed_texts(self, mock_cohere_client, mock_openai_client, sample_pain_points):
        """Test text embedding with Cohere"""
        mock_cohere_client.embed.return_value.embeddings = [
            [0.1, 0.2, 0.3] for _ in range(len(sample_pain_points))
        ]
        
        with patch('cluster_jtbd.cohere.Client', return_value=mock_cohere_client):
            with patch('cluster_jtbd.openai.OpenAI', return_value=mock_openai_client):
                clusterer = JTBDClusterer()
                embeddings = clusterer.embed_texts(sample_pain_points)
                
                assert embeddings.shape == (5, 3)
                assert mock_cohere_client.embed.called
    
    @patch('cluster_jtbd.HDBSCAN')
    def test_cluster_embeddings(self, mock_hdbscan, mock_cohere_client, mock_openai_client):
        """Test clustering with HDBSCAN"""
        mock_clusterer = MagicMock()
        mock_clusterer.fit_predict.return_value = np.array([0, 0, 1, 1, -1])
        mock_hdbscan.return_value = mock_clusterer
        
        with patch('cluster_jtbd.cohere.Client', return_value=mock_cohere_client):
            with patch('cluster_jtbd.openai.OpenAI', return_value=mock_openai_client):
                clusterer = JTBDClusterer()
                embeddings = np.random.rand(5, 3)
                
                labels, silhouette = clusterer.cluster_embeddings(embeddings)
                
                assert len(labels) == 5
                assert 0 in labels
                assert 1 in labels
                assert -1 in labels  # noise
    
    def test_label_clusters(self, mock_cohere_client, mock_openai_client):
        """Test cluster labeling with GPT-4o"""
        mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "label": "Integration Issues",
                "summary": "Problems with system integration",
                "job_to_be_done": "When I integrate systems, I want it to work, so I can save time",
                "severity": "High"
            })))
        ]
        
        with patch('cluster_jtbd.cohere.Client', return_value=mock_cohere_client):
            with patch('cluster_jtbd.openai.OpenAI', return_value=mock_openai_client):
                clusterer = JTBDClusterer()
                clusters = {
                    0: ["Can't integrate", "Integration fails", "Complex setup"]
                }
                
                labeled = clusterer.label_clusters(clusters)
                
                assert 0 in labeled
                assert labeled[0]['label'] == "Integration Issues"
                assert labeled[0]['severity'] == "High"
                assert labeled[0]['size'] == 3
    
    def test_generate_opportunity_zones(self, mock_cohere_client, mock_openai_client):
        """Test opportunity zone generation"""
        mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "opportunity_zones": [
                    {
                        "name": "Seamless Integration",
                        "description": "Remove integration friction",
                        "clusters_addressed": ["Integration Issues"],
                        "importance_percentage": 60,
                        "potential_impact": "High",
                        "implementation_complexity": "Medium"
                    },
                    {
                        "name": "Cost Optimization",
                        "description": "Reduce operational costs",
                        "clusters_addressed": ["High Costs"],
                        "importance_percentage": 40,
                        "potential_impact": "Medium",
                        "implementation_complexity": "Low"
                    }
                ],
                "rationale": "Focus on biggest pain points"
            })))
        ]
        
        with patch('cluster_jtbd.cohere.Client', return_value=mock_cohere_client):
            with patch('cluster_jtbd.openai.OpenAI', return_value=mock_openai_client):
                clusterer = JTBDClusterer()
                labeled_clusters = {
                    0: {
                        "label": "Integration Issues",
                        "summary": "Integration problems",
                        "job_to_be_done": "When I integrate, I want it to work, so I can save time",
                        "severity": "High",
                        "size": 10
                    }
                }
                
                zones = clusterer.generate_opportunity_zones(labeled_clusters)
                
                assert 'opportunity_zones' in zones
                assert len(zones['opportunity_zones']) == 2
                assert zones['opportunity_zones'][0]['importance_percentage'] == 60
                assert zones['opportunity_zones'][1]['importance_percentage'] == 40
    
    def test_save_results(self, tmp_path, mock_cohere_client, mock_openai_client):
        """Test saving results to JSON"""
        with patch('cluster_jtbd.cohere.Client', return_value=mock_cohere_client):
            with patch('cluster_jtbd.openai.OpenAI', return_value=mock_openai_client):
                clusterer = JTBDClusterer()
                
                labeled_clusters = {
                    0: {"label": "Test", "size": 5}
                }
                opportunity_zones = {
                    "opportunity_zones": [
                        {"name": "Test Zone", "importance_percentage": 100}
                    ]
                }
                
                output_file = tmp_path / "test_results.json"
                clusterer.save_results(labeled_clusters, opportunity_zones, str(output_file))
                
                assert output_file.exists()
                data = json.loads(output_file.read_text())
                assert 'metadata' in data
                assert 'clusters' in data
                assert 'opportunity_zones' in data