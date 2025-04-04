import os
import time
from typing import Any

import requests
import streamlit as st
from dotenv import find_dotenv, load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from PIL import Image
from transformers import pipeline
from utils.custom import css_code

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForVision2Seq
from transformers.image_utils import load_image
import soundfile
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig
import base64
from openai import OpenAI
import openai

load_dotenv(find_dotenv())
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def progress_bar(amount_of_time: int) -> Any:
    """
    A very simple progress bar the increases over time,
    then disappears when it reached completion
    :param amount_of_time: time taken
    :return: None
    """
    progress_text = "Please wait, Generative models hard at work"
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(amount_of_time):
        time.sleep(0.04)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()


def generate_text_from_image(url: str) -> str:

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Function to encode image to base64
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Path to your image
    # image_path = "path/to/your/image.jpg"
    base64_image = encode_image(url)

    # API call to extract features
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the main features from this image: describe objects, colors, and text if any in paragraph. If it is a text, just extract the text."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=300
    )

    response = response.choices[0].message.content



    print(response)

    # print(f"IMAGE INPUT: {url}")
    # print(f"GENERATED TEXT OUTPUT: {generated_text}")
    # return generated_text

    return response


def generate_story_from_text(scenario: str) -> str:
    """
    A function using a prompt template and GPT to generate a short story. LangChain is also
    used for chaining purposes
    :param scenario: generated text from the image
    :return: generated story from the text
    """
    prompt_template: str = f"""
    You are a talented story teller who can create a story from a simple narrative./
    Create a story using the following scenario; the story should have be maximum 50 words long;
    
    CONTEXT: {scenario}
    STORY:
    """

    prompt: PromptTemplate = PromptTemplate(
        template=prompt_template, input_variables=["scenario"]
    )

    llm: Any = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.9)

    story_llm: Any = LLMChain(llm=llm, prompt=prompt, verbose=True)

    generated_story: str = story_llm.predict(scenario=scenario)

    print(f"TEXT INPUT: {scenario}")
    print(f"GENERATED STORY OUTPUT: {generated_story}")
    return generated_story


def generate_speech_from_text(message: str) -> Any:
    """
    A function using the ESPnet text to speech model from HuggingFace
    :param message: short story generated by the GPT model
    :return: generated audio from the short story
    """
    API_URL: str = (
        "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits"
    )
    headers: dict[str, str] = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    payloads: dict[str, str] = {"inputs": message}

    response: Any = requests.post(API_URL, headers=headers, json=payloads)
    with open("generated_audio.flac", "wb") as file:
        file.write(response.content)


def main() -> None:
    """
    Main function
    :return: None
    """
    st.set_page_config(page_title="Audible Frames", page_icon="🖼️")

    st.markdown(css_code, unsafe_allow_html=True)

    # with st.sidebar:
    #     st.image("img/gkj.jpg")

    st.header("Audible Frames")
    uploaded_file: Any = st.file_uploader("Please choose a file to upload", type="jpg")

    if uploaded_file is not None:
        print(uploaded_file)
        bytes_data: Any = uploaded_file.getvalue()
        with open(uploaded_file.name, "wb") as file:
            file.write(bytes_data)
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        progress_bar(100)
        scenario: str = generate_text_from_image(uploaded_file.name)
        # story: str = generate_story_from_text(scenario)
        generate_speech_from_text(scenario)

        with st.expander("Generated Image scenario"):
            st.write(scenario)
        # with st.expander("Generated short story"):
        #     st.write(story)

        st.audio("generated_audio.flac")


if __name__ == "__main__":
    main()
