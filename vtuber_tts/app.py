"""Web app (Gradio): pick a model and voice, type text or a dialogue script, get speech.

Run with start.bat (or: python app.py). Saved defaults live in config/settings.json.
"""
import os
import time

import gradio as gr
import soundfile as sf

from .config import DEFAULTS, load_config, save_config
from .engine import VoiceEngine
from .models import default_model_name, find_model, is_downloaded, list_models
from .paths import OUTPUTS_DIR as OUT_DIR
from .stt import transcribe
from .text import load_pronunciations, parse_script, save_pronunciations
from .voices import add_voice, default_voice_name, find_voice, list_voices

engine = None  # created in main()


def preview(voice_name):
    v = list_voices().get(voice_name)
    return v["ref_audio"] if v else None


# ---------- Model picker ----------

def model_status(selected):
    _, info = find_model(selected)
    if not info:
        return ""
    if engine.model_info["id"] == info["id"]:
        state = "✅ ใช้อยู่ตอนนี้"
    elif is_downloaded(info):
        state = "📦 ดาวน์โหลดแล้ว (กดสร้างแล้วจะสลับให้)"
    else:
        state = f"⬇️ ยังไม่ได้ดาวน์โหลด ({info.get('size_mb', 0) / 1000:.1f} GB) จะดาวน์โหลดตอนกดโหลดหรือกดสร้างครั้งแรก"
    warn = "" if info.get("thai", True) or info.get("type") != "f5" else " · ⚠️ อ่านภาษาไทยไม่ได้ ให้พิมพ์ภาษาอังกฤษ"
    return f"**{info['name']}**: {info.get('note', '')}{warn}  \n{state}"


def ensure_model(selected, progress=None):
    """Switch the engine to the selected model if it is not the one loaded."""
    _, info = find_model(selected)
    if not info:
        raise gr.Error("กรุณาเลือกโมเดล")
    if engine.model_info["id"] != info["id"]:
        if progress:
            msg = "กำลังสลับโมเดล" if is_downloaded(info) else "กำลังดาวน์โหลดโมเดล (ดูความคืบหน้าในหน้าต่างดำ)"
            progress(0, desc=msg)
        try:
            engine.load(info["id"])
        except Exception as e:
            raise gr.Error(f"โหลดโมเดลไม่สำเร็จ: {e}")


def model_choices(show_all, selected):
    choices = list(list_models(downloaded_only=not show_all))
    value = selected if selected in choices else engine.model_name
    return gr.update(choices=choices, value=value, label="โมเดล (ทั้งหมด)" if show_all else "โมเดล (ที่มีในเครื่อง)")


def load_selected_model(selected, progress=gr.Progress()):
    ensure_model(selected, progress)
    return model_status(selected)


def current_settings():
    """Values for [voice, speed, nfe, seed, remove_silence, preview, model] from config.json."""
    cfg = load_config()
    name = default_voice_name()
    return (gr.update(choices=list(list_voices()), value=name), cfg["speed"], cfg["nfe"],
            cfg["seed"], cfg["remove_silence"], preview(name), default_model_name())


def refresh_voices(selected):
    choices = list(list_voices())
    value = selected if selected in choices else default_voice_name()
    return gr.update(choices=choices, value=value), preview(value)


def save_defaults(model_name, voice_name, speed, nfe, seed, remove_silence):
    _, v = find_voice(voice_name)
    _, m = find_model(model_name)
    save_config(model=m["id"] if m else None, voice=v["id"] if v else None, speed=float(speed),
                nfe=int(nfe), seed=int(seed), remove_silence=bool(remove_silence))
    return (f"💾 บันทึกค่าเริ่มต้นแล้ว: โมเดล **{model_name}** · เสียง **{voice_name}** · "
            f"ความเร็ว {speed} · คุณภาพ {int(nfe)}")


def reset_defaults():
    save_config(**DEFAULTS)
    return (*current_settings(), "↺ คืนค่าเริ่มต้นจากโรงงานแล้ว")


def generate(model_name, voice_name, text, speed, nfe, seed, remove_silence, progress=gr.Progress()):
    voices = list_voices()
    if voice_name not in voices:
        raise gr.Error("กรุณาเลือกเสียง")
    if not text or not text.strip():
        raise gr.Error("กรุณาพิมพ์ข้อความ")
    ensure_model(model_name, progress)
    v = voices[voice_name]
    t0 = time.time()
    sr, wave, used_seed = engine.speak(text, v, speed=speed, nfe=nfe, seed=int(seed),
                                       remove_silence=remove_silence)
    out = os.path.join(OUT_DIR, f"{time.strftime('%Y%m%d-%H%M%S')}_{v['id']}_{engine.model_info['id']}.wav")
    sf.write(out, wave, sr)
    info = (f"สร้างเสร็จใน {time.time() - t0:.1f} วินาที · โมเดล {engine.model_name} · seed {used_seed} · "
            f"บันทึกที่ outputs/{os.path.basename(out)}")
    return out, info, model_status(model_name)


