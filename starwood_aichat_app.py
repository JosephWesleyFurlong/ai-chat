import streamlit as st
import openai
import requests
from io import BytesIO
from docx import Document

# Set the OpenAI API key using Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]

# Initialize the OpenAI client with the API key
client = openai.OpenAI(api_key=api_key)

# Function to download the Word document from a URL
def download_word_doc(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)  # Return a BytesIO object
    else:
        st.error("Failed to download the document.")
        return None

# Function to extract text from a Word document
def extract_text_from_word(file):
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# GitHub URL to your Word document (raw link to the file)
docx_url = "https://raw.githubusercontent.com/Starwood-Animal-Transport/ai_chat/main/Starwood%20Knowledge%20Corpus.docx"

# Download the Word document
word_file = download_word_doc(docx_url)

# Extract text from the Word document if download was successful
if word_file:
    document_text = extract_text_from_word(word_file)

    # Chunking the text if necessary
    def chunk_text(text, chunk_size=500):
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    all_chunks = chunk_text(document_text)

    # Set up the context for the first query
    context_message = {
        "role": "system",
        "content": f"You are a helpful assistant. Here is the context based on the Word document: {''.join(all_chunks[:5])[:500]}"
    }

    # Initialize the conversation history list
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize input query in session state if not already present
    if "input_query" not in st.session_state:
        st.session_state.input_query = ""

    # Function to query OpenAI with a user's prompt and conversation history
    def query_openai(conversation_history, first_query=False):
        try:
            if first_query:
                conversation_history = [context_message] + conversation_history

            response = client.chat.completions.with_raw_response.create(
                model="gpt-4",  # You can use "gpt-3.5-turbo" or another model
                messages=conversation_history
            )
            completion = response.parse()

            if hasattr(completion.choices[0], 'message'):
                message_content = completion.choices[0].message.content
                return message_content.strip()
            else:
                return "No response generated."
        except Exception as e:
            return f"Error in API request: {e}"

    # Callback function to handle input submission
    def handle_submit():
        user_query = st.session_state.input_query
        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})

            first_query = len(st.session_state.messages) == 1

            response = query_openai(st.session_state.messages, first_query=first_query)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.input_query = ""  # Clear the input field

    # Streamlit UI
    st.title("Starwood AI Chatbot")

    for message in st.session_state.messages:
        if message['role'] == 'user':
            st.write(f"**You**: {message['content']}")
        else:
            st.write(f"**Assistant**: {message['content']}")

    st.text_input("How can I help you with your move:", key="input_query", on_change=handle_submit)
