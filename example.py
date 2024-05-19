import requests

res = requests.post("http://127.0.0.1:8000/chat_with_gpt/", json={
    "message": "hello?",
    "proxies": {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
})
print(res.text)