# ---------- Dialogue ----------

EXAMPLE_SCRIPT = """ผช: Deploy คือ ง่ายๆเลยคือการเอาเว็บของเราไปวางไว้บน server ให้คนอื่นเข้ามาใช้งานได้
ผญ: แล้วทำไมต้อง Deploy ล่ะ?
ผช: ก็เพราะถ้าไม่ deploy คนอื่นเข้ามาใช้เว็บเราไม่ได้ไงล่ะ hahaha
ผญ: อ่าว กวนตีนนี่หว่า
ผช: โอเคๆ เดี๋ยวอธิบายดีๆ ตอนเรา dev เว็บอยู่เนี่ย เว็บมันรันอยู่บน local หรือก็คือในเครื่องเราเอง เราเปิด localhost ได้ แต่เพื่อนเราเปิดไม่ได้ เพราะมันอยู่ในเครื่องเรา ไม่ได้อยู่บนอินเทอร์เน็ต"""


def other_voice(name):
    names = list(list_voices())
    rest = [n for n in names if n != name]
    return rest[0] if rest else name


def script_table(script, voice_a, voice_b):
    try:
        lines = parse_script(script or "", voice_a, voice_b)
    except ValueError as e:
        raise gr.Error(str(e))
    return [[i + 1, sp, name, engine.prepare_text(t)] for i, (sp, name, t) in enumerate(lines)]


def generate_dialogue(model_name, script, voice_a, voice_b, pause, speed, progress=gr.Progress()):
    try:
        lines = parse_script(script or "", voice_a, voice_b)
    except ValueError as e:
        raise gr.Error(str(e))
    if not lines:
        raise gr.Error("กรุณาพิมพ์บทพูด")
    ensure_model(model_name, progress)
    t0 = time.time()

    def on_line(i, total, line):
        progress(i / total, desc=f"บรรทัด {i + 1}/{total} ({line[0]})")

    sr, combined, parts = engine.speak_dialogue(lines, pause=pause, speed=speed, progress=on_line)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    folder = os.path.join(OUT_DIR, f"dialogue_{stamp}")
    os.makedirs(folder, exist_ok=True)
    voices = list_voices()
    for i, (sp, name, _, wave) in enumerate(parts, 1):
        sf.write(os.path.join(folder, f"{i:02d}_{voices[name]['id']}.wav"), wave, sr)
    out = os.path.join(OUT_DIR, f"dialogue_{stamp}.wav")
    sf.write(out, combined, sr)
    table = [[i + 1, sp, name, engine.prepare_text(t)] for i, (sp, name, t, _) in enumerate(parts)]
    info = (f"สร้าง {len(parts)} บรรทัด ยาว {len(combined) / sr:.1f} วินาที ใน {time.time() - t0:.1f} วินาที · "
            f"โมเดล {engine.model_name} · ไฟล์รวม outputs/{os.path.basename(out)} · "
            f"แยกรายบรรทัดใน outputs/dialogue_{stamp}/")
    return out, table, info, model_status(model_name)


# ---------- Add a new voice ----------

def transcribe_clip(audio_path, progress=gr.Progress()):
    if not audio_path:
        raise gr.Error("กรุณาอัปโหลดหรืออัดคลิปเสียงก่อน")
    progress(0, desc="กำลังถอดข้อความด้วย faster-whisper medium")
    try:
        text = transcribe(audio_path)
    except Exception as e:
        raise gr.Error(f"ถอดข้อความไม่สำเร็จ: {e}")
    return text, "📝 ถอดข้อความแล้ว ตรวจและแก้ให้ตรงกับที่พูดจริงก่อนบันทึก (คำอังกฤษเขียนเป็นคำอ่านไทย)"


def save_new_voice(audio_path, name, gender, ref_text):
    if not audio_path:
        raise gr.Error("กรุณาอัปโหลดหรืออัดคลิปเสียงก่อน")
    if not name or not name.strip():
        raise gr.Error("กรุณาตั้งชื่อเสียง")
    if not ref_text or not ref_text.strip():
        raise gr.Error("กรุณาใส่ข้อความที่พูดในคลิป (กดถอดข้อความก็ได้)")
    vid, dur = add_voice(audio_path, name, ref_text, "female" if gender == "ผู้หญิง" else "male")
    choices = list(list_voices())
    warn = " ⚠️ คลิปยาวเกิน 10 วินาที เสียงที่ได้อาจเพี้ยน ลองตัดให้สั้นลง" if dur > 10 else ""
    short = " ⚠️ คลิปสั้นมาก ควรยาว 5-8 วินาที" if dur < 3 else ""
    msg = f"✅ บันทึกเสียง **{name.strip()}** แล้ว ({dur:.1f} วินาที) ที่ voices/{vid}/{warn}{short}"
    return (msg, gr.update(choices=choices, value=name.strip()), gr.update(choices=choices),
            gr.update(choices=choices))


