import os
import requests

def generate_response(prompt):
    api_key = os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that schedules meetings using Google Calendar. Respond with natural language and include date and time if you can extract it from the user input."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        json_resp = response.json()
        if "choices" in json_resp and json_resp["choices"]:
            return json_resp['choices'][0]['message']['content']
        else:
            return "Sorry, I received an unexpected response from the language model."
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.ConnectionError:
        return "Connection error: Please check your internet connection."
    except requests.exceptions.Timeout:
        return "Request timed out. Please try again."
    except Exception as e:
        return f"Unexpected error: {str(e)}"
