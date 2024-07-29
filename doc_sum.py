from dotenv import load_dotenv
import streamlit as st
import os
import pathlib
import textwrap
import google.generativeai as genai
from IPython.display import display
from IPython.display import Markdown
import fitz  # PyMuPDF
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from docx import Document

# Load environment variables
load_dotenv()

def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

# Configure Google API for Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load OpenAI model and get responses
def get_gemini_response(text):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(text)
    return response.text

# Function to read text from a .docx file
def read_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Function to extract text from a PDF file
def read_pdf(file_path):
    doc = fitz.open(file_path)
    full_text = []
    for page in doc:
        full_text.append(page.get_text())
    return '\n'.join(full_text)

# Function to summarize text using spaCy
def initial_summarize_text(text, num_sentences=3):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    # Extract sentences that are not stop words and are sufficiently long
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.split()) > 5 and sent.text.lower() not in STOP_WORDS]
    ranked_sentences = sorted(sentences, key=len, reverse=True)
    
    # Construct a paragraph from key sentences
    if len(ranked_sentences) > num_sentences:
        paragraph = ' '.join(ranked_sentences[:num_sentences])
    else:
        paragraph = ' '.join(ranked_sentences)
    
    return paragraph

# Function to determine file type and read text accordingly
def read_file(file_path):
    if file_path.endswith('.docx'):
        return read_docx(file_path)
    elif file_path.endswith('.pdf'):
        return read_pdf(file_path)
    else:
        raise ValueError("Unsupported file format. Please provide a .docx or .pdf file.")


# Initialize Streamlit app
st.set_page_config(page_title="Q&A Demo")
st.title("Gemini Application")

# Input field for user question
input_text = st.text_input("Input:", key="input")

# File uploader for document analysis
uploaded_file = st.file_uploader("Upload a .docx or .pdf file", type=["docx", "pdf"])

# Button to submit the question
submit_button = st.button("Enter")

# If ask button is clicked
if submit_button:
    if uploaded_file is not None:
        # Save the uploaded file directly to the current directory
        file_path = os.path.join('.', uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            # Read and summarize the document
            text = read_file(file_path)
            initial_summary = initial_summarize_text(text)
            
            # Generate a precise summary using the Gemini API
            summary_prompt = f"Please provide a concise and precise summary of the following text:\n\n{initial_summary}"
            refined_summary = get_gemini_response(summary_prompt)
            
            # Display both the summarized paragraph and the Gemini API response
            response = f"Gemini Response:\n\n{refined_summary}"
        except Exception as e:
            response = str(e)
        finally:
            os.remove(file_path)  # Clean up the file
    else:
        response = get_gemini_response(input_text)

    st.subheader("The Response is")
    st.write(response)