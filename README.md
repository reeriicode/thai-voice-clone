# VTuber Thai TTS

เปลี่ยนข้อความภาษาไทยเป็นเสียงพูด โคลนเสียงจากคลิปสั้น 5-8 วินาที สร้างบทสนทนาหลายตัวละคร
และเลือกได้หลายโมเดล (F5-TTS-THAI, Microsoft Edge TTS) ผ่านหน้าเว็บหรือคำสั่ง

**English:** Thai text-to-speech toolkit for VTubers and content creators. Clone a voice from a
5-8 second clip with [F5-TTS-THAI](https://github.com/VYNCX/F5-TTS-THAI), render multi-speaker
dialogue scripts, or use Microsoft Edge TTS. Web UI (Gradio) + CLI, pluggable backends.
Windows + NVIDIA GPU (4 GB is enough). See [Quick start](#ติดตั้ง-install) and [docs/EXTENDING.md](docs/EXTENDING.md).

## ความสามารถ

- 🎙️ **โคลนเสียง** จากคลิป 5-8 วินาที (ไม่ต้อง train)
- 🎬 **บทสนทนา** หลายตัวละคร `ผช:` / `ผญ:` ได้ไฟล์รวม + แยกรายบรรทัดไว้ตัดต่อ
- 🔀 **เลือกโมเดล**: ไทย v1, ไทย v2 (IPA), รุ่นเก่า, ต้นฉบับ F5-TTS, Microsoft Edge TTS, โมเดลที่ train เอง
- 📖 **คำอ่านภาษาอังกฤษ**: Deploy → ดีพลอย, server → เซิร์ฟเวอร์ (แก้/เพิ่มได้)
- ➕ **เพิ่มเสียงใหม่** ในแอป พร้อมถอดข้อความอัตโนมัติ (faster-whisper)
- 💾 **บันทึกค่าเริ่มต้น** (โมเดล เสียง ความเร็ว คุณภาพ)
- 🧩 **ต่อยอดง่าย**: เพิ่มตัวสร้างเสียงใหม่ได้ด้วยไฟล์เดียว ([docs/EXTENDING.md](docs/EXTENDING.md))

## ความต้องการ (Requirements)

- Windows 10/11, Python 3.10 หรือ 3.11, Git
- การ์ดจอ NVIDIA (4 GB ขึ้นไป) แนะนำ ไม่มีก็รันบน CPU ได้แต่ช้ามาก (Edge TTS ไม่ต้องใช้การ์ดจอ)
- พื้นที่ว่าง ~10 GB, อินเทอร์เน็ตตอนติดตั้งและตอนใช้ Edge TTS

## ติดตั้ง (Install)

```bash
git clone https://github.com/reeriicode/thai-voice-clone.git
cd thai-voice-clone
setup.bat
```

`setup.bat` สร้าง `.venv`, ติดตั้ง PyTorch (CUDA 12.6) และแพ็กเกจทั้งหมดให้

## ใช้งาน (Usage)

ดับเบิลคลิก **`start.bat`** แล้วเบราว์เซอร์จะเปิด http://127.0.0.1:7860 (ครั้งแรกจะดาวน์โหลดโมเดลไทย ~1.3 GB)

| แท็บ | ทำอะไร |
|---|---|
| พูดประโยคเดียว | เลือกเสียง พิมพ์ข้อความ กดสร้าง |
| บทสนทนา | พิมพ์บททีละบรรทัด `ผช: ...` / `ผญ: ...` แล้วกดสร้าง |
| เพิ่มเสียง | อัปโหลด/อัดคลิป กดถอดข้อความ บันทึกเป็นเสียงใหม่ |

ด้านบนสุดเลือก **โมเดล** ได้ (ติ๊ก "แสดงโมเดลที่ยังไม่ได้ดาวน์โหลด" เพื่อดูทั้งหมด)

### คำสั่ง (CLI)

```bash
.venv\Scripts\python speak.py --text "สวัสดีครับ"
.venv\Scripts\python speak.py --voice female --model edge --text "สวัสดีค่ะ" --play
.venv\Scripts\python speak.py --list            # รายชื่อเสียง
.venv\Scripts\python speak.py --list-models     # รายชื่อโมเดล
.venv\Scripts\python dialogue.py --script dialogues\deploy.txt
```

### ตัวอย่างบทสนทนา

```
ผช: Deploy คือการเอาเว็บของเราไปวางไว้บน server ให้คนอื่นเข้ามาใช้งานได้
ผญ: แล้วทำไมต้อง Deploy ล่ะ?
ผช: ก็เพราะถ้าไม่ deploy คนอื่นเข้ามาใช้เว็บเราไม่ได้ไงล่ะ hahaha
```

ใส่ชื่อตัวละครแทนได้ (`เบน:` `แอน:`) หรือไม่ใส่เลยก็ได้ จะสลับเสียง A/B ให้เอง

## โมเดล (Models)

| id | โมเดล | หมายเหตุ |
|---|---|---|
| `th_v1` | ไทย v1 (แนะนำ) | ค่าเริ่มต้น |
| `edge` | Microsoft Edge TTS | ออนไลน์ เสียงสำเร็จรูป ไม่ใช่เสียงโคลน |
| `th_v2` | ไทย v2 IPA | ลดการข้ามคำ/พูดซ้ำ |
| `th_v2_250k`, `th_v1_850k` ... | รุ่นเก่า | ลองเทียบเสียง |
| `orig_v1`, `orig_base` | ต้นฉบับ F5-TTS (SWivid) | อังกฤษ/จีน อ่านไทยไม่ได้ |

โมเดลดาวน์โหลดอัตโนมัติตอนเลือกใช้ครั้งแรก เก็บใน `models/downloaded/`
โมเดลที่ train เองวางใน `models/custom/` (วิธีเทรน: [docs/TRAINING.md](docs/TRAINING.md))

## โครงสร้างโฟลเดอร์ (Project layout)

```
├─ start.bat / setup.bat     เปิดแอป / ติดตั้ง
├─ app.py, speak.py, dialogue.py
├─ vtuber_tts/               โค้ดหลัก (engine, backends, app, cli)
├─ config/
│  ├─ models.json            รายชื่อโมเดล
│  ├─ pronunciations.json    คำอ่านภาษาอังกฤษ
│  └─ settings.json          ค่าเริ่มต้นของคุณ (ไม่ขึ้น git)
├─ voices/                   เสียง (ขึ้น git เฉพาะเสียงตัวอย่าง)
├─ dialogues/                บทสนทนาตัวอย่าง
├─ models/                   downloaded/, custom/, whisper/ (ไม่ขึ้น git)
├─ assets/vocab/             vocab ของ F5-TTS-THAI
├─ docs/EXTENDING.md         วิธีต่อยอดโค้ด (เพิ่ม backend/แท็บ)
├─ docs/TRAINING.md          วิธีเทรนโมเดลเสียงตัวเอง
├─ outputs/                  ไฟล์เสียงที่สร้าง (ไม่ขึ้น git)
└─ data/                     เสียงบันทึก/ข้อมูล train ของคุณ (ไม่ขึ้น git)
```

## เคล็ดลับ (Tips)

- อ่านข้ามคำหรือพูดซ้ำ: ลดความเร็วเป็น 0.8-0.9 หรือลองโมเดล `th_v2`
- เสียงไม่เหมือน: ใช้คลิปที่สะอาดกว่า (ห้องเงียบ ไม่มีเพลง) และ `ref_text` ต้องตรงกับที่พูด
- คำอังกฤษอ่านผิด: เพิ่มใน `config/pronunciations.json` หรือในแอป (แท็บบทสนทนา → 📖)
- เร็วขึ้น: ลดคุณภาพ (NFE Step) เป็น 16

## ข้อควรระวัง (Responsible use)

โคลนเสียงเฉพาะเสียงของตัวเอง หรือเสียงที่เจ้าของอนุญาตแล้วเท่านั้น
ห้ามใช้ปลอมเป็นผู้อื่นหรือหลอกลวง / Only clone voices you own or have permission to use.

## เครดิต (Credits)

- [F5-TTS](https://github.com/SWivid/F5-TTS) (SWivid) และ [F5-TTS-THAI](https://github.com/VYNCX/F5-TTS-THAI) (VYNCX / VIZINTZOR), MIT
- [edge-tts](https://github.com/rany2/edge-tts), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [Gradio](https://gradio.app)

## License

[MIT](LICENSE)
