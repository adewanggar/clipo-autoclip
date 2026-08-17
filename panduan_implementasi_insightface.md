# Panduan Lengkap Implementasi InsightFace untuk Project Video Clipper AI

Dokumen ini adalah panduan teknis, modular, dan arsitektur umum mengenai cara mengimplementasikan **InsightFace** untuk kebutuhan **Smart Cropping (16:9 ke 9:16 / Shorts / Reels / TikTok)**, **Face Tracking**, **Active Speaker Detection**, dan **Cinematic Smoothing**.

Panduan ini dirancang **agnostik terhadap project** (modular) agar dapat langsung diadaptasi ke repositori seperti ViralCutter maupun project video editor/clipper AI lainnya (MoviePy, PyAV, FFmpeg, OpenCV, FastVideo, dll).

---

## 1. Mengapa Memilih InsightFace?

Dalam project pembuatan klip otomatis (seperti OpusClip, AutoCut, ViralCutter), kualitas pemotongan video sangat bergantung pada seberapa presisi sistem mendeteksi dan melacak wajah pembicara.

### Perbandingan dengan Engine Lain:
| Fitur | InsightFace (Buffalo_L) | MediaPipe | YOLOv8-Face | OpenCV Haar/DNN |
| :--- | :--- | :--- | :--- | :--- |
| **Akurasi Sudut Ekstrem (Profil/Samping)** | ⭐⭐⭐⭐⭐ (Sangat Tinggi) | ⭐⭐⭐ (Sedang) | ⭐⭐⭐⭐ (Tinggi) | ⭐⭐ (Rendah) |
| **Face Re-ID (512-d Embedding)** | ✅ Built-in (ArcFace) | ❌ Tidak ada | ❌ Perlu model tambahan | ❌ Tidak ada |
| **Landmark Presisi (Bibir, Mata, Pose)** | ✅ 5-KPS / 106-Point / 68-3D | ✅ 468-Mesh | ⚠️ Hanya 5-KPS | ❌ Tidak ada |
| **Akselerasi GPU (CUDA/TensorRT)** | ✅ Sangat Cepat via ONNX | ⚠️ Terbatas pada CPU/Web | ✅ Sangat Cepat | ⚠️ Terbatas |
| **Konsistensi Pelacakan Identitas** | ⭐⭐⭐⭐⭐ (Cosine Similarity) | ⭐⭐ (Sering tertukar) | ⭐⭐⭐ (Perlu DeepSORT) | ⭐ (Tidak stabil) |

> **Kelebihan Utama InsightFace:** Dengan fitur **Face Embedding** bawaan, Anda dapat mengenali pembicara utama sepanjang durasi video meskipun pembicara sempat menoleh ke samping, tertutup objek (occlusion), atau berpindah posisi.

---

## 2. Arsitektur Pipeline Video Clipper

Berikut adalah alur standar sistem smart-cropping berbasis AI:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Input Video (16:9)                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Frame Sampling & Pre-processing                   │
│  - Ekstraksi frame (Full FPS atau Keyframe misal tiap 3-5f) │
│  - Resize frame ke resolusi deteksi (misal 640x360)         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: InsightFace Analysis                              │
│  - Deteksi Bounding Box [x1, y1, x2, y2]                    │
│  - Ekstraksi Facial Landmarks (106 / 68 point)              │
│  - Ekstraksi Face Embedding (512-dim vector)                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Tracking, Re-ID & Active Speaker Detection        │
│  - Cocokkan wajah antar frame (Cosine Similarity Embedding) │
│  - Hitung rasio bukaan bibir (Lip-Opening Distance)         │
│  - Tentukan Target Utama (Single Speaker / Split-Screen)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 4: Camera Interpolation & Smoothing                  │
│  - Terapkan Deadzone Margin (kamera tidak bergetar)         │
│  - Interpolasi EMA / Kalman Filter untuk pergerakan halus   │
│  - Rule of Thirds (posisi mata di ~30-35% bagian atas)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 5: Rendering & Export (9:16 Vertical)                │
│  - Dynamic Crop & Resize ke 1080x1920                       │
│  - Audio Remuxing & Subtitle Burning                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Instalasi & Persiapan Dependency

