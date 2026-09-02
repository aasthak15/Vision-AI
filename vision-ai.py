import os
import subprocess
import speech_recognition as sr
from gtts import gTTS
from time import sleep
from pathlib import Path
from google import genai
from PIL import Image
from deepface import DeepFace
import cv2

def record_audio():
    r = sr.Recognizer()

    # Make recognition less sensitive to small background sounds
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8
    r.phrase_threshold = 0.3
    r.non_speaking_duration = 0.5

    with sr.Microphone() as source:
        print("\nAdjusting for background noise...")
        r.adjust_for_ambient_noise(source, duration=1)

        print("🎤 Say something...")

        try:
            audio = r.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )
        except sr.WaitTimeoutError:
            print("❌ No speech detected.")
            return None

    print("Processing...")

    try:
        text = r.recognize_google(audio)
        print("You said:", text)
        return text

    except sr.UnknownValueError:
        print("❌ Could not understand audio. Please speak clearly.")
        return None

    except sr.RequestError as e:
        print("❌ Google Speech Recognition error:", e)
        return None

def find_match(image_path):
    images_folder = "images"
    test_image = cv2.imread(image_path)

    if test_image is None:
        print("❌ Could not read captured image.")
        return

    image_files = os.listdir(images_folder)
    match_found = False

    for image_file in image_files:

        full_image_path = os.path.join(images_folder, image_file)

        image = cv2.imread(full_image_path)

        if image is None:
            continue

        try:
            result = DeepFace.verify(
                test_image,
                image,
                enforce_detection=False
            )

            if result["verified"]:
                match_found = True

                print(f"✅ Match found: {full_image_path}")

                text_to_speech(
                    f"Match found. The person is {image_file}"
                )

                break

        except Exception as e:
            print(f"Face verification error: {e}")

    if not match_found:
        print("❌ No match found.")
        text_to_speech("No match found.")

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")
    sleep(2)
    os.startfile("output.mp3")

def call_api_with_gemini(prompt):
    try:
        # Connect to Gemini
        client = genai.Client(api_key="AQ.Ab8RN6I4PnLoF1Kw3XB5pv_Qb4czOjB_WXAE8XzXosG1St_9Uw")

        # Read the compressed image
        image_data = Path("compressed_image.png").read_bytes()

        # Send prompt + image to Gemini
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                prompt,
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_data
                    }
                }
            ]
        )

        # Get Gemini's response
        answer = response.text

        print("\n🤖 Gemini:")
        print(answer)

        # Speak the response
        text_to_speech(answer)

        return answer

    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return None

def compress_image(input_path, output_path, scale_factor=0.5):
    # Image Compression as Gemini doesn't take images above 4mb
    try:
        with Image.open(input_path) as img:
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)
            resized_img = img.resize((new_width, new_height))
            resized_img.save(output_path)
        print(f"Image compressed and saved to {output_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def capture_image(file_path='captured_image.png'):
    try:
        camera = cv2.VideoCapture(0)

        if not camera.isOpened():
            print("❌ Could not open camera.")
            return None

        print("📷 Camera opened.")
        print("Press SPACE to capture image.")
        print("Press ESC to cancel.")

        while True:
            ret, frame = camera.read()

            if not ret:
                print("❌ Could not read camera.")
                camera.release()
                return None

            cv2.imshow("Vision AI Camera", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 32:  # SPACE
                cv2.imwrite(file_path, frame)
                print(f"✅ Image captured and saved to {file_path}")
                break

            elif key == 27:  # ESC
                print("❌ Capture cancelled.")
                camera.release()
                cv2.destroyAllWindows()
                return None

        camera.release()
        cv2.destroyAllWindows()

        compressed_file_path = 'compressed_image.png'
        compress_image(file_path, compressed_file_path)

        return compressed_file_path

    except Exception as e:
        print(f"❌ Camera error: {e}")
        return None

if __name__ == "__main__":
    print("================================")
    print("      VISION AI STARTED")
    print("Say 'Hello Vision' to activate")
    print("================================")

    while True:
        command = record_audio()

        if command:
            command = command.lower().strip()

            if "hello vision" in command or "hey vision" in command:
                print("\n🎯 Wake word detected!")
                print("📷 Capturing image...")

                compressed_image_path = capture_image()

                if compressed_image_path is None:
                    print("❌ Image capture failed.")
                    continue

                print("✅ Image captured successfully!")

                # Show captured image
                image = cv2.imread("captured_image.png")

                if image is not None:
                    cv2.imshow("Captured Image", image)
                    cv2.waitKey(3000)
                    cv2.destroyAllWindows()

                print("🎤 Recording prompt...")

                prompt_text = record_audio()

                if not prompt_text:
                    print("❌ No prompt detected.")
                    continue

                prompt_text = prompt_text.lower()

                if (
                    "who is this person" in prompt_text
                    or "describe the person" in prompt_text
                    or "person" in prompt_text
                ):
                    print("👤 Identifying person...")

                    image_path = "captured_image.png"

                    find_match(image_path)

                    continue

                print("🤖 Sending image and prompt to Gemini...")

                call_api_with_gemini(prompt_text)

                # Delete temporary images
                if os.path.exists("compressed_image.png"):
                    os.remove("compressed_image.png")

                if os.path.exists("captured_image.png"):
                    os.remove("captured_image.png")

                print("✅ Done!")
                print("Say 'Hello Vision' again to activate.")