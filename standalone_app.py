import streamlit as st
import sqlite3
import google.generativeai as genai
from groq import Groq
from streamlit_searchbox import st_searchbox
from datetime import datetime
from st_copy_to_clipboard import st_copy_to_clipboard
import urllib.parse

st.set_page_config(page_title="أروح إزاي", page_icon="🚌", layout="wide")

# Get API keys from Streamlit secrets
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
GROQ_API_KEY = st.secrets.get("Groq_API_KEY", "")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Database functions
def get_db_connection():
    conn = sqlite3.connect('aroh_ezay.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_cached_ai_response(from_loc, to_loc):
    conn = get_db_connection()
    query = "SELECT response_text FROM ai_routes_cache WHERE from_loc = ? AND to_loc = ?"
    result = conn.execute(query, (from_loc, to_loc)).fetchone()
    conn.close()
    return result['response_text'] if result else None

def save_ai_response_to_cache(from_loc, to_loc, text):
    conn = get_db_connection()
    query = "INSERT INTO ai_routes_cache (from_loc, to_loc, response_text) VALUES (?, ?, ?)"
    conn.execute(query, (from_loc, to_loc, text))
    conn.commit()
    conn.close()

def get_ai_advice(from_loc, to_loc):
    prompt = f"""
    أنت خبير مواصلات في القاهرة. مستخدم بيسأل إزاي يروح من {from_loc} لـ {to_loc}.
    جاوب بلهجة مصرية عامية بسيطة. نظم الإجابة في نقط.
    قوله يركب إيه والأسعار والوقت التقريبي.
    نبه دايما عليه ان الاسعار اللي بتديهاله هي اسعار تقريبيه مش بالظبط عشان دايما اسعار المواصلات في تغير.
    لو مش عارف الطريق، قوله يروح لأقرب محطة مترو ويسأل هناك.
    اكتب الرد كنص فقط بدون رموز غريبة.
    """

    gemini_models_priority = [
        'gemini-3-flash-preview',
        'gemini-2.5-flash',
        'gemini-2.5-flash-preview-09-2025',
        'gemini-2.5-flash-lite-preview-09-2025'
    ]

    for model_name in gemini_models_priority:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response.text:
                return response.text
        except Exception as e:
            continue

    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content
    except Exception as groq_error:
        return "⚠️ معلش، السيستم عليه ضغط كبير حالياً ومش قادرين نوصل للموديل دلوقتي. جرب تاني كمان دقيقة."

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

def search_routes_logic(from_area, to_area):
    conn = get_db_connection()
    query = """
        SELECT r.* FROM routes r
        JOIN locations l1 ON r.from_location_id = l1.id
        JOIN locations l2 ON r.to_location_id = l2.id
        WHERE l1.name LIKE ? AND l2.name LIKE ?
    """
    db_routes = conn.execute(query, (f'%{from_area}%', f'%{to_area}%')).fetchall()
    conn.close()
    
    results = []
    
    if db_routes:
        for route in db_routes:
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

    cached_response = get_cached_ai_response(from_area, to_area)
    if cached_response:
        return [{"type": "ai", "content": cached_response, "source": "cache"}]

    ai_msg = get_ai_advice(from_area, to_area)
    
    if ai_msg:
        save_ai_response_to_cache(from_area, to_area, ai_msg)
        return [{"type": "ai", "content": ai_msg, "source": "live"}]
    else:
        return [{"type": "ai", "content": "معلش السيستم واقع، اسأل أقرب سواق."}]

def get_all_areas_logic(search_term):
    conn = get_db_connection()
    query = "SELECT name FROM locations WHERE name LIKE ?"
    areas = conn.execute(query, (f'%{search_term}%',)).fetchall()
    conn.close()
    return [a['name'] for a in areas]

# Initialize Session State
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'from_location' not in st.session_state:
    st.session_state.from_location = None
if 'to_location' not in st.session_state:
    st.session_state.to_location = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

def add_to_history(from_loc, to_loc, result_count):
    timestamp = datetime.now().strftime("%H:%M - %d/%m")
    history_item = {
        'from': from_loc,
        'to': to_loc,
        'time': timestamp,
        'count': result_count
    }
    
    st.session_state.search_history = [
        h for h in st.session_state.search_history 
        if not (h['from'] == from_loc and h['to'] == to_loc)
    ]
    
    st.session_state.search_history.insert(0, history_item)
    st.session_state.search_history = st.session_state.search_history[:4]

def parse_ai_response(content):
    lines = content.split('\n')
    formatted_html = ""
    
    in_list = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.endswith(':') and len(line) < 100:
            if in_list:
                formatted_html += "</ul>"
                in_list = False
            formatted_html += f'<h4 style="color: #4CAF50; margin-top: 15px; margin-bottom: 8px;">📌 {line}</h4>'
        
        elif line.startswith(('- ', '* ', '• ')) or (len(line) > 2 and line[0].isdigit() and line[1] in '.-) '):
            if not in_list:
                formatted_html += '<ul style="margin-right: 20px; line-height: 1.8;">'
                in_list = True
            clean_line = line.lstrip('-*•0123456789.) ')
            formatted_html += f'<li style="margin-bottom: 8px;">{clean_line}</li>'
        
        else:
            if in_list:
                formatted_html += "</ul>"
                in_list = False
            
            if any(keyword in line for keyword in ['اركب', 'انزل', 'امشي', 'خد', 'روح', 'اتجه']):
                formatted_html += f'<p style="background: rgba(31, 119, 180, 0.1); padding: 10px; border-radius: 8px; margin: 8px 0; border-right: 3px solid #1f77b4;">🚶 {line}</p>'
            else:
                formatted_html += f'<p style="margin: 10px 0; line-height: 1.7;">{line}</p>'
    
    if in_list:
        formatted_html += "</ul>"
    
    return formatted_html

def get_suggestions(search_term):
    if not search_term:
        return []
    
    suggestions = [search_term]
    db_suggestions = get_all_areas_logic(search_term)
    
    for suggestion in db_suggestions:
        if suggestion not in suggestions:
            suggestions.append(suggestion)
    
    return suggestions

def format_route_for_copy(item, from_loc, to_loc):
    if item['type'] == 'db':
        text = f"🚌 الطريق من {from_loc} إلى {to_loc}\n"
        text += f"💰 التكلفة: {item['total_price']} جنيه\n"
        text += f"⏱️ الوقت: {item['total_time']} دقيقة\n"
        text += f"📌 {item['tag']}\n\n"
        text += "📍 الخطوات:\n"
        for i, step in enumerate(item['steps'], 1):
            text += f"{i}. {step}\n"
        text += "\n🔗 تطبيق أروح إزاي"
        return text
    else:
        import re
        clean_text = item['content'].replace('<br>', '\n')
        clean_text = re.sub('<[^<]+?>', '', clean_text)
        return f"🚌 الطريق من {from_loc} إلى {to_loc}\n\n{clean_text}\n\n⚠️ ملحوظة: هذا المسار تم إنشاءه بواسطة الذكاء الاصطناعي\n🔗 تطبيق أروح إزاي"

def share_on_whatsapp(route_text):
    encoded_text = urllib.parse.quote(route_text)
    return f"https://wa.me/?text={encoded_text}"

# CSS (same as before but inline)
if st.session_state.dark_mode:
    bg_color = "#1E1E1E"
    text_color = "#FFFFFF"
    card_bg = "#2D2D2D"
    input_bg = "#3D3D3D"
    border_color = "#FF4B4B"
    ai_card_bg = "#1a3d1a"
    step_box_bg = "#3a3a3a"
    sidebar_bg = "#252525"
else:
    bg_color = "#FFFFFF"
    text_color = "#000000"
    card_bg = "#FFFFFF"
    input_bg = "#F0F2F6"
    border_color = "#FF4B4B"
    ai_card_bg = "#f0f9f0"
    step_box_bg = "#f8f9fa"
    sidebar_bg = "#f0f2f6"

st.markdown(f"""
    <style>
    .stApp {{ 
        direction: RTL; 
        text-align: right;
        background-color: {bg_color};
        color: {text_color};
    }}
    
    h1, h2, h3, h4, p, span, div {{
        text-align: right !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
    }}
    
    .route-card {{
        background: {card_bg};
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        border-right: 10px solid {border_color};
        color: {text_color};
    }}
    
    .ai-card {{ 
        border-right: 10px solid #4CAF50;
        background: {ai_card_bg};
        font-size: 1.05em;
        line-height: 1.8;
    }}
    
    .step-box {{
        background: {step_box_bg};
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        border-right: 4px solid #1f77b4;
        color: {text_color};
    }}
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🕒 آخر رحلاتك")
    
    if st.session_state.search_history:
        for idx, item in enumerate(st.session_state.search_history):
            if st.button(
                f"🚌 {item['from']} ← {item['to']}\n⏰ {item['time']} | 📊 {item['count']} طريق",
                key=f"history_{idx}",
                use_container_width=True
            ):
                st.session_state.from_location = item['from']
                st.session_state.to_location = item['to']
                st.rerun()
            st.markdown("---")
    else:
        st.info("📍 لسه مفيش رحلات\nابدأ ابحث عن طريقك!")
    
    st.markdown("### ⚙️ الإعدادات")
    theme_label = "🌙 الوضع الليلي" if not st.session_state.dark_mode else "☀️ الوضع النهاري"
    if st.button(theme_label, use_container_width=True):
        toggle_theme()
        st.rerun()

# Main Content
st.title("🚌 أروح إزاي")
st.write("اختار من الاقتراحات أو اكتب منطقتك واختارها من القائمة")

col1, col2 = st.columns(2)

with col1:
    from_loc = st_searchbox(
        get_suggestions,
        key="from_search",
        placeholder="أنت فين؟ (مثلاً: رمسيس)",
        clear_on_submit=False,
        default=st.session_state.from_location
    )

with col2:
    to_loc = st_searchbox(
        get_suggestions,
        key="to_search",
        placeholder="رايح فين؟ (مثلاً: التجمع)",
        clear_on_submit=False,
        default=st.session_state.to_location
    )

if st.button("وَرّيني الطريق 🔍", use_container_width=True, type="primary"):
    if from_loc and to_loc:
        if from_loc == to_loc:
            st.warning("⚠️ يا هندسة أنت في نفس المكان!")
        else:
            st.session_state.from_location = from_loc
            st.session_state.to_location = to_loc
            
            with st.spinner("🔍 بندور على أحسن طريق ليك..."):
                results = search_routes_logic(from_loc, to_loc)
                st.session_state.search_results = results
                
                if results:
                    add_to_history(from_loc, to_loc, len(results))
    else:
        st.info("ℹ️ اختار المكانين من القائمة الأول يا برنس 😉")

# Display Results
if st.session_state.search_results:
    results = st.session_state.search_results
    from_loc = st.session_state.from_location
    to_loc = st.session_state.to_location
    
    if results:
        st.success("✅ لقينا الطريق!")
        
        for idx, item in enumerate(results):
            if item['type'] == 'db':
                st.markdown(f"""
                    <div class="route-card">
                        <div style="display:flex; justify-content:space-between; align-items: center;">
                            <div>
                                <b style="font-size: 1.2em;">💰 التكلفة: {item['total_price']} جنيه</b>
                            </div>
                            <div>
                                <b style="font-size: 1.2em;">⏱️ الوقت: {item['total_time']} دقيقة</b>
                            </div>
                        </div>
                        <p style="color:gray; margin-top:10px; font-size: 0.95em;">📌 {item['tag']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📍 اضغط هنا لشرح الطريق بالتفصيل", expanded=False):
                    for step in item['steps']:
                        st.markdown(f'<div class="step-box">🚶 {step}</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                route_text = format_route_for_copy(item, from_loc, to_loc)
                
                with col1:
                    st_copy_to_clipboard(
                        route_text, 
                        before_copy_label="📋 انسخ الطريق", 
                        after_copy_label="✅ تم نسخ الطريق!",
                        key=f"copy_db_{idx}"
                    )
                
                with col2:
                    whatsapp_url = share_on_whatsapp(route_text)
                    st.markdown(
                        f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%; height:50px; border-radius:10px; border:none; font-size:18px; cursor:pointer; background:#25D366; color:white;">📱 شارك على WhatsApp</button></a>',
                        unsafe_allow_html=True
                    )
            
            elif item['type'] == 'ai':
                st.warning("⚠️ تنويه: النتيجة دي من الذكاء الاصطناعي، ممكن يكون فيها أخطاء بسيطة.")
                
                formatted_content = parse_ai_response(item['content'])
                
                st.markdown(f"""
                    <div class="route-card ai-card">
                        <div class="ai-content">
                            {formatted_content}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                route_text = format_route_for_copy(item, from_loc, to_loc)
                
                with col1:
                    st_copy_to_clipboard(
                        route_text, 
                        before_copy_label="📋 انسخ الطريق", 
                        after_copy_label="✅ تم نسخ الطريق!",
                        key=f"copy_ai_{idx}"
                    )
                
                with col2:
                    whatsapp_url = share_on_whatsapp(route_text)
                    st.markdown(
                        f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%; height:50px; border-radius:10px; border:none; font-size:18px; cursor:pointer; background:#25D366; color:white;">📱 شارك على WhatsApp</button></a>',
                        unsafe_allow_html=True
                    )
    else:
        st.info("🤔 مفيش نتائج، جرب تكتب المنطقة بطريقة تانية")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p style='font-size: 1.1em;'>تطبيق "أروح إزاي" 🚌 | مشروع مفتوح المصدر</p>
        <p style='font-size: 0.9em;'>مدعوم بالذكاء الاصطناعي لمساعدتك في الوصول لوجهتك</p>
    </div>
    """, 
    unsafe_allow_html=True
)
