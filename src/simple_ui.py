import numpy as np
import PySimpleGUI as sg
import openai
from loguru import logger
# openai.verify_ssl_certs = False

from src import audio, llm
from src.constants import APPLICATION_WIDTH, OFF_IMAGE, ON_IMAGE

def get_text_area(text: str, size: tuple) -> sg.Text:
    """
    Create a text area widget with the given text and size.

    Parameters:
        text (str): The initial text to display in the text area.
        size (tuple): The size of the text area widget.

    Returns:
        sg.Text: The created text area widget.
    """
    return sg.Text(
        text,
        size=size,
        background_color=sg.theme_background_color(),
        text_color="white",
    )


class BtnInfo:
    def __init__(self, state=False):
        self.state = state


# All the stuff inside your window:
sg.theme("DarkAmber")  # Add a touch of color
record_status_button = sg.Button(
    image_data=OFF_IMAGE,
    k="-TOGGLE1-",
    border_width=0,
    button_color=(sg.theme_background_color(), sg.theme_background_color()),
    disabled_button_color=(sg.theme_background_color(), sg.theme_background_color()),
    metadata=BtnInfo(),
)
analyzed_text_label = get_text_area("", size=(APPLICATION_WIDTH, 2))
quick_chat_gpt_answer = get_text_area("", size=(APPLICATION_WIDTH, 5))
full_chat_gpt_answer = get_text_area("", size=(APPLICATION_WIDTH, 45))


layout = [
    [sg.Text("Press R to start recording", size=(int(APPLICATION_WIDTH * 0.8), 2)), record_status_button],
    [sg.Text("Press A to analyze the recording")],
    [analyzed_text_label],
    [sg.Text("Short answer:")],
    [quick_chat_gpt_answer],
    [sg.Text("Full answer:")],
    [full_chat_gpt_answer],  # This will take more space due to expand settings
    [sg.Button("Cancel", size=(10, 1), button_color=("white", "red"), expand_x=True)],  # Moved to the bottom and centered
]

# Adjusting the full_chat_gpt_answer to expand

WINDOW = sg.Window("Interview Assistant", layout, size=(600, 800), return_keyboard_events=True, use_default_focus=False)


def background_recording_loop() -> str:
    """
    Records audio until stopped and saves it to a file.

    Returns:
        str: The path to the saved audio file.
    """
    audio_data = None
    while record_status_button.metadata.state:
        audio_sample = audio.record_audio_pyaudio()
        if audio_data is None:
            audio_data = audio_sample
        else:
            audio_data = np.vstack((audio_data, audio_sample))
    # After saving the audio
    audio.save_audio_file_pyaudio(audio_data, "recorded_audio.wav")
    return "recorded_audio.wav"

while True:
    event, values = WINDOW.read()
    if event in ["Cancel", sg.WIN_CLOSED]:
        logger.debug("Closing...")
        break

    if event in ("r", "R"):  # Toggle recording
        if not record_status_button.metadata.state:  # Start recording
            logger.debug("Starting recording...")
            record_status_button.metadata.state = True
            record_status_button.update(image_data=ON_IMAGE)
            WINDOW.perform_long_operation(background_recording_loop, "-RECORDING COMPLETED-")
        else:  # Stop recording
            logger.debug("Stopping recording...")
            record_status_button.metadata.state = False
            record_status_button.update(image_data=OFF_IMAGE)

    elif event == "-RECORDING COMPLETED-":
        recorded_audio_path = values["-RECORDING COMPLETED-"]
        logger.debug("Transcribing recorded audio...")
        analyzed_text_label.update("Transcribing...")
        WINDOW.perform_long_operation(lambda: llm.transcribe_audio(recorded_audio_path), "-WHISPER COMPLETED-")

    elif event == "-WHISPER COMPLETED-":
        audio_transcript = values["-WHISPER COMPLETED-"]
        analyzed_text_label.update(audio_transcript)

        # Generate quick answer:
        quick_chat_gpt_answer.update("ChatGPT is generating a quick answer...")
        WINDOW.perform_long_operation(
            lambda: llm.generate_answer(audio_transcript, short_answer=True, temperature=0),
            "-CHAT_GPT SHORT ANSWER-",
        )

        # Generate full answer:
        full_chat_gpt_answer.update("ChatGPT is generating a detailed answer...")
        WINDOW.perform_long_operation(
            lambda: llm.generate_answer(audio_transcript, short_answer=False, temperature=0.7),
            "-CHAT_GPT LONG ANSWER-",
        )

    elif event == "-CHAT_GPT SHORT ANSWER-":
        quick_chat_gpt_answer.update(values["-CHAT_GPT SHORT ANSWER-"])
    elif event == "-CHAT_GPT LONG ANSWER-":
        full_chat_gpt_answer.update(values["-CHAT_GPT LONG ANSWER-"])
