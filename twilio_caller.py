import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Play
import requests
import json

class TwilioVoiceCaller:
    def __init__(self, account_sid=None, auth_token=None, from_number=None):
        """
        Initialize Twilio voice caller
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token  
            from_number: Twilio phone number (e.g., +1234567890)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_FROM_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Missing Twilio credentials. Set env vars or pass parameters.")
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def generate_voice_audio(self, text, emotion='default', output_file='call_audio.mp3'):
        """
        Generate voice audio using local Edge-TTS server
        
        Args:
            text: Text to speak
            emotion: Emotion preset
            output_file: Output file path
        
        Returns:
            Path to generated audio file
        """
        import subprocess
        
        voices = {
            'default': 'en-US-GuyNeural',
            'excited': 'en-US-GuyNeural',
            'cheerful': 'en-US-AnaNeural',
            'friendly': 'en-US-AnaNeural',
            'calm': 'en-US-JennyNeural',
            'professional': 'en-US-SteffanNeural',
            'serious': 'en-US-SteffanNeural',
            'sad': 'en-GB-RyanNeural',
            'whisper': 'en-US-JennyNeural',
            'narrator': 'en-GB-SoniaNeural'
        }
        
        voice = voices.get(emotion, voices['default'])
        
        cmd = ['edge-tts', '--voice', voice, '--text', text, '--write-media', output_file]
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            raise Exception(f"Voice generation failed: {result.stderr.decode()}")
        
        return output_file
    
    def make_call(self, to_number, text, emotion='default', status_callback=None):
        """
        Make a phone call with AI-generated voice
        
        Args:
            to_number: Phone number to call (e.g., +1234567890)
            text: Text to speak
            emotion: Emotion preset
            status_callback: URL for call status callbacks
        
        Returns:
            Call SID
        """
        # Generate voice audio
        audio_file = self.generate_voice_audio(text, emotion)
        
        # Upload audio to publicly accessible URL (you'll need to host this)
        # For now, we'll use TwiML to generate speech on the fly
        
        # Create TwiML response
        twiml = VoiceResponse()
        twiml.say(text, voice='Polly.Matthew' if emotion == 'default' else 'Polly.Joanna')
        
        # Make the call
        call = self.client.calls.create(
            twiml=str(twiml),
            to=to_number,
            from_=self.from_number,
            status_callback=status_callback,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        return call.sid
    
    def make_call_with_custom_voice(self, to_number, audio_url, status_callback=None):
        """
        Make a call with custom audio file (hosted URL)
        
        Args:
            to_number: Phone number to call
            audio_url: Publicly accessible URL to audio file
            status_callback: Status callback URL
        
        Returns:
            Call SID
        """
        twiml = VoiceResponse()
        twiml.play(audio_url)
        
        call = self.client.calls.create(
            twiml=str(twiml),
            to=to_number,
            from_=self.from_number,
            status_callback=status_callback,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        return call.sid
    
    def send_sms(self, to_number, message):
        """
        Send SMS message
        
        Args:
            to_number: Phone number
            message: Message text
        
        Returns:
            Message SID
        """
        message = self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=to_number
        )
        
        return message.sid
    
    def list_calls(self, limit=20):
        """List recent calls"""
        calls = self.client.calls.list(limit=limit)
        return [
            {
                'sid': call.sid,
                'to': call.to,
                'from': call.from_,
                'status': call.status,
                'duration': call.duration,
                'date': call.date_created.strftime('%Y-%m-%d %H:%M:%S')
            }
            for call in calls
        ]
    
    def get_call_status(self, call_sid):
        """Get status of a specific call"""
        call = self.client.calls(call_sid).fetch()
        return {
            'sid': call.sid,
            'status': call.status,
            'duration': call.duration,
            'price': call.price
        }

# Example usage
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python twilio_caller.py <to_number> <text> [emotion]")
        print("Example: python twilio_caller.py +1234567890 'Hello!' excited")
        sys.exit(1)
    
    to_number = sys.argv[1]
    text = sys.argv[2]
    emotion = sys.argv[3] if len(sys.argv) > 3 else 'default'
    
    # Initialize (will use env vars)
    caller = TwilioVoiceCaller()
    
    # Make call
    print(f"Calling {to_number}...")
    call_sid = caller.make_call(to_number, text, emotion)
    print(f"Call initiated! SID: {call_sid}")
