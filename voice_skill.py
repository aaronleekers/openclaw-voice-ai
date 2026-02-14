"""
OpenClaw Voice Skill
Simple Twilio integration - no RunPod needed

Dependencies: pip install requests
"""

import os
import json
import requests

# Configuration - change these or set env vars
TWILIO_BRIDGE_URL = os.getenv('TWILIO_BRIDGE_URL', 'http://localhost:5001')
VOICE_API_KEY = os.getenv('VOICE_API_KEY', 'openclaw-secret-123')

class VoiceSkill:
    """Voice calling skill for OpenClaw"""
    
    def __init__(self, bridge_url=None, api_key=None):
        self.bridge_url = bridge_url or TWILIO_BRIDGE_URL
        self.api_key = api_key or VOICE_API_KEY
        self.headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
    
    def status(self):
        """Check voice service status"""
        try:
            r = requests.get(f"{self.bridge_url}/api/status", headers=self.headers)
            return r.json()
        except Exception as e:
            return {'error': str(e), 'status': 'offline'}
    
    def call(self, phone_number, message, voice='Polly.Matthew', gather=True):
        """
        Make a phone call
        
        Args:
            phone_number: E.164 format (+1234567890)
            message: What to say
            voice: Polly voice (Polly.Matthew, Polly.Joanna, etc.)
            gather: Listen for response
        
        Returns:
            {'success': True, 'call_sid': '...'}
        """
        try:
            r = requests.post(
                f"{self.bridge_url}/api/call",
                headers=self.headers,
                json={
                    'to': phone_number,
                    'message': message,
                    'voice': voice,
                    'gather': gather
                },
                timeout=10
            )
            return r.json()
        except Exception as e:
            return {'error': str(e)}
    
    def speak(self, call_sid, message, voice='Polly.Matthew'):
        """Say something on active call"""
        try:
            r = requests.post(
                f"{self.bridge_url}/api/speak",
                headers=self.headers,
                json={'call_sid': call_sid, 'message': message, 'voice': voice}
            )
            return r.json()
        except Exception as e:
            return {'error': str(e)}
    
    def end_call(self, call_sid):
        """Hang up call"""
        try:
            r = requests.post(
                f"{self.bridge_url}/api/end",
                headers=self.headers,
                json={'call_sid': call_sid}
            )
            return r.json()
        except Exception as e:
            return {'error': str(e)}
    
    def list_calls(self):
        """Get recent calls"""
        try:
            r = requests.get(f"{self.bridge_url}/api/calls", headers=self.headers)
            return r.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_call(self, call_sid):
        """Get specific call details"""
        try:
            r = requests.get(f"{self.bridge_url}/api/call/{call_sid}", headers=self.headers)
            return r.json()
        except Exception as e:
            return {'error': str(e)}

# Convenience functions for direct use
def voice_status():
    """Check voice service"""
    return VoiceSkill().status()

def make_call(phone, message, voice='Polly.Matthew'):
    """Make a call"""
    return VoiceSkill().call(phone, message, voice)

def say_on_call(call_sid, message):
    """Speak to active call"""
    return VoiceSkill().speak(call_sid, message)

def hangup(call_sid):
    """End call"""
    return VoiceSkill().end_call(call_sid)

def recent_calls():
    """List recent calls"""
    return VoiceSkill().list_calls()

# Example usage
if __name__ == '__main__':
    skill = VoiceSkill()
    
    # Check status
    print("Status:", skill.status())
    
    # Make a test call (uncomment to use)
    # result = skill.call('+1234567890', 'Hello from OpenClaw!')
    # print("Call result:", result)
