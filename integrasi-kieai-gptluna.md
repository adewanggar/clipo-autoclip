# Integrasi GPT-5.6 Luna Kie.ai dengan Python

Dokumen ini menjelaskan implementasi langsung GPT-5.6 Luna melalui REST API Kie.ai menggunakan Python. Endpoint yang digunakan adalah `POST https://api.kie.ai/codex/v1/responses`, dengan model `gpt-5-6-luna`; model ini mendukung input teks, gambar, file, reasoning, web search, dan function calling. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

> Catatan: dokumentasi Kie.ai menyebutkan model dan fitur dapat berubah. Pastikan nama model, parameter, harga, dan batas penggunaan tetap sesuai dokumentasi model sebelum deployment produksi. [docs.kie](https://docs.kie.ai/)

## 1. Arsitektur Implementasi

Alur dasarnya:

```text
Python application
        │
        │ HTTPS POST + Bearer API key
        ▼
https://api.kie.ai/codex/v1/responses
        │
        ▼
GPT-5.6 Luna
        │
        ▼
JSON response
        │
        ▼
Extract output_text
```

Berbeda dengan beberapa model generatif Kie.ai yang menggunakan sistem task asynchronous, endpoint GPT-5.6 Luna pada dokumentasi model ditampilkan sebagai response endpoint yang mengembalikan output model dalam response JSON yang sama. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

## 2. Persiapan Project

Buat virtual environment:

```bash
mkdir kie-luna-python
cd kie-luna-python

python -m venv .venv
```

Aktifkan environment.

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependency:

```bash
pip install requests python-dotenv
```

Dependency yang digunakan:

- `requests`: melakukan HTTP request ke Kie.ai.
- `python-dotenv`: membaca API key dari file `.env`.

## 3. Konfigurasi API Key

Buat file `.env`:

```env
KIE_API_KEY=your_kie_api_key_here
```

Jangan commit `.env` ke Git:

```gitignore
.env
.venv/
__pycache__/
```

API key harus dikirim melalui header `Authorization: Bearer <token>`. Kie.ai juga merekomendasikan agar API key tidak pernah diekspos di frontend, aplikasi mobile, repository publik, atau kode yang dikirim ke browser. [docs.kie](https://docs.kie.ai/)

## 4. Request Teks Dasar

Buat file `main.py`:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KIE_API_KEY")
API_URL = "https://api.kie.ai/codex/v1/responses"
MODEL = "gpt-5-6-luna"

if not API_KEY:
    raise RuntimeError("KIE_API_KEY belum diset di environment")

payload = {
    "model": MODEL,
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Jelaskan perbedaan REST API dan GraphQL secara singkat."
                }
            ]
        }
    ],
    "reasoning": {
        "effort": "medium"
    }
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    API_URL,
    headers=headers,
    json=payload,
    timeout=120
)

response.raise_for_status()

data = response.json()
print(data)
```

Jalankan:

```bash
python main.py
```

Struktur request mengikuti format `input` berbentuk array berisi message dengan `role` dan `content`. Untuk input teks, tipe kontennya adalah `input_text`. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

## 5. Mengekstrak Jawaban Model

Response Kie.ai dapat memiliki struktur seperti:

```json
{
  "output": [
    {
      "type": "reasoning",
      "id": "rs_xxx",
      "summary": []
    },
    {
      "type": "message",
      "role": "assistant",
      "id": "msg_xxx",
      "content": [
        {
          "type": "output_text",
          "text": "Jawaban model..."
        }
      ],
      "status": "completed"
    }
  ],
  "usage": {
    "total_tokens": 4490,
    "output_tokens": 47,
    "input_tokens": 4443
  },
  "credits_consumed": 0.48,
  "status": "completed"
}
```

Jangan hanya mengambil `data["output"][0]`, karena item pertama dapat berupa reasoning. Gunakan fungsi ekstraksi yang mencari content bertipe `output_text`:

```python
def extract_text(data: dict) -> str:
    output = data.get("output", [])

    for item in output:
        if item.get("type") != "message":
            continue

        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "")

    return ""
