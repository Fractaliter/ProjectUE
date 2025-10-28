"""
Serwis LLM do generowania onboardingowych tasków
Wykorzystuje Together AI API
"""
import json
import hashlib
import logging
import requests
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def update_document_status(document_id: int, status: str, progress: int = 0, error_message: str = None):
    """
    Update the AI generation status of a document.
    
    Args:
        document_id: ID of the DocumentSource
        status: New status ('pending', 'processing', 'completed', 'failed', 'skipped')
        progress: Progress percentage (0-100)
        error_message: Error message if status is 'failed'
    """
    try:
        from webapp.models import DocumentSource
        
        document = DocumentSource.objects.get(id=document_id)
        document.ai_generation_status = status
        document.ai_processing_progress = progress
        
        if status == 'processing' and not document.ai_processing_started_at:
            document.ai_processing_started_at = timezone.now()
        elif status in ['completed', 'failed', 'skipped']:
            document.ai_processing_completed_at = timezone.now()
        
        if error_message:
            document.ai_processing_error = error_message
        
        document.save()
        logger.info(f"Updated document {document_id} status to {status} with progress {progress}%")
        
    except DocumentSource.DoesNotExist:
        logger.error(f"Document {document_id} not found")
    except Exception as e:
        logger.error(f"Error updating document {document_id} status: {e}")

def fix_json_syntax(json_str: str) -> str:
    """
    Fix common JSON syntax issues in LLM output.
    Enhanced to handle more edge cases.
    """
    import re
    
    # First, try to fix missing commas between array elements
    # Look for patterns like "}" followed by "{" without a comma
    json_str = re.sub(r'}\s*{', '}, {', json_str)
    
    # Fix missing commas between objects in arrays: }] { -> }], {
    json_str = re.sub(r'}\s*\]\s*{', '}], {', json_str)
    
    # Fix missing commas after closing array: ] " -> ], "
    json_str = re.sub(r'\]\s*"', '], "', json_str)
    
    # Fix missing commas between array elements more carefully
    # Only add comma if there's a } followed by { without comma
    json_str = re.sub(r'}\s*{', '}, {', json_str)
    
    # Fix missing values - look for patterns like "key": } or "key": ,
    json_str = re.sub(r':\s*}', ': null}', json_str)
    json_str = re.sub(r':\s*,', ': null,', json_str)
    
    # Fix boolean values that are quoted as strings
    json_str = re.sub(r':\s*"true"\s*([,}])', r': true\1', json_str)
    json_str = re.sub(r':\s*"false"\s*([,}])', r': false\1', json_str)
    json_str = re.sub(r':\s*"null"\s*([,}])', r': null\1', json_str)
    
    # Fix missing quotes around string values
    # Look for patterns like "key": value (where value is not quoted and not a number/boolean)
    json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2', json_str)
    
    # Fix array syntax issues - convert ["key": "value"] to [{"key": "value"}]
    
    # Fix steps array
    steps_pattern = r'"steps":\s*\[([^\]]+)\]'
    steps_match = re.search(steps_pattern, json_str)
    if steps_match:
        steps_content = steps_match.group(1)
        # Split by }, and wrap each item in {}
        steps_items = []
        for item in steps_content.split('},'):
            if item.strip():
                if not item.strip().startswith('{'):
                    item = '{' + item.strip()
                if not item.strip().endswith('}'):
                    item = item.strip() + '}'
                steps_items.append(item)
        steps_fixed = '[' + ', '.join(steps_items) + ']'
        json_str = re.sub(steps_pattern, f'"steps": {steps_fixed}', json_str)
    
    # Fix tasks array
    tasks_pattern = r'"tasks":\s*\[([^\]]+)\]'
    tasks_match = re.search(tasks_pattern, json_str)
    if tasks_match:
        tasks_content = tasks_match.group(1)
        # Split by }, and wrap each item in {}
        tasks_items = []
        for item in tasks_content.split('},'):
            if item.strip():
                if not item.strip().startswith('{'):
                    item = '{' + item.strip()
                if not item.strip().endswith('}'):
                    item = item.strip() + '}'
                tasks_items.append(item)
        tasks_fixed = '[' + ', '.join(tasks_items) + ']'
        json_str = re.sub(tasks_pattern, f'"tasks": {tasks_fixed}', json_str)
    
    # Fix missing commas in object properties (more specific patterns)
    # Look for patterns like "value" followed by "key" without a comma
    json_str = re.sub(r'"\s*"([^"]+)":', r'", "\1":', json_str)
    
    # Fix missing commas between object properties (be more careful)
    # Only add comma if there's a value followed by a key without comma
    json_str = re.sub(r'([^,}])\s*"([^"]+)":', r'\1, "\2":', json_str)
    
    # Clean up any double commas that might have been created
    json_str = re.sub(r',\s*,', ',', json_str)
    
    # Clean up any commas at the beginning of objects
    json_str = re.sub(r'{\s*,', '{', json_str)
    
    # Fix incomplete JSON - if it ends abruptly, try to close it properly
    if json_str.count('{') > json_str.count('}'):
        # Add missing closing braces
        missing_braces = json_str.count('{') - json_str.count('}')
        json_str += '}' * missing_braces
    
    return json_str

