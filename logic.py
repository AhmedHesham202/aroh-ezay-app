import sqlite3
import google.generativeai as genai
import os
from dotenv import load_dotenv # مكتبة قراءة ملف الـ .env

# تحميل البيانات من ملف .env
load_dotenv()

# --- إعدادات Gemini API ---
# ⚠️ متنساش تحط مفتاحك هنا
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("Groq_API_KEY")
# إعداد المكتبة (النسخة المستقرة)
genai.configure(api_key=GOOGLE_API_KEY)

def get_db_connection():
    conn = sqlite3.connect('aroh_ezay.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- دوال الكاش (الذاكرة) ---
def get_cached_ai_response(from_loc, to_loc):
    """التدويـر في الكاش عن رد سابق"""
    conn = get_db_connection()
    query = "SELECT response_text FROM ai_routes_cache WHERE from_loc = ? AND to_loc = ?"
    result = conn.execute(query, (from_loc, to_loc)).fetchone()
    conn.close()
    return result['response_text'] if result else None

def save_ai_response_to_cache(from_loc, to_loc, text):
    """حفظ رد الـ AI في الكاش للمستقبل"""
    conn = get_db_connection()
    query = "INSERT INTO ai_routes_cache (from_loc, to_loc, response_text) VALUES (?, ?, ?)"
    conn.execute(query, (from_loc, to_loc, text))
    conn.commit()
    conn.close()

# --- دوال الـ AI ---

import google.generativeai as genai
from groq import Groq

def get_ai_advice(from_loc, to_loc):
    # 1. تجهيز البرومبت مرة واحدة
    prompt = f"""
    أنت خبير مواصلات في القاهرة. مستخدم بيسأل إزاي يروح من {from_loc} لـ {to_loc}.
    جاوب بلهجة مصرية عامية بسيطة. نظم الإجابة في نقط.
    قوله يركب إيه والأسعار والوقت التقريبي.
    نبه دايما عليه ان الاسعار اللي بتديهاله هي اسعار تقريبيه مش بالظبط عشان دايما اسعار المواصلات في تغير.
    لو مش عارف الطريق، قوله يروح لأقرب محطة مترو ويسأل هناك.
    اكتب الرد كنص فقط بدون رموز غريبة.
    """

    # 2. قائمة الموديلات بالترتيب (الأولوية من الأول للأخير)
    # ضيف هنا أي موديل جديد تحب تجربه في المستقبل بسهولة
    gemini_models_priority = [
        'gemini-3-flash-preview',                # أحدث وأذكى (تجريبي)
        'gemini-2.5-flash',                      # الأساسي القوي
        'gemini-2.5-flash-preview-09-2025',      # بديل أول
        'gemini-2.5-flash-lite-preview-09-2025'  # بديل خفيف وسريع
    ]

    # 3. محاولة استخدام موديلات Gemini بالترتيب
    for model_name in gemini_models_priority:
        try:
            # print(f"Trying Gemini Model: {model_name}...") # (اختياري) للدييباج عشان تعرف هو شغال بـ مين
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            # لو نجح ورجع نص، نرجعه ونخرج من الدالة فوراً
            if response.text:
                return response.text
                
        except Exception as e:
            # لو فشل، بنطبع الخطأ ونكمل اللفة للي بعده (continue)
            print(f"⚠️ Failed with {model_name}: {e}")
            continue 

    # 4. لو اللوب خلصت ومفيش ولا موديل Gemini اشتغل، نروح لـ Groq (الملاذ الأخير)
    try:
        print("🔻 All Gemini models failed. Switching to Groq...")
        groq_client = Groq(api_key= GROQ_API_KEY) # تأكد إن المفتاح موجود
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content
        
    except Exception as groq_error:
        print(f"❌ Groq also failed: {groq_error}")
        return "⚠️ معلش، السيستم عليه ضغط كبير حالياً ومش قادرين نوصل للموديل دلوقتي. جرب تاني كمان دقيقة."




# --- دوال المعالجة والعرض ---
def clean_text(text):
    if not text: return ""
    return text.replace("محطة ", "").replace("اتجاه ", "")

def humanize_step(step):
    t_type = step['transport_type']
    line = step['line_name']
    boarding = step['boarding_point']
    exit_p = step['exit_point']
    direction = step['direction_details']
    tip = step['human_tip']

    if t_type == 'مترو':
        msg = f"هتركب المترو من محطة {clean_text(boarding)} ({line}) في اتجاه {clean_text(direction)}، وهتنزّل في محطة {clean_text(exit_p)}."
    elif t_type == 'ميكروباص':
        loc_desc = f"وده هتلاقيه بيحمّل من {boarding}" if boarding else "اسأل عليه في الموقف العمومي"
        msg = f"هتركب ميكروباص {line}، {loc_desc}، وهتنزّل عند {exit_p}."
    else:
        msg = f"اركب {t_type} ({line}) من {boarding} وانزل في {exit_p}."

    if tip: msg += f" (نصيحة: {tip})"
    return msg

# --- الدالة الرئيسية (The Brain) ---
def search_routes_logic(from_area, to_area):
    conn = get_db_connection()
    
    # 1. البحث في الداتا بيز الأصلية (Structured Data)
    query = """
        SELECT r.* FROM routes r
        JOIN locations l1 ON r.from_location_id = l1.id
        JOIN locations l2 ON r.to_location_id = l2.id
        WHERE l1.name LIKE ? AND l2.name LIKE ?
    """
    db_routes = conn.execute(query, (f'%{from_area}%', f'%{to_area}%')).fetchall()
    conn.close()
    
    results = []
    
    # لو لقينا داتا منظمة، نعرضها
    if db_routes:
        for route in db_routes:
            # فتح اتصال جديد لجلب الخطوات
            conn_steps = get_db_connection()
            steps_query = "SELECT * FROM route_steps WHERE route_id = ? ORDER BY step_order"
            steps = conn_steps.execute(steps_query, (route['id'],)).fetchall()
            conn_steps.close()
            
            results.append({
                "type": "db",
                "total_price": route['total_price'],
                "total_time": route['total_time'],
                "tag": route['route_tag'],
                "steps": [humanize_step(s) for s in steps]
            })
        return results

    # 2. لو مفيش داتا منظمة -> نشوف "الكاش" (هل حد سأل السؤال ده قبل كده؟)
    cached_response = get_cached_ai_response(from_area, to_area)
    if cached_response:
        # يا سلام! لقيناه متخزن، نرجعه علطول من غير ما نكلم جوجل
        return [{"type": "ai", "content": cached_response, "source": "cache"}]

    # 3. لو مش في الكاش -> نكلم Gemini (Live Request)
    ai_msg = get_ai_advice(from_area, to_area)
    
    if ai_msg:
        # نحفظ الرد في الكاش عشان المرة الجاية
        save_ai_response_to_cache(from_area, to_area, ai_msg)
        return [{"type": "ai", "content": ai_msg, "source": "live"}]
    else:
        # لو حتى Gemini مردش (نت قاطع أو خطأ)
        return [{"type": "ai", "content": "معلش السيستم واقع، اسأل أقرب سواق."}]

def get_all_areas_logic(search_term):
    conn = get_db_connection()
    query = "SELECT name FROM locations WHERE name LIKE ?"
    areas = conn.execute(query, (f'%{search_term}%',)).fetchall()
    conn.close()
    return [a['name'] for a in areas]