```

Implementasi lengkap:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KIE_API_KEY")
API_URL = "https://api.kie.ai/codex/v1/responses"
MODEL = "gpt-5-6-luna"


def extract_text(data: dict) -> str:
    for item in data.get("output", []):
        if item.get("type") != "message":
            continue

        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "")

    return ""


def ask_luna(prompt: str, reasoning_effort: str = "medium") -> dict:
    if not API_KEY:
        raise RuntimeError("KIE_API_KEY belum diset")

    payload = {
        "model": MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    }
                ]
            }
        ],
        "reasoning": {
            "effort": reasoning_effort
        }
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    if not response.ok:
        raise RuntimeError(
            f"Kie.ai error {response.status_code}: {response.text}"
        )

    data = response.json()
    data["text"] = extract_text(data)
    return data


if __name__ == "__main__":
    result = ask_luna(
        "Buatkan contoh struktur project Python untuk REST API.",
        reasoning_effort="medium"
    )

    print(result["text"])
    print("\nUsage:", result.get("usage"))
    print("Credits:", result.get("credits_consumed"))
```

## 6. Reasoning Effort

GPT-5.6 Luna mendukung pengaturan reasoning effort dari `low` sampai `xhigh`. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

Contoh:

```python
"reasoning": {
    "effort": "low"
}
```

Nilai yang dapat digunakan:

```text
low
medium
high
xhigh
```

Rekomendasi penggunaan:

| Effort   | Kegunaan                                                            |
| -------- | ------------------------------------------------------------------- |
| `low`    | Pertanyaan sederhana, klasifikasi, ekstraksi ringan                 |
| `medium` | Chat umum, coding standar, transformasi teks                        |
| `high`   | Debugging, analisis teknis, perencanaan multi-langkah               |
| `xhigh`  | Reasoning kompleks dan pekerjaan yang membutuhkan analisis mendalam |

