from curl_cffi import requests
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from pydantic import BaseModel
from hashlib import sha3_512
import uuid
import base64
import json
import re
import random


app = FastAPI()
init_headers = {
    "Accept": "text/event-stream",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://chat.openai.com",
    "Referer": "https://chat.openai.com/",
    "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Oai-Language": "en-US",
}


class ProofWorker:
    def __init__(self, difficulty=None, required=False, seed=None):
        self.difficulty = difficulty
        self.required = required
        self.seed = seed
        self.proof_token_prefix = "gAAAAABwQ8Lk5FbGpA2NcR9dShT6gYjU7VxZ4D"
        self.proof_token = None

    @staticmethod
    def get_parse_time():
        now = datetime.now()
        tz = timezone(timedelta(hours=8))
        now = now.astimezone(tz)
        time_format = "%a %b %d %Y %H:%M:%S"
        return now.strftime(time_format) + " GMT+0800 (中国标准时间)"

    def get_config(self, openai_get_headers):
        cores = [8, 12, 16, 24]
        core = random.choice(cores)
        screens = [3000, 4000, 6000]
        screen = random.choice(screens)
        return [
            str(core) + str(screen),
            self.get_parse_time(),
            4294705152,
            0,
            openai_get_headers,
        ]

    def calc_proof_token(self, seed: str, difficulty: str, openai_get_headers: str):
        config = self.get_config(openai_get_headers)
        diff_len = len(difficulty) // 2
        for i in range(100000):
            config[3] = i
            json_str = json.dumps(config)
            base = base64.b64encode(json_str.encode()).decode()
            hasher = sha3_512()
            hasher.update((seed + base).encode())
            hash_hex = hasher.digest().hex()
            if hash_hex[:diff_len] <= difficulty:
                return "gAAAAAB" + base
        self.proof_token = (self.proof_token_prefix + base64.b64encode(seed.encode()).decode())
        return self.proof_token


class ChatGpt:
    def __init__(self, headers=None, proxies=None):
        self.headers = headers
        self.init_url = "https://chat.openai.com/?model=text-davinci-002-render-sha"
        self.sess = requests.Session()
        self.proxies = proxies
        self.sess.get(self.init_url, headers=self.headers, proxies=self.proxies)
        self.proof_worker = ProofWorker()
        self.chat_requirements_url = "https://chat.openai.com/backend-anon/sentinel/chat-requirements"
        self.chat_url = "https://chat.openai.com/backend-anon/conversation"
        self.parent_id = None
        self.conversation_id = None

    def send_message(self, message, parent_message_id=None, conversation_id=None, retry_count=5):
        err = retry_count
        while err > 0:
            try:
                requirements = self.sess.post(self.chat_requirements_url, json={}, headers=self.headers, proxies=self.proxies).json()
                token = requirements['token']
                proofofwork = requirements['proofofwork']
                proof_token = self.proof_worker.calc_proof_token(proofofwork['seed'], proofofwork['difficulty'], self.headers['User-Agent'])
                self.headers['Openai-Sentinel-Chat-Requirements-Token'] = token
                self.headers['Openai-Sentinel-Proof-Token'] = proof_token
                data = {
                    "action": "next",
                    "messages": [{
                        "id": str(uuid.uuid4()),
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": [message]},
                        "metadata": {}
                    }],
                    "parent_message_id": parent_message_id if parent_message_id else str(uuid.uuid4()),
                    "model": "text-davinci-002-render-sha",
                    "timezone_offset_min": -480,
                    "suggestions": [],
                    "history_and_training_disabled": False,
                    "conversation_mode": {"kind": "primary_assistant"},
                    "force_paragen": False,
                    "force_paragen_model_slug": "",
                    "force_nulligen": False,
                    "force_rate_limit": False,
                    "websocket_request_id": str(uuid.uuid4())
                }
                if conversation_id:
                    data['conversation_id'] = conversation_id
                response = self.sess.post(self.chat_url, headers=self.headers, json=data, proxies=self.proxies)
                res = json.loads(re.findall("data: ({.*?})\n", response.text, re.S)[-1])
                return True, res
            except Exception as e:
                err -= 1
        return False, "Maybe your proxy is blocked.Please change another proxy."

    def chat(self, message, remember_history=False, retry_count=5):
        if remember_history:
            if self.parent_id and self.conversation_id:
                status, res = self.send_message(
                    message,
                    parent_message_id=self.parent_id,
                    conversation_id=self.conversation_id,
                    retry_count=retry_count
                )
            else:
                status, res = self.send_message(message, retry_count=retry_count)
        else:
            status, res = self.send_message(message, retry_count)
        if status:
            self.parent_id = res['message']['id']
            self.conversation_id = res['conversation_id']
            content = res['message']['content']['parts'][0]
            return True, content
        else:
            return False, res


class ChatItem(BaseModel):
    message: str
    remember_history: bool = False
    headers: dict = None
    proxies: dict = None
    retry_count: int = 5


@app.post("/chat_with_gpt/")
def chat_with_gpt(chat_item: ChatItem):
    headers = chat_item.headers
    proxies = chat_item.proxies
    message = chat_item.message
    remember_history = chat_item.remember_history
    retry_count = chat_item.retry_count
    chatgpt = ChatGpt(headers if headers else init_headers, proxies)
    status, reply_msg = chatgpt.chat(message, remember_history, retry_count)
    code = 0
    if status:
        code = 1
    return {"message": reply_msg, "code": code}