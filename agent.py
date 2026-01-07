from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from parser import parse_resume

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self, resume_data: dict) -> None:
        # Construct dynamic instructions based on resume data
        skills = resume_data.get("skills", "Not specified")
        experience = resume_data.get("experience", "Not specified")
        projects = resume_data.get("projects", "Not specified")

        instructions = f"""You are a professional interview agent conducting a structured interview.
        
        The candidate's resume highlights:
        - SKILLS: {skills}
        - EXPERIENCE: {experience}
        - PROJECTS: {projects}

        Your task is to ask exactly 5 interview questions. While following the structure, try to tailor the questions slightly to their background if relevant:
        
        1. Tell me about yourself.
        2. Based on your experience in {skills[:100]}, what are your greatest strengths?
        3. Describe a challenging situation you faced in one of your projects and how you handled it.
        4. Where do you see yourself in five years?
        5. Why should we hire you for this position given your background?
        
        Important guidelines:
        - Ask ONE question at a time and wait for the candidate's complete answer before moving to the next question.
        - Listen carefully to each response without interrupting.
        - After each answer, acknowledge their response briefly with phrases like "Thank you" or "I see" before asking the next question.
        - Keep your responses concise and professional.
        - Do not use emojis, asterisks, or special formatting.
        - After all 5 questions are answered, thank the candidate and conclude the interview by saying "That concludes our interview today. Thank you for your time."
        - Stay focused on the interview structure and do not deviate from these questions.
        - Be professional, friendly, and encouraging throughout."""

        super().__init__(instructions=instructions)


server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    # Parse the resume when a session starts
    resume_path = "resume.pdf"
    try:
        resume_data = parse_resume(resume_path)
    except Exception as e:
        print(f"Error parsing resume: {e}")
        resume_data = {}

    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(resume_data),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user, mention you have reviewed their resume, and start the interview with the first question."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
