import json
import re
from typing import Dict, Any
from google import genai
from google.genai import types

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Send the prompt to Gemini API and ask for a JSON structured format of tone parameters.
        Returns a dictionary representing the structured tone intent.
        """
        from core.param_mapping import MIDI_CC_MAP
        available_params = list(MIDI_CC_MAP.keys())
        
        system_prompt = f'''You are a professional audio engineer and DSP architect designing signal chains for the NUX MG-400 hardware processor.
Extract requested sonic characteristics from the user's prompt and map them to a highly calculated JSON object of processor parameters.
Return ONLY valid JSON. Think like a studio engineer balancing dynamic range, parametric EQ curves, and spatial effects.
All valid parameter keys you can output are: {', '.join(available_params)}.
Each parameter must be critically evaluated and output as a precise integer value between 0 and 100.
Also include a "patchName" field (max 10 characters, uppercase string) that creatively summarizes the generated tone profile.'''

        full_prompt = f"{system_prompt}\n\nClient/Producer prompt:\n{prompt}"
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            output = response.text.strip()
            return self._parse_json_safely(output)
            
        except Exception as e:
            raise RuntimeError(f"Gemini API generation failed: {e}")

    def _parse_json_safely(self, text: str) -> Dict[str, Any]:
        """
        Safely extract and parse JSON from the response text, cleanly handling malformed responses.
        """
        clean_text = text.replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            pass
            
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
                
        raise ValueError(f"Failed to parse malformed JSON response from LLM:\n{text}")

    def analyze_tone(self, parameters: Dict[str, Any]) -> str:
        """
        Reverse AI Analytics: Reads a dictionary of numeric MG400 parameters and
        returns a natural language description of what this tone likely sounds like.
        """
        system_prompt = '''You are a seasoned mixing and mastering engineer working with a NUX MG-400 DSP unit.
You will receive a JSON dictionary representing processor parameters and block toggles extracting from a patch memory block.
Your job is to provide a brief, highly professional "Spectrum Analysis" describing how this signal chain will physically sound in a mix.
Mention EQ curve shapes (scooped, focused midrange), dynamic compression behaviors, and modulation/spatial footprint.
Do NOT output markdown, just a single, concise professional paragraph.'''

        full_prompt = f"{system_prompt}\n\nHardware DSP State Payload:\n{json.dumps(parameters)}"
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Gemini API tone analysis failed: {e}")
