import google.generativeai as genai
import PIL.Image

class AIInsights:
    def __init__(self):
        # Google Gemini API key (already inserted)
        genai.configure(api_key="AIzaSyAIFQijh_mCe9tyU70jY8M_d--pAh8Ux9A")
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    def get_ai_insights(self, image_path, stock, market, fundamentals=None):
        try:
            image = PIL.Image.open(image_path)
        
            prompt = (
                f"Analyze the stock performance chart for '{stock}' on market '{market}' over the past 100 days. "
                "The chart includes Close Price, Volume, 7-day and 20-day Moving Averages, Bollinger Bands, "
                "Relative Strength Index (RSI), and MACD indicators. "
            )

            if fundamentals:
                fundamental_summary = "\n".join([f"{k.replace('_', ' ')}: {v}" for k, v in fundamentals.items()])
                prompt += (
                    "\n\nIn addition to the technical analysis, consider the following fundamental indicators:\n"
                    f"{fundamental_summary}\n"
                    "Incorporate these fundamentals in your analysis and give a final recommendation "
                    "on whether to Buy, Hold, or Sell the stock."
                )
            else:
                prompt += (
                    "\n\nBased on this data, provide an analysis, highlight patterns, trends, "
                    "and give a recommendation on whether this stock should be bought, held, or sold."
                )

            response = self.model.generate_content([prompt, image])

            if response and response.candidates:
                return response.candidates[0].content.parts[0].text
            else:
                return "No insights generated."

        except Exception as e:
            raise ValueError(f"Error generating AI insights: {e}")