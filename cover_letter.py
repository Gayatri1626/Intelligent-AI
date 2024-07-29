import google.generativeai as genai
import streamlit as st


# Function to generate cover letter content based on inputs
def generate_cover_letter(from_name, to_name, subject, from_lastname="", from_email="", from_profession="", from_phone="", from_address="", to_lastname="", to_company="", to_department="", to_address="", date=""):
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # Constructing the prompt based on provided inputs
        prompt = f"{date}\n\n{from_address}\n\n{to_name} {to_lastname}\n{to_department}\n{to_company}\n{to_address}\n\nSubject: {subject}\n\nDear {to_name},\n\nI am writing to express my interest in the position at {to_company} within the {to_department}."
        
        if from_profession:
            prompt += f" With my background in {from_profession},"
        
        prompt += " I am confident that my skills in [specific skills] make me a strong candidate. "
        
        if from_email:
            prompt += f"You can reach me at {from_email}. "
        
        if from_phone:
            prompt += f"Feel free to contact me at {from_phone}. "
        
        prompt += "I am particularly drawn to your company's commitment to [mention something specific about the company that impresses you]. I look forward to the opportunity to discuss how my background, professionalism, and enthusiasm would be an asset to your team.\n\nSincerely,\t{from_name}"
        
        if from_lastname:
            prompt += f" {from_lastname}"
        
        response = model.generate_content(prompt)
        cover_letter_content = response.text
    except Exception as e:
        st.warning(f"AI content generation failed. Please try again later.")
        cover_letter_content = ""
    
    return cover_letter_content