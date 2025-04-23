import google.generativeai as genai
import PIL.Image

class AIInsights:
    def __init__(self):
        # Google Gemini API key (already inserted)
        genai.configure(api_key="AIzaSyAIFQijh_mCe9tyU70jY8M_d--pAh8Ux9A")
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    def get_ai_insights(self, image_path, stock, market):
        try:
            image = PIL.Image.open(image_path)
            prompt = (
                f"Analyze the stock performance chart for '{stock}' on market '{market}' over the past 100 days. "
                "The chart includes Close Price, Volume, 7-day and 20-day Moving Averages, Bollinger Bands, "
                "Relative Strength Index (RSI), and MACD indicators. Based on this data, provide an analysis, "
                "highlight patterns, trends, and give a recommendation on whether this stock should be bought, held, or sold."
            )
            response = self.model.generate_content([prompt, image])
            return response
        except Exception as e:
            raise ValueError(f"Error generating AI insights: {e}")
