import asyncio
from app.models import GameSpec, ConversationState
from app.ai.llm_client import analyze_message_with_llm

async def main():
    print("Testing Ollama extraction...")
    res = await analyze_message_with_llm(
        user_message="Make it a dark fantasy platformer with double jump",
        current_state=ConversationState.GREETING,
        current_spec=GameSpec(),
        history=[]
    )
    print("Intent:", res.intent)
    print("Spec:", res.extracted_spec)

if __name__ == "__main__":
    asyncio.run(main())
