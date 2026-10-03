import json
import time

import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import (
    SUMMARY_REQUEST_PROMPT,
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
)


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "gemini-3.8-flash"

st.set_page_config(
    page_title="MacroSnap",
    page_icon="🥗",
    layout="centered",
)


# =========================================================
# SECRETS
# =========================================================

GEMINI_API_KEY = "AQ.Ab8RN6IUtRwxE_sSyXBNLSkyH4GoYM9ecHaMBWsmqL9EQn7FvA"

# Twilio is optional
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = st.secrets.get("TWILIO_WHATSAPP_FROM", "")
TWILIO_CONTENT_SID = st.secrets.get("TWILIO_CONTENT_SID", "")


# =========================================================
# CLIENTS
# =========================================================

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_resource
def get_twilio_client():
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return None

    return TwilioClient(
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
    )


gemini_client = get_gemini_client()
twilio_client = get_twilio_client()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def render_message(message):
    """Display a message in the chat."""

    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    """Store and display a chat message."""

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content,
        }
    )

    render_message(st.session_state.messages[-1])


# =========================================================
# GEMINI
# =========================================================

def ask_gemini(parts):
    """Send text/image content to Gemini with retry support."""

    for attempt in range(4):

        try:

            response = st.session_state.chat.send_message(parts)

            return response.text

        except Exception as error:

            error_text = str(error)

            # Retry temporary Gemini server errors
            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue

            return f"Sorry, something went wrong: {error}"


# =========================================================
# WHATSAPP HELPERS
# =========================================================

def clean_whatsapp_text(text):

    if not text:
        return "No nutrition summary available."

    text = " ".join(text.split())

    if len(text) > 1500:
        return text[:1500] + "..."

    return text


def send_whatsapp(to_number, user_name, summary):

    # Twilio not configured
    if not twilio_client:

        return (
            False,
            "WhatsApp integration is not configured yet.",
        )

    # Content SID not configured
    if not TWILIO_CONTENT_SID:

        return (
            False,
            "WhatsApp Content SID is not configured yet.",
        )

    try:

        content_variables = json.dumps(
            {
                "1": user_name,
                "2": clean_whatsapp_text(summary),
            },
            ensure_ascii=False,
        )

        message = twilio_client.messages.create(

            from_=TWILIO_WHATSAPP_FROM,

            to=f"whatsapp:{to_number}",

            content_sid=TWILIO_CONTENT_SID,

            content_variables=content_variables,
        )

        return True, message.sid

    except Exception as error:

        return False, str(error)


# =========================================================
# STEP 1 - ONBOARDING
# =========================================================

if "onboarded" not in st.session_state:

    st.title("🥗 MacroSnap")

    st.caption(
        "Snap it. Track it. Text yourself the results."
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name"
        )

        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="This number can be used to receive your nutrition summary.",
        )

        submitted = st.form_submit_button(
            "Let's go 🚀"
        )

    if submitted:

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        else:

            st.session_state.name = name.strip()

            st.session_state.whatsapp_number = (
                whatsapp_number.strip()
            )

            # Create Gemini chat
            st.session_state.chat = (
                gemini_client.chats.create(

                    model=MODEL_NAME,

                    config=types.GenerateContentConfig(

                        system_instruction=SYSTEM_PROMPT

                    ),
                )
            )

            st.session_state.messages = []

            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# =========================================================
# STEP 2 - CHAT INTERFACE
# =========================================================

header_col, button_col = st.columns(
    [5, 2],
    vertical_alignment="center",
)


# =========================================================
# HEADER
# =========================================================

with header_col:

    st.title("🥗 MacroSnap")


# =========================================================
# WHATSAPP BUTTON
# =========================================================

with button_col:

    # Only enable when enough messages exist
    # and Twilio is configured
    send_disabled = (
        len(st.session_state.messages) <= 2
        or not twilio_client
        or not TWILIO_CONTENT_SID
        or not st.session_state.whatsapp_number
    )

    if st.button(
        "📤 Send to WhatsApp",
        disabled=send_disabled,
        use_container_width=True,
    ):

        with st.spinner(
            "Summarizing your day..."
        ):

            summary = ask_gemini(
                [SUMMARY_REQUEST_PROMPT]
            )

        success, info = send_whatsapp(

            st.session_state.whatsapp_number,

            st.session_state.name,

            summary,
        )

        if success:

            st.success(
                "Sent! Check your WhatsApp 📲"
            )

        else:

            st.error(
                f"Couldn't send that: {info}"
            )


# =========================================================
# USER INFO
# =========================================================

if st.session_state.whatsapp_number:

    st.caption(
        f"Logged in as {st.session_state.name} - "
        f"updates go to "
        f"{st.session_state.whatsapp_number}"
    )

else:

    st.caption(
        f"Logged in as {st.session_state.name}"
    )


# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

if not st.session_state.messages:

    add_message(

        "assistant",

        "text",

        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        ),
    )

else:

    for message in st.session_state.messages:

        render_message(message)


# =========================================================
# CHAT INPUT + IMAGE UPLOAD
# =========================================================

user_input = st.chat_input(

    "Ask a question, or attach a photo of your meal",

    accept_file=True,

    file_type=[
        "jpg",
        "jpeg",
        "png",
    ],
)


# =========================================================
# PROCESS USER INPUT
# =========================================================

if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    if photo is not None:

        photo_bytes = photo.getvalue()

        # Display uploaded image
        add_message(
            "user",
            "image",
            photo_bytes,
        )

        # Send image to Gemini
        parts.append(
            types.Part.from_bytes(

                data=photo_bytes,

                mime_type=photo.type,
            )
        )


    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

    if text:

        add_message(
            "user",
            "text",
            text,
        )

        parts.append(text)


    # -----------------------------------------------------
    # IMAGE ONLY
    # -----------------------------------------------------

    elif photo is not None:

        parts.append(
            """
            Analyze this meal.

            Identify the food items and estimate:

            - Calories
            - Protein
            - Carbohydrates
            - Fat

            Clearly mention that the nutrition values
            are estimates.

            Keep the answer short and easy to understand.
            """
        )


    # -----------------------------------------------------
    # GEMINI RESPONSE
    # -----------------------------------------------------

    if parts:

        with st.spinner(
            "🥗 Crunching the numbers..."
        ):

            answer = ask_gemini(parts)

        add_message(
            "assistant",
            "text",
            answer,
        )
