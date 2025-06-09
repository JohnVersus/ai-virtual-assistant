# src/core/dspy_handler.py
import dspy
from dspy.streaming import StreamResponse # Corrected import path
from ..config.settings import load_settings

class GenerateResponse(dspy.Signature):
    """Generate a helpful and friendly response based on the conversation history."""
    
    history: list[dict] = dspy.InputField(desc="The conversation history, with roles 'user' and 'assistant'.")
    answer: str = dspy.OutputField(desc="The assistant's response.")

class DspyHandler:
    def __init__(self):
        self.lm = self._setup_dspy()
        
        self.predictor = dspy.Predict(GenerateResponse)
        
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
            
        lm = dspy.LM(model='gemini/gemini-1.5-flash', api_key=api_key)
        dspy.configure(lm=lm)
        return lm

    async def get_streamed_response(self, history: list[dict]):
        """
        Calls the LM with conversation history and yields streamed response chunks.
        """
        output_stream = self.stream_predictor(history=history)

        # The stream yields StreamResponse objects first, and a Prediction object last.
        # We must check the type before trying to access attributes.
        async for item in output_stream:
            if isinstance(item, StreamResponse):
                yield item.chunk
            # We can safely ignore the final Prediction object.