import streamlit as st
import os
import io
from groq import Groq
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

# 1. إعدادات الصفحة
st.set_page_config(page_title="مساعد الصيدلة الذكي Pro", page_icon="💊", layout="wide")
st.title("🎙️ منصة التفريغ الثلاثية (3 API Keys)")
st.markdown("---")

# 2. جلب 3 مفاتيح API من الأسرار (Secrets)
api_keys = [
    st.secrets.get("groq_api_key_1"),
    st.secrets.get("groq_api_key_2"),
    st.secrets.get("groq_api_key_3")
]
# تنقية القائمة من أي مفاتيح فارغة
api_keys = [k for k in api_keys if k]

if not api_keys:
    st.error("⚠️ لم يتم العثور على مفاتيح API. تأكد من إضافة groq_api_key_1 و 2 و 3 في Secrets.")
    st.stop()

# 3. رفع الملف ومعالجته
uploaded_file = st.file_uploader("ارفع ملف المحاضرة (أقل من 25MB)", type=["mp3", "wav", "m4a"])

if uploaded_file:
    # تخزين الملف في الذاكرة لتجنب خطأ "File is empty"
    file_bytes = uploaded_file.read()
    
    if st.button("🚀 بدء المعالجة الاحترافية"):
        raw_text = ""
        success_client = None
        
        # نظام التبديل التلقائي بين الـ 3 حسابات
        for i, key in enumerate(api_keys):
            try:
                client = Groq(api_key=key)
                with st.spinner(f"جاري المحاولة باستخدام الحساب رقم ({i+1})..."):
                    # توجيه Whisper للحفاظ على العامية وكتابة المصطلحات بالإنجليزية
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=(uploaded_file.name, io.BytesIO(file_bytes)),
                        language="ar",
                        prompt="Keep Egyptian slang. Write medical terms in English: Pharmacology, Mechanism of action, Dosage."
                    )
                    raw_text = transcription.text
                    success_client = client
                    break # نجحت العملية، اخرج من الحلقة
            except Exception as e:
                if "rate_limit_exceeded" in str(e):
                    st.warning(f"⚠️ الحساب رقم ({i+1}) وصل للحد الأقصى، جاري التبديل للحساب التالي...")
                    continue
                else:
                    st.error(f"❌ حدث خطأ: {e}")
                    st.stop()
        
        if not raw_text:
            st.error("❌ للأسف، جميع الحسابات الثلاثة وصلت للحد الأقصى. يرجى المحاولة بعد 30 دقيقة.")
            st.stop()

        # المرحلة الثانية: التنسيق والتلخيص الطبي (Llama 3.3 70B)
        try:
            with st.spinner("جاري تنسيق النص وتصحيح المصطلحات الإنجليزية..."):
                med_prompt = f"""
                أنت صيدلي خبير. النص التالي هو تفريغ لمحاضرة مصرية.
                المطلوب:
                1- حافظ على اللهجة العامية كما هي بدون تغيير.
                2- أي اسم دواء أو مصطلح علمي اكتبه بالإنجليزية حصراً وبإملاء صحيح.
                3- نسق المحتوى في نقاط واضحة (الخلاصة الطبية).
                
                النص: {raw_text[:15000]}
                """
                completion = success_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": med_prompt}]
                )
                refined_output = completion.choices[0].message.content

            st.success("✅ تمت المعالجة بنجاح!")

            # 4. عرض النتائج
            tab1, tab2 = st.tabs(["📝 الملخص والمنقح", "📄 النص كما قيل"])
            with tab1:
                st.markdown(refined_output)
            with tab2:
                st.write(raw_text)

            # 5. توليد ملف PDF (للملخص)
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
