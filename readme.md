## ChatGPT 3.5 Web API for Free
no code need change, just change proxy, and you can use it for free.
### Introduction
This project allows you to use the ChatGPT 3.5 API for free by simply changing the proxy settings. It supports additional features like adding cookies for GPT-4 access and more.

### Features
- [ ] Add cookies to use GPT-4
- [ ] Add more models for free, like GPT-4o

### Installing
#### PC/Server
1. Install Python 3.9.19+
2. Clone this repository
   ```bash
   git clone https://github.com/datehoer/i_need_chat_with_gpt.git
   ```
3. Install requirements
   ```bash
    pip install -r requirements.txt
    ```
4. Run the server
   ```bash
    uvicorn app:app --host 0.0.0.0 --port 8000
   ```
5. Post your text to `http://127.0.0.1:8000/chat_with_gpt/`

### Usage Examples
Python Example:
```python
import requests

res = requests.post("http://127.0.0.1:8000/chat_with_gpt/", json={
    "message": "hello?",
    "proxies": {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
})
print(res.text)
# If you want remember the history, you need send remember_history: true
```
Response:
```json
{
    "message": "Hey there! What's up?",
    "code": 1
}
```