Semakin tinggi effort, kemungkinan latency dan konsumsi token/credit juga dapat meningkat. Nilai aktual biaya tetap perlu diperiksa pada halaman pricing Kie.ai karena harga dapat berubah. [docs.kie](https://docs.kie.ai/)

## 7. Percakapan Multi-turn

Kirim histori percakapan di dalam `input`:

```python
payload = {
    "model": MODEL,
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Saya sedang membuat aplikasi Python."
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": "Bagus. Aplikasi tersebut akan digunakan untuk apa?"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Untuk memproses data CSV dan membuat laporan."
                }
            ]
        }
    ],
    "reasoning": {
        "effort": "medium"
    }
}
```

Fungsi reusable:

```python
def ask_with_history(messages: list[dict], reasoning_effort="medium") -> dict:
    payload = {
        "model": MODEL,
        "input": messages,
        "reasoning": {
            "effort": reasoning_effort
        }
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()
    data["text"] = extract_text(data)
    return data
```

Contoh pemakaian:

```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": "Apa fungsi virtual environment di Python?"
            }
        ]
    }
]

result = ask_with_history(messages)
print(result["text"])
```

## 8. Input Gambar

GPT-5.6 Luna mendukung input multimodal yang mencampur teks dan gambar dalam satu message. Gunakan tipe `input_image` dengan URL gambar yang dapat diakses oleh Kie.ai. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

```python
payload = {
    "model": MODEL,
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Analisis isi gambar ini dan jelaskan objek utamanya."
                },
                {
                    "type": "input_image",
                    "image_url": "https://example.com/image.jpg"
                }
            ]
        }
    ],
    "reasoning": {
        "effort": "high"
    }
}
```

Fungsi Python:

```python
def analyze_image(image_url: str, prompt: str) -> dict:
    payload = {
        "model": MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url
                    }
                ]
            }
        ],
        "reasoning": {
            "effort": "high"
        }
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()
    data["text"] = extract_text(data)
    return data
```

Contoh:

```python
result = analyze_image(
    "https://example.com/screenshot.png",
    "Jelaskan error yang terlihat pada screenshot ini."
)

print(result["text"])
```

Gunakan URL publik atau URL signed yang masih valid. Jangan mengirim URL lokal seperti:

```text
http://localhost:8000/image.jpg
```

karena server Kie.ai tidak dapat mengakses komputer lokal Anda.

## 9. Input File

Dokumentasi GPT-5.6 Luna menyebutkan dukungan input file, tetapi format field dan metode upload dapat bergantung pada spesifikasi endpoint yang sedang aktif. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

Pola payload yang dapat digunakan jika dokumentasi endpoint menerima `input_file`:

```python
payload = {
    "model": MODEL,
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Ringkas isi file ini."
                },
                {
                    "type": "input_file",
                    "file_url": "https://example.com/document.pdf"
                }
            ]
        }
    ]
}
```

Namun, jangan mengasumsikan nama field file tanpa memverifikasi dokumentasi model terbaru. Jika API mengharuskan upload terlebih dahulu, gunakan File Upload API Kie.ai untuk mendapatkan URL file, kemudian masukkan URL tersebut ke request model. Daftar dokumentasi Kie.ai memisahkan File Upload API sebagai API tersendiri. [docs.kie](https://docs.kie.ai/llms.txt)

## 10. Web Search

Web search diaktifkan dengan menambahkan tool:

```python
"tools": [
    {
        "type": "web_search"
    }
]
```

Contoh lengkap:

```python
def ask_with_web_search(prompt: str) -> dict:
    payload = {
        "model": MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    }
                ]
            }
        ],
        "tools": [
            {
                "type": "web_search"
            }
        ],
        "reasoning": {
            "effort": "high"
        }
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    data = response.json()
    data["text"] = extract_text(data)
    return data
```

Contoh:

```python
result = ask_with_web_search(
    "Cari perkembangan terbaru framework AI Python dan bandingkan kelebihannya."
)

print(result["text"])
```

Web search dan function calling bersifat mutually exclusive. Dalam satu request, pilih salah satu; jangan mengirim `web_search` dan `function` sekaligus di dalam `tools`. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

## 11. Function Calling

Function calling digunakan agar model dapat menghasilkan instruksi pemanggilan fungsi berdasarkan schema yang Anda berikan.

Contoh definisi function:

```python
tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Mengambil informasi cuaca berdasarkan nama kota.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Nama kota, misalnya Surabaya"
                }
            },
            "required": ["city"],
            "additionalProperties": False
        }
    }
]
```

Payload:

```python
payload = {
    "model": MODEL,
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Bagaimana cuaca di Surabaya?"
                }
            ]
        }
    ],
    "tools": tools,
    "reasoning": {
        "effort": "medium"
    }
}
```

Perlu memeriksa struktur output aktual untuk mengetahui format tool call:

```python
def inspect_output(data: dict) -> None:
    for item in data.get("output", []):
        print(item)
```

Implementasi router sederhana:

```python
import json


def get_weather(city: str) -> dict:
    # Ganti dengan API cuaca Anda sendiri.
    return {
        "city": city,
        "temperature": 30,
        "condition": "Cerah"
    }


def find_function_calls(data: dict) -> list[dict]:
    calls = []

    for item in data.get("output", []):
        item_type = item.get("type", "")

        if item_type in {"function_call", "tool_call"}:
            calls.append(item)

    return calls


def execute_function_call(call: dict) -> dict:
    name = call.get("name")
    raw_arguments = call.get("arguments", "{}")

    if isinstance(raw_arguments, str):
        arguments = json.loads(raw_arguments)
    else:
        arguments = raw_arguments

    if name == "get_weather":
        return get_weather(**arguments)

    raise ValueError(f"Function tidak dikenal: {name}")
```

Pola umum function calling:

```text
1. Kirim prompt + schema function ke model.
2. Periksa apakah output berisi function call.
3. Parse nama function dan argumen.
4. Jalankan function secara lokal.
5. Kirim hasil function kembali ke model.
6. Ambil jawaban final model.
```

Contoh loop konseptual:

```python
def run_agent(initial_messages: list[dict]) -> str:
    messages = list(initial_messages)

    while True:
        payload = {
            "model": MODEL,
            "input": messages,
            "tools": tools,
            "reasoning": {
                "effort": "medium"
            }
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        data = response.json()
        function_calls = find_function_calls(data)

        if not function_calls:
            return extract_text(data)

        messages.extend(data.get("output", []))

        for call in function_calls:
            result = execute_function_call(call)

            messages.append({
                "role": "tool",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }
                ]
            })
```

Format message untuk hasil tool dapat berbeda sesuai implementasi endpoint. Karena itu, lakukan pengujian terhadap response aktual dan sesuaikan item tool result dengan schema resmi Kie.ai yang berlaku. Dokumentasi model hanya menegaskan dukungan function calling serta mutual exclusion dengan web search. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

## 12. Error Handling

Jangan hanya menggunakan `raise_for_status()`. Buat error yang menyimpan HTTP status dan body dari Kie.ai:

```python
class KieAPIError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(
            f"Kie.ai API error {status_code}: {body}"
        )


def post_kie(payload: dict, timeout: int = 120) -> dict:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=timeout
    )

    if not response.ok:
        raise KieAPIError(
            response.status_code,
            response.text
        )

    try:
        return response.json()
    except ValueError as error:
        raise KieAPIError(
            response.status_code,
            "Response bukan JSON valid"
        ) from error
```

Penanganan error berdasarkan status:

```python
import time


def post_with_retry(
    payload: dict,
    retries: int = 3,
    timeout: int = 120
) -> dict:
    for attempt in range(retries):
        try:
            return post_kie(payload, timeout=timeout)

        except KieAPIError as error:
            retryable = error.status_code in {
                408, 409, 429, 500, 502, 503, 504
            }

            if not retryable or attempt == retries - 1:
                raise

            delay = 2 ** attempt
            time.sleep(delay)

        except requests.RequestException:
            if attempt == retries - 1:
                raise

            time.sleep(2 ** attempt)

    raise RuntimeError("Request gagal setelah retry")
```

Interpretasi umum:

| Status        | Kemungkinan penyebab            | Tindakan                                 |
| ------------- | ------------------------------- | ---------------------------------------- |
| `400`         | Payload tidak valid             | Periksa struktur JSON dan nama parameter |
| `401`         | API key salah/tidak ada         | Periksa `.env` dan header Bearer         |
| `403`         | Tidak punya akses ke model/API  | Periksa akun, permission, dan model      |
| `408`         | Request timeout                 | Retry dengan timeout lebih tinggi        |
| `429`         | Rate limit atau credit terbatas | Backoff, batasi concurrency, cek saldo   |
| `500`         | Error server                    | Retry dengan exponential backoff         |
| `502/503/504` | Gangguan gateway atau service   | Retry dan logging                        |

Dokumentasi umum Kie.ai menyebutkan request yang melebihi rate limit dapat menghasilkan HTTP `429`; dokumentasi tersebut juga mencantumkan batas default hingga 20 request baru per 10 detik, tetapi batas aktual dapat berubah berdasarkan akun dan kebijakan layanan. [docs.kie](https://docs.kie.ai/)

## 13. Client Class yang Lebih Rapi

Untuk aplikasi yang lebih besar, bungkus integrasi ke dalam class:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class KieLunaClient:
    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 120
    ):
        self.api_key = api_key or os.getenv("KIE_API_KEY")
        self.timeout = timeout
        self.base_url = "https://api.kie.ai"
        self.endpoint = "/codex/v1/responses"
        self.model = "gpt-5-6-luna"

        if not self.api_key:
            raise ValueError("KIE_API_KEY tidak ditemukan")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _extract_text(self, data: dict) -> str:
        for item in data.get("output", []):
            if item.get("type") != "message":
                continue

            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")

        return ""

    def response(
        self,
        messages: list[dict],
        reasoning_effort: str = "medium",
        tools: list[dict] | None = None
    ) -> dict:
        payload = {
            "model": self.model,
            "input": messages,
            "reasoning": {
                "effort": reasoning_effort
            }
        }

        if tools:
            payload["tools"] = tools

        response = requests.post(
            f"{self.base_url}{self.endpoint}",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout
        )

        if not response.ok:
            raise RuntimeError(
                f"Kie.ai {response.status_code}: {response.text}"
            )

        data = response.json()
        data["text"] = self._extract_text(data)
        return data

    def ask(
        self,
        prompt: str,
        reasoning_effort: str = "medium"
    ) -> str:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    }
                ]
            }
        ]

        result = self.response(
            messages=messages,
            reasoning_effort=reasoning_effort
        )

        return result["text"]

    def analyze_image(
        self,
        image_url: str,
        prompt: str,
        reasoning_effort: str = "high"
    ) -> str:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url
                    }
                ]
            }
        ]

        result = self.response(
            messages=messages,
            reasoning_effort=reasoning_effort
        )

        return result["text"]
