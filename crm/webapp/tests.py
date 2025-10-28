from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json

from webapp.models import Project, ProjectRole, ProjectMembership, DocumentSource
from webapp.llm_service import (
    generate_onboarding_draft,
    parse_llm_output,
    create_fallback_structure,
    chunk_text,
    extract_text_from_document
)


class LLMServiceTests(TestCase):
    """Test cases for LLM service functions."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            creator=self.user
        )
        self.role = ProjectRole.objects.create(
            project=self.project,
            name='Backend Developer'
        )
        ProjectMembership.objects.create(
            user=self.user,
            project=self.project,
            role=self.role,
            is_admin=True
        )
    
    def test_chunk_text_basic(self):
        """Test basic text chunking functionality."""
        text = "This is a test document with multiple words that should be chunked properly."
        chunks = chunk_text(text, chunk_size=5, overlap=2)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        # Check that chunks don't exceed the specified size
        for chunk in chunks:
            words = chunk.split()
            self.assertLessEqual(len(words), 5)
    
    def test_chunk_text_empty(self):
        """Test chunking with empty text."""
        chunks = chunk_text("", chunk_size=10, overlap=2)
        self.assertEqual(chunks, [])
    
    def test_create_fallback_structure(self):
        """Test fallback structure creation."""
        role_name = "Test Role"
        structure = create_fallback_structure(role_name)
        
        # Check structure
        self.assertIn('steps', structure)
        self.assertIn('tasks', structure)
        self.assertIsInstance(structure['steps'], list)
        self.assertIsInstance(structure['tasks'], list)
        
        # Check steps
        self.assertGreater(len(structure['steps']), 0)
        for step in structure['steps']:
            self.assertIn('id', step)
            self.assertIn('title', step)
            self.assertIn('order', step)
            self.assertIn('description', step)
        
        # Check tasks
        self.assertGreater(len(structure['tasks']), 0)
        for task in structure['tasks']:
            self.assertIn('step_id', task)
            self.assertIn('title', task)
            self.assertIn('is_required', task)
            self.assertIn('description', task)
            self.assertIn('acceptance_criteria', task)
            self.assertIn('estimated_time_hours', task)
            self.assertIn('depends_on', task)
    
    def test_parse_llm_output_valid_json(self):
        """Test parsing valid JSON output."""
        valid_json = {
            "steps": [
                {
                    "id": "S1",
                    "title": "Test Step",
                    "order": 1,
                    "description": "Test description"
                }
            ],
            "tasks": [
                {
                    "step_id": "S1",
                    "title": "Test Task",
                    "is_required": True,
                    "description": "Test task description",
                    "acceptance_criteria": ["Criterion 1"],
                    "estimated_time_hours": 2.0,
                    "depends_on": []
                }
            ]
        }
        
        json_str = json.dumps(valid_json)
        result = parse_llm_output(json_str, "Test Role")
        
        self.assertEqual(result['steps'], valid_json['steps'])
        self.assertEqual(result['tasks'], valid_json['tasks'])
    
    def test_parse_llm_output_no_json(self):
        """Test parsing output with no JSON."""
        no_json = "This is just plain text with no JSON structure."
        
        result = parse_llm_output(no_json, "Test Role")
        
        # Should return fallback structure
        self.assertIn('steps', result)
        self.assertIn('tasks', result)
    
    def test_extract_text_from_document_txt(self):
        """Test text extraction from TXT document."""
        content = "This is a test document content."
        result = extract_text_from_document(content, 'txt')
        self.assertEqual(result, content)
    
    def test_generate_onboarding_draft_template_fallback(self):
        """Test template-based onboarding draft generation fallback."""
        result = generate_onboarding_draft(
            role_name="Backend Developer",
            project_stack="Django, PostgreSQL",
            documentation_chunks=["Test documentation"]
        )
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertIn('metadata', result)
        self.assertIn('steps', result['data'])
        self.assertIn('tasks', result['data'])
        self.assertGreaterEqual(len(result['data']['steps']), 8)  # Should have comprehensive steps
        self.assertGreaterEqual(len(result['data']['tasks']), 15)  # Should have comprehensive tasks


class LLMOnboardingViewsTests(TestCase):
    """Test cases for LLM onboarding views."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            creator=self.user
        )
        self.role = ProjectRole.objects.create(
            project=self.project,
            name='Backend Developer'
        )
        ProjectMembership.objects.create(
            user=self.user,
            project=self.project,
            role=self.role,
            is_admin=True
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_llm_onboarding_generate_get(self):
        """Test GET request to LLM onboarding generate view."""
        url = reverse('llm_onboarding_generate', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI-Assisted Onboarding')
        self.assertContains(response, 'Generate an onboarding plan using AI')
    
    def test_llm_onboarding_generate_post_success(self):
        """Test successful POST request to LLM onboarding generate view."""
        url = reverse('llm_onboarding_generate', kwargs={'project_id': self.project.id})
        
        with patch('webapp.llm_service.generate_onboarding_draft') as mock_generate:
            mock_generate.return_value = {
                'success': True,
                'data': {
                    'steps': [{'id': 'S1', 'title': 'Test Step', 'order': 1, 'description': 'Test'}],
                    'tasks': [{'step_id': 'S1', 'title': 'Test Task', 'is_required': True, 'description': 'Test', 'acceptance_criteria': ['Criterion'], 'estimated_time_hours': 1.0, 'depends_on': []}]
                },
                'metadata': {'llm_model': 'test-model'}
            }
            
            response = self.client.post(url, {
                'role_id': self.role.id,
                'project_stack': 'Django, PostgreSQL',
                'document_ids': []
            })
            
            self.assertEqual(response.status_code, 302)  # Redirect to review
            self.assertIn('llm_draft', self.client.session)
    
    def test_upload_document_post_success(self):
        """Test successful document upload."""
        url = reverse('upload_document', kwargs={'project_id': self.project.id})
        
        response = self.client.post(url, {
            'title': 'Test Document',
            'doc_type': 'txt',
            'content': 'This is test document content.'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to generate
        
        # Check document was created
        doc = DocumentSource.objects.get(title='Test Document')
        self.assertEqual(doc.project, self.project)
        self.assertEqual(doc.doc_type, 'txt')
        self.assertEqual(doc.content, 'This is test document content.')
