"""
TTS (Text-to-Speech) Generator for Patient Briefing
Generates audio files from text summaries for patient accessibility
"""

import os
from typing import Optional
import asyncio


class TTSGenerator:
    """Generate audio from text using TTS capabilities"""
    
    def __init__(self):
        self.output_dir = "outputs/audio"
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def generate_audio(
        self,
        text: str,
        output_filename: str = "patient_briefing.mp3",
        voice: str = "en-US",
        rate: str = "medium"
    ) -> str:
        """
        Generate audio from text using TTS
        
        Args:
            text: Text to convert to audio
            output_filename: Name of the output audio file
            voice: Voice type (e.g., 'en-US', 'en-GB')
            rate: Speech rate ('slow', 'medium', 'fast')
            
        Returns:
            Path to the generated audio file
        """
        try:
            # Try using gTTS (Google Text-to-Speech)
            return await self._generate_with_gtts(text, output_filename)
        except ImportError:
            # Fallback to pyttsx3
            try:
                return await self._generate_with_pyttsx3(text, output_filename)
            except ImportError:
                # Final fallback to edge-tts
                try:
                    return await self._generate_with_edge_tts(text, output_filename)
                except ImportError:
                    print("No TTS library available. Audio generation skipped.")
                    return None
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
    
    async def _generate_with_gtts(self, text: str, output_filename: str) -> str:
        """Generate audio using gTTS (Google Text-to-Speech)"""
        try:
            from gtts import gTTS
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Create TTS object
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save audio file
            tts.save(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"gTTS generation failed: {e}")
            raise
    
    async def _generate_with_pyttsx3(self, text: str, output_filename: str) -> str:
        """Generate audio using pyttsx3"""
        try:
            import pyttsx3
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Initialize engine
            engine = pyttsx3.init()
            
            # Set properties
            engine.setProperty('rate', 150)  # Speech rate
            engine.setProperty('volume', 0.9)  # Volume
            
            # Save to file
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            return output_path
            
        except Exception as e:
            print(f"pyttsx3 generation failed: {e}")
            raise
    
    async def _generate_with_edge_tts(self, text: str, output_filename: str) -> str:
        """Generate audio using edge-tts (Microsoft Edge TTS)"""
        try:
            import edge_tts
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Generate audio
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            await communicate.save(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"edge-tts generation failed: {e}")
            raise
    
    def generate_audio_script(self, text: str) -> str:
        """
        Generate an audio-friendly script from text
        Optimizes text for TTS pronunciation and pacing
        
        Args:
            text: Original text
            
        Returns:
            Audio-optimized script
        """
        # Add pauses for better comprehension
        audio_script = text
        
        # Add pause indicators for important sections
        audio_script = audio_script.replace('.', '. <break time="500ms"/>')
        audio_script = audio_script.replace('!', '! <break time="700ms"/>')
        audio_script = audio_script.replace('?', '? <break time="700ms"/>')
        
        # Add emphasis for important terms
        important_terms = ['₹', 'Plan A', 'Plan B', 'primary', 'secondary', 'out of pocket']
        for term in important_terms:
            audio_script = audio_script.replace(term, f'<emphasis level="strong">{term}</emphasis>')
        
        # Add slower rate for numbers
        audio_script = audio_script.replace('₹', '₹ <prosody rate="0.8">')
        audio_script = audio_script.replace(',', '</prosody>,')
        
        return audio_script
    
    def get_audio_metadata(self, audio_path: str) -> dict:
        """
        Get metadata about generated audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata
        """
        try:
            import wave
            
            with wave.open(audio_path, 'rb') as audio_file:
                frames = audio_file.getnframes()
                rate = audio_file.getframerate()
                duration = frames / float(rate)
                
                return {
                    'duration_seconds': duration,
                    'sample_rate': rate,
                    'frames': frames,
                    'channels': audio_file.getnchannels(),
                    'sample_width': audio_file.getsampwidth()
                }
        except:
            try:
                # Try using mutagen for other formats
                from mutagen.mp3 import MP3
                
                audio = MP3(audio_path)
                duration = audio.info.length
                
                return {
                    'duration_seconds': duration,
                    'sample_rate': audio.info.sample_rate,
                    'bitrate': audio.info.bitrate
                }
            except:
                return {
                    'duration_seconds': 0,
                    'sample_rate': 0,
                    'error': 'Could not read audio metadata'
                }