```

Pemakaian:

```python
client = KieLunaClient()

answer = client.ask(
    "Buatkan fungsi Python untuk membaca file CSV.",
    reasoning_effort="medium"
)

print(answer)
```

Analisis gambar:

```python
analysis = client.analyze_image(
    image_url="https://example.com/error.png",
    prompt="Identifikasi error pada screenshot ini."
)

print(analysis)
```

## 14. Output Terstruktur

Jika aplikasi membutuhkan JSON, jangan langsung menganggap jawaban model selalu JSON valid. Instruksikan format dengan jelas:

```python
prompt = """
Analisis data berikut dan kembalikan JSON valid tanpa markdown.

Data:
- nama: Andi
- umur: 29
- pekerjaan: developer

Schema:
{
  "name": "string",
  "age": "number",
  "occupation": "string"
}
"""
```

Parse hasilnya:

```python
import json

result = client.ask(prompt)

try:
    parsed = json.loads(result)
except json.JSONDecodeError as error:
    raise ValueError(
        f"Model tidak mengembalikan JSON valid: {result}"
    ) from error

print(parsed["name"])
```

Untuk produksi, tambahkan validasi schema menggunakan Pydantic:

```bash
pip install pydantic
```

```python
from pydantic import BaseModel


class Person(BaseModel):
    name: str
    age: int
    occupation: str