def extract_steps_and_tasks_separately(json_str: str) -> Dict[str, Any]:
    """
    Extract steps and tasks separately when the main JSON parsing fails.
    This is a more robust approach that handles malformed JSON better.
    """
    import re
    
    result = {"steps": [], "tasks": []}
    
    # Extract steps using regex
    steps_pattern = r'"steps"\s*:\s*\[(.*?)\]'
    steps_match = re.search(steps_pattern, json_str, re.DOTALL)
    if steps_match:
        steps_content = steps_match.group(1)
        # Try to parse individual step objects
        step_objects = []
        # Split by }, { pattern
        step_parts = re.split(r'}\s*,\s*{', steps_content)
        for i, part in enumerate(step_parts):
            if part.strip():
                # Clean up the part
                part = part.strip()
                if not part.startswith('{'):
                    part = '{' + part
                if not part.endswith('}'):
                    part = part + '}'
                
                try:
                    step_obj = json.loads(part)
                    step_objects.append(step_obj)
                except json.JSONDecodeError:
                    # Try to create a basic step object from the content
                    step_obj = {
                        "id": f"S{i+1}",
                        "title": f"Step {i+1}",
                        "order": i+1,
                        "description": "Generated step"
                    }
                    step_objects.append(step_obj)
        
        result["steps"] = step_objects
        logger.info(f"Extracted {len(step_objects)} steps separately")
    
    # Extract tasks using regex
    tasks_pattern = r'"tasks"\s*:\s*\[(.*?)\]'
    tasks_match = re.search(tasks_pattern, json_str, re.DOTALL)
    if tasks_match:
        tasks_content = tasks_match.group(1)
        # Try to parse individual task objects
        task_objects = []
        # Split by }, { pattern
        task_parts = re.split(r'}\s*,\s*{', tasks_content)
        for i, part in enumerate(task_parts):
            if part.strip():
                # Clean up the part
                part = part.strip()
                if not part.startswith('{'):
                    part = '{' + part
                if not part.endswith('}'):
                    part = part + '}'
                
                try:
                    task_obj = json.loads(part)
                    task_objects.append(task_obj)
                except json.JSONDecodeError:
                    # Try to create a basic task object from the content
                    task_obj = {
                        "step_id": f"S{((i // 2) + 1)}",  # Distribute across steps
                        "title": f"Task {i+1}",
                        "is_required": True,
                        "description": "Generated task",
                        "acceptance_criteria": ["Complete the task"],
                        "estimated_time_hours": 2.0,
                        "depends_on": []
                    }
                    task_objects.append(task_obj)
        
        result["tasks"] = task_objects
        logger.info(f"Extracted {len(task_objects)} tasks separately")
    
    return result


