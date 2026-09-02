from google import genai

client = genai.Client(api_key="AQ.Ab8RN6I4PnLoF1Kw3XB5pv_Qb4czOjB_WXAE8XzXosG1St_9Uw")

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Hello Gemini! Say hello to Vision AI."
)

print(response.text)