# 🎬 Clipo - Auto-clip, auto-viral

[![Instagram](https://img.shields.io/badge/Instagram-%23E4405F.svg?style=for-the-badge&logo=Instagram&logoColor=white)](https://www.instagram.com/alfansyahdr_)
[![Open in Colab](https://img.shields.io/badge/Open%20in%20Colab-%23F9AB00.svg?style=for-the-badge&logo=googlecolab&logoColor=white)](https://colab.research.google.com/)

**100% Free, Local, and Unlimited Open-Source Alternative to Opus Clip & Vidyo.ai**  
*Created by: **adewanggar** (Instagram: [**@alfansyahdr_**](https://www.instagram.com/alfansyahdr_))*

Turn long YouTube videos into viral shorts optimized for **TikTok, Instagram Reels, and YouTube Shorts** – with cutting-edge AI, dynamic animated captions (Alex Hormozi style), precise *face tracking*, automatic 2-person split screen, and instant multi-language translation.

[🇮🇩 Bahasa Indonesia](README.md) • [🇬🇧 English](README_en.md)

---

## ⚡ Why Clipo?

Forget expensive subscriptions and minute limits. Clipo provides unlimited creative power running directly on your machine or on Google Colab.

| Feature | Clipo (Open-Source) | Opus Clip / Klap / Munch (SaaS) |
| :--- | :--- | :--- |
| **Price** | **100% Free & Unlimited** | $20–$100/month + strict minute limits |
| **Privacy** | **100% Local / Safe** (Your data stays yours) | Uploaded to 3rd-party clouds |
| **AI Options** | **Flexible**: Kie.ai (GPT Luna), Gemini, **Local GGUF (Offline)** | Limited to vendor defaults |
| **Face Tracking** | **Split Screen (2 Faces)**, Active Speaker, Auto 9:16 Crop | Basic or extra tier cost |
| **Translation** | **Yes** (Supports 10+ languages) | Limited |
| **Export Editing** | **Export XML to Premiere Pro** (Beta) | Basic web editor |
| **Watermark** | **ZERO WATERMARK** | Present on free SaaS tiers |

---

## 🚀 Key Features

- 🤖 **AI Viral Cut**: Automatically identifies viral hooks and highlights using **Kie.ai (GPT-5.6 Luna)**, **Google Gemini**, **GPT-4**, or **Local Offline LLMs (Llama 3, DeepSeek, etc.)**.
- 🗣️ **Ultra-Precise Transcription**: Powered by **WhisperX** with GPU acceleration for perfect word-by-word subtitle alignment.
- 🎨 **Dynamic Captions**: Alex Hormozi style animated highlights, customizable color schemes, auto-emojis, and modern typography.
- 🎥 **Smart Framing & Layouts**:
  - **Auto-Crop 9:16**: Adapts landscape videos to vertical mode while keeping faces centered.
  - **Smart Split Screen**: Detects 2-person dialogues and splits the screen automatically.
  - **Active Speaker (Experimental)**: Automatically shifts focus to the person speaking.
- 🌍 **Automatic Video Translation**: Generate translated subtitles instantly (e.g. English Audio ➔ Indonesian / Portuguese / Spanish subtitles).
- ⚡ **Ultra-Fast Setup**: Powered by the modern `uv` Python package manager.
- 🖥️ **Modern WebUI**: Clean Gradio interface, Dark Mode, Project Gallery, and integrated Subtitle Editor.

---

## ☁️ Running on Google Colab (No GPU PC Required)

If your local PC doesn't have an NVIDIA GPU, you can run Clipo for free on **Google Colab**:

1. Open [Google Colab](https://colab.research.google.com/) and upload [`ViralCutter.ipynb`](ViralCutter.ipynb).
2. Enable GPU: Click **Runtime** ➔ **Change runtime type** ➔ Select **T4 GPU** ➔ **Save**.
3. Run **Step 1 (Installation)**: Takes ~2-4 minutes to configure all dependencies.
4. Run **Step 2 (API Config & Start WebUI)**: Provide Kie.ai or Gemini API Key, then click Play. Open the public link (`https://xxxx.gradio.live`).
5. Run **Step 3 (Download Results)**: Download all rendered clips as a `.zip` file directly to your PC.

---

## 💻 Local Installation (Windows)

### 1. Prerequisites
- **OS**: Windows 10 / 11 (64-bit)
- **Python**: Python 3.10.x or 3.11.x (Ensure *"Add Python to PATH"* is checked)
- **GPU**: NVIDIA GPU recommended (with updated CUDA drivers)
- **FFmpeg**: Install via Administrator terminal: `winget install ffmpeg`
- **Visual Studio C++ Build Tools**: Required for *InsightFace* compilation ([Download Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/))

### 2. Installation Steps
1. Clone or extract this repository to your computer.
2. Run one of the installer scripts:
   - `install_dependencies.bat` : **Standard Installation** (Recommended - uses Kie.ai / Gemini / OpenAI API).
   - `install_dependencies_advanced_LocalLLM.bat` : **Offline/Local LLM Installation** (To run Llama 3 / GGUF offline).
3. Run `run_webui.bat` to launch the Clipo WebUI in your default browser.

---

## 🔑 AI API Configuration (Optional)
- **Kie.ai (GPT Luna)**: Enter your API key in the WebUI or inside `api_config.json`.
- **Google Gemini (Free)**: Obtain a free API key at [Google AI Studio](https://aistudio.google.com/) and input it in the WebUI or inside `api_config.json`.
- **Local GGUF Models**: Place `.gguf` model files into the `models/` directory; the system will detect them automatically.

---

## 👨‍💻 Developer & Contact

- **Creator / Developer**: **adewanggar**
- **Instagram**: [**@alfansyahdr_**](https://www.instagram.com/alfansyahdr_)
- **License**: Open Source (GPL-3.0 License)

*Clipo: Auto-clip, auto-viral. Because viral content shouldn't cost a fortune.* 🚀
