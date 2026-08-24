"""
Gemini LLM Integration for SQL Generation
"""
import os
from typing import Optional, Tuple

# Try the new google.genai package first, fall back to deprecated one
try:
    import google.genai as genai
    USING_NEW_API = True
except ImportError:
    try:
        import google.generativeai as genai
        USING_NEW_API = False
    except ImportError:
        genai = None
        USING_NEW_API = None


class GeminiLLM:
    """Wrapper for Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini LLM
        
        Args:
            api_key: Gemini API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        self.is_configured = False
        self.last_error = None
        
        if not genai:
            self.last_error = "Gemini SDK not installed"
            self.is_configured = False
            return
        
        if self.api_key:
            try:
                if USING_NEW_API:
                    # New API (google.genai)
                    client = genai.Client(api_key=self.api_key)
                    self.model = client
                    # Use recommended model for free tier
                    self.model_name = 'gemini-2.5-flash'
                else:
                    # Old deprecated API (google.generativeai)
                    genai.configure(api_key=self.api_key)
                    # Use recommended model name from Google's free tier docs
                    self.model = genai.GenerativeModel('gemini-2.5-flash')
                self.is_configured = True
            except Exception as e:
                self.last_error = f"Failed to configure Gemini: {str(e)}"
                self.is_configured = False
    
    def generate(self, prompt: str) -> Tuple[bool, str, Optional[str]]:
        """
        Generate SQL from natural language prompt
        
        Args:
            prompt: The prompt containing schema and question
            
        Returns:
            Tuple of (success, result, error_message)
        """
        if not self.is_configured:
            return False, "", self.last_error or "Gemini API not configured"
        
        try:
            if USING_NEW_API:
                # New API
                response = self.model.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                response_text = response.text
            else:
                # Old API - try with recommended models in order
                fallback_models = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-pro']
                last_error = None
                
                for model_name in fallback_models:
                    try:
                        test_model = genai.GenerativeModel(model_name)
                        response = test_model.generate_content(prompt)
                        response_text = response.text
                        # If successful, update our model
                        self.model = test_model
                        break
                    except Exception as e:
                        last_error = e
                        continue
                else:
                    # If all models failed, raise the last error
                    if last_error:
                        raise last_error
            
            if not response_text:
                return False, "", "Empty response from Gemini"
            
            # Extract SQL from response
            sql = self._extract_sql(response_text)
            return True, sql, None
            
        except Exception as e:
            error_msg = str(e)
            # Common Gemini errors
            if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                error_msg = "Invalid Gemini API key"
            elif "quota" in error_msg.lower():
                error_msg = "Gemini API quota exceeded"
            elif "rate_limit" in error_msg.lower():
                error_msg = "Gemini API rate limit reached"
            elif "404" in error_msg and "not found" in error_msg.lower():
                error_msg = "Model not available for your API key (Free tier). Try upgrading or check available models."
            else:
                error_msg = f"Gemini API error: {error_msg}"
            
            return False, "", error_msg
    
    def _extract_sql(self, response_text: str) -> str:
        """Extract SQL query from Gemini response"""
        import re
        
        # Check for special responses first
        if "OUT_OF_SCOPE:" in response_text or "NEEDS_CLARIFICATION:" in response_text:
            return response_text.strip()
        
        # Try to extract SQL from code blocks
        sql_patterns = [
            r'```sql\n(.*?)\n```',  # SQL code blocks
            r'```\n(.*?)\n```',      # Generic code blocks
            r'SELECT.*?;',           # Direct SQL
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                sql = match.group(1) if '(' in pattern and ')' in pattern else match.group(0)
                return sql.strip()
        
        # If no code block, try to find SELECT statement
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.upper().startswith('SELECT'):
                return line
        
        # Return cleaned response
        return response_text.strip()


def test_gemini_connection() -> Tuple[bool, str]:
    """
    Test if Gemini API is working
    
    Returns:
        Tuple of (success, message)
    """
    try:
        gemini = GeminiLLM()
        if not gemini.is_configured:
            return False, gemini.last_error or "API key not configured"
        
        # Simple test
        success, result, error = gemini.generate("Generate SQL: SELECT 1")
        if success:
            return True, "Gemini API connected successfully"
        else:
            return False, error or "Unknown error"
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"