def aggressive_json_repair(json_str: str) -> str:
    """
    More aggressive JSON repair for severely malformed JSON.
    Uses proper bracket counting instead of simple regex to handle nested structures.
    """
    import re
    
    def extract_array_content(text: str, array_name: str) -> str:
        """Extract array content with proper bracket counting"""
        pattern = f'"{array_name}"\\s*:\\s*\\['
        match = re.search(pattern, text)
        if not match:
            return ""
        
        start = match.end()
        bracket_count = 1
        i = start
        
        while i < len(text) and bracket_count > 0:
            if text[i] == '[':
                bracket_count += 1
            elif text[i] == ']':
                bracket_count -= 1
            i += 1
        
        if bracket_count == 0:
            # Return content without the closing bracket
            return text[start:i-1]
        return ""
    
    # Extract arrays with proper bracket counting
    steps_content = extract_array_content(json_str, 'steps')
    tasks_content = extract_array_content(json_str, 'tasks')
    
    logger.info(f"Extracted steps_content: {len(steps_content)} chars")
    logger.info(f"Extracted tasks_content: {len(tasks_content)} chars")
    if tasks_content:
        logger.info(f"Tasks content preview: {tasks_content[:200]}...")
        logger.info(f"Tasks content starts with: '{tasks_content[:50]}'")
        logger.info(f"Tasks content ends with: '{tasks_content[-50:]}'")
    
    if steps_content or tasks_content:
        # Create minimal valid structure
        repaired = {
            "steps": [],
            "tasks": []
        }
        
        # Try to parse steps array directly
        if steps_content:
            try:
                steps_array = json.loads(f'[{steps_content}]')
                repaired["steps"] = steps_array
            except:
                # Fallback: Try to parse individual objects
                logger.warning("Failed to parse steps array, trying individual objects")
                repaired["steps"] = []
        
        # Try to parse tasks array directly
        if tasks_content:
            try:
                # The extracted content doesn't include the outer brackets
                # We need to wrap it in brackets to make it a valid array
                tasks_to_parse = f'[{tasks_content}]'
                logger.debug(f"Attempting to parse tasks array: {tasks_to_parse[:200]}...")
                
                # Try to parse without fixes first
                tasks_array = json.loads(tasks_to_parse)
                repaired["tasks"] = tasks_array
                logger.info(f"Successfully parsed {len(tasks_array)} tasks directly from array")
            except Exception as e:
                # Fallback: Try to parse individual objects
                logger.warning(f"Failed to parse tasks array: {e}, trying individual objects")
                logger.info("About to start individual task parsing...")
                
                # Try to split by individual task objects and parse them one by one
                try:
                    logger.info("Starting individual task parsing...")
                    logger.info(f"tasks_content available: {tasks_content is not None}, length: {len(tasks_content) if tasks_content else 0}")
                    task_objects = []
                    # Remove leading/trailing brackets if present
                    clean_content = tasks_content.strip()
                    logger.debug(f"Tasks content before cleaning: '{tasks_content[:50]}...'")
                    if clean_content.startswith('['):
                        clean_content = clean_content[1:]
                    if clean_content.endswith(']'):
                        clean_content = clean_content[:-1]
                    
                    logger.debug(f"Clean content for parsing: {clean_content[:200]}...")
                    
                    # Use a more robust approach to split task objects
                    import re
                    
                    # First, try to find all complete JSON objects using brace counting
                    parts = []
                    current_part = ""
                    brace_count = 0
                    in_string = False
                    escape_next = False
                    
                    for i, char in enumerate(clean_content):
                        if escape_next:
                            current_part += char
                            escape_next = False
                            continue
                            
                        if char == '\\':
                            current_part += char
                            escape_next = True
                            continue
                            
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            
                        current_part += char
                        
                        if not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                
                                # If we hit a closing brace and count is 0, we have a complete object
                                if brace_count == 0 and current_part.strip():
                                    parts.append(current_part.strip())
                                    current_part = ""
                    
                    # Add any remaining content
                    if current_part.strip():
                        logger.warning(f"Remaining content after brace counting: {current_part[:100]}...")
                        parts.append(current_part.strip())
                    
                    logger.info(f"Split into {len(parts)} task parts")
                    logger.debug(f"Parts: {[p[:50] + '...' if len(p) > 50 else p for p in parts]}")
                    
                    # Parse each part as a separate JSON object
                    for i, part in enumerate(parts):
                        if part.strip():
                            # Clean up the part
                            part = part.strip()
                            if not part.startswith('{'):
                                part = '{' + part
                            if not part.endswith('}'):
                                part = part + '}'
                            
                            # Fix common JSON issues in individual tasks
                            part = part.replace('"is_required": "true"', '"is_required": true')
                            part = part.replace('"is_required": "false"', '"is_required": false')
                            
                            # Fix missing commas between array elements
                            part = re.sub(r'}\s*{', '}, {', part)
                            
                            try:
                                task_obj = json.loads(part)
                                task_objects.append(task_obj)
                                logger.debug(f"Successfully parsed task {i+1}: {task_obj.get('title', 'Unknown')}")
                            except json.JSONDecodeError as parse_error:
                                logger.warning(f"Failed to parse individual task {i+1}: {parse_error}")
                                logger.debug(f"Problematic task content: {part[:200]}...")
                                
                                # Try to fix the JSON by adding missing commas
                                try:
                                    # Add missing comma before the closing brace
                                    if not part.rstrip().endswith(','):
                                        part = part.rstrip() + ','
                                    # Remove trailing comma before closing brace
                                    part = re.sub(r',\s*}', '}', part)
                                    
                                    task_obj = json.loads(part)
                                    task_objects.append(task_obj)
                                    logger.debug(f"Successfully parsed task {i+1} after fix: {task_obj.get('title', 'Unknown')}")
                                except json.JSONDecodeError as fix_error:
                                    logger.warning(f"Failed to parse individual task {i+1} even after fix: {fix_error}")
                                    continue
                    
                    repaired["tasks"] = task_objects
                    logger.info(f"Successfully parsed {len(task_objects)} individual tasks")
                    logger.debug(f"Individual tasks: {[t.get('title', 'Unknown') for t in task_objects]}")
                    
                except Exception as individual_error:
                    logger.warning(f"Failed to parse individual tasks: {individual_error}")
                    import traceback
                    logger.warning(f"Individual parsing error traceback: {traceback.format_exc()}")
                    repaired["tasks"] = []
                    logger.warning("Setting tasks to empty array")
        
        return json.dumps(repaired)
    
    # If we can't extract anything, return a minimal valid structure
    return json.dumps({
        "steps": [{"id": "S1", "title": "Initial Step", "order": 1, "description": "Generated step"}],
        "tasks": [{"step_id": "S1", "title": "Initial Task", "is_required": True, "description": "Generated task", "acceptance_criteria": ["Complete the task"], "estimated_time_hours": 1.0, "depends_on": []}]
    })

