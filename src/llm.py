import openai
import requests
from loguru import logger

from src.constants import INTERVIEW_POSTION, OPENAI_API_KEY, OUTPUT_FILE_NAME

openai.api_key = OPENAI_API_KEY
# openai.verify_ssl_certs = False
session = requests.Session()
session.verify = False
proxies = {

            "HTTP_PROXY": 'http://genproxy.corp.amdocs.com:8080',
            "http_proxy": 'http://genproxy.corp.amdocs.com:8080',
            "https_proxy": 'http://genproxy.corp.amdocs.com:8080',
            "HTTPS_PROXY": 'http://genproxy.corp.amdocs.com:8080',
            "no_proxy" : 'api.openai.com',
            "NO_PROXY" : 'api.openai.com',
            "no_http_proxy": 'api.openai.com',
            "NO_HTTP_PROXY": 'api.openai.com',
            "no_https_proxy": 'api.openai.com',
            "NO_HTTPS_PROXY": 'api.openai.com'
        }

SYSTEM_PROMPT = f"""You are interviewing for a {INTERVIEW_POSTION} position.
You will receive an audio transcription of the question. It may not be complete. 
You need to understand the question and generate an answer to it .\n
"""
SHORTER_INSTRACT = "Concisely respond, limiting your answer to 70 words."
LONGER_INSTRACT = (
    "Before answering, take a deep breath and think one step at a time. "
    "Believe the answer in no more than 400 words in simple plain english. preferably in Ordered List"
    "make shorter sentences with some uhm sounds and grammatical mistakes. "
    "I will read out these lines and it should not sound like I m plainly reading out"
)


def transcribe_audio(path_to_file: str = OUTPUT_FILE_NAME) -> str:
    """
    Transcribes an audio file into text.

    Args:
        path_to_file (str, optional): The path to the audio file to be transcribed.

    Returns:
        str: The transcribed text.

    Raises:
        Exception: If the audio file fails to transcribe.
    """
    with open(path_to_file, "rb") as audio_file:
        try:
            session = requests.Session()
            session.verify = False
            transcript = openai.Audio.translate("whisper-1", audio_file)
        except Exception as error:
            logger.error(f"Can't transcribe audio: {error}")
            raise error
    return transcript["text"]

def generate_answer(transcript: str, short_answer: bool = True, temperature: float = 0.7, callback=None) -> None:
    """
    Generates an answer based on the given transcript using the OpenAI GPT-3.5-turbo model.

    Args:
        transcript (str): The transcript to generate an answer from.
        short_answer (bool): Whether to generate a short answer or not. Defaults to True.
        temperature (float): The temperature parameter for controlling the randomness of the generated answer.
        callback (function): A callback function to handle streaming updates.

    Raises:
        Exception: If the LLM fails to generate an answer.
    """
    if short_answer:
        system_prompt = SYSTEM_PROMPT + SHORTER_INSTRACT
    else:
        system_prompt = SYSTEM_PROMPT + LONGER_INSTRACT

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
            stream=True  # Enable streaming
        )

        full_response = ""  # Store the full response here

        # Process the streamed response
        for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    # Append the new chunk to the full response
                    full_response += delta['content']

                    # Call the callback function to update the UI with the full response
                    if callback:
                        callback(full_response)

    except Exception as error:
        logger.error(f"Can't generate answer: {error}")
        raise error


