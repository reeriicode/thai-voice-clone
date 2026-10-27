# การต่อยอด (Extending)

โค้ดหลักอยู่ใน `vtuber_tts/` แยกเป็นส่วน ๆ แก้ทีละส่วนได้โดยไม่กระทบส่วนอื่น

```
vtuber_tts/
├─ paths.py        ตำแหน่งโฟลเดอร์ทั้งหมด
├─ config.py       ค่าเริ่มต้น + อ่าน/บันทึก config/settings.json
├─ voices.py       รายชื่อเสียงใน voices/ + เพิ่มเสียงใหม่
├─ models.py       รายชื่อโมเดลจาก config/models.json + models/custom/ + ดาวน์โหลด
├─ text.py         พจนานุกรมคำอ่าน + แยกบทสนทนา
├─ stt.py          ถอดเสียงเป็นข้อความ (faster-whisper)
├─ engine.py       VoiceEngine: โหลดโมเดลทีละตัว เรียก backend สร้างเสียง/บทสนทนา
├─ backends/       ตัวสร้างเสียงแต่ละแบบ (เสียบเพิ่มได้)
│  ├─ base.py      คลาสแม่ Backend
│  ├─ f5.py        F5-TTS-THAI (โคลนเสียงจากคลิป)
│  └─ edge.py      Microsoft Edge TTS (ออนไลน์)
├─ app.py          หน้าเว็บ (Gradio)
└─ cli.py          คำสั่ง speak.py / dialogue.py
```

## เพิ่มตัวสร้างเสียงใหม่ (backend)

ตัวอย่าง: เพิ่ม Google TTS (`gTTS`)

**1. สร้างไฟล์ `vtuber_tts/backends/gtts.py`**

```python
import io

from .base import Backend


class GTTSBackend(Backend):
    type = "gtts"
    uses_pronunciations = False   # True = แปลงคำอังกฤษเป็นคำอ่านไทยก่อนส่งมา

    def __init__(self, info):
        super().__init__(info)    # โหลดโมเดลตรงนี้ (ถ้ามี)

    def speak(self, text, voice, speed=1.0, nfe=32, seed=-1, remove_silence=True):
        import soundfile as sf
        from gtts import gTTS

        buf = io.BytesIO()
        gTTS(text, lang="th").write_to_fp(buf)
        buf.seek(0)
        wave, sr = sf.read(buf, dtype="float32")
        return sr, wave, "-"      # (sample rate, เสียง mono float32, seed)

    def close(self):
        pass                      # คืนหน่วยความจำการ์ดจอ (ถ้าใช้)
```

`voice` คือข้อมูลเสียงที่ผู้ใช้เลือก: `id`, `ref_audio`, `ref_text`, `gender`, `edge_voice`
ใช้อะไรก็ได้ตามที่ backend ต้องการ เช่น เลือกเสียงตาม `gender`

**2. ลงทะเบียนใน `vtuber_tts/backends/__init__.py`**

```python
BACKENDS = {
    "f5": "f5:F5Backend",
    "edge": "edge:EdgeBackend",
    "gtts": "gtts:GTTSBackend",
}
```

**3. เพิ่มในช่องโมเดล `config/models.json`**

```json
{ "id": "gtts", "name": "Google TTS", "type": "gtts", "note": "เสียง Google ออนไลน์", "size_mb": 0 }
```

เปิดแอปใหม่ จะเลือก "Google TTS" ได้ทันที ทั้งในหน้าเว็บ, `speak.py --model gtts` และบทสนทนา

## เพิ่มโมเดล F5 ที่ train เอง

วางไฟล์ `.pt` ใน `models/custom/` แล้วเปิดแอปใหม่ (รายละเอียดใน `models/custom/README.txt`)
หรือเพิ่มใน `config/models.json` ถ้าโมเดลอยู่บน Hugging Face:

```json
{
  "id": "my_voice", "name": "เสียงผม (fine-tune)", "type": "f5",
  "repo": "<user>/<repo>", "file": "model_50000.pt",
  "arch": "v1", "vocab": "thai", "ipa": false, "thai": true, "size_mb": 1349
}
```

- `arch`: `v1` (ไทย v1 / ต้นฉบับ Base) หรือ `v2` (ไทย v2 / ต้นฉบับ v1)
- `vocab`: `thai`, `thai_ipa`, path ไฟล์ หรือ `{"repo": ..., "file": ...}`
- `ipa`: แปลงข้อความเป็น IPA ก่อน (โมเดล v2)
- `thai`: ใช้พจนานุกรมคำอ่านและ normalize ภาษาไทย

## ใช้จากโค้ด Python

```python
from vtuber_tts.engine import VoiceEngine
from vtuber_tts.text import parse_script
import soundfile as sf

engine = VoiceEngine("th_v1")                 # หรือ "edge"
sr, wave, seed = engine.speak("สวัสดีครับ", "male")
sf.write("hello.wav", wave, sr)

lines = parse_script("ผช: สวัสดีครับ\nผญ: สวัสดีค่ะ", "ผู้ชาย (เสียงผม)", "ผู้หญิง")
sr, wave, parts = engine.speak_dialogue(lines, pause=0.4)
```

## เพิ่มแท็บในหน้าเว็บ

แก้ `vtuber_tts/app.py` ในฟังก์ชัน `build_ui()` เพิ่ม `with gr.Tab("ชื่อแท็บ"):` แล้วเรียก `engine` ได้เลย