### 3.1. Prasyarat Environment
- **Python**: 3.9 - 3.11 (Direkomendasikan 3.10 atau 3.11).
- **C++ Build Tools**: Diperlukan di Windows untuk kompilasi beberapa dependensi InsightFace (Microsoft Visual C++ Build Tools).

### 3.2. Instalasi Paket

#### Untuk Pengguna GPU (NVIDIA CUDA):
```bash
pip install numpy opencv-python scipy
pip install onnxruntime-gpu
pip install insightface
```

#### Untuk Pengguna CPU:
```bash
pip install numpy opencv-python scipy
pip install onnxruntime
pip install insightface
```

### 3.3. Model Zoo InsightFace
Secara default, InsightFace akan mendownload model otomatis ke `~/.insightface/models/` pada pemanggilan pertama.

Model-model populer:
1. **`buffalo_l`** (Rekomendasi Utama): Kualitas tertinggi, akurasi deteksi dan embedding sangat tajam.
2. **`buffalo_m` / `buffalo_sc`**: Versi ringan jika sumber daya CPU terbatas.
3. **`antelopev2`**: Model premium dengan akurasi landmark dan embedding ekstra tinggi.

---

## 4. Konsep Kunci Implementasi

### 4.1. Inisialisasi Engine (Dengan Redirection Log C++)
InsightFace dan ONNX Runtime sering mencetak banyak output log debug C++. Sebaiknya bungkus inisialisasi dengan context manager peredam output.

```python
import os
import sys
import warnings
from contextlib import contextmanager
from insightface.app import FaceAnalysis

warnings.filterwarnings("ignore")

@contextmanager
def suppress_stdout_stderr():
    with open(os.devnull, "w") as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

def init_face_analyzer(model_name="buffalo_l", ctx_id=0, det_size=(640, 640)):
    """
    ctx_id: 0 untuk GPU CUDA pertama, -1 untuk CPU.
    """
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if ctx_id >= 0 else ['CPUExecutionProvider']
    
    with suppress_stdout_stderr():
        app = FaceAnalysis(name=model_name, providers=providers)
        app.prepare(ctx_id=ctx_id, det_size=det_size)
    return app
```

---

### 4.2. Ekstraksi Data Wajah dari Frame
Setiap kali `app.get(frame)` dipanggil, InsightFace mengembalikan daftar objek wajah dengan atribut:
- `bbox`: Array `[x1, y1, x2, y2]` batas wajah.
- `kps`: 5 titik kunci utama (Mata Kiri, Mata Kanan, Hidung, Sudut Kiri Mulut, Sudut Kanan Mulut).
- `det_score`: Nilai confidence score deteksi (0.0 - 1.0).
- `embedding`: Vektor fitur 512 dimensi (Representasi sidik wajah numerik).
- `landmark_2d_106` / `landmark_3d_68`: Titik kontur detail (jika model mendukung).

```python
def extract_face_data(app, frame_bgr):
    faces = app.get(frame_bgr)
    extracted = []
    
    for face in faces:
        if face.det_score < 0.6:  # Filter false positive
            continue
            
        data = {
            "bbox": face.bbox.astype(int).tolist(),       # [x1, y1, x2, y2]
            "score": float(face.det_score),
            "kps": face.kps.tolist() if face.kps is not None else None,
            "embedding": face.embedding,                  # 512-D numpy array
            "landmarks_106": getattr(face, "landmark_2d_106", None)
        }
        extracted.append(data)
    return extracted
```

---

### 4.3. Face Re-Identification & Tracking (Cosine Similarity)
Di video dengan banyak orang atau pergantian angle kamera, kita perlu mengenali apakah wajah di frame $N$ sama dengan wajah di frame $N-1$.

