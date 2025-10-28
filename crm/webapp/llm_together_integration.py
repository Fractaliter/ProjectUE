"""
Together AI Integration for LLM Service
Provides access to open-source models (Llama, Mistral, etc.) via Together AI API

Advantages:
- 10x cheaper than OpenAI ($0.0002 vs $0.002 per generation)
- $25 free credits on signup
- Fast response times (2-3 seconds)
- High quality models (Llama 3.1, Mistral, etc.)
- Simple API compatible with OpenAI format
"""

import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_with_together(
    system_prompt: str,
    user_prompt: str,
    model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
) -> str:
    """
    Generate text using Together AI API
    
    Args:
        system_prompt: System instruction for the model
        user_prompt: User's actual prompt
        model: Together AI model to use (default: Llama 3.1 8B Turbo)
    
    Returns:
        Generated text
        
    Raises:
        Exception: If API call fails
    """
    api_key = getattr(settings, 'TOGETHER_API_KEY', '')
    
    if not api_key:
        raise ValueError("TOGETHER_API_KEY not configured")
    
    url = "https://api.together.xyz/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Format zgodny z OpenAI API
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 2048,  # Więcej dla pełnego JSON
        "temperature": 0.7,
        "top_p": 0.9,
        "stop": ["<|eot_id|>", "<|end_of_text|>"],  # Llama stop tokens
    }
    
    try:
        logger.info(f"Calling Together AI with model: {model}")
        logger.info(f"System prompt: {len(system_prompt)} chars, User prompt: {len(user_prompt)} chars")
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        # Wyciągnij wygenerowany tekst
        generated_text = result['choices'][0]['message']['content']
        
        # Log usage
        if 'usage' in result:
            usage = result['usage']
            logger.info(
                f"Together AI tokens: {usage.get('prompt_tokens', 0)} input, "
                f"{usage.get('completion_tokens', 0)} output, "
                f"{usage.get('total_tokens', 0)} total"
            )
        
        logger.info(f"Together AI generated {len(generated_text)} characters")
        
        return generated_text
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Together AI request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Together AI error: {e}")
        raise


# Rekomendowane modele dla różnych use cases
RECOMMENDED_MODELS = {
    # Najlepszy balans ceny i jakości
    'default': 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
    
    # Najlepsza jakość (droższy)
    'best_quality': 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo',
    
    # Najtańszy (nadal dobry)
    'cheapest': 'mistralai/Mistral-7B-Instruct-v0.3',
    
    # Dobry do kodu i JSON
    'structured': 'Qwen/Qwen2.5-7B-Instruct-Turbo',
}


def get_recommended_model(use_case: str = 'default') -> str:
    """Get recommended model for specific use case"""
    return RECOMMENDED_MODELS.get(use_case, RECOMMENDED_MODELS['default'])