person = Person.model_validate(parsed)
print(person)
```

## 15. Streaming

Dokumentasi halaman GPT-5.6 Luna yang tersedia mendeskripsikan endpoint response biasa dan tidak menampilkan parameter streaming pada contoh request tersebut. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

Karena itu, jangan mengasumsikan `stream=True` sudah didukung hanya berdasarkan format API. Jika streaming tersedia pada akun atau endpoint Anda, konfirmasi format event dari dokumentasi terbaru sebelum mengimplementasikannya.

Implementasi non-streaming yang aman:

```python
response = requests.post(
    API_URL,
    headers=headers,
    json=payload,
    timeout=120
)

data = response.json()
text = extract_text(data)
```

## 16. Logging dan Monitoring

Catat metadata, bukan API key:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)


def log_usage(data: dict) -> None:
    usage = data.get("usage", {})

    logger.info(
        "KIE request completed: status=%s input_tokens=%s "
        "output_tokens=%s total_tokens=%s credits=%s",
        data.get("status"),
        usage.get("input_tokens"),
        usage.get("output_tokens"),
        usage.get("total_tokens"),
        data.get("credits_consumed")
    )
```

Pemakaian:

```python
result = client.response(messages)

log_usage(result)
print(result["text"])
```

Kie.ai menampilkan penggunaan token, status, dan credit consumption pada response contoh GPT-5.6 Luna. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)

Jangan log:

```python
logger.info("API key: %s", API_KEY)
```

Jangan juga menyimpan prompt sensitif tanpa kebutuhan yang jelas.

## 17. Membuat REST API Lokal dengan FastAPI

