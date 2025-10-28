"""
Tests for LLM-assisted onboarding functionality.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock

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
    
    def test_chunk_text_small(self):
        """Test chunking with text smaller than chunk size."""
        text = "Short text"
        chunks = chunk_text(text, chunk_size=20, overlap=5)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)
    
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
    
    def test_parse_llm_output_malformed_json(self):
        """Test parsing malformed JSON with repair."""
        # Missing opening brace
        malformed_json = '"steps": [{"id": "S1", "title": "Test", "order": 1, "description": "Test"}], "tasks": [{"step_id": "S1", "title": "Task", "is_required": true, "description": "Test", "acceptance_criteria": ["Criterion"], "estimated_time_hours": 2.0, "depends_on": []}]'
        
        result = parse_llm_output(malformed_json, "Test Role")
        
        # Should return fallback structure
        self.assertIn('steps', result)
        self.assertIn('tasks', result)
    
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
    
    def test_extract_text_from_document_md(self):
        """Test text extraction from Markdown document."""
        content = "# Title\n\nThis is **bold** text."
        result = extract_text_from_document(content, 'md')
        # Should extract plain text (implementation depends on markdown processing)
        self.assertIsInstance(result, str)
    
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
    
    def test_generate_onboarding_draft_fallback_on_error(self):
        """Test onboarding draft generation fallback when Together AI fails."""
        # This test verifies that the system falls back to template-based generation
        # when Together AI fails (which is the current behavior)
        
        result = generate_onboarding_draft(
            role_name="Backend Developer",
            project_stack="Django, PostgreSQL",
            documentation_chunks=["Test documentation"]
        )
        
        # Should succeed with template fallback
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertGreaterEqual(len(result['data']['steps']), 8)


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
    
    def test_llm_onboarding_generate_post_no_role(self):
        """Test POST request without selecting a role."""
        url = reverse('llm_onboarding_generate', kwargs={'project_id': self.project.id})
        
        response = self.client.post(url, {
            'role_id': '',
            'project_stack': 'Django, PostgreSQL',
            'document_ids': []
        })
        
        self.assertEqual(response.status_code, 200)  # Back to form
        self.assertContains(response, 'Please select a role')
    
    def test_llm_onboarding_generate_post_llm_error(self):
        """Test POST request when LLM generation fails."""
        url = reverse('llm_onboarding_generate', kwargs={'project_id': self.project.id})
        
        with patch('webapp.llm_service.generate_onboarding_draft') as mock_generate:
            mock_generate.return_value = {
                'success': False,
                'error': 'LLM generation failed'
            }
            
            response = self.client.post(url, {
                'role_id': self.role.id,
                'project_stack': 'Django, PostgreSQL',
                'document_ids': []
            })
            
            self.assertEqual(response.status_code, 200)  # Back to form
            self.assertContains(response, 'Generation error')
    
    def test_llm_onboarding_generate_permission_denied(self):
        """Test LLM onboarding generate with non-admin user."""
        # Create non-admin user
        non_admin = User.objects.create_user(
            username='nonadmin',
            email='nonadmin@example.com',
            password='testpass123'
        )
        ProjectMembership.objects.create(
            user=non_admin,
            project=self.project,
            role=self.role,
            is_admin=False
        )
        
        self.client.login(username='nonadmin', password='testpass123')
        url = reverse('llm_onboarding_generate', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect to onboarding setup
    
    def test_upload_document_get(self):
        """Test GET request to upload document view."""
        url = reverse('upload_document', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Project Documentation')
    
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
    
    def test_upload_document_post_file_upload(self):
        """Test document upload with file."""
        url = reverse('upload_document', kwargs={'project_id': self.project.id})
        
        test_file = SimpleUploadedFile(
            "test.txt",
            b"This is test file content.",
            content_type="text/plain"
        )
        
        response = self.client.post(url, {
            'title': 'Test File Document',
            'doc_type': 'txt',
            'file': test_file
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to generate
        
        # Check document was created
        doc = DocumentSource.objects.get(title='Test File Document')
        self.assertEqual(doc.project, self.project)
        self.assertEqual(doc.doc_type, 'txt')
        self.assertEqual(doc.content, 'This is test file content.')
    
    def test_llm_onboarding_review_get_no_draft(self):
        """Test review view with no draft in session."""
        url = reverse('llm_onboarding_review', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect to generate
    
    def test_llm_onboarding_review_get_with_draft(self):
        """Test review view with draft in session."""
        # Set up session with draft
        session = self.client.session
        session['llm_draft'] = {
            'project_id': self.project.id,
            'role_id': self.role.id,
            'draft_data': {
                'steps': [{'id': 'S1', 'title': 'Test Step', 'order': 1, 'description': 'Test'}],
                'tasks': [{'step_id': 'S1', 'title': 'Test Task', 'is_required': True, 'description': 'Test', 'acceptance_criteria': ['Criterion'], 'estimated_time_hours': 1.0, 'depends_on': []}]
            }
        }
        session.save()
        
        url = reverse('llm_onboarding_review', kwargs={'project_id': self.project.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Review Generated Plan')
    
    def test_llm_onboarding_review_post_approve(self):
        """Test approving draft in review view."""
        # Set up session with draft
        session = self.client.session
        session['llm_draft'] = {
            'project_id': self.project.id,
            'role_id': self.role.id,
            'draft_data': {
                'steps': [{'id': 'S1', 'title': 'Test Step', 'order': 1, 'description': 'Test'}],
                'tasks': [{'step_id': 'S1', 'title': 'Test Task', 'is_required': True, 'description': 'Test', 'acceptance_criteria': ['Criterion'], 'estimated_time_hours': 1.0, 'depends_on': []}]
            }
        }
        session.save()
        
        url = reverse('llm_onboarding_review', kwargs={'project_id': self.project.id})
        response = self.client.post(url, {'action': 'approve'})
        
        self.assertEqual(response.status_code, 302)  # Redirect to onboarding setup
        self.assertNotIn('llm_draft', self.client.session)  # Draft should be removed
    
    def test_llm_onboarding_review_post_reject(self):
        """Test rejecting draft in review view."""
        # Set up session with draft
        session = self.client.session
        session['llm_draft'] = {
            'project_id': self.project.id,
            'role_id': self.role.id,
            'draft_data': {
                'steps': [{'id': 'S1', 'title': 'Test Step', 'order': 1, 'description': 'Test'}],
                'tasks': [{'step_id': 'S1', 'title': 'Test Task', 'is_required': True, 'description': 'Test', 'acceptance_criteria': ['Criterion'], 'estimated_time_hours': 1.0, 'depends_on': []}]
            }
        }
        session.save()
        
        url = reverse('llm_onboarding_review', kwargs={'project_id': self.project.id})
        response = self.client.post(url, {'action': 'reject'})
        
        self.assertEqual(response.status_code, 302)  # Redirect to generate
        self.assertNotIn('llm_draft', self.client.session)  # Draft should be removed


class LLMIntegrationTests(TestCase):
    """Integration tests for the complete LLM onboarding flow."""
    
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
    
    def test_complete_workflow_with_mock_llm(self):
        """Test the complete workflow from document upload to approval."""
        # Step 1: Upload document
        upload_url = reverse('upload_document', kwargs={'project_id': self.project.id})
        response = self.client.post(upload_url, {
            'title': 'Integration Test Document',
            'doc_type': 'txt',
            'content': 'This is a test document for integration testing.'
        })
        self.assertEqual(response.status_code, 302)
        
        # Step 2: Generate onboarding plan
        generate_url = reverse('llm_onboarding_generate', kwargs={'project_id': self.project.id})
        
        with patch('webapp.llm_service.generate_onboarding_draft') as mock_generate:
            mock_generate.return_value = {
                'success': True,
                'data': {
                    'steps': [
                        {
                            'id': 'S1',
                            'title': 'Environment Setup',
                            'order': 1,
                            'description': 'Set up development environment'
                        }
                    ],
                    'tasks': [
                        {
                            'step_id': 'S1',
                            'title': 'Install Docker',
                            'is_required': True,
                            'description': 'Install Docker and Docker Compose',
                            'acceptance_criteria': ['Docker is running'],
                            'estimated_time_hours': 1.0,
                            'depends_on': []
                        }
                    ]
                },
                'metadata': {'llm_model': 'test-model'}
            }
            
            response = self.client.post(generate_url, {
                'role_id': self.role.id,
                'project_stack': 'Django, PostgreSQL',
                'document_ids': [1]  # Assuming document ID 1
            })
            self.assertEqual(response.status_code, 302)
        
        # Step 3: Review generated plan
        review_url = reverse('llm_onboarding_review', kwargs={'project_id': self.project.id})
        response = self.client.get(review_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Review Generated Plan')
        
        # Step 4: Approve the plan
        response = self.client.post(review_url, {'action': 'approve'})
        self.assertEqual(response.status_code, 302)
    
    def test_error_handling_workflow(self):
        """Test error handling in the workflow."""
        # Test with non-admin user
        non_admin = User.objects.create_user(
            username='nonadmin',
            email='nonadmin@example.com',
            password='testpass123'
        )
        ProjectMembership.objects.create(
            user=non_admin,
            project=self.project,
            role=self.role,
            is_admin=False
        )
        
        self.client.login(username='nonadmin', password='testpass123')
        
        # Try to access LLM generation
        generate_url = reverse('llm_onboarding_generate', kwargs={'project_id': self.project.id})
        response = self.client.get(generate_url)
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Try to upload document
        upload_url = reverse('upload_document', kwargs={'project_id': self.project.id})
        response = self.client.get(upload_url)
        self.assertEqual(response.status_code, 302)  # Should redirect

