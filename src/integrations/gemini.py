from google import genai
from src.data.wishes import EMOJIS
from src.config import EnvManager


class GeminiIntegration:

    def __init__(self, template_type: str):
        google_api_key: str | None = EnvManager.GEMINI_API_KEY
        self.google_model: str = "gemini-2.0-flash"
        self.google_client: genai.Client = genai.Client(api_key=google_api_key)
        self.google_system_prompt: str = """
        You are a helpful assistant that generates a template for {template_type} message.
        Include emojis in the template as needed.
        Also you can include some of this emojis created on slack:
        {emojis}
        You can use the emojis to make the message more engaging.
        Your answer should be the template itself.
        Generate only one template.
        Supose that I'm sending the message.
        The template should be complete.
        Dont add the farewell sentence.
        Avoid adding things that need to be filled by the user.
        Add something hilarious to the message.
        If the template_type is work_anniversary, add the number of years of the work anniversary.
        3 to 4 sentences should be enough.
        The message should be as it follows:
        <Username>
        <Message>
        """

    def generate_template(self, template_type: str):
        if template_type == "birthday":
            return self.google_client.models.generate_content(
                model=self.google_model,
                contents=self.google_system_prompt.format(emojis=EMOJIS, template_type=template_type),
            )
        elif template_type == "work_anniversary":
            return self.google_client.models.generate_content(
                model=self.google_model,
                contents=self.google_system_prompt.format(emojis=EMOJIS, template_type=template_type),
            )
        elif template_type == "birthday_anniversary":
            return self.google_client.models.generate_content(
                model=self.google_model,
                contents=self.google_system_prompt.format(emojis=EMOJIS, template_type=template_type),
            )
        else:
            raise ValueError(f"Invalid template type: {template_type}")
