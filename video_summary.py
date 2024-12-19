import streamlit as st
import openai
import os
import assemblyai as aai
import tempfile
from moviepy import VideoFileClip

class VideoProcessor:
    def __init__(self, openai_key, assemblyai_key):
        """Initialize the processor with API keys."""
        self.openai_key = openai_key
        openai.api_key = openai_key
        aai.settings.api_key = assemblyai_key
        self.transcriber = aai.Transcriber()
    
    def convert_to_mp4(self, input_path):
        """Convert video to MP4 format."""
        try:
            # Create temporary file for MP4
            temp_mp4 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_mp4.close()
            
            # Load video and convert
            video = VideoFileClip(input_path)
            video.write_videofile(temp_mp4.name, codec='libx264', audio_codec='aac', 
                                temp_audiofile='temp-audio.m4a', remove_temp=True, 
                                logger=None)
            video.close()
            
            return temp_mp4.name
        except Exception as e:
            raise Exception(f"Error converting video: {str(e)}")
    
    def transcribe_video(self, video_path):
        """Transcribe video file using AssemblyAI."""
        try:
            transcript = self.transcriber.transcribe(video_path)
            return transcript.text
        except Exception as e:
            raise Exception(f"Error transcribing video: {str(e)}")

    def summarize_text(self, text, max_tokens=150):
        """Summarize text using OpenAI API."""
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                    {"role": "user", "content": f"Please summarize the following text:\n\n{text}"}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error summarizing text: {str(e)}")

    def process_video(self, video_path):
        """Process video: convert, transcribe and summarize."""
        temp_files = []
        try:
            # Convert to MP4 if needed
            file_extension = os.path.splitext(video_path)[1].lower()
            if file_extension != '.mp4':
                st.info("Converting video to MP4 format...")
                mp4_path = self.convert_to_mp4(video_path)
                temp_files.append(mp4_path)
            else:
                mp4_path = video_path
            
            # Transcribe video
            st.info("Transcribing video...")
            transcript = self.transcribe_video(mp4_path)
            
            # Summarize transcript
            st.info("Generating summary...")
            summary = self.summarize_text(transcript)
            
            return {
                "transcript": transcript,
                "summary": summary
            }
        finally:
            # Cleanup temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

def main():
    st.set_page_config(page_title="Video Transcription & Summarization", layout="wide")
    
    st.title("Video Transcription & Summarization")
    
    # Sidebar for API keys
    with st.sidebar:
        st.header("Configuration")
        openai_key = st.text_input("Enter OpenAI API Key", type="password")
        assemblyai_key = st.text_input("Enter AssemblyAI API Key", type="password")
        st.markdown("""
        ### Instructions:
        1. Enter your API keys
        2. Upload a video file
        3. Click 'Process Video'
        4. Wait for results
        
        Supported formats: MP4, AVI, MOV, WMV, FLV, etc.
        (Files will be automatically converted to MP4 if needed)
        
        Get your AssemblyAI API key at: https://www.assemblyai.com/
        """)
    
    # Main content
    uploaded_file = st.file_uploader("Upload a video file", 
                                   type=['mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv'])
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_video = tempfile.NamedTemporaryFile(delete=False, 
                                               suffix=os.path.splitext(uploaded_file.name)[1])
        temp_video.write(uploaded_file.read())
        temp_video.close()
        
        # Process button
        if st.button("Process Video"):
            if not openai_key or not assemblyai_key:
                st.error("Please enter both API keys in the sidebar.")
            else:
                try:
                    with st.spinner("Processing video..."):
                        processor = VideoProcessor(openai_key, assemblyai_key)
                        result = processor.process_video(temp_video.name)
                        
                        # Display results in tabs
                        tab1, tab2 = st.tabs(["Transcript", "Summary"])
                        
                        with tab1:
                            st.header("Transcript")
                            st.text_area("Full transcript", result["transcript"], height=300)
                            
                            # Add download button for transcript
                            st.download_button(
                                "Download Transcript",
                                result["transcript"],
                                file_name="transcript.txt",
                                mime="text/plain"
                            )
                        
                        with tab2:
                            st.header("Summary")
                            st.text_area("Summary", result["summary"], height=150)
                            
                            # Add download button for summary
                            st.download_button(
                                "Download Summary",
                                result["summary"],
                                file_name="summary.txt",
                                mime="text/plain"
                            )
                            
                except Exception as e:
                    st.error(f"Error processing video: {str(e)}")
                finally:
                    # Cleanup temporary video file
                    if os.path.exists(temp_video.name):
                        os.unlink(temp_video.name)

if __name__ == "__main__":
    main()