def pron_rows():
    return [[k, v] for k, v in load_pronunciations().items()]


def save_pron(rows):
    rows = rows.values.tolist() if hasattr(rows, "values") else rows
    saved = save_pronunciations({str(r[0]): str(r[1]) for r in rows if len(r) >= 2 and r[0] and r[1]})
    return [[k, v] for k, v in saved.items()], f"💾 บันทึกคำอ่าน {len(saved)} คำแล้ว"


def build_ui():
    cfg = load_config()
    start_voice = default_voice_name()

    with gr.Blocks(title="เสียงพากย์ VTuber", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# เสียงพากย์ VTuber\nเลือกเสียง พิมพ์ข้อความภาษาไทย แล้วกดสร้าง")

        with gr.Row(equal_height=True):
            model_dd = gr.Dropdown(choices=list(list_models(downloaded_only=True)), value=engine.model_name,
                                   label="โมเดล (ที่มีในเครื่อง)", scale=3)
            load_btn = gr.Button("⬇️ โหลดโมเดลนี้", scale=1)
        show_all = gr.Checkbox(value=False, label="แสดงโมเดลที่ยังไม่ได้ดาวน์โหลดด้วย")
        m_status = gr.Markdown(model_status(engine.model_name))

        with gr.Tab("พูดประโยคเดียว"), gr.Row():
            with gr.Column():
                voice = gr.Radio(choices=list(list_voices()), value=start_voice, label="เลือกเสียง")
                with gr.Accordion("ฟังเสียงต้นแบบ", open=False):
                    ref_preview = gr.Audio(value=preview(start_voice), label="เสียงต้นแบบ",
                                           interactive=False)
                    refresh_btn = gr.Button("🔄 โหลดรายชื่อเสียงใหม่", size="sm")
                text = gr.Textbox(label="ข้อความที่จะพูด", lines=4,
                                  placeholder="เช่น สวัสดีครับทุกคน ยินดีต้อนรับเข้าสตรีมนะครับ")
                speed = gr.Slider(0.5, 1.5, value=cfg["speed"], step=0.05, label="ความเร็ว",
                                  info="ถ้าอ่านข้ามคำ ลองลดเหลือ 0.8-0.9")
                with gr.Accordion("ตั้งค่าเพิ่มเติม", open=False):
                    nfe = gr.Slider(8, 64, value=cfg["nfe"], step=1, label="คุณภาพ (NFE Step)",
                                    info="มาก = ชัดขึ้นแต่ช้าลง")
                    seed = gr.Number(value=cfg["seed"], precision=0, label="Seed",
                                     info="-1 = สุ่ม · ใส่เลขเดิมเพื่อได้เสียงแบบเดิม")
                    remove_silence = gr.Checkbox(value=cfg["remove_silence"], label="ตัดช่วงเงียบ")
                btn = gr.Button("🚀 สร้างเสียง", variant="primary")
                with gr.Row():
                    save_btn = gr.Button("💾 บันทึกเป็นค่าเริ่มต้น", size="sm")
                    reset_btn = gr.Button("↺ คืนค่าโรงงาน", size="sm")
                status = gr.Markdown()
            with gr.Column():
                out_audio = gr.Audio(label="เสียงที่สร้าง", type="filepath", autoplay=True)
                info = gr.Markdown()

        with gr.Tab("บทสนทนา"):
            gr.Markdown(
                "พิมพ์บทพูดทีละบรรทัด ใส่ชื่อหน้าบรรทัดได้ เช่น `ผช:` `ผญ:` หรือชื่อตัวละคร `เบน:` `แอน:` "
                "ถ้าไม่ใส่ชื่อ จะสลับเสียง A กับ B ให้เอง"
            )
            with gr.Row():
                with gr.Column():
                    script = gr.Textbox(label="บทพูด", lines=12, value=EXAMPLE_SCRIPT)
                    with gr.Row():
                        voice_a = gr.Dropdown(choices=list(list_voices()), value=start_voice,
                                              label="เสียง A (คนพูดคนแรก)")
                        voice_b = gr.Dropdown(choices=list(list_voices()), value=other_voice(start_voice),
                                              label="เสียง B (คนตอบ)")
                    with gr.Row():
                        pause = gr.Slider(0.0, 2.0, value=0.4, step=0.1, label="เว้นระหว่างบรรทัด (วินาที)")
                        d_speed = gr.Slider(0.5, 1.5, value=cfg["speed"], step=0.05, label="ความเร็ว")
                    with gr.Row():
                        check_btn = gr.Button("👀 ตรวจบท")
                        d_btn = gr.Button("🎬 สร้างบทสนทนา", variant="primary")
                with gr.Column():
                    d_audio = gr.Audio(label="บทสนทนาที่สร้าง", type="filepath", autoplay=True)
                    d_info = gr.Markdown()
                    d_table = gr.Dataframe(headers=["#", "ผู้พูด", "เสียง", "คำที่จะอ่าน"],
                                           label="บทที่แบ่งแล้ว", wrap=True, interactive=False)

            with gr.Accordion("📖 คำอ่านภาษาอังกฤษ (เช่น Deploy → ดีพลอย)", open=False):
                gr.Markdown("แก้หรือเพิ่มแถวได้เลย แล้วกดบันทึก ใช้กับทุกเสียงทั้งสองแท็บ ตัวพิมพ์เล็ก/ใหญ่ไม่มีผล")
                pron_table = gr.Dataframe(value=pron_rows(), headers=["คำ", "คำอ่าน"], col_count=(2, "fixed"),
                                          interactive=True, wrap=True)
                pron_save = gr.Button("💾 บันทึกคำอ่าน", size="sm")
                pron_status = gr.Markdown()

        model_dd.change(model_status, model_dd, m_status)
        load_btn.click(load_selected_model, model_dd, m_status)
        show_all.change(model_choices, [show_all, model_dd], model_dd)

        with gr.Tab("เพิ่มเสียง"):
            gr.Markdown(
                "อัปโหลดหรืออัดคลิปเสียงยาว **5-8 วินาที** (เสียงสะอาด ไม่มีเพลง) กดถอดข้อความ ตรวจแก้ แล้วบันทึก "
                "จะได้เสียงใหม่ไว้เลือกใช้ทันที (ใช้กับโมเดล F5 ส่วน Edge TTS จะใช้เสียงผู้ชาย/ผู้หญิงสำเร็จรูปตามเพศที่เลือก)"
            )
            with gr.Row():
                with gr.Column():
                    nv_audio = gr.Audio(label="คลิปเสียง", type="filepath", sources=["upload", "microphone"])
                    nv_name = gr.Textbox(label="ชื่อเสียง", placeholder="เช่น เสียงตอนสตรีม, สาวน่ารัก")
                    nv_gender = gr.Radio(["ผู้ชาย", "ผู้หญิง"], value="ผู้ชาย", label="เพศ (ใช้เลือกเสียง Edge TTS)")
                with gr.Column():
                    nv_text = gr.Textbox(label="ข้อความที่พูดในคลิป", lines=4)
                    with gr.Row():
                        nv_trans_btn = gr.Button("📝 ถอดข้อความ (faster-whisper)")
                        nv_save_btn = gr.Button("💾 บันทึกเป็นเสียงใหม่", variant="primary")
                    nv_status = gr.Markdown()

        nv_trans_btn.click(transcribe_clip, nv_audio, [nv_text, nv_status])
        nv_save_btn.click(save_new_voice, [nv_audio, nv_name, nv_gender, nv_text],
                          [nv_status, voice, voice_a, voice_b])

        check_btn.click(script_table, [script, voice_a, voice_b], d_table)
        d_btn.click(generate_dialogue, [model_dd, script, voice_a, voice_b, pause, d_speed],
                    [d_audio, d_table, d_info, m_status], api_name="dialogue")
        pron_save.click(save_pron, pron_table, [pron_table, pron_status])

        settings = [voice, speed, nfe, seed, remove_silence]
        voice.change(preview, voice, ref_preview)
        refresh_btn.click(refresh_voices, voice, [voice, ref_preview])
        save_btn.click(save_defaults, [model_dd] + settings, status)
        reset_btn.click(reset_defaults, None, settings + [ref_preview, model_dd, status])
        gen_inputs = [model_dd, voice, text] + settings[1:]
        btn.click(generate, gen_inputs, [out_audio, info, m_status], api_name="generate")
        text.submit(generate, gen_inputs, [out_audio, info, m_status], api_name=False)
        # Reload saved defaults every time the page is opened
        demo.load(current_settings, None, settings + [ref_preview, model_dd])
    return demo


def main():
    global engine
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Loading model... (first time takes 1-2 minutes)")
    engine = VoiceEngine()
    print(f"Model ready on {engine.device}: {engine.model_name}")
    build_ui().launch(inbrowser=True)


if __name__ == "__main__":
    main()
