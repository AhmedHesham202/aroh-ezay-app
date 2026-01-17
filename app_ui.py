import streamlit as st
import requests
from streamlit_searchbox import st_searchbox
import json
from datetime import datetime
import streamlit.components.v1 as components
from st_copy_to_clipboard import st_copy_to_clipboard
import urllib.parse

st.set_page_config(page_title="أروح إزاي؟", page_icon="🚌", layout="wide")

# بيشوف لو إحنا شغالين على السيرفر (Streamlit Cloud) بياخد الرابط من الـ Secrets
# لو شغالين لوكال بياخد الـ localhost الافتراضي

API_URL = st.secrets.get("API_URL", "http://127.0.0.1:8000")


# --- Initialize Session State ---
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
if 'copy_feedback' not in st.session_state:
    st.session_state.copy_feedback = {}

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# --- Add to History Function ---
def add_to_history(from_loc, to_loc, result_count):
    """Add search to history, keep only last 4"""
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

# --- Enhanced AI Response Parser ---
def parse_ai_response(content):
    """Parse and format AI response for better readability"""
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

# --- Dynamic CSS ---
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
    
    [data-testid="stSidebar"] > div:first-child {{
        direction: RTL;
        text-align: right;
    }}
    
    .history-item {{
        background: {card_bg};
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border-right: 4px solid {border_color};
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    
    .history-item:hover {{
        transform: translateX(-5px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    
    .route-card {{
        background: {card_bg};
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        border-right: 10px solid {border_color};
        color: {text_color};
        animation: slideIn 0.5s ease-out;
    }}
    
    @keyframes slideIn {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
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
        transition: all 0.3s ease;
    }}
    
    .step-box:hover {{
        transform: translateX(-3px);
        box-shadow: 0 2px 8px rgba(31, 119, 180, 0.3);
    }}
    
    .stButton button {{
        background-color: #FF4B4B;
        color: white;
        font-size: 18px;
        border-radius: 10px;
        height: 50px;
        transition: all 0.3s ease;
    }}
    
    .stButton button:hover {{
        background-color: #FF3333;
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
    }}
    
    /* WhatsApp Button */
    .whatsapp-button {{
        background-color: #25D366 !important;
        color: white !important;
    }}
    
    .whatsapp-button:hover {{
        background-color: #20BA5A !important;
    }}
    
    input {{
        text-align: right !important;
        direction: RTL !important;
        background-color: {input_bg} !important;
        color: {text_color} !important;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    .loading-spinner {{
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s linear infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    
    .loading {{
        animation: pulse 1.5s ease-in-out infinite;
    }}
    
    .ai-content h4 {{
        color: #4CAF50;
        margin-top: 15px;
        margin-bottom: 8px;
    }}
    
    .ai-content ul {{
        margin-right: 20px;
        line-height: 1.8;
    }}
    
    .ai-content li {{
        margin-bottom: 8px;
    }}
    
    .ai-content p {{
        margin: 10px 0;
        line-height: 1.7;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar with History ---
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
        st.info("📝 لسه مفيش رحلات\nابدأ ابحث عن طريقك!")
    
    st.markdown("### ⚙️ الإعدادات")
    theme_label = "🌙 الوضع الليلي" if not st.session_state.dark_mode else "☀️ الوضع النهاري"
    if st.button(theme_label, use_container_width=True):
        toggle_theme()
        st.rerun()

# --- Main Content ---
st.title("🚌 أروح إزاي؟")
st.write("اختار من الاقتراحات أو اكتب منطقتك واختارها من القائمة")

# --- Enhanced Suggestions Function ---
def get_suggestions(search_term):
    """تحسين الـ Suggestions لتشمل ما يكتبه المستخدم أولاً"""
    if not search_term:
        return []
    
    suggestions = []
    
    # إضافة ما يكتبه المستخدم كخيار أول دائماً
    suggestions.append(search_term)
    
    # جلب الاقتراحات من قاعدة البيانات
    try:
        res = requests.get(f"{API_URL}/areas", params={"query": search_term}, timeout=3)
        if res.status_code == 200:
            db_suggestions = res.json()
            # إضافة الاقتراحات من DB (بدون تكرار)
            for suggestion in db_suggestions:
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
    except:
        pass
    
    return suggestions

# --- Format Route for Copy and WhatsApp ---
def format_route_for_copy(item, from_loc, to_loc):
    """تحويل بيانات المسار لنص قابل للنسخ"""
    if item['type'] == 'db':
        text = f"🚌 الطريق من {from_loc} إلى {to_loc}\n"
        text += f"💰 التكلفة: {item['total_price']} جنيه\n"
        text += f"⏱️ الوقت: {item['total_time']} دقيقة\n"
        text += f"📌 {item['tag']}\n\n"
        text += "📝 الخطوات:\n"
        for i, step in enumerate(item['steps'], 1):
            text += f"{i}. {step}\n"
        text += "\n🔗 تطبيق أروح إزاي"
        return text
    else:
        clean_text = item['content'].replace('<br>', '\n')
        import re
        clean_text = re.sub('<[^<]+?>', '', clean_text)
        return f"🚌 الطريق من {from_loc} إلى {to_loc}\n\n{clean_text}\n\n⚠️ ملحوظة: هذا المسار تم إنشاؤه بواسطة الذكاء الاصطناعي\n🔗 تطبيق أروح إزاي"

def share_on_whatsapp(route_text):
    """إنشاء رابط WhatsApp للمشاركة"""
    encoded_text = urllib.parse.quote(route_text)
    whatsapp_url = f"https://wa.me/?text={encoded_text}"
    return whatsapp_url

# --- Input Fields ---
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

# --- Search Button ---
if st.button("ورّيني الطريق 🔍", use_container_width=True, type="primary"):
    if from_loc and to_loc:
        if from_loc == to_loc:
            st.warning("⚠️ يا هندسة أنت في نفس المكان!")
        else:
            st.session_state.from_location = from_loc
            st.session_state.to_location = to_loc
            
            loading_placeholder = st.empty()
            loading_placeholder.markdown("""
                <div style='text-align: center; padding: 40px;'>
                    <div class='loading-spinner' style='margin: 0 auto;'></div>
                    <h3 style='margin-top: 20px; animation: pulse 1.5s ease-in-out infinite;'>
                        🔍 بندور على أحسن طريق ليك...
                    </h3>
                </div>
            """, unsafe_allow_html=True)
            
            try:
                res = requests.get(
                    f"{API_URL}/search", 
                    params={"from_area": from_loc, "to_area": to_loc},
                    timeout=30
                )
                
                loading_placeholder.empty()
                
                if res.status_code == 200:
                    results = res.json()
                    st.session_state.search_results = results
                    
                    if results:
                        add_to_history(from_loc, to_loc, len(results))
                else:
                    st.error("❌ السيرفر مش شغال، حاول كمان شوية.")
                    st.session_state.search_results = None
            
            except requests.exceptions.Timeout:
                loading_placeholder.empty()
                st.error("⏱️ الطلب أخد وقت طويل، جرب تاني")
                st.session_state.search_results = None
            except requests.exceptions.ConnectionError:
                loading_placeholder.empty()
                st.error("❌ مفيش اتصال بالسيرفر، تأكد إن الـ API شغال (python main.py)")
                st.session_state.search_results = None
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"❌ حصل خطأ: {e}")
                st.session_state.search_results = None
    else:
        st.info("ℹ️ اختار المكانين من القائمة الأول يا برنس 😉")

# --- Display Results ---
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
                
                with st.expander("📝 اضغط هنا لشرح الطريق بالتفصيل", expanded=False):
                    for step in item['steps']:
                        st.markdown(f'<div class="step-box">🚶 {step}</div>', unsafe_allow_html=True)
                
                # أزرار النسخ و WhatsApp
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
                        f'<a href="{whatsapp_url}" target="_blank"><button class="stButton whatsapp-button" style="width:100%; height:50px; border-radius:10px; border:none; font-size:18px; cursor:pointer;">📱 شارك على WhatsApp</button></a>',
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
                
                # أزرار النسخ و WhatsApp
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
                        f'<a href="{whatsapp_url}" target="_blank"><button class="stButton whatsapp-button" style="width:100%; height:50px; border-radius:10px; border:none; font-size:18px; cursor:pointer;">📱 شارك على WhatsApp</button></a>',
                        unsafe_allow_html=True
                    )
    else:
        st.info("🤔 مفيش نتائج، جرب تكتب المنطقة بطريقة تانية")

# --- Footer ---
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