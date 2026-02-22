import random
from typing import Dict, Any

class ToneEngine:
    """
    A rule-based tone mapping engine.
    Converts abstract tone intents into safe MG400 parameter ranges
    and randomizes values within those safe bounds to generate unique patches.
    """
    
    # Define safe parameter ranges for different tone styles
    STYLES = {
        "modern metal": {
            "gain": (75.0, 95.0),
            "bass": (40.0, 60.0),
            "mid": (20.0, 45.0),  # Scooped mids
            "treble": (65.0, 85.0),
            "presence": (60.0, 85.0),
            "master": (50.0, 60.0)
        },
        "clean blues": {
            "gain": (15.0, 35.0), # Edge of breakup
            "bass": (50.0, 70.0),
            "mid": (55.0, 75.0),  # Pushed mids
            "treble": (50.0, 65.0),
            "presence": (40.0, 60.0),
            "master": (50.0, 65.0)
        },
        "classic rock": {
            "gain": (45.0, 70.0),
            "bass": (45.0, 65.0),
            "mid": (60.0, 80.0),
            "treble": (55.0, 75.0),
            "presence": (50.0, 70.0),
            "master": (50.0, 65.0)
        },
        "ambient": {
            "gain": (10.0, 25.0),
            "bass": (40.0, 60.0),
            "mid": (40.0, 60.0),
            "treble": (45.0, 70.0),
            "presence": (30.0, 50.0),
            "master": (50.0, 60.0)
        },
        "worship": {
            "gain": (25.0, 45.0),
            "bass": (50.0, 65.0),
            "mid": (50.0, 70.0),
            "treble": (55.0, 75.0),
            "presence": (45.0, 65.0),
            "master": (50.0, 60.0)
        }
    }
    
    # Fallback/default generic ranges if style is not matched perfectly
    DEFAULT_RANGES = {
        "gain": (30.0, 70.0),
        "bass": (40.0, 60.0),
        "mid": (40.0, 60.0),
        "treble": (40.0, 60.0),
        "presence": (40.0, 60.0),
        "master": (50.0, 50.0)
    }

    def _get_random_value(self, min_val: float, max_val: float) -> float:
        """Returns a random float rounded to 1 decimal place within the given range."""
        return round(random.uniform(min_val, max_val), 1)

    def generate_tone(self, intent: str) -> Dict[str, float]:
        """
        Parses the abstract tone intent to find a matching style and 
        returns a validated dictionary of randomized MG400 parameters.
        """
        intent_lower = intent.lower()
        matched_style_ranges = self.DEFAULT_RANGES
        
        # Check against supported styles based on keywords
        if "metal" in intent_lower:
            matched_style_ranges = self.STYLES["modern metal"]
        elif "blues" in intent_lower:
            matched_style_ranges = self.STYLES["clean blues"]
        elif "rock" in intent_lower:
            matched_style_ranges = self.STYLES["classic rock"]
        elif "ambient" in intent_lower:
            matched_style_ranges = self.STYLES["ambient"]
        elif "worship" in intent_lower:
            matched_style_ranges = self.STYLES["worship"]
            
        validated_params = {}
        
        for param, (min_val, max_val) in matched_style_ranges.items():
            value = self._get_random_value(min_val, max_val)
            # Ensure values are strictly within 0.0 - 100.0 as safe bounds
            validated_params[param] = max(0.0, min(100.0, value))
            
        return validated_params

    def parse_llm_intent(self, llm_response: Dict[str, Any]) -> Dict[str, float]:
        """
        Optional usage: If LLM returns a structured format with an explicit 'style' 
        or unstructured params, this fallback ensures parameters are safe and mapped correctly.
        """
        style = llm_response.get("style", "")
        # Fallback to the text-based intent if a style is explicitly provided
        if style:
             return self.generate_tone(style)
             
        # If the LLM returned raw numbers, clamp them to safe absolute limits
        safe_params = {}
        for param in self.DEFAULT_RANGES.keys():
            val = llm_response.get(param)
            if val is not None:
                safe_params[param] = max(0.0, min(100.0, float(val)))
            else:
                 # Default randomization if parameter is missing
                 min_val, max_val = self.DEFAULT_RANGES[param]
                 safe_params[param] = self._get_random_value(min_val, max_val)
                 
        return safe_params