Jika GPT-5.6 Luna digunakan oleh aplikasi React, Vue, Telegram bot, atau layanan lain, API key tetap harus berada di backend Python.

Install:

```bash
pip install fastapi uvicorn
```

Buat `app.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from main import KieLunaClient

app = FastAPI()
client = KieLunaClient()


class ChatRequest(BaseModel):
    prompt: str
    reasoning_effort: str = "medium"


class ChatResponse(BaseModel):
    text: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        text = client.ask(
            prompt=request.prompt,
            reasoning_effort=request.reasoning_effort
        )

        return ChatResponse(text=text)

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        ) from error
```

Jalankan:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Request dari Python client lain:

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "prompt": "Jelaskan dependency injection.",
        "reasoning_effort": "medium"
    },
    timeout=120
)

response.raise_for_status()
print(response.json()["text"])
```

Arsitektur ini lebih aman daripada memanggil Kie.ai langsung dari frontend:

```text
Frontend / Telegram bot
          │
          ▼
Python backend Anda
          │
          ▼
Kie.ai GPT-5.6 Luna
```

## 18. Testing

Buat `test_client.py`:

```python
from unittest.mock import Mock, patch

from main import KieLunaClient


def test_extract_text():
    client = KieLunaClient(api_key="test-key")

    data = {
        "output": [
            {
                "type": "reasoning",
                "summary": []
            },
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": "Jawaban test"
                    }
                ]
            }
        ]
    }

    assert client._extract_text(data) == "Jawaban test"


@patch("main.requests.post")
def test_ask(mock_post):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": "Hello"
                    }
                ]
            }
        ]
    }

    mock_post.return_value = mock_response

    client = KieLunaClient(api_key="test-key")
    result = client.ask("Say hello")

    assert result == "Hello"

    mock_post.assert_called_once()
    request_payload = mock_post.call_args.kwargs["json"]

    assert request_payload["model"] == "gpt-5-6-luna"
```

Jalankan:

```bash
pip install pytest
pytest -q
```

## 19. Checklist Production

Sebelum deployment:

- Simpan API key di environment variable atau secret manager.
- Jangan expose API key di frontend.
- Validasi semua input dari user.
- Gunakan timeout.
- Implementasikan retry hanya untuk error yang retryable.
- Tangani HTTP `429`.
- Batasi ukuran prompt dan file.
- Simpan `usage` dan `credits_consumed` untuk monitoring biaya.
- Jangan mencatat API key ke log.
- Pisahkan web search dan function calling.
- Validasi JSON output sebelum diproses aplikasi.
- Gunakan backend sebagai proxy untuk frontend.
- Periksa pricing dan credit sebelum menjalankan request dalam jumlah besar.
- Simpan hasil penting di storage sendiri karena dokumentasi Kie.ai menyebutkan file hasil memiliki masa penyimpanan terbatas, termasuk media yang disebut disimpan selama 14 hari. [docs.kie](https://docs.kie.ai/)
- Uji kembali payload setelah Kie.ai memperbarui dokumentasi model.

## 20. Versi Minimal Siap Pakai

Jika hanya membutuhkan implementasi sederhana, gunakan kode berikut:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("KIE_API_KEY")

payload = {
    "model": "gpt-5-6-luna",
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Buatkan contoh kode Python untuk membaca JSON."
                }
            ]
        }
    ],
    "reasoning": {
        "effort": "medium"
    }
}

response = requests.post(
    "https://api.kie.ai/codex/v1/responses",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json=payload,
    timeout=120
)

response.raise_for_status()
data = response.json()

for item in data.get("output", []):
    if item.get("type") == "message":
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                print(content["text"])
```

Implementasi inti hanya membutuhkan tiga bagian: API key pada header Bearer, payload dengan model `gpt-5-6-luna`, dan ekstraksi `output_text` dari response. Endpoint, struktur input, reasoning, multimodal input, web search, dan function calling mengikuti dokumentasi model Kie.ai. [docs.kie](https://docs.kie.ai/market/chat/gpt-5-6-luna)
