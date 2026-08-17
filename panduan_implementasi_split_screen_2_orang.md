# Panduan Lengkap Implementasi Editing Split-Screen 2 Orang (Atas & Bawah) dengan InsightFace

Dokumen ini menjelaskan secara teknis dan arsitektural cara membangun sistem **Split-Screen Vertikal (Top-Bottom Layout)** untuk 2 orang yang sedang berbicara (Podcast, Wawancara, Talkshow, Debat) agar menghasilkan video vertikal 9:16 (1080x1920) untuk TikTok, Instagram Reels, dan YouTube Shorts.

Panduan ini bersifat **umum, modular, dan agnostik terhadap framework**, sehingga dapat langsung diterapkan pada ViralCutter maupun project video clipper berbasis Python lainnya.

---

## 1. Konsep Arsitektur Layout Atas-Bawah (9:16)

Pada video vertikal standar ($1080 \times 1920$ px), layout split-screen 2 orang membagi layar menjadi 2 slot sama rata (masing-masing $1080 \times 960$ px):

```text
┌──────────────────────────────────────────────────────────┐
│                   Input Frame (16:9)                     │
│   ┌─────────────────────┐      ┌─────────────────────┐   │
│   │   [Speaker 1 / A]   │      │   [Speaker 2 / B]   │   │
│   │     (Sisi Kiri)     │      │    (Sisi Kanan)     │   │
│   └─────────────────────┘      └─────────────────────┘   │
└─────────────────────────────┬────────────────────────────┘
                              │
               InsightFace Detection & Tracking
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                 Output Frame 9:16                        │
│ ┌──────────────────────────────────────────────────────┐ │
│ │                                                      │ │
│ │                   SPEAKER 1 (ATAS)                   │ │
│ │                  (1080 x 960 piksel)                 │ │
│ │             Aspect Ratio 9:8 (1.125 : 1)             │ │
│ │                                                      │ │
│ ├══════════════════════════════════════════════════════┤ │ ◄── Garis Pembatas (Divider / Border)
│ │                                                      │ │
│ │                   SPEAKER 2 (BAWAH)                  │ │
│ │                  (1080 x 960 piksel)                 │ │
│ │             Aspect Ratio 9:8 (1.125 : 1)             │ │
│ │                                                      │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Mengapa Layout Atas-Bawah Sangat Efektif?
1. **Konteks Percakapan Terjaga**: Penonton melihat ekspresi kedua orang sekaligus (pembicara aktif dan reaksi pendengar).
2. **Tidak Perlu Terlalu Sering Hard-Cut**: Mengurangi efek pusing akibat kamera yang berpindah-pindah terlalu cepat jika kedua orang saling memotong pembicaraan (*rapid back-and-forth*).
3. **Standar Industri**: Digunakan secara luas oleh platform seperti OpusClip, Klap, Submagic, dan Vizard.

---

## 2. Tantangan Utama & Solusi Rekayasa

| Tantangan | Risiko Visual | Solusi Teknis |
| :--- | :--- | :--- |
| **1. Speaker Flapping / Swap** | Posisi orang di layar atas dan bawah tertukar-tukar antar frame secara acak. | **Spatial Anchor + Face Re-ID**: Orang di sisi kiri frame 16:9 selalu di-assign ke panel Atas; orang di kanan selalu ke panel Bawah, divalidasi dengan Cosine Similarity 512-D embedding. |
| **2. Wajah Bergetar (Jitter)** | Gambar bergetar saat orang bergerak sedikit. | **Dual Independent Smoother**: Setiap pembicara memiliki instance *Exponential Moving Average (EMA)* dan *Deadzone Filter* terpisah. |
| **3. Distorsi Proporsi Wajah** | Wajah terlihat gepeng atau lonjong saat di-resize ke $1080 \times 960$. | **Strict Aspect Ratio Cropping**: Hitung bounding box crop dari frame asli dengan rasio $9:8$ ($1.125$) sebelum di-resize. |
| **4. Wajah Hilang Sejenak (Occlusion)** | Panel menjadi hitam jika satu orang menunduk atau menoleh ekstrem. | **Position Memory Buffer**: Pertahankan posisi crop terakhir selama $N$ frame jika deteksi drop sejenak. |

---

## 3. Matematika Framing & Cropping Rasio 9:8 (1080x960)

Untuk memotong satu wajah ke resolusi slot target $W_{\text{slot}} \times H_{\text{slot}}$ ($1080 \times 960$), aspect ratio target adalah:
$$\text{AR}_{\text{target}} = \frac{1080}{960} = 1.125$$

### Rumus Perhitungan Window Crop pada Frame Sumber ($W_{\text{src}} \times H_{\text{src}}$):
1. Tentukan ukuran wajah: $\text{face\_size} = \max(w_{\text{face}}, h_{\text{face}})$
2. Tentukan tinggi crop yang diinginkan dengan faktor zoom:
   $$\text{crop\_h} = \text{face\_size} \times \text{zoom\_factor} \quad (\text{misal zoom\_factor} = 2.4)$$
3. Tentukan lebar crop agar rasio $9:8$ terpenuhi:
   $$\text{crop\_w} = \text{crop\_h} \times 1.125$$
4. Validasi batas frame sumber (jika $\text{crop\_h} > H_{\text{src}}$ atau $\text{crop\_w} > W_{\text{src}}$):
   $$\text{crop\_w} = \min(\text{crop\_w}, W_{\text{src}}), \quad \text{crop\_h} = \frac{\text{crop\_w}}{1.125}$$
5. Tempatkan pusat wajah $(\text{cx}, \text{cy})$ dengan offset *eye-level* vertikal:
   $$x_1 = \text{cx} - \frac{\text{crop\_w}}{2}, \quad y_1 = \text{cy} - (\text{crop\_h} \times \text{eye\_ratio})$$
6. Clamping koordinat agar tidak keluar dari $0 \le x_1 \le W_{\text{src}} - \text{crop\_w}$ dan $0 \le y_1 \le H_{\text{src}} - \text{crop\_h}$.

---

## 4. Logika Identifikasi & Pengurutan 2 Pembicara

Saat InsightFace mendeteksi beberapa wajah dalam satu frame, kita perlu memilih **2 wajah utama** dan menguncinya ke slot yang tepat:

```python
def assign_speakers(detected_faces, frame_width):
    """
    Mengelompokkan 2 wajah utama secara konsisten:
    - Speaker 1 (Panel Atas) -> Orang di sisi kiri frame asli (X lebih kecil)
    - Speaker 2 (Panel Bawah) -> Orang di sisi kanan frame asli (X lebih besar)
    """
    if len(detected_faces) < 2:
        return detected_faces  # Fallback

    # Urutkan berdasarkan posisi horizontal (X center)
    sorted_by_x = sorted(detected_faces, key=lambda f: (f['bbox'][0] + f['bbox'][2]) // 2)

    speaker_left = sorted_by_x[0]   # Wajah paling kiri -> Slot Atas
    speaker_right = sorted_by_x[-1]  # Wajah paling kanan -> Slot Bawah

    return [speaker_left, speaker_right]
```

---

## 5. Implementasi Kelas Modular Python (`DualSpeakerSplitClipper`)

Berikut adalah kode Python lengkap yang dapat langsung di-import atau disalin ke project Anda:

```python
import os
import sys
import warnings
from contextlib import contextmanager
import cv2
import numpy as np

warnings.filterwarnings("ignore")

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False


@contextmanager
def suppress_stdout_stderr():
    """Meredam log C++ dari ONNX Runtime dan InsightFace"""
    with open(os.devnull, "w") as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


class SmoothTracker:
    """Filter pergerakan kamera per pembicara untuk mencegah getaran."""
    def __init__(self, alpha=0.10, deadzone=15):
        self.alpha = alpha
        self.deadzone = deadzone
        self.cx = None
        self.cy = None

    def update(self, target_cx, target_cy):
        if self.cx is None:
            self.cx = float(target_cx)
            self.cy = float(target_cy)
            return int(self.cx), int(self.cy)

        dx = target_cx - self.cx
        dy = target_cy - self.cy
        dist = (dx**2 + dy**2) ** 0.5

        if dist > self.deadzone:
            self.cx += self.alpha * dx
            self.cy += self.alpha * dy

        return int(self.cx), int(self.cy)


class DualSpeakerSplitClipper:
    """
    Kelas pemotong video pintar untuk layout Split-Screen 2 Orang (Atas-Bawah 9:16).
    """
    def __init__(self, model_name="buffalo_l", use_gpu=True, det_size=(640, 640),
                 target_w=1080, target_h=1920, divider_thickness=4, divider_color=(25, 25, 25)):
        if not INSIGHTFACE_AVAILABLE:
            raise ImportError("InsightFace belum terpasang. Jalankan: pip install insightface onnxruntime-gpu")

        self.target_w = target_w
        self.target_h = target_h
        self.slot_w = target_w
        self.slot_h = target_h // 2  # 960 piksel
        self.divider_thickness = divider_thickness
        self.divider_color = divider_color

        # Tracker independen untuk masing-masing slot
        self.tracker_top = SmoothTracker(alpha=0.10, deadzone=18)
        self.tracker_bottom = SmoothTracker(alpha=0.10, deadzone=18)

        # Buffer memori untuk posisi terakhir jika wajah hilang sesaat
        self.last_bbox_top = None
        self.last_bbox_bottom = None

        # Inisialisasi InsightFace
        ctx_id = 0 if use_gpu else -1
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']

        with suppress_stdout_stderr():
            self.app = FaceAnalysis(name=model_name, providers=providers)
            self.app.prepare(ctx_id=ctx_id, det_size=det_size)

    def detect_two_faces(self, frame):
        """
        Mendeteksi dan memisahkan 2 wajah:
        Returns: (bbox_top, bbox_bottom) masing-masing dalam format [x1, y1, x2, y2]
        """
        faces = self.app.get(frame)
        if not faces:
            return self.last_bbox_top, self.last_bbox_bottom

        # Filter berdasarkan confidence score
        valid_faces = [f for f in faces if f.det_score >= 0.5]
        if not valid_faces:
            return self.last_bbox_top, self.last_bbox_bottom

        if len(valid_faces) == 1:
            # Jika hanya 1 wajah terdeteksi, gunakan untuk slot yang paling sesuai atau fallback
            box = valid_faces[0].bbox.astype(int).tolist()
            frame_w = frame.shape[1]
            cx = (box[0] + box[2]) // 2
            if cx < frame_w // 2:
                self.last_bbox_top = box
            else:
                self.last_bbox_bottom = box
            return self.last_bbox_top, self.last_bbox_bottom

        # Urutkan berdasarkan posisi horizontal (kiri ke kanan)
        sorted_faces = sorted(valid_faces, key=lambda f: (f.bbox[0] + f.bbox[2]) // 2)

        # Wajah paling kiri untuk panel Atas, wajah paling kanan untuk panel Bawah
        self.last_bbox_top = sorted_faces[0].bbox.astype(int).tolist()
        self.last_bbox_bottom = sorted_faces[-1].bbox.astype(int).tolist()

        return self.last_bbox_top, self.last_bbox_bottom

    def crop_slot(self, frame, face_bbox, tracker, zoom_out_factor=2.4, eye_ratio=0.35):
        """
        Memotong area satu wajah dengan aspect ratio 9:8 (slot 1080x960) tanpa distorsi.
        """
        img_h, img_w = frame.shape[:2]
        target_ar = self.slot_w / self.slot_h  # 1080 / 960 = 1.125

        if face_bbox is not None:
            x1, y1, x2, y2 = face_bbox
            w_face = x2 - x1
            h_face = y2 - y1
            raw_cx = x1 + w_face // 2
            raw_cy = y1 + h_face // 2
            face_size = max(w_face, h_face)
        else:
            # Fallback jika belum pernah ada deteksi wajah
            raw_cx = img_w // 2
            raw_cy = img_h // 2
            face_size = img_h // 3

        # Haluskan pergerakan kamera
        smooth_cx, smooth_cy = tracker.update(raw_cx, raw_cy)

        # Hitung dimensi crop
        req_h = face_size * zoom_out_factor
        crop_h = req_h
        crop_w = crop_h * target_ar

        # Batasi jika ukuran crop melebihi ukuran video asli
        if crop_w > img_w:
            crop_w = float(img_w)
            crop_h = crop_w / target_ar
        if crop_h > img_h:
            crop_h = float(img_h)
            crop_w = crop_h * target_ar

        crop_w = int(crop_w)
        crop_h = int(crop_h)

        # Tempatkan dengan eye-level offset
        crop_x1 = smooth_cx - (crop_w // 2)
        crop_y1 = smooth_cy - int(crop_h * eye_ratio)

        # Clamping
        crop_x1 = max(0, min(crop_x1, img_w - crop_w))
        crop_y1 = max(0, min(crop_y1, img_h - crop_h))
        crop_x2 = crop_x1 + crop_w
        crop_y2 = crop_y1 + crop_h

        # Lakukan pemotongan dan resize ke 1080x960
        cropped = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        if cropped.size == 0:
            return np.zeros((self.slot_h, self.slot_w, 3), dtype=np.uint8)

        slot_img = cv2.resize(cropped, (self.slot_w, self.slot_h), interpolation=cv2.INTER_LINEAR)
        return slot_img

    def render_split_frame(self, frame, bbox_top, bbox_bottom):
        """
        Menghasilkan 1 frame vertikal 1080x1920 berisi Speaker 1 (Atas) dan Speaker 2 (Bawah).
        """
        # Crop kedua slot
        top_img = self.crop_slot(frame, bbox_top, self.tracker_top, zoom_out_factor=2.5, eye_ratio=0.35)
        bottom_img = self.crop_slot(frame, bbox_bottom, self.tracker_bottom, zoom_out_factor=2.5, eye_ratio=0.35)

        # Gabungkan secara vertikal (1080x960 + 1080x960 = 1080x1920)
        split_frame = np.vstack((top_img, bottom_img))

        # Tambahkan garis pembatas tengah (Divider Line) yang bersih
        if self.divider_thickness > 0:
            mid_y = self.slot_h
            half_t = self.divider_thickness // 2
            y_start = max(0, mid_y - half_t)
            y_end = min(self.target_h, mid_y + half_t)
            split_frame[y_start:y_end, :] = self.divider_color

        return split_frame
```

---

## 6. Contoh Skrip Batch Pemrosesan Video Lengkap

Skrip di bawah ini membaca video input (16:9), memprosesnya dengan InsightFace, dan mengekspornya ke format 9:16 Split-Screen:

```python
import cv2
import time
from dual_speaker_clipper import DualSpeakerSplitClipper

def process_podcast_split_screen(input_video_path, output_video_path, sample_every_n_frames=3):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Gagal membuka file: {input_video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out_w, out_h = 1080, 1920

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (out_w, out_h))

    # Inisialisasi Clipper
    clipper = DualSpeakerSplitClipper(
        model_name="buffalo_l",
        use_gpu=True,
        target_w=out_w,
        target_h=out_h,
        divider_thickness=4,
        divider_color=(20, 20, 20)  # Warna abu-abu gelap elegan
    )

    bbox_top = None
    bbox_bottom = None
    frame_idx = 0

    print(f"Memulai rendering Split-Screen ({total_frames} frames)...")
    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Jalankan deteksi InsightFace setiap N frame
        if frame_idx % sample_every_n_frames == 0 or bbox_top is None or bbox_bottom is None:
            bbox_top, bbox_bottom = clipper.detect_two_faces(frame)

        # Render komposisi vertikal
        final_frame = clipper.render_split_frame(frame, bbox_top, bbox_bottom)
        out.write(final_frame)

        frame_idx += 1
        if frame_idx % 60 == 0:
            progress = (frame_idx / total_frames) * 100
            print(f"Progress: {frame_idx}/{total_frames} ({progress:.1f}%)")

    cap.release()
    out.release()
    total_time = time.time() - start_time
    print(f"Rendering selesai dalam {total_time:.2f} detik! File: {output_video_path}")

if __name__ == "__main__":
    process_podcast_split_screen("interview_landscape.mp4", "podcast_split_shorts.mp4")
```

---

## 7. Fitur Lanjutan: Active Speaker Highlight (Border / Glow Dinamis)

Untuk membuat klip terlihat lebih profesional, Anda dapat menambahkan **indikator visual (Border Glow / Highlight)** pada pembicara yang sedang aktif berbicara:

```text
┌──────────────────────────────────────────────────────────┐
│ ┌──────────────────────────────────────────────────────┐ │
│ │ [SPEAKER 1]  (SEDANG BICARA)                         │ │
│ │ 🟨 BORDER EMAS / CYAN MENYALA (Active Speaker)       │ │
│ └──────────────────────────────────────────────────────┘ │
│ ├══════════════════════════════════════════════════════┤ │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ [SPEAKER 2]  (MENDENGARKAN)                          │ │
│ │ (Border Netral)                                      │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Logika Penambahan Active Speaker Border:
```python
def draw_active_speaker_border(slot_image, is_active=False, border_color=(0, 215, 255), thickness=6):
    """
    Menambahkan highlight border di sekeliling slot jika speaker aktif.
    border_color: BGR format (default: Emas / Gold)
    """
    if not is_active:
        return slot_image

    h, w = slot_image.shape[:2]
    # Gambar border tipis di dalam batas gambar
    cv2.rectangle(slot_image, (thickness // 2, thickness // 2), 
                  (w - thickness // 2, h - thickness // 2), 
                  border_color, thickness)
    return slot_image
```

---

## 8. Menggabungkan Kembali Audio Asli dengan FFmpeg

OpenCV hanya memproses stream video. Agar video output memiliki suara asli yang tersinkronisasi, gunakan perintah FFmpeg berikut:

```bash
ffmpeg -i podcast_split_shorts.mp4 -i interview_landscape.mp4 \
  -c:v copy \
  -c:a aac -b:a 192k \
  -map 0:v:0 -map 1:a:0 \
  -shortest final_split_shorts_with_audio.mp4
```

Atau otomatis via Python `subprocess`:
```python
import subprocess

def remux_audio(video_no_audio, original_video, output_final):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_no_audio,
        "-i", original_video,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_final
    ]
    subprocess.run(cmd, check=True)
```

---

## 9. Ringkasan Parameter Konfigurasi yang Dianjurkan

| Parameter | Nilai Rekomendasi | Keterangan |
| :--- | :--- | :--- |
| `zoom_out_factor` | `2.2` – `2.6` | Mengatur luas pandang kamera. Nilai 2.4 memberikan framing dada-ke-kepala (*medium close-up*) yang ideal. |
| `eye_ratio` | `0.33` – `0.36` | Ketinggian mata dari atas panel slot. Menjaga ruang estetika di bawah untuk teks/subtitle. |
| `alpha_smooth` | `0.08` – `0.12` | Kecepatan kamera mengikuti kepala. Nilai lebih kecil = pergerakan lebih sinematik/lambat. |
| `deadzone` | `15` – `20` px | Toleransi gerakan mikro kepala agar kamera tidak bergetar. |
| `sample_every_n_frames` | `3` – `5` frame | Melewatkan inferensi berat pada frame berdekatan untuk mempercepat proses 3x–5x lipat. |
