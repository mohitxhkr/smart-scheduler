import os
import requests

def generate_response(prompt):
    # api_key = os.getenv("OPENROUTER_API_KEY")
    # if not api_key:
    #     return "OpenRouter API key is missing. Please set OPENROUTER_API_KEY environment variable."

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that schedules meetings using Google Calendar. "
                    "When the user provides time information, extract and reflect it clearly in your response. "
                    "Stick to natural and helpful language."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        json_resp = response.json()

        if "choices" in json_resp and json_resp["choices"]:
            return json_resp["choices"][0]["message"]["content"]
        else:
            return "Sorry, I received an empty response from the language model."

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.ConnectionError:
        return "Connection error: Please check your internet connection."
    except requests.exceptions.Timeout:
        return "Request timed out. Please try again."
    except Exception as e:
        return f"Unexpected error: {str(e)}"