def process_documents_with_status(document_ids: List[int], role_name: str, project_stack: str) -> Dict[str, Any]:
    """
    Process multiple documents with status tracking.
    
    Args:
        document_ids: List of DocumentSource IDs to process
        role_name: Role name for onboarding generation
        project_stack: Project technology stack
    
    Returns:
        Dict with processing results
    """
    results = {
        'success': True,
        'processed_documents': [],
        'failed_documents': [],
        'total_documents': len(document_ids)
    }
    
    try:
        from webapp.models import DocumentSource
        
        # Get all documents
        documents = DocumentSource.objects.filter(id__in=document_ids)
        
        if not documents.exists():
            return {
                'success': False,
                'error': 'No documents found',
                'processed_documents': [],
                'failed_documents': [],
                'total_documents': 0
            }
        
        # Extract content from all documents
        documentation_chunks = []
        for doc in documents:
            try:
                # Update status to processing
                update_document_status(doc.id, 'processing', 10)
                
                # Extract text content
                content = extract_text_from_document(doc.content, doc.doc_type)
                if content:
                    chunks = chunk_text(content)
                    documentation_chunks.extend(chunks)
                
                # Update progress
                update_document_status(doc.id, 'processing', 50)
                
            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {e}")
                update_document_status(doc.id, 'failed', 0, str(e))
                results['failed_documents'].append({
                    'document_id': doc.id,
                    'title': doc.title,
                    'error': str(e)
                })
                continue
        
        if not documentation_chunks:
            # Mark all documents as failed
            for doc in documents:
                update_document_status(doc.id, 'failed', 0, 'No content extracted')
            return {
                'success': False,
                'error': 'No content could be extracted from documents',
                'processed_documents': [],
                'failed_documents': [{'document_id': doc.id, 'title': doc.title, 'error': 'No content extracted'} for doc in documents],
                'total_documents': len(document_ids)
            }
        
        # Generate onboarding draft
        update_document_status(documents[0].id, 'processing', 75)  # Update first document as representative
        
        draft_result = generate_onboarding_draft(
            role_name=role_name,
            project_stack=project_stack,
            documentation_chunks=documentation_chunks
        )
        
        if draft_result['success']:
            # Mark all documents as completed
            for doc in documents:
                update_document_status(doc.id, 'completed', 100)
                results['processed_documents'].append({
                    'document_id': doc.id,
                    'title': doc.title,
                    'status': 'completed'
                })
            
            results['draft_data'] = draft_result['data']
            results['metadata'] = draft_result['metadata']
        else:
            # Mark all documents as failed
            for doc in documents:
                update_document_status(doc.id, 'failed', 0, draft_result.get('error', 'Generation failed'))
                results['failed_documents'].append({
                    'document_id': doc.id,
                    'title': doc.title,
                    'error': draft_result.get('error', 'Generation failed')
                })
            results['success'] = False
            results['error'] = draft_result.get('error', 'Generation failed')
        
        return results
        
    except Exception as e:
        logger.error(f"Error in process_documents_with_status: {e}")
        # Mark all documents as failed
        for doc_id in document_ids:
            update_document_status(doc_id, 'failed', 0, str(e))
        return {
            'success': False,
            'error': str(e),
            'processed_documents': [],
            'failed_documents': [{'document_id': doc_id, 'error': str(e)} for doc_id in document_ids],
            'total_documents': len(document_ids)
        }



def extract_text_from_document(doc_content: str, doc_type: str) -> str:
    """
    Ekstrakcja tekstu z różnych formatów dokumentów.
    """
    if doc_type == 'md':
        import markdown
        from bs4 import BeautifulSoup
        html = markdown.markdown(doc_content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    elif doc_type == 'html':
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(doc_content, 'html.parser')
        return soup.get_text()
    
    elif doc_type == 'pdf':
        # PDF należy wcześniej przetworzić
        return doc_content
    
    else:  # txt
        return doc_content


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 30) -> List[str]:
    """
    Dzieli tekst na mniejsze fragmenty z overlapem.
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    return chunks


def build_system_prompt() -> str:
    """
    System prompt - stały dla wszystkich requestów.
    """
    return """You are an expert onboarding architect. Generate a comprehensive, detailed onboarding plan as JSON. Output ONLY valid JSON, no other text.

REQUIREMENTS:
- Create 8-12 detailed steps (not just 3-4)
- Each step should cover a specific domain/area
- Include 2-4 tasks per step
- Make steps comprehensive and thorough
- Cover: Environment Setup, Development Tools, Project Architecture, Database, Testing, CI/CD, Documentation, etc.

Format:
{
  "steps": [
    {"id": "S1", "title": "Environment Setup", "order": 1, "description": "Set up development environment and tools"}
  ],
  "tasks": [
    {"step_id": "S1", "title": "Install tools", "is_required": true, "description": "Install Docker and IDE", "acceptance_criteria": ["Tools installed"], "estimated_time_hours": 2.0, "depends_on": []}
  ]
}

Create a comprehensive plan with 8-12 steps covering all aspects of the role."""


def build_user_prompt(role_name: str, project_stack: str, documentation: str) -> str:
    """
    User prompt - specyficzny dla danego requestu.
    """
    # Skracamy dokumentację jeśli jest za długa
    max_doc_length = 2000  # Increased to allow more context
    if len(documentation) > max_doc_length:
        documentation = documentation[:max_doc_length] + "..."
    
    doc_section = f"\n\nDocumentation:\n{documentation[:1000]}" if documentation else ""
    
    return f"""Create a comprehensive onboarding plan for: {role_name}
Technology stack: {project_stack}{doc_section}

REQUIREMENTS:
- Generate 8-12 detailed steps (not just 3-4)
- Each step should be specific and actionable
- Include tasks for: Environment Setup, Development Tools, Project Architecture, Database Setup, Testing, CI/CD, Documentation, Code Review, etc.
- Make it thorough and comprehensive
- Base steps on the provided documentation when available
- Each task should have clear acceptance criteria and time estimates

