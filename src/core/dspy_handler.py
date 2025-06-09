# src/core/dspy_handler.py
import dspy
from ..config.settings import load_settings # Corrected import path

class GenerateResponse(dspy.Signature):
    """Generate a helpful and friendly response to a user's question."""
    
    question: str = dspy.InputField(desc="The user's query.")
    answer: str = dspy.OutputField(desc="The assistant's response.")

class DspyHandler:
    def __init__(self):
        self.lm = self._setup_dspy()
        
        # Define the DSPy module with the signature
        self.predictor = dspy.Predict(GenerateResponse)
        
        # Enable streaming for the 'answer' field
        self.stream_predictor = dspy.streamify(
            self.predictor,
            stream_listeners=[dspy.streaming.StreamListener(signature_field_name="answer")],
        )

    def _setup_dspy(self):
        """Initializes and configures the DSPy language model."""
        settings = load_settings()
        api_key = settings.get('GOOGLE_API_KEY')
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please set it in your environment variables or settings.")
            
        # CORRECTED: Use dspy.LM with the model name string
        lm = dspy.LM(model='gemini/gemini-1.5-flash', api_key=api_key)
        dspy.configure(lm=lm)
        return lm

    async def get_streamed_response(self, question: str):
        """
        Calls the LM and yields streamed response chunks.
        
        Args:
            question (str): The user's question.
        
        Yields:
            str: Chunks of the response text.
        """
        output_stream = self.stream_predictor(question=question)
        async for chunk in output_stream:
            yield chunk

    def get_response(self, question: str) -> str:
        """Gets a non-streamed response from the language model."""
        response = self.predictor(question=question)
        return response.answer