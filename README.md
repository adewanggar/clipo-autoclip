# 🎬 Clipo - Auto-clip, auto-viral

[![Instagram](https://img.shields.io/badge/Instagram-%23E4405F.svg?style=for-the-badge&logo=Instagram&logoColor=white)](https://www.instagram.com/alfansyahdr_)
[![Open in Colab](https://img.shields.io/badge/Open%20in%20Colab-%23F9AB00.svg?style=for-the-badge&logo=googlecolab&logoColor=white)](https://colab.research.google.com/)

**Alternatif Open-Source 100% Gratis, Lokal, dan Tanpa Batas untuk Opus Clip & Vidyo.ai**  
*Dibuat oleh: **adewanggar** (Instagram: [**@alfansyahdr_**](https://www.instagram.com/alfansyahdr_))*

Transformasikan video panjang YouTube menjadi klip pendek viral yang dioptimalkan untuk **TikTok, Instagram Reels, dan YouTube Shorts** – dilengkapi dengan AI canggih, subtitle animasi dinamis (Gaya Alex Hormozi), pelacakan wajah (*face tracking*), split-screen 2 orang otomatis, dan terjemahan instan.

[🇮🇩 Bahasa Indonesia](README.md) • [🇬🇧 English](README_en.md)

---

## ⚡ Mengapa Clipo?

Lupakan langganan mahal dan batasan kuota menit. Clipo memberikan kebebasan tanpa batas langsung di komputer Anda atau di Google Colab.

| Fitur | Clipo (Open-Source) | Opus Clip / Klap / Munch (SaaS Berbayar) |
| :--- | :--- | :--- |
| **Harga** | **100% Gratis & Tanpa Batas** | $20–$100/bulan + dibatasi menit |
| **Privasi** | **100% Aman/Lokal** (Data di tangan Anda) | Video diunggah ke cloud pihak ketiga |
| **Pilihan AI** | **Fleksibel**: Kie.ai (GPT Luna), Gemini, **Local GGUF (Offline)** | Terbatas pada model bawaan mereka |
| **Face Tracking** | **Split Screen (2 Wajah)**, Active Speaker, Auto-Crop 9:16 | Fitur dasar / biaya tambahan |
| **Terjemahan** | **Ya** (Mendukung 10+ bahasa) | Sangat terbatas |
| **Export Editing** | **Export XML ke Premiere Pro** (Beta) | Editor web terbatas |
| **Watermark** | **TIDAK ADA WATERMARK** | Ada (pada versi gratis SaaS) |

---

## 🚀 Fitur Utama

- 🤖 **Pemotong AI Viral Otomatis**: Mendeteksi hook & momen paling berpotensi viral menggunakan **Kie.ai (GPT-5.6 Luna)**, **Google Gemini**, **GPT-4**, atau **Model Lokal Offline (Llama 3, DeepSeek, dll)**.
- 🗣️ **Transkripsi Ultra-Presisi**: Ditenagai oleh **WhisperX** dengan akselerasi GPU untuk sinkronisasi subtitle kata-per-kata yang akurat.
- 🎨 **Subtitle Dinamis (Gaya Hormozi)**: Highlight animasi per kata, warna cerah yang dapat disesuaikan, emoji otomatis, dan font modern.
- 🎥 **Sistem Kamera & Layout Cerdas**:
  - **Auto-Crop 9:16**: Mengubah video landscape menjadi format vertikal sambil menjaga wajah tetap di tengah.
  - **Smart Split Screen**: Mendeteksi 2 orang yang sedang berdialog dan membagi layar secara otomatis.
  - **Active Speaker (Eksperimental)**: Kamera beralih otomatis ke orang yang sedang berbicara.
- 🌍 **Penerjemah Video Otomatis**: Buat subtitle terjemahan otomatis (contoh: Video Bahasa Inggris ➔ Subtitle Bahasa Indonesia).
- ⚡ **Instalasi Super Cepat**: Menggunakan package manager `uv` modern.
- 🖥️ **WebUI Modern**: Tampilan antarmuka Gradio yang elegan, Mode Gelap, Galeria Proyek, dan Editor Subtitle terintegrasi.

---

## ☁️ Menjalankan di Google Colab (Tanpa Perlu PC Spek Tinggi)

Jika komputer Anda tidak memiliki GPU NVIDIA, Anda bisa menjalankannya secara gratis di **Google Colab**:

1. Buka [Google Colab](https://colab.research.google.com/) dan unggah file [`ViralCutter.ipynb`](ViralCutter.ipynb).
2. Aktifkan GPU: Klik **Runtime** ➔ **Change runtime type** ➔ Pilih **T4 GPU** ➔ **Save**.
3. Jalankan **Langkah 1 (Instalasi)**: Tunggu sekitar 2-4 menit hingga semua dependensi selesai disiapkan.
4. Jalankan **Langkah 2 (Konfigurasi API & Mulai WebUI)**: Masukkan API Key Kie.ai atau Gemini di form, lalu klik Play. Buka link publik `https://xxxx.gradio.live` yang muncul.
5. Jalankan **Langkah 3 (Download Hasil)**: Untuk mendownload semua hasil klip video dalam format `.zip` langsung ke komputer Anda.

---

## 💻 Instalasi Lokal (Windows)

### 1. Prasyarat Sistem
- **OS**: Windows 10 / 11 (64-bit)
- **Python**: Python 3.10.x atau 3.11.x (Centang *"Add Python to PATH"* saat instalasi)
- **GPU**: NVIDIA GPU direkomendasikan (dengan Driver CUDA terbaru)
- **FFmpeg**: Instal via terminal administrator: `winget install ffmpeg`
- **Visual Studio C++ Build Tools**: Diperlukan untuk kompilasi *InsightFace* ([Download Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/))

### 2. Langkah Instalasi
1. Clone atau ekstrak repository ini ke komputer Anda.
2. Jalankan salah satu file installer:
   - `install_dependencies.bat` : **Instalasi Standar** (Direkomendasikan - menggunakan Kie.ai / Gemini / OpenAI via API).
   - `install_dependencies_advanced_LocalLLM.bat` : **Instalasi Offline/Lokal LLM** (Untuk menjalankan Llama 3 / GGUF offline di PC).
3. Jalankan `run_webui.bat` untuk membuka antarmuka Clipo di browser Anda.

---

## 🔑 Konfigurasi API (Opsional untuk AI Cut Otomatis)
- **Kie.ai (GPT Luna)**: Masukkan API Key Kie.ai di WebUI atau di file `api_config.json`.
- **Google Gemini (Gratis)**: Dapatkan API Key gratis di [Google AI Studio](https://aistudio.google.com/) dan masukkan ke WebUI atau di file `api_config.json`.
- **Model GGUF Lokal**: Masukkan file model `.gguf` ke folder `models/`, sistem akan mendeteksinya secara otomatis.

---

## 👨‍💻 Pengembang & Kontak

- **Pengembang**: **adewanggar**
- **Instagram**: [**@alfansyahdr_**](https://www.instagram.com/alfansyahdr_)
- **Lisensi**: Open Source (GPL-3.0 License)

*Clipo: Auto-clip, auto-viral. Karena konten viral berkualitas tidak harus mahal.* 🚀
