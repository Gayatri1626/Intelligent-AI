from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import fitz  # PyMuPDF
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from docx import Document
import speech_recognition as sr
import sounddevice as sd
import wavio
import numpy as np
from resume_temp import generate_resume
from cover_letter import generate_cover_letter  # Assuming generate_resume is correctly defined
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configure Google API for Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load OpenAI model and get responses
def get_gemini_response(text):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(text)
    return response.text

# Function to load OpenAI model and get image description
def get_gemini_image_description(image_bytes):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = "Describe this image in detail."
    response = model.generate_content([prompt, image_bytes])
    return response.text

# Function to read text from a .docx file
def read_docx(file_path):
    doc = Document(file_path)
    full_text = [para.text for para in doc.paragraphs]
    return '\n'.join(full_text)

# Function to extract text from a PDF file
def read_pdf(file_path):
    doc = fitz.open(file_path)
    full_text = [page.get_text() for page in doc]
    return '\n'.join(full_text)

# Function to summarize text using spaCy
def initial_summarize_text(text, num_sentences=3):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.split()) > 5 and sent.text.lower() not in STOP_WORDS]
    ranked_sentences = sorted(sentences, key=len, reverse=True)
    
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

# Function to convert audio to text
def audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
    return text

# Function to record audio
def record_audio(duration=5, fs=44100):
    st.info("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()
    wavio.write("live_audio.wav", recording, fs, sampwidth=2)
    st.success("Recording finished.")
    return "live_audio.wav"

# Function to generate job description using Gemini API
def generate_job_description(job_title):
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Generate a job description for a {job_title} in 1 lines precisely."
        response = model.generate_content(prompt)
        job_description = response.text
    except Exception as e:
        st.warning(f"AI content generation failed. Please try again later.")
        job_description = ""
    
    return job_description

# Function to generate objective using AI based on job title
def generate_objective(job_title):
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Generate an objective for a {job_title} in 2-3 lines."
        response = model.generate_content(prompt)
        objective = response.text
    except Exception as e:
        st.warning(f"AI content generation failed. Please try again later.")
        objective = ""
    
    return objective

# Initialize Streamlit app
st.set_page_config(page_title="Gemini Application")
st.title("Gemini Application")

# Sidebar for functionality selection
st.sidebar.title("Select a function")
option = st.sidebar.selectbox("Select an option:", ["Q&A", "Document Summarization", "Resume Generator", "Cover Letter Generator", "Image Analysis"])

# Q&A Section
if option == "Q&A":
    st.header("Ask a Question")
    input_text = st.text_input("Type your question:")

    # Button to submit typed question
    if st.button("Submit"):
        if input_text:
            response = get_gemini_response(input_text)
            st.subheader("The Response is")
            st.write(response)
        else:
            st.warning("Please enter a question.")
    
    # Button to record voice input
    if st.button("Record Voice"):
        audio_file = record_audio()
        try:
            input_text = audio_to_text(audio_file)
            response = get_gemini_response(input_text)
            st.subheader("The Response is")
            st.write(response)
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            os.remove(audio_file)

elif option == "Document Summarization":
    st.header("Document Summarization")
    uploaded_file = st.file_uploader("Upload a .docx or .pdf file", type=["docx", "pdf"])
    if st.button("Summarize"):
        if uploaded_file:
            file_path = os.path.join('.', uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            try:
                text = read_file(file_path)
                initial_summary = initial_summarize_text(text)
                summary_prompt = f"Please provide a concise and precise summary of the following text:\n\n{initial_summary}"
                refined_summary = get_gemini_response(summary_prompt)
                st.subheader("Summary")
                st.write(refined_summary)
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                os.remove(file_path)
        else:
            st.warning("Please upload a document.")

elif option == "Resume Generator":
    st.header("Resume Generator")

    with st.form("resume_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        education = st.text_area("Education")
        experience = st.text_area("Experience")
        skills = st.text_area("Skills")
        job_title = st.text_input("Job Title (optional)")

        # Automatically generate job description based on job title input
        if job_title:
            job_description = generate_job_description(job_title)
        else:
            job_description = ""
        
        # Display job description
        st.text_area("Job Description", value=job_description, height=100)
        
        # Automatically generate objective based on job title input
        if job_title:
            objective = generate_objective(job_title)
        else:
            objective = ""
        
        # Display objective
        st.text_area("Objective", value=objective, height=100)
        
        submit_button = st.form_submit_button("Generate Resume")

    if submit_button:
        if job_title:
            # Assuming a default template or a single template option
            template = "Template 1"  # Update this based on your actual template names or default selection
            
            # Generate resume using user inputs, job description, and objective
            resume_path = generate_resume(template, name, email, phone, education, experience, skills, job_title, job_description=job_description, objective=objective)
            
            st.success("Resume generated successfully!")
            st.download_button(label="Download Resume", data=open(resume_path, "rb"), file_name="resume.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif option == "Cover Letter Generator":
    st.header("Cover Letter Generator")
    from_name = st.text_input("From (Your First Name):")
    from_lastname = st.text_input("From (Your Last Name):")
    from_email = st.text_input("From (Your Email):")
    from_profession = st.text_input("From (Your Profession):")
    from_phone = st.text_input("From (Your Phone Number):")
    from_address = st.text_area("From (Your Address):")
    
    to_name = st.text_input("To (Recipient's First Name):")
    to_lastname = st.text_input("To (Recipient's Last Name):")
    to_company = st.text_input("To (Recipient's Company Name):")
    to_department = st.text_input("To (Recipient's Department):")
    to_address = st.text_area("To (Recipient's Address):")

    subject = st.text_input("Subject:")
    date = st.date_input("Date:")

    if st.button("Generate Cover Letter"):
        date_str = date.strftime("%B %d, %Y")  # Convert date to string format
        cover_letter_content = generate_cover_letter(from_name, from_lastname, from_email, from_profession, from_phone, from_address, to_name, to_lastname, to_company, to_department, to_address, subject, date_str)
        st.subheader("Generated Cover Letter")
        st.write(cover_letter_content)

elif option == "Image Analysis":
    st.header("Image Description")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image.", use_column_width=True)

    if st.button("Tell me about the image"):
        if uploaded_file is not None:
            response = get_gemini_image_description(image)
            st.subheader("The Response is")
            st.write(response)
        else:
            st.warning("Please upload an image.")