Rumus Cosine Similarity:
$$\text{Similarity}(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$

```python
import numpy as np

def compute_similarity(emb1, emb2):
    """Menghitung Cosine Similarity antara dua embedding wajah."""
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(emb1, emb2) / (norm1 * norm2)

class SpeakerTracker:
    def __init__(self, similarity_threshold=0.55):
        self.known_speakers = {}  # {speaker_id: average_embedding}
        self.similarity_threshold = similarity_threshold
        self.next_id = 0

    def match_or_register(self, embedding):
        best_id = None
        best_score = -1.0

        for s_id, s_emb in self.known_speakers.items():
            sim = compute_similarity(embedding, s_emb)
            if sim > best_score:
                best_score = sim
                best_id = s_id

        if best_score >= self.similarity_threshold:
            # Update embedding dengan moving average (adaptif terhadap perubahan pose/cahaya)
            self.known_speakers[best_id] = 0.9 * self.known_speakers[best_id] + 0.1 * embedding
            return best_id, best_score
        else:
            new_id = self.next_id
            self.known_speakers[new_id] = embedding
            self.next_id += 1
            return new_id, 1.0
```

---

### 4.4. Active Speaker Detection (Analisis Gerakan Bibir)
Untuk mengetahui siapa yang sedang berbicara (terutama dalam podcast multi-orang), kita dapat menghitung rasio bukaan bibir (*Lip-Opening Aspect Ratio*).

Menggunakan 106-landmark atau 5-KPS:
```python
def calculate_lip_opening_score(face_data):
    """
    Menghitung skor bukaan bibir.
    Jika menggunakan 106 landmark, ambil jarak antara bibir atas dan bawah 
    dibandingkan dengan lebar bibir atau tinggi wajah.
    """
    lmk = face_data.get("landmarks_106")
    if lmk is not None and len(lmk) >= 106:
        # Indeks standar landmark 106 untuk bibir:
        # Bibir atas tengah: index 52, Bibir bawah tengah: index 60
        # Sudut bibir kiri: index 57, Sudut bibir kanan: index 63
        top_lip = lmk[52]
        bottom_lip = lmk[60]
        left_corner = lmk[57]
        right_corner = lmk[63]
        
        vertical_dist = np.linalg.norm(top_lip - bottom_lip)
        horizontal_dist = np.linalg.norm(left_corner - right_corner) + 1e-6
        
        ratio = vertical_dist / horizontal_dist
        return ratio
    
    # Fallback jika hanya ada 5 KPS (KPS[3] = mulut kiri, KPS[4] = mulut kanan)
    # Gunakan variasi tinggi bbox sebagai aproksimasi kasar
    return 0.0
```

---

### 4.5. Smoothing Kamera & Deadzone (Anti-Shaking)
Jika posisi crop diubah setiap frame mengikuti koordinat mentah wajah, hasil video akan bergetar dan tidak nyaman ditonton.

Solusi:
1. **Deadzone Margin**: Jika pergeseran wajah kurang dari $D$ piksel (misal 20px), jangan gerakkan kamera sama sekali.
2. **Exponential Moving Average (EMA)**: Interpolasikan koordinat pusat kamera secara gradual.

$$\text{Center}_{\text{smooth}}(t) = \alpha \cdot \text{Center}_{\text{target}}(t) + (1 - \alpha) \cdot \text{Center}_{\text{smooth}}(t-1)$$
*(Nilai $\alpha \approx 0.05 - 0.15$ untuk pergerakan sinematik yang lembut).*

```python
class CameraSmoother:
    def __init__(self, alpha=0.08, deadzone_px=25):
        self.alpha = alpha
        self.deadzone_px = deadzone_px
        self.current_center = None

    def update(self, target_center_x, target_center_y):
        if self.current_center is None:
            self.current_center = (float(target_center_x), float(target_center_y))
            return int(self.current_center[0]), int(self.current_center[1])

        curr_x, curr_y = self.current_center
        dx = target_center_x - curr_x
        dy = target_center_y - curr_y
        dist = (dx**2 + dy**2)**0.5

        # Terapkan deadzone
        if dist > self.deadzone_px:
            new_x = curr_x + self.alpha * dx
            new_y = curr_y + self.alpha * dy
            self.current_center = (new_x, new_y)
        
        return int(self.current_center[0]), int(self.current_center[1])
```

---

### 4.6. Komposisi Smart Crop (Rule of Thirds 9:16)
Di video vertikal, wajah sebaiknya tidak berada tepat di tengah secara vertikal ($y = 50\%$), melainkan berada pada garis **1/3 atas** ($y \approx 30\% - 35\%$). Ini memberikan ruang estetika untuk leher/bahu dan menyisakan area bawah untuk teks/subtitle otomatis.

```python
def calculate_9_16_crop_window(frame_width, frame_height, face_bbox, smooth_center_x=None, eye_level_ratio=0.32):
    """
    Menghitung window cropping (x1, y1, x2, y2) dari frame 16:9 agar pas ke 9:16.
    """
    target_aspect = 9 / 16.0
    
    # Hitung dimensi kotak crop pada frame sumber
    crop_height = frame_height
    crop_width = int(crop_height * target_aspect)
    
    if crop_width > frame_width:
        crop_width = frame_width
        crop_height = int(crop_width / target_aspect)
        
    x1, y1, x2, y2 = face_bbox
    face_cx = (x1 + x2) // 2 if smooth_center_x is None else smooth_center_x
    face_cy = (y1 + y2) // 2

    # Tempatkan pusat horizontal wajah di tengah crop window
    crop_x1 = face_cx - (crop_width // 2)
    
    # Tempatkan wajah di ketinggian mata ideal (misal 32% dari atas)
    crop_y1 = face_cy - int(crop_height * eye_level_ratio)

    # Validasi batas frame (clamping agar tidak keluar layar)
    crop_x1 = max(0, min(crop_x1, frame_width - crop_width))
    crop_y1 = max(0, min(crop_y1, frame_height - crop_height))

    crop_x2 = crop_x1 + crop_width
    crop_y2 = crop_y1 + crop_height

    return crop_x1, crop_y1, crop_x2, crop_y2
```

---

## 5. Modul Python Siap Pakai (Stand-Alone Class)

Berikut adalah modul lengkap `smart_clipper_insightface.py` yang dapat Anda salin langsung ke project manapun:

```python
import cv2
import numpy as np
import os
import sys
from contextlib import contextmanager
import warnings

warnings.filterwarnings("ignore")

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False


@contextmanager
def suppress_stdout_stderr():
    with open(os.devnull, "w") as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


class InsightFaceClipper:
    """
    Modul cerdas untuk deteksi wajah, tracking, dan smart-crop 9:16 menggunakan InsightFace.
    """
    def __init__(self, model_name="buffalo_l", use_gpu=True, det_size=(640, 640), alpha_smooth=0.10, deadzone=20):
        if not INSIGHTFACE_AVAILABLE:
            raise ImportError("InsightFace belum terpasang. Jalankan: pip install insightface onnxruntime-gpu")

        self.det_size = det_size
        self.alpha_smooth = alpha_smooth
        self.deadzone = deadzone
        self.cam_center_x = None
        self.cam_center_y = None

        # Pilihan provider eksekusi
        ctx_id = 0 if use_gpu else -1
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        
        with suppress_stdout_stderr():
            self.app = FaceAnalysis(name=model_name, providers=providers)
            self.app.prepare(ctx_id=ctx_id, det_size=self.det_size)

    def detect_primary_face(self, frame):
        """
        Mendeteksi wajah utama (berdasarkan bounding box terbesar atau det_score tertinggi).
        Returns: [x1, y1, x2, y2] atau None jika tidak ditemukan.
        """
        faces = self.app.get(frame)
        if not faces:
            return None

        # Sort berdasarkan luas bounding box (wajah paling depan / close-up)
        def face_area(f):
            box = f.bbox
            return (box[2] - box[0]) * (box[3] - box[1])

        primary_face = max(faces, key=face_area)
        return primary_face.bbox.astype(int).tolist()

    def smooth_position(self, target_x, target_y):
        """Menghaluskan pergerakan kamera menggunakan Exponential Moving Average & Deadzone."""
        if self.cam_center_x is None or self.cam_center_y is None:
            self.cam_center_x = float(target_x)
            self.cam_center_y = float(target_y)
            return int(self.cam_center_x), int(self.cam_center_y)

        dx = target_x - self.cam_center_x
        dy = target_y - self.cam_center_y
        dist = (dx**2 + dy**2) ** 0.5

        if dist > self.deadzone:
            self.cam_center_x += self.alpha_smooth * dx
            self.cam_center_y += self.alpha_smooth * dy

        return int(self.cam_center_x), int(self.cam_center_y)

    def crop_smart_portrait(self, frame, face_bbox=None, target_w=1080, target_h=1920, eye_ratio=0.33):
        """
        Melakukan cropping 9:16 terpusat pada wajah dengan smoothing dan rule-of-thirds.
        """
        h, w = frame.shape[:2]
        target_aspect = target_w / target_h

        # Tentukan ukuran kotak crop
        crop_h = h
        crop_w = int(crop_h * target_aspect)
        if crop_w > w:
            crop_w = w
            crop_h = int(crop_w / target_aspect)

        if face_bbox is not None:
            raw_cx = (face_bbox[0] + face_bbox[2]) // 2
            raw_cy = (face_bbox[1] + face_bbox[3]) // 2
            smooth_cx, smooth_cy = self.smooth_position(raw_cx, raw_cy)
        else:
            # Fallback ke tengah layar jika tidak ada wajah
            smooth_cx, smooth_cy = self.smooth_position(w // 2, h // 2)

        # Hitung bounding box crop dengan eye-level offset
        crop_x1 = smooth_cx - (crop_w // 2)
        crop_y1 = smooth_cy - int(crop_h * eye_ratio)

        # Clamping
        crop_x1 = max(0, min(crop_x1, w - crop_w))
        crop_y1 = max(0, min(crop_y1, h - crop_h))
        crop_x2 = crop_x1 + crop_w
        crop_y2 = crop_y1 + crop_h

        # Lakukan Crop & Resize
        cropped = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        result = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
        return result
```

---

## 6. Contoh Skrip Pemrosesan Video Penuh

Berikut contoh skrip CLI untuk memproses satu file video 16:9 menjadi 9:16 dengan teknik **Keyframe Sampling** (deteksi setiap 4 frame untuk kecepatan maksimal):

```python
import cv2
import time
from smart_clipper_insightface import InsightFaceClipper

def process_video_clip(input_path, output_path, sample_every_n_frames=3):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Tidak bisa membuka {input_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out_w, out_h = 1080, 1920

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (out_w, out_h))

    clipper = InsightFaceClipper(model_name="buffalo_l", use_gpu=True, alpha_smooth=0.12)

    last_known_bbox = None
    frame_idx = 0

    start_time = time.time()
    print(f"Memproses video ({total_frames} frame)...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Jalankan deteksi berat hanya pada keyframe interval
        if frame_idx % sample_every_n_frames == 0 or last_known_bbox is None:
            detected_bbox = clipper.detect_primary_face(frame)
            if detected_bbox is not None:
                last_known_bbox = detected_bbox

        # Lakukan smart crop dengan smoothing
        result_frame = clipper.crop_smart_portrait(frame, face_bbox=last_known_bbox, target_w=out_w, target_h=out_h)
        out.write(result_frame)

        frame_idx += 1
        if frame_idx % 60 == 0:
            pct = (frame_idx / total_frames) * 100
            print(f"Progress: {frame_idx}/{total_frames} ({pct:.1f}%)")

    cap.release()
    out.release()
    elapsed = time.time() - start_time
    print(f"Selesai dalam {elapsed:.2f} detik! Output: {output_path}")

if __name__ == "__main__":
    process_video_clip("input_podcast.mp4", "output_shorts_9_16.mp4")
```

---

## 7. Strategi Optimasi Performa (Production-Grade)

Jika Anda ingin memproses video berdurasi panjang dengan latensi rendah:

### 1. Frame Downscaling untuk Tahap Deteksi
- **Masalah**: Menjalankan deteksi pada frame 4K / 1080p secara penuh memakan banyak komputasi.
- **Solusi**: Perkecil frame ke resolusi rendah (misal lebar 640px) sebelum dilempar ke `app.get()`. Kemudian kalikan kembali koordinat bounding box dengan faktor skala `(orig_w / 640)`.

```python
scale = 640.0 / orig_w
small_frame = cv2.resize(frame, (640, int(orig_h * scale)))
faces = app.get(small_frame)
# Scale koordinat kembali ke resolusi asli
bbox = (faces[0].bbox / scale).astype(int)
```

### 2. Temporal Interpolation (Keyframe Skipping)
- Jalankan deteksi InsightFace setiap **$N$ frame** (misal tiap 3 atau 5 frame = ~6–10 FPS).
- Gunakan interpolasi linier untuk frame-frame di antaranya. Hasil visual tetap mulus karena wajah manusia di video podcast/wawancara tidak bergerak secara instan.

### 3. VRAM Caching
- Gunakan satu instance `FaceAnalysis` secara global / singleton (jangan re-instantiate di dalam loop frame).

---

## 8. Mode Layout Khusus (Split-Screen 2 Pembicara)

Untuk podcast dengan 2 orang, sering kali digunakan format **Split-Screen** (Pembicara A di atas, Pembicara B di bawah):

```text
┌─────────────────────────┐
│                         │
│       Speaker 1         │   (Top Half: 1080 x 960)
│                         │
├─────────────────────────┤
│                         │
│       Speaker 2         │   (Bottom Half: 1080 x 960)
│                         │
└─────────────────────────┘
```

### Logika Ekstraksi Dual-Face:
```python
def crop_split_screen(frame, face_bbox_1, face_bbox_2, target_w=1080, target_h=1920):
    half_h = target_h // 2
    
    # 1. Crop untuk Speaker 1 (Atas)
    crop_top = crop_single_person(frame, face_bbox_1, target_w, half_h, eye_ratio=0.35)
    
    # 2. Crop untuk Speaker 2 (Bawah)
    crop_bottom = crop_single_person(frame, face_bbox_2, target_w, half_h, eye_ratio=0.35)
    
    # 3. Gabungkan secara vertikal (Stacking)
    stacked = np.vstack((crop_top, crop_bottom))
    return stacked
```

---

## 9. Checklist Integrasi ke Project Baru

Saat membawa logika ini ke project baru Anda, ikuti checklist berikut:

1. [ ] **Verifikasi GPU Runtime**: Pastikan `onnxruntime-gpu` berjalan di CUDA (`ort.get_available_providers()` menampilkan `CUDAExecutionProvider`).
2. [ ] **Inisialisasi Model Terpusat**: Simpan instance `FaceAnalysis` di modul service/worker tersendiri.
3. [ ] **Pasang Camera Smoother**: Terapkan EMA/Deadzone agar kamera tidak goyang.
4. [ ] **Atur Eye-Level Offset**: Pasang offset vertikal $30\% - 35\%$ agar posisi framing natural untuk video vertikal.
5. [ ] **Tambahkan Audio Remuxing**: Setelah pemrosesan visual dengan OpenCV, gabungkan kembali audio asli menggunakan FFmpeg:
   ```bash
   ffmpeg -i output_visual.mp4 -i input_original.mp4 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest final_with_audio.mp4
   ```
