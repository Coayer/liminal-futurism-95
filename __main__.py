import mimetypes
import os
import datetime
import logging
import random
from pathlib import Path
import threading
import queue
from google import genai
from google.genai import types
from flask import Flask, send_from_directory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

GEMINI_API_KEY = ""
GEMINI_TEXT_MODEL = ""
GEMINI_IMAGE_MODEL = ""

GENERATED_IMAGES_PATH = "generated_images"

unseen_generated_images = queue.SimpleQueue()


def save_binary_file(file_name, data):
    """Save binary data to a file and return the path"""
    output_dir = Path(GENERATED_IMAGES_PATH)
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / file_name
    with open(file_path, "wb") as f:
        f.write(data)
    logger.info(f"File saved to: {file_path}")
    return file_path


def generate_image():
    """Generate an image using the provided prompt with Gemini image generation model"""
    client = genai.Client(api_key=GEMINI_API_KEY)

    image_prompt = f"1950s futurism, sci fi, landscape, surreal, LIMINAL space, {random.choice(['sunlight', 'mid century modern', ''])}, gradient blue sky, hazy, flat colors, {random.choice(['desert', 'green Northern', 'Southern', 'coastal'])} California, no signature, acrylic on board painting"

    logger.info(f"Generating image with prompt: {image_prompt}")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=image_prompt),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
        safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_ONLY_HIGH",
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_ONLY_HIGH",
            ),
        ],
        response_mime_type="text/plain",
    )

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = False

    try:
        for chunk in client.models.generate_content_stream(
            model=GEMINI_IMAGE_MODEL,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue

            if chunk.candidates[0].content.parts[0].inline_data:
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                mime_type = inline_data.mime_type
                file_extension = mimetypes.guess_extension(mime_type)
                filename = f"liminal_space_{timestamp}{file_extension}"
                saved_path = save_binary_file(filename, data_buffer)
                unseen_generated_images.put(saved_path.name)
            else:
                logger.info(f"Text response: {chunk.text}")

        if not saved:
            logger.warning("No image was generated or saved.")
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}"[:150])


def trigger_image_generation():
    thread = threading.Thread(target=generate_image)
    thread.start()


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/image", methods=["GET"])
def get_image():
    trigger_image_generation()

    try:
        next_unseen_image = unseen_generated_images.get(block=False)
        logger.info(f"Sending unseen image: {next_unseen_image}")
        return send_from_directory(GENERATED_IMAGES_PATH, next_unseen_image)
    except queue.Empty:
        output_dir = Path(GENERATED_IMAGES_PATH)
        image_files = list(output_dir.glob("*"))
        random_image = random.choice(image_files)
        logger.info(f"No unseen images available, sending random image: {random_image}")
        return send_from_directory(output_dir, random_image.name)
    except Exception as e:
        logger.error(f"Error sending image: {str(e)}")


def main():
    global GEMINI_API_KEY, GEMINI_TEXT_MODEL, GEMINI_IMAGE_MODEL

    # Set your API key in environment variable or replace this with direct assignment
    if "GEMINI_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    if "GEMINI_TEXT_MODEL" not in os.environ:
        raise ValueError("GEMINI_TEXT_MODEL environment variable not set")

    GEMINI_TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL")

    if "GEMINI_IMAGE_MODEL" not in os.environ:
        raise ValueError("GEMINI_IMAGE_MODEL environment variable not set")

    GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL")

    try:
        output_dir = Path(GENERATED_IMAGES_PATH)
        output_dir.mkdir()
        logger.info(
            f"Directory {GENERATED_IMAGES_PATH} created successfully, generating initial image."
        )
        trigger_image_generation()
    except OSError:
        logger.info(
            f"Directory {GENERATED_IMAGES_PATH} already exists, skipping creation."
        )

    # Start Flask server
    logger.info("Starting Flask server on port 8080")
    app.run(
        host="0.0.0.0", port=8080, debug=False
    )  # Set debug to False to avoid issues with threading


if __name__ == "__main__":
    main()
