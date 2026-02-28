"""LLM Integration for structured extraction using Ollama."""

from __future__ import annotations

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.models import GameSpec, ConversationState
from app.ai.intent import Intent

# We use the AsyncOpenAI client pointing to local Ollama
_client = instructor.from_openai(
    AsyncOpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama", # API key is required by the SDK but ignored by Ollama
    ),
    mode=instructor.Mode.JSON,
)

OLLAMA_MODEL = "qwen2.5:7b-instruct"

class GameExtractionResult(BaseModel):
    """The structured result from analyzing exactly what the user said."""
    intent: Intent = Field(..., description="The user's primary intent.")
    extracted_spec: GameSpec = Field(..., description="The game specification parameters extracted from the conversation so far. If the user didn't mention a parameter, keep it as the default or current value.")


async def analyze_message_with_llm(
    user_message: str, 
    current_state: ConversationState, 
    current_spec: GameSpec,
    history: list[dict]
) -> GameExtractionResult:
    """Pass the conversation to Ollama to extract intent and parameters."""
    
    # Build conversation context
    messages = [
        {"role": "system", "content": f"""You are an expert game design assistant AI. Your job is to extract game parameters and classify intent.
Current Conversation State: {current_state.value}
Current Game Specification:
{current_spec.model_dump_json(indent=2)}

Analyze the user's latest message and return the updated GameSpec and their Intent.
Only update fields in the GameSpec if the user explicitly mentioned them. Otherwise, leave them as they are in the Current Game Specification.
"""}
    ]
    
    # Add recent history for context
    for msg in history[-4:]:
        messages.append(msg)
        
    messages.append({"role": "user", "content": user_message})

    # Call Ollama using Instructor for structured output
    response = await _client.chat.completions.create(
        model=OLLAMA_MODEL,
        response_model=GameExtractionResult,
        messages=messages,
        temperature=0.0,
    )
    
    return response

