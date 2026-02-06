import streamlit as st
import os
import io
from groq import Groq
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

# 1. إعدادات الصفحة والواجهة
st.set_page_config(page_title="مساعد الصيدلة الذكي Pro", page_icon="💊", layout="wide")
st.title("🎙️ منصة تفريغ وتلخيص المحاضرات الصيدلانية")

# 2. جلب مفاتيح API من الأسرار (Secrets)
api_keys = [
    st.secrets.get("groq_api_key_1"),
    st.secrets.get("groq_api_key_2")
]
api_keys = [k for k in api_keys if k]

if not api_keys:
    st.error("⚠️ خطأ: لم يتم العثور على مفاتيح API. يرجى إضافتها في الإعدادات باسم groq_api_key_1 و groq_api_key_2")
    st.stop()

# 3. رفع الملف ومعالجته
uploaded_file = st.file_uploader("ارفع ملف المحاضرة (أقل من 25MB)", type=["mp3", "wav", "m4a"])

if uploaded_file:
    # قراءة الملف مرة واحدة في الذاكرة لتجنب خطأ "File is Empty"
    file_bytes = uploaded_file.read()
    
    if st.button("🚀 بدء المعالجة الاحترافية"):
        raw_text = ""
        success_client = None
        
        # محاولة التحويل مع نظام التبديل التلقائي (Rotation)
        for i, key in enumerate(api_keys):
            try:
                client = Groq(api_key=key)
                with st.spinner(f"جاري التفريغ باستخدام الحساب رقم ({i+1})..."):
                    # توجيه Whisper لكتابة المصطلحات بالإنجليزية والحفاظ على العامية
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=(uploaded_file.name, io.BytesIO(file_bytes)),
                        language="ar",
                        prompt="Keep the Egyptian slang. Write medical terms in English: Pharmacology, Amlodipine, Gastritis, Mechanism of action."
                    )
                    raw_text = transcription.text
                    success_client = client
                    break 
            except Exception as e:
                if "rate_limit_exceeded" in str(e):
                    st.warning(f"⚠️ الحساب رقم ({i+1}) وصل للحد الأقصى، جاري التبديل...")
                    continue
                else:
                    st.error(f"❌ حدث خطأ: {e}")
                    st.stop()
        
        if not raw_text:
            st.error("❌ جميع الحسابات وصلت للحد الأقصى. يرجى المحاولة بعد 30 دقيقة.")
            st.stop()

        # المرحلة الثانية: التنقيح الطبي العميق
        try:
            with st.spinner("جاري تنسيق النص وتصحيح المصطلحات الإنجليزية..."):
                med_prompt = f"""
                أنت صيدلي خبير. النص التالي هو تفريغ لمحاضرة مصرية.
                المطلوب:
                1- حافظ على اللهجة العامية كما هي بدون "فصحنة".
                2- أي اسم دواء أو مصطلح علمي اكتبه بالإنجليزية وبإملاء صحيح.
                3- لا تكتب الكلمات الإنجليزية بحروف عربية (اكتب Aspirin وليس أسبرين).
                4- لخص المحاضرة في نقاط منظمة تحت عنوان "الخلاصة الطبية".
                
                النص: {raw_text[:15000]}
                """
                completion = success_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": med_prompt}]
                )
                refined_output = completion.choices[0].message.content

            st.success("✅ تمت المعالجة بنجاح!")

            # 4. عرض النتائج في تبويبات
            tab1, tab2 = st.tabs(["📝 الملخص والمنقح", "📄 النص كما قيل"])
            with tab1:
                st.markdown(refined_output)
            with tab2:
                st.write(raw_text)

            # 5. زر تحميل PDF (يُفضل استخدامه للملخص فقط لضمان جودة التنسيق)
            def create_pdf(text_content):
                pdf = FPDF()
                pdf.add_page()
                font_path = "Amiri-Regular.ttf"
                if os.path.exists(font_path):
                    pdf.add_font("Amiri", "", font_path)
                    pdf.set_font("Amiri", size=12)
                else:
                    pdf.set_font("Arial", size=12)
                
                reshaped = arabic_reshaper.reshape(text_content)
                bidi_text = get_display(reshaped)
                pdf.multi_cell(0, 10, bidi_text, align='R')
                pdf.output("Pharmacy_Summary.pdf")
                return "Pharmacy_Summary.pdf"

            pdf_file = create_pdf(refined_output)
            with open(pdf_file, "rb") as f:
                st.download_button("📥 تحميل الملخص PDF", f, file_name="Pharmacy_Lecture.pdf")

        except Exception as e:
            st.error(f"حدث خطأ في التنسيق: {e}")
