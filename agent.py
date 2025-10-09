from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation, silero, openai  
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a professional interview agent conducting a structured interview.
            
            Your task is to ask exactly 5 interview questions in this specific order:
            
            1. Tell me about yourself.
            2. What are your greatest strengths?
            3. Describe a challenging situation you faced and how you handled it.
            4. Where do you see yourself in five years?
            5. Why should we hire you for this position?
            
            Important guidelines:
            - Ask ONE question at a time and wait for the candidate's complete answer before moving to the next question.
            - Listen carefully to each response without interrupting.
            - After each answer, acknowledge their response briefly with phrases like "Thank you" or "I see" before asking the next question.
            - Keep your responses concise and professional.
            - Do not use emojis, asterisks, or special formatting.
            - After all 5 questions are answered, thank the candidate and conclude the interview by saying "That concludes our interview today. Thank you for your time."
            - Stay focused on the interview structure and do not deviate from these questions.
            - Be professional, friendly, and encouraging throughout.""",
        )

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm=openai.LLM.with_ollama(
            model="gemma3:4b",  # Make sure this model exists in Ollama
            base_url="http://localhost:11434/v1",
            temperature=0.7,
        ),
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await session.generate_reply(
        instructions="Greet the candidate warmly, introduce yourself as their interviewer, and then ask the first question: Tell me about yourself."
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
