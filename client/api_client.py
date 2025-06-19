import requests

def send_text_to_server(user_text):
    url = "http://127.0.0.1:5001/api/dispatch"
    payload = {
        "source": "frontend",
        "text": user_text
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
