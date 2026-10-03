# 🥗 MacroSnap

MacroSnap is a Streamlit AI nutrition buddy. A user enters their name and WhatsApp number, then can:

- Ask nutrition questions
- Upload a meal photo
- Get AI-estimated calories and macros
- Generate a conversation summary
- Send the summary to WhatsApp through Twilio

The project uses Gemini for chat/vision and Twilio for WhatsApp.

## Project structure

```text
macrosnap/
├── app.py
├── prompts.py
├── requirements.txt
├── .gitignore
├── README.md
└── .streamlit/
    └── secrets.toml.example
```

## 1. Create the environment

Python 3.9+ is recommended.

### Windows PowerShell

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Configure Gemini

Create a Gemini API key in Google AI Studio.

Then copy:

```text
.streamlit/secrets.toml.example
```

to:

```text
.streamlit/secrets.toml
```

and add your real Gemini API key.

## 3. Configure Twilio WhatsApp

Create/sign in to a Twilio account and configure the WhatsApp Sandbox.

You need:

- Account SID
- Auth Token
- WhatsApp Sandbox sender number
- Approved WhatsApp Content Template SID

The WhatsApp number used for testing must join the sandbox.

The template should accept two variables:

```text
{{1}} = recipient name
{{2}} = nutrition summary
```

Example:

```text
Hi {{1}}, here's your MacroSnap summary:

{{2}}
```

## 4. Run the application

```powershell
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## 5. Test

1. Enter your name.
2. Enter your WhatsApp number with country code.
3. Ask a nutrition question.
4. Upload a JPG/PNG meal photo.
5. Click **Send to WhatsApp** after logging a meal.

## Important

Never commit `.streamlit/secrets.toml` to GitHub.

The project estimates nutrition values; estimates are not medical or dietary advice.
