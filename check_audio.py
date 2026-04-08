import pyaudio
import speech_recognition as sr

def list_devices():
    p = pyaudio.PyAudio()
    print("\n--- DISPOSITIVOS DE ENTRADA DISPONÍVEIS ---")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get('maxInputChannels') > 0:
            print(f"Index {i}: {info.get('name')}")
    p.terminate()

if __name__ == "__main__":
    list_devices()
