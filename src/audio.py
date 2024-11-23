import pyaudio
import wave
import numpy as np

# Function to record audio using pyaudio
def record_audio_pyaudio(record_sec=5, samplerate=44100, channels=1):
    try:
        p = pyaudio.PyAudio()

        # Open the stream with the desired settings
        stream = p.open(format=pyaudio.paInt16,  # 16-bit audio
                        channels=channels,
                        rate=samplerate,
                        input=True,
                        frames_per_buffer=1024)

        print(f"Recording for {record_sec} second(s)...")
        frames = []

        # Record audio
        for _ in range(0, int(samplerate / 1024 * record_sec)):
            data = stream.read(1024)
            frames.append(data)

        # Stop recording and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        print(f"Recording completed. Total frames recorded: {len(frames)}")
        return b''.join(frames)

    except Exception as e:
        print(f"Error during recording: {e}")
        return None


# Function to save the recorded audio data as a WAV file
def save_audio_file_pyaudio(audio_data, filename="recorded_audio.wav", samplerate=44100):
    try:
        # Write audio data to a file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # 2 bytes per sample (16-bit)
        wf.setframerate(samplerate)
        wf.writeframes(audio_data)
        wf.close()
        print(f"Audio saved to {filename}")
    except Exception as e:
        print(f"Error saving audio file: {e}")


# Test the recording function with pyaudio
if __name__ == "__main__":
    print("Starting main function...")
    audio_data = record_audio_pyaudio(5)  # Record for 5 seconds
    if audio_data is not None:
        save_audio_file_pyaudio(audio_data, "test_audio.wav")  # Save the audio to a file
    else:
        print("Recording failed.")