Generate detailed JSON with comprehensive steps and tasks for onboarding this role."""


def calculate_prompt_hash(system_prompt: str, user_prompt: str) -> str:
    """
    Oblicza hash promptu dla audytu i cache.
    """
    combined = system_prompt + user_prompt
    return hashlib.sha256(combined.encode()).hexdigest()


def parse_llm_output(raw_output: str, role_name: str = "Developer") -> Dict[str, Any]:
    """
    Parsuje output z LLM i waliduje strukturę JSON.
    """
    try:
        # Clean up the output first
        raw_output = raw_output.strip()
        
        logger.info(f"Parsing LLM output, length: {len(raw_output)} chars")
        
        # Extract JSON from output - find first { to last }
        # This handles both clean JSON and JSON with extra text
        json_start = raw_output.find('{')
        json_end = raw_output.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            logger.warning("No JSON braces found, trying alternative extraction")
            # Try to fix common JSON issues
            if '"steps":' in raw_output and '"tasks":' in raw_output:
                # Add missing opening brace
                json_str = '{' + raw_output[raw_output.find('"steps"'):]
                # Find the last } and add it if missing
                if json_str.rfind('}') == -1:
                    json_str = json_str[:json_str.rfind(']') + 1] + '}'
            else:
                logger.error(f"No JSON structure found in LLM output: {raw_output[:500]}...")
                raise ValueError("No JSON found in LLM output")
        else:
            json_str = raw_output[json_start:json_end]
        
        logger.debug(f"Extracted JSON string: {json_str[:300]}...")
        
        # Try to parse JSON first without any fixes
        try:
            data = json.loads(json_str)
            logger.info(f"JSON parsed successfully without fixes: {len(data.get('steps', []))} steps, {len(data.get('tasks', []))} tasks")
            
            # Fix boolean values in tasks
            if 'tasks' in data:
                for task in data['tasks']:
                    if 'is_required' in task and isinstance(task['is_required'], str):
                        task['is_required'] = task['is_required'].lower() == 'true'
        except json.JSONDecodeError as e:
            logger.info("JSON parsing failed, attempting repair strategies")
            logger.debug(f"Problematic JSON: {json_str[:300]}...")
            
            # Try more aggressive repair strategies first
            try:
                # Use the original JSON string for repair, not the broken one
                logger.info("Attempting aggressive JSON repair...")
                logger.debug(f"JSON to repair: {raw_output[json_start:json_end][:300]}...")
                repaired_json = aggressive_json_repair(raw_output[json_start:json_end])
                logger.info(f"Repaired JSON length: {len(repaired_json)} chars")
                logger.debug(f"Repaired JSON: {repaired_json[:300]}...")
                data = json.loads(repaired_json)
                logger.info(f"JSON repaired successfully: {len(data.get('steps', []))} steps, {len(data.get('tasks', []))} tasks")
            except Exception as repair_error:
                logger.error(f"JSON repair failed: {repair_error}")
                import traceback
                logger.error(f"Repair error traceback: {traceback.format_exc()}")
                
                # Try to fix common JSON issues as fallback
                try:
                    json_str = fix_json_syntax(raw_output[json_start:json_end])
                    data = json.loads(json_str)
                    logger.info("JSON parsed successfully after fixes")
                except json.JSONDecodeError as e2:
                    logger.error(f"JSON fixes also failed: {e2}")
                    
                    # Try one more approach - extract and parse steps and tasks separately
                    try:
                        logger.info("Attempting separate extraction of steps and tasks")
                        data = extract_steps_and_tasks_separately(raw_output[json_start:json_end])
                        logger.info("Separate extraction successful")
                    except Exception as separate_error:
                        logger.error(f"Separate extraction also failed: {separate_error}")
                        raise ValueError(f"Invalid JSON from LLM: {e}")
        
        # Walidacja struktury
        logger.info(f"Validating data structure: {list(data.keys())}")
        if 'steps' not in data or 'tasks' not in data:
            logger.error(f"Missing steps or tasks in data: {data.keys()}")
            raise ValueError("Nieprawidłowa struktura JSON - brakuje 'steps' lub 'tasks'")
        
        logger.info(f"Data validation passed: {len(data.get('steps', []))} steps, {len(data.get('tasks', []))} tasks")
        
        # Podstawowa walidacja
        for i, step in enumerate(data['steps']):
            if 'id' not in step or 'title' not in step:
                logger.error(f"Invalid step {i}: {step}")
                raise ValueError(f"Nieprawidłowa struktura step: {step}")
        
        for i, task in enumerate(data['tasks']):
            required_fields = ['step_id', 'title', 'description']
            if not all(field in task for field in required_fields):
                logger.error(f"Invalid task {i}: {task}")
                raise ValueError(f"Nieprawidłowa struktura task: {task}")
        
        logger.info(f"Validation successful: {len(data['steps'])} steps, {len(data['tasks'])} tasks")
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"Błąd parsowania JSON: {e}\nOutput: {raw_output[:500]}")
        # Fallback: create basic structure
        logger.info("Using fallback structure")
        return create_fallback_structure(role_name)
    except Exception as e:
        logger.error(f"Błąd walidacji outputu LLM: {e}", exc_info=True)
        # Fallback: create basic structure
        logger.info("Using fallback structure due to error")
        return create_fallback_structure(role_name)


def create_role_based_onboarding(role_name: str, project_stack: str, documentation_chunks: List[str]) -> Dict[str, Any]:
    """
    Creates a structured onboarding plan based on role and project stack.
    This is much faster than LLM generation and more reliable.
    Uses uploaded documentation if available.
    """
    # Extract technologies from project stack
    technologies = [tech.strip() for tech in project_stack.split(',') if tech.strip()]
    
    # Check if we have documentation to extract info from
    has_documentation = bool(documentation_chunks and any(chunk.strip() for chunk in documentation_chunks))
    
    if has_documentation:
        logger.info(f"Using documentation to enhance onboarding plan ({len(documentation_chunks)} chunks)")
        # Combine all documentation
        full_doc = ' '.join(documentation_chunks)
        
        # Try to extract structured information from documentation
        # Look for common patterns like numbered lists, sections, etc.
        doc_lower = full_doc.lower()
        
        # Check for specific keywords that indicate detailed steps
        has_setup_instructions = any(word in doc_lower for word in ['install', 'setup', 'configure', 'docker'])
        has_testing_info = any(word in doc_lower for word in ['test', 'pytest', 'unittest'])
        has_architecture_info = any(word in doc_lower for word in ['architecture', 'structure', 'modules', 'components'])
    else:
        logger.info("No documentation provided, using generic template")
        has_setup_instructions = False
        has_testing_info = False
        has_architecture_info = False
    
    # Create comprehensive role-specific steps
    steps = [
        {
            'id': 'S1',
            'title': 'Environment Setup',
            'order': 1,
            'description': f'Set up development environment and tools for {role_name} role'
        },
        {
            'id': 'S2',
            'title': 'Development Tools Configuration',
            'order': 2,
            'description': 'Configure IDE, linters, formatters, and development tools'
        },
        {
            'id': 'S3',
            'title': 'Project Architecture Overview',
            'order': 3,
            'description': 'Learn about project structure, modules, and architecture'
        },
        {
            'id': 'S4',
            'title': 'Database and Data Layer',
            'order': 4,
            'description': 'Set up and understand database configuration and models'
        },
        {
            'id': 'S5',
            'title': 'Authentication and Permissions',
            'order': 5,
            'description': 'Understand user roles, permissions, and authentication system'
        },
        {
            'id': 'S6',
            'title': 'API and Integration Setup',
            'order': 6,
            'description': 'Learn about APIs, external integrations, and service connections'
        },
        {
            'id': 'S7',
            'title': 'Testing Framework',
            'order': 7,
            'description': 'Set up testing environment and learn testing practices'
        },
        {
            'id': 'S8',
            'title': 'CI/CD and Deployment',
            'order': 8,
            'description': 'Understand build, test, and deployment processes'
        },
        {
            'id': 'S9',
            'title': 'Code Review and Standards',
            'order': 9,
            'description': 'Learn coding standards, review process, and best practices'
        },
        {
            'id': 'S10',
            'title': 'Documentation and Knowledge Transfer',
            'order': 10,
            'description': 'Review documentation and complete knowledge transfer'
        }
    ]
    
    # Create comprehensive role-specific tasks for all 10 steps
    tasks = []
    
    # S1: Environment Setup tasks
    setup_desc = 'Install required development tools and dependencies'
    if has_setup_instructions and has_documentation:
        setup_desc += '. Refer to uploaded onboarding documentation for specific installation steps'
    
    tasks.extend([
        {
            'step_id': 'S1',
            'title': 'Install Development Tools',
            'is_required': True,
            'description': setup_desc,
            'acceptance_criteria': ['All tools installed and working', 'Can run project locally'],
            'estimated_time_hours': 2.0,
            'depends_on': []
        },
        {
            'step_id': 'S1',
            'title': 'Clone and Setup Repository',
            'is_required': True,
            'description': 'Clone the project repository and set up local development environment',
            'acceptance_criteria': ['Repository cloned', 'Local environment configured'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        }
    ])
    
    # S2: Development Tools Configuration tasks
    tasks.extend([
        {
            'step_id': 'S2',
            'title': 'Configure IDE and Extensions',
            'is_required': True,
            'description': 'Set up IDE with project-specific extensions and configurations',
            'acceptance_criteria': ['IDE configured with project settings', 'Required extensions installed'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        },
        {
            'step_id': 'S2',
            'title': 'Setup Linters and Formatters',
            'is_required': True,
            'description': 'Configure code quality tools (Black, Flake8, isort, etc.)',
            'acceptance_criteria': ['Linter and formatter working', 'Code style enforced'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        }
    ])
    
    # S3: Project Architecture Overview tasks
    doc_desc = 'Review project documentation, README, and uploaded onboarding materials' if has_documentation else 'Review project documentation and README'
    arch_desc = 'Familiarize yourself with the project structure and architecture'
    if has_architecture_info and has_documentation:
        arch_desc += '. Refer to uploaded documentation for architecture details'
    
    tasks.extend([
        {
            'step_id': 'S3',
            'title': 'Read Project Documentation',
            'is_required': True,
            'description': doc_desc,
            'acceptance_criteria': ['Documentation reviewed', 'Understand project goals and architecture'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        },
        {
            'step_id': 'S3',
            'title': 'Explore Codebase Structure',
            'is_required': True,
            'description': arch_desc,
            'acceptance_criteria': ['Codebase structure understood', 'Can navigate main modules'],
            'estimated_time_hours': 2.0,
            'depends_on': []
        }
    ])
    
    # S4: Database and Data Layer tasks
    tasks.extend([
        {
            'step_id': 'S4',
            'title': 'Setup Database',
            'is_required': True,
            'description': 'Configure and set up the database environment',
            'acceptance_criteria': ['Database running', 'Connection established'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        },
        {
            'step_id': 'S4',
            'title': 'Run Migrations',
            'is_required': True,
            'description': 'Apply database migrations and understand data models',
            'acceptance_criteria': ['Migrations applied', 'Data models understood'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        }
    ])
    
    # S5: Authentication and Permissions tasks
    tasks.extend([
        {
            'step_id': 'S5',
            'title': 'Understand User Roles',
            'is_required': True,
            'description': 'Learn about the RBAC system and user permission model',
            'acceptance_criteria': ['Role system understood', 'Can explain permissions'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        },
        {
            'step_id': 'S5',
            'title': 'Test Authentication Flow',
            'is_required': True,
            'description': 'Test login, logout, and permission-based access',
            'acceptance_criteria': ['Authentication working', 'Permissions tested'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        }
    ])
    
    # S6: API and Integration Setup tasks
    tasks.extend([
        {
            'step_id': 'S6',
            'title': 'Explore API Endpoints',
            'is_required': True,
            'description': 'Learn about available APIs and their usage',
            'acceptance_criteria': ['API endpoints documented', 'Can make API calls'],
            'estimated_time_hours': 2.0,
            'depends_on': []
        },
        {
            'step_id': 'S6',
            'title': 'Setup External Integrations',
            'is_required': False,
            'description': 'Configure external service integrations (Spotify, etc.)',
            'acceptance_criteria': ['Integrations configured', 'Test connections working'],
            'estimated_time_hours': 2.0,
            'depends_on': []
        }
    ])
    
    # S7: Testing Framework tasks
    test_desc = 'Write unit tests for your changes'
    if has_testing_info and has_documentation:
        test_desc += '. Follow testing guidelines from uploaded documentation'
    
    tasks.extend([
        {
            'step_id': 'S7',
            'title': 'Setup Testing Environment',
            'is_required': True,
            'description': 'Configure testing framework and run existing tests',
            'acceptance_criteria': ['Tests running', 'Test environment configured'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        },
        {
            'step_id': 'S7',
            'title': 'Write Your First Tests',
            'is_required': True,
            'description': test_desc,
            'acceptance_criteria': ['Tests written and passing', 'Code coverage maintained'],
            'estimated_time_hours': 2.0,
            'depends_on': []
        }
    ])
    
    # S8: CI/CD and Deployment tasks
    tasks.extend([
        {
            'step_id': 'S8',
            'title': 'Understand CI/CD Pipeline',
            'is_required': True,
            'description': 'Learn about the build, test, and deployment process',
            'acceptance_criteria': ['Pipeline understood', 'Can trigger builds'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        },
        {
            'step_id': 'S8',
            'title': 'Test Deployment Process',
            'is_required': True,
            'description': 'Practice deployment to staging environment',
            'acceptance_criteria': ['Deployment successful', 'Process documented'],
            'estimated_time_hours': 2.0,
            'depends_on': []
        }
    ])
    
    # S9: Code Review and Standards tasks
    tasks.extend([
        {
            'step_id': 'S9',
            'title': 'Learn Coding Standards',
            'is_required': True,
            'description': 'Study project coding standards and best practices',
            'acceptance_criteria': ['Standards understood', 'Can apply consistently'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        },
        {
            'step_id': 'S9',
            'title': 'Participate in Code Review',
            'is_required': True,
            'description': 'Review code from other team members and learn the process',
            'acceptance_criteria': ['Code review completed', 'Feedback provided'],
            'estimated_time_hours': 2.0,
            'depends_on': []
        }
    ])
    
    # S10: Documentation and Knowledge Transfer tasks
    tasks.extend([
        {
            'step_id': 'S10',
            'title': 'Complete Knowledge Transfer',
            'is_required': True,
            'description': 'Final review of all documentation and knowledge sharing',
            'acceptance_criteria': ['All docs reviewed', 'Knowledge gaps filled'],
            'estimated_time_hours': 2.0,
            'depends_on': []
        },
        {
            'step_id': 'S10',
            'title': 'Provide Onboarding Feedback',
            'is_required': True,
            'description': 'Share feedback on the onboarding process and suggest improvements',
            'acceptance_criteria': ['Feedback provided', 'Process documented'],
            'estimated_time_hours': 1.0,
            'depends_on': []
        }
    ])
    
    return {
        'steps': steps,
        'tasks': tasks
    }

def create_fallback_structure(role_name: str, project_stack: str = "", documentation_chunks: List[str] = None) -> dict:
    """
    Tworzy podstawową strukturę gdy LLM nie zwróci prawidłowego JSON.
    Uses role and stack info to create relevant structure.
    """
    logger.info(f"Creating fallback structure for role: {role_name}")
    
    # Use template-based generation which is actually quite good
    return create_role_based_onboarding(role_name, project_stack or "Software Development", documentation_chunks or [])


def generate_onboarding_draft(
    role_name: str,
    project_stack: str,
    documentation_chunks: List[str],
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Główna funkcja generująca draft onboardingu.
    
    Args:
        role_name: Nazwa roli (np. "Backend Developer")
        project_stack: Stack technologiczny projektu
        documentation_chunks: Lista fragmentów dokumentacji
        model_name: Opcjonalna nazwa modelu (domyślnie z settings)
    
    Returns:
        Dict z wygenerowanym planem onboardingu + metadata
    """
    try:
        # Build prompts
        system_prompt = build_system_prompt()
        documentation = ' '.join(documentation_chunks[:5])  # Limit to first 5 chunks
        user_prompt = build_user_prompt(role_name, project_stack, documentation)
        
        # Calculate prompt hash for audit
        prompt_hash = calculate_prompt_hash(system_prompt, user_prompt)
        
        logger.info(f"Generowanie onboardingu dla roli: {role_name} z LLM")
        
        # Multi-tier LLM generation strategy
        try:
            raw_output = None
            model_name_used = "unknown"
            generation_method = "unknown"
            
            # TIER 1: Try Together AI (best quality/price ratio)
            together_key = getattr(settings, 'TOGETHER_API_KEY', '')
            if together_key:
                try:
                    from webapp.llm_together_integration import generate_with_together
                    
                    # Use configurable model from settings
                    model_name_used = getattr(settings, 'TOGETHER_MODEL', 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo')
                    logger.info(f"Attempting Together AI with {model_name_used}")
                    
                    raw_output = generate_with_together(system_prompt, user_prompt, model_name_used)
                    generation_method = "together_ai"
                    logger.info("✅ Together AI succeeded!")
                    
                except Exception as together_error:
                    logger.warning(f"Together AI failed: {together_error}")
                    logger.info("Falling back to next tier...")
                    raw_output = None
            
            # TIER 2: Use template-based fallback (most reliable fallback)
            if raw_output is None:
                logger.info("Using template-based generation fallback...")
                generation_method = "template_fallback"
                
                # Use the comprehensive template-based generation
                result = create_role_based_onboarding(
                    role_name=role_name,
                    project_stack=project_stack,
                    documentation_chunks=documentation_chunks
                )
                
                # Convert to the expected format
                raw_output = json.dumps(result, indent=2)
                model_name_used = "template_based"
            
            logger.info(f"LLM wygenerował output ({len(raw_output)} znaków)")
            logger.debug(f"LLM raw output: {raw_output[:500]}...")  # Log first 500 chars
            
            # Parse LLM output
            parsed_data = parse_llm_output(raw_output, role_name)
            
            # Validate and fix
            parsed_data = validate_and_fix_draft(parsed_data)
            
            return {
                'success': True,
                'data': parsed_data,
                'metadata': {
                    'llm_model': model_name_used,
                    'generation_method': generation_method,
                    'prompt_hash': prompt_hash,
                    'role_name': role_name,
                    'project_stack': project_stack,
                    'generation_time': timezone.now().isoformat(),
                    'raw_output_length': len(raw_output)
                }
            }
            
        except Exception as llm_error:
            logger.warning(f"LLM generation failed: {llm_error}, falling back to template-based", exc_info=True)
            # Fallback to template-based if LLM fails
            parsed_data = create_fallback_structure(role_name, project_stack, documentation_chunks)
            
            return {
                'success': True,
                'data': parsed_data,
                'metadata': {
                    'llm_model': 'template-based-fallback',
                    'prompt_hash': prompt_hash,
                    'role_name': role_name,
                    'project_stack': project_stack,
                    'generation_time': timezone.now().isoformat(),
                    'fallback_reason': str(llm_error)
                }
            }
    
    except Exception as e:
        logger.error(f"Błąd generowania onboardingu: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'metadata': {
                'role_name': role_name,
                'project_stack': project_stack,
            }
        }


def validate_and_fix_draft(draft_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Waliduje i naprawia draft przed zapisem.
    Dodaje brakujące pola, sanityzuje dane.
    """
    # Dodajemy domyślne wartości
    for task in draft_data.get('tasks', []):
        if 'is_required' not in task:
            task['is_required'] = True
        if 'acceptance_criteria' not in task:
            task['acceptance_criteria'] = []
        if 'estimated_time_hours' not in task:
            task['estimated_time_hours'] = 2.0
        if 'depends_on' not in task:
            task['depends_on'] = []
        
        # Sanityzacja
        task['title'] = task['title'][:200]  # Limit długości
        task['description'] = task['description'][:1000]
    
    for step in draft_data.get('steps', []):
        if 'order' not in step:
            step['order'] = 1
        if 'description' not in step:
            step['description'] = ""
    
    return draft_data


