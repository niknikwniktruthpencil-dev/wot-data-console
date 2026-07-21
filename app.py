import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import re
import math
import os
import base64

# 画像クリック機能と描画機能のインポート
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    from PIL import Image, ImageDraw
    HAS_IMG_COORD = True
except ImportError:
    HAS_IMG_COORD = False

# ページ設定 (サイドバーを常に展開する設定)
st.set_page_config(page_title="RECAT 総合データコンソール", layout="wide", initial_sidebar_state="expanded")

# === スマホでのピンチズーム(拡大縮小)を強制的に許可するハック ===
# Streamlitが自動で設定する「ズーム禁止」を1秒に1回監視して破壊し、許可状態にします。
components.html(
    """
    <script>
    setInterval(function() {
        try {
            var metaTags = window.parent.document.getElementsByTagName('meta');
            for (var i = 0; i < metaTags.length; i++) {
                if (metaTags[i].name === "viewport" && metaTags[i].content.includes("user-scalable=no")) {
                    metaTags[i].content = "width=device-width, initial-scale=1.0, maximum-scale=10.0, user-scalable=yes";
                }
            }
        } catch(e) {}
    }, 1000);
    </script>
    """,
    height=0, width=0
)

# === セッションステートの初期化 ===
PAGES = [
    "🏠 ホーム (メインメニュー)", 
    "📖 車輌図鑑", 
    "⚖️ 車輌比較", 
    "🏆 ランキング", 
    "🛡️ 装甲計算シミュレーター", 
    "📸 スーパー簡易画像装甲測定"
]
if 'app_mode' not in st.session_state:
    st.session_state['app_mode'] = PAGES[0]

if 'img_clicks' not in st.session_state:
    st.session_state['img_clicks'] = []

# === ファイル名とパスの自動解決 ===
base_dir = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = "wot_wwii_all_tanks_modules.csv"
ZIP_FILE = "wot_wwii_all_tanks_modules.zip"

LOGO_FILE = None
for potential_logo in ["1782708565492 (1)-Photoroom_2.png", "1782708565492 (1)-Photoroom.png"]:
    if os.path.exists(os.path.join(base_dir, potential_logo)):
        LOGO_FILE = potential_logo
        break

SAMPLE_IMG_FILE = None
for potential_img in ["Screenshot 2026-07-17 23-00-25.jpg", "Screenshot 2026-07-17 23-00-25_3.jpg"]:
    if os.path.exists(os.path.join(base_dir, potential_img)):
        SAMPLE_IMG_FILE = potential_img
        break

# === キャラクター画像の自動解決 ===
CHAR1_FILE = None
for f in ["1.png", "1.jpg", "1.jpeg", "1-Photoroom.png", "1-Photoroom.jpg", "1.PNG", "1.JPG"]:
    if os.path.exists(os.path.join(base_dir, f)):
        CHAR1_FILE = f
        break

CHAR2_FILE = None
for f in ["3-Photoroom.png", "3-Photoroom.jpg", "3.png", "3.jpg", "3.jpeg", "3.PNG", "3.JPG"]:
    if os.path.exists(os.path.join(base_dir, f)):
        CHAR2_FILE = f
        break

# === Base64エンコード関数 ===
def get_base64_of_bin_file(bin_file):
    if bin_file:
        full_path = os.path.join(base_dir, bin_file)
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
    return None

def get_character_img_html(filename, max_height_pc, img_class=""):
    """キャラクター画像のHTMLタグを生成"""
    if not filename:
        return ""
    b64 = get_base64_of_bin_file(filename)
    if b64:
        ext = filename.split('.')[-1].lower()
        mime = "jpeg" if ext in ["jpg", "jpeg"] else "png"
        return f'<img src="data:image/{mime};base64,{b64}" class="{img_class}" style="max-height: {max_height_pc}px; width: auto; object-fit: contain; filter: drop-shadow(0px 10px 15px rgba(0,0,0,0.5));">'
    return ""

logo_base64 = get_base64_of_bin_file(LOGO_FILE)

# 背景画像のCSS生成
bg_css = ""
if logo_base64:
    bg_css = f"""
    background-image: linear-gradient(rgba(11, 15, 25, 0.88), rgba(11, 15, 25, 0.88)), url("data:image/png;base64,{logo_base64}");
    background-size: 50%;
    background-position: center center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    """

# === CSS (完全ダークモード・すりガラスUI・モジュール全収め対応) ===
css_string = f"""
<style>
/* スマホでの拡大縮小(ピンチ)をCSSから強制的に許可する */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    touch-action: pinch-zoom pan-x pan-y !important;
}}

/* 全体背景の設定 */
.stApp {{
    background-color: #0d1117 !important;
    {bg_css}
}}
[data-testid="stSidebar"] {{ background-color: rgba(26, 26, 26, 0.95) !important; border-right: 1px solid #333; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);}}
.stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp span {{ color: #e5e5e5 !important; }}

/* 共通パネル (半透明すりガラス調) */
.panel-box {{ 
    padding: 20px; 
    background-color: rgba(22, 27, 34, 0.65) !important; 
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 12px; 
    margin-bottom: 24px; 
    border: 1px solid rgba(255, 255, 255, 0.1); 
    box-shadow: 0 8px 24px rgba(0,0,0,0.8); 
}}

/* =========================================================
   ラジオボタンを公式風ガラス調丸みパネルに完全偽装 (PC・基本共通)
   ========================================================= */
.stRadio div[role="radiogroup"] {{
    gap: 8px;
}}
.stRadio div[role="radiogroup"] > label {{
    background-color: rgba(31, 41, 55, 0.7) !important;
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 6px !important;
    padding: 8px 6px !important; /* 無駄な余白をカット */
    margin-bottom: 0 !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}}
/* 選択時のハイライト (水色発光枠) */
.stRadio div[role="radiogroup"] > label[aria-checked="true"],
.stRadio div[role="radiogroup"] > label:has(input:checked) {{
    background-color: rgba(88, 166, 255, 0.15) !important;
    border: 1px solid #58a6ff !important; 
    box-shadow: 0 0 8px rgba(88,166,255,0.4);
}}
/* Hover時 */
.stRadio div[role="radiogroup"] > label:hover {{
    border-color: #8b949e !important;
}}
/* ラジオの丸(○)を確実に消す */
.stRadio div[role="radiogroup"] > label div[data-baseweb="radio"] {{ display: none !important; }}

/* テキストのスタイル */
.stRadio div[role="radiogroup"] > label p {{ 
    color: #8b949e !important; 
    font-size: 0.85em !important; 
    font-weight: 500 !important; 
    margin: 0 !important; 
    text-align: center !important; 
    line-height: 1.2 !important; 
    word-break: break-word;
    width: 100%;
}}
.stRadio div[role="radiogroup"] > label[aria-checked="true"] p,
.stRadio div[role="radiogroup"] > label:has(input:checked) p {{ 
    color: #ffffff !important; 
    font-weight: bold !important; 
}}
/* ========================================================= */

/* その他のUIパーツ */
ul[role="listbox"], ul[role="listbox"] * {{ background-color: #1f1f1f !important; color: #ffffff !important; }}
li[role="option"]:hover, li[role="option"]:focus, li[aria-selected="true"] {{ background-color: #333333 !important; color: #58a6ff !important; border-left: 3px solid #58a6ff; }}
div[data-baseweb="select"] > div, input, div[data-testid="stButton"] button {{ background-color: rgba(31, 41, 55, 0.7) !important; color: #ffffff !important; border: 1px solid rgba(255,255,255,0.15) !important; border-radius: 6px !important; backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px); }}
div[data-testid="stButton"] button {{ color: #58a6ff !important; font-weight:bold; }}
div[data-testid="stButton"] button:hover {{ background-color: rgba(88, 166, 255, 0.2) !important; border-color: #58a6ff !important; color: #ffffff !important; }}

/* 公式サイト風リストレイアウト (半透明化) */
.off-row {{ 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    padding: 10px 12px; 
    margin-bottom: 4px;
    background-color: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
}}
.off-row:hover {{ background-color: rgba(255,255,255,0.05); }}
.off-label {{ color: #a1a1aa; font-size: 0.85em; font-weight: 400; width: 55%; line-height: 1.2; }}
.off-val {{ color: #ffffff; font-size: 0.9em; font-weight: 600; text-align: right; width: 45%; transition: color 0.3s; }}
.off-suf {{ color: #9ca3af; font-size: 0.75em; font-weight: normal; margin-left: 2px; }}

/* ★バフ適用時の青文字発光クラス★ */
.buffed-text {{ color: #58a6ff !important; font-weight: bold !important; text-shadow: 0 0 8px rgba(88, 166, 255, 0.4); }}

/* セクションタイトル */
.mod-header {{ border-bottom: 2px solid rgba(229,229,229,0.3); padding-bottom: 5px; margin-bottom: 10px; font-size: 0.95em; font-weight: bold; color: #e5e5e5; text-align: center; }}
.panel-title {{ font-size: 1.2em !important; color: #e2e8f0 !important; margin-top: 25px; margin-bottom: 10px; border-bottom: 2px solid rgba(148,163,184,0.5) !important; padding-bottom: 8px; font-weight: 500; letter-spacing: 0.5px; }}

/* 主要性能トップボード (半透明化) */
.major-stat-box {{ background-color: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 15px; margin-bottom: 15px; backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);}}
.major-stat-title {{ font-size: 0.9em; color: #a1a1aa; border-bottom: 1px solid rgba(55,65,81,0.5); padding-bottom: 3px; margin-bottom: 5px; }}
.major-stat-value {{ font-size: 1.8em; font-weight: bold; color: #ffffff; line-height: 1.1; transition: color 0.3s; }}
.major-stat-unit {{ font-size: 0.45em; color: #a1a1aa; font-weight: normal; }}

/* PC向けのコンテナ調整 */
.block-container {{ max-width: 1600px; padding-top: 1.5rem; }}

/* 比較テーブル (半透明化) */
.comp-table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 10px; font-size: 0.95em; background-color: rgba(22, 27, 34, 0.65); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-radius: 8px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.1); }}
.comp-table th {{ background-color: rgba(31, 41, 55, 0.8); padding: 12px; border-bottom: 2px solid #58a6ff; text-align: center; font-size: 1.0em; color: #ffffff !important; }}
.comp-table td {{ padding: 10px 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); text-align: center; color: #e5e5e5 !important; }}
.comp-label {{ text-align: left !important; color: #9ca3af !important; width: 28%; font-weight: 500; background-color: rgba(11, 15, 25, 0.5); }}
.win-stat {{ color: #58a6ff !important; font-weight: bold; background-color: rgba(88, 166, 255, 0.15); text-shadow: 0 0 5px rgba(88,166,255,0.4); }}

/* 装甲シミュレーター結果を超巨大化 */
.armor-result {{ font-size: 5.5em !important; font-weight: 900 !important; color: #ff4b4b !important; text-align: center !important; margin: 20px 0 !important; line-height: 1.0 !important; display: block !important; text-shadow: 0 0 25px rgba(255,75,75,0.6); }}
.armor-result-bounce {{ font-size: 4.5em !important; font-weight: 900 !important; color: #a1a1aa !important; text-align: center !important; margin: 20px 0 !important; display: block !important; text-shadow: 0 0 15px rgba(161,161,170,0.4); line-height: 1.0 !important; }}

/* 画像表示コンテナ */
.tank-image-container {{ text-align: center; margin-bottom: 10px; padding: 10px; }}
.tank-image {{ max-width: 100%; max-height: 250px; object-fit: contain; filter: drop-shadow(0px 10px 15px rgba(0,0,0,0.8)); }}
.sidebar-logo {{ width: 110px; height: auto; display: block; margin: 0 auto 10px auto; }}

/* キャラクター反転用クラス */
.home-char-left {{ transform: scaleX(-1); }}

/* === スマホ向け専用レイアウト（画面幅768px以下） === */
@media (max-width: 768px) {{
    .block-container {{ padding-left: 8px !important; padding-right: 8px !important; padding-top: 1rem !important; }}
    .panel-box {{ padding: 12px !important; margin-bottom: 20px !important; }}
    .tank-image {{ max-height: 180px; }}
    .major-stat-value {{ font-size: 1.5em; }}
    .off-row {{ padding: 12px 6px; }}
    .off-label {{ font-size: 0.9em; }}
    .off-val {{ font-size: 1.0em; }}
    .off-suf {{ font-size: 0.8em; }}
    
    /* ======== スマホ版モジュールの「完全強制・5等分グリッド」ハック ======== */
    /* Flexboxの押し出しを無効化し、数学的に画面を5つに割る CSS Grid を使用 */
    .mobile-grid-anchor + div[data-testid="stHorizontalBlock"] {{
        display: grid !important;
        grid-template-columns: repeat(5, 1fr) !important;
        gap: 4px !important;
        width: 100% !important;
        max-width: 100vw !important;
        overflow: hidden !important;
    }}
    
    .mobile-grid-anchor + div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    /* スマホ版モジュールヘッダー文字調整 */
    .mod-header {{
        font-size: 0.55rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: clip !important;
        padding-bottom: 2px !important;
        margin-bottom: 4px !important;
        text-align: center !important;
    }}
    
    /* ラジオボタン枠の調整 */
    .stRadio div[role="radiogroup"] > label {{
        padding: 6px 2px !important;
        min-height: 48px !important;
        height: 100% !important;
    }}
    
    /* 文字が枠を押し広げようとするのを完全に無力化 */
    .stRadio div[role="radiogroup"] > label p {{
        font-size: 0.55rem !important;
        white-space: pre-wrap !important; /* テキストの折り返しを強制 */
        word-break: break-all !important;
        overflow-wrap: anywhere !important;
        line-height: 1.1 !important;
        text-align: center !important;
    }}
    /* ============================================================ */

    .comp-table {{ font-size: 0.75em !important; border-radius: 4px !important; }}
    .comp-table th {{ padding: 8px 4px !important; font-size: 0.9em !important; }}
    .comp-table td {{ padding: 8px 4px !important; }}
    .comp-label {{ width: 35% !important; font-size: 0.85em !important; }}
    
    /* 装甲シミュレーター結果のスマホ用巨大化 */
    .armor-result {{ font-size: 4.5em !important; }}
    .armor-result-bounce {{ font-size: 3.5em !important; }}
    
    h1 {{ font-size: 1.4em !important; margin-top: -15px !important; }}
    div[data-testid="stExpander"] {{ background-color: rgba(31, 41, 55, 0.8) !important; border-radius: 8px !important; border: 1px solid rgba(255,255,255,0.1) !important; backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px); }}
    
    /* ======== ホーム画面スマホ最適化（キャラ縦積みを防ぐ） ======== */
    .home-hero-container {{
        flex-direction: row !important; /* スマホでも強制的に横並び */
        padding: 5px 0 !important;
        margin-bottom: 20px !important;
    }}
    .home-char-left {{
        max-height: 100px !important; /* 画面に収まるように縮小 */
        transform: scaleX(-1);
        margin-bottom: 0 !important;
    }}
    .home-char-right {{
        max-height: 110px !important;
        margin-top: 0 !important;
    }}
    .home-char-wrapper {{
        margin-right: -10px !important; /* スマホ用の密着マージン */
        margin-left: -10px !important;
        min-width: 0 !important;
    }}
    .home-text-wrapper {{
        min-width: 0 !important;
    }}
    .home-top-logo {{
        width: 50px !important;
        margin-bottom: 5px !important;
    }}
    .home-title {{
        font-size: 1.2em !important;
    }}
    .home-subtitle {{
        font-size: 0.65em !important;
        margin-top: 4px !important;
    }}
}}
</style>
"""
safe_css = css_string.replace('\n', ' ')
st.markdown(safe_css, unsafe_allow_html=True)

@st.cache_data
def load_and_parse_data():
    try:
        zip_path = os.path.join(base_dir, ZIP_FILE)
        csv_path = os.path.join(base_dir, CSV_FILE)
        if os.path.exists(zip_path):
            df = pd.read_csv(zip_path, encoding="utf-8-sig", compression="zip")
        else:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame()

    def get_match(pattern, text):
        m = re.search(pattern, str(text), re.IGNORECASE)
        return m.group(1).replace(' ', '').strip('/') if m else "-"
        
    def get_match_all(pattern, text):
        return [m.replace(' ', '').strip('/') for m in re.findall(pattern, str(text), re.IGNORECASE)]
        
    def extract_basics(text):
        m = re.search(r'ホーム › 戦車事典 › ([^/]+) / (.*?) / (?:価格|戦闘獲得レート|主要性能)', str(text))
        if m: return pd.Series([m.group(1).replace(' ', ''), re.sub(r'\s*/\s*(プレミアム車輌|退役車輌)$', '', m.group(2).strip())])
        return pd.Series(["-", "-"])

    df[['国', '正確な車輌名']] = df['詳細・モジュール生データ'].apply(extract_basics)
    df = df[df['正確な車輌名'] != "-"]

    df['Tier'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'TIER / ([IVX]+)', x))
    df['時代'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'時代 / (戦後|エスカレーション|デタント)', x))
    df['モード'] = df.apply(lambda row: 'WWII' if row['Tier'] != "-" else ('Cold War' if row['時代'] != "-" else '-'), axis=1)
    df = df[df['モード'] != "-"]
    df['タイプ'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'タイプ / (軽戦車|中戦車|重戦車|駆逐戦車|自走砲)', x))

    def get_module_type(row):
        module_name = str(row['モジュール状態']).strip()
        text = str(row['詳細・モジュール生データ'])
        if module_name == '初期装備': return '初期装備'
        s_idx = text.find('初期へとリセット')
        if s_idx == -1: s_idx = 0
        cat_indices = [(text.find(f' / {c} /', s_idx), c) for c in ['主砲', '砲塔', 'エンジン', 'サスペンション', '無線'] if text.find(f' / {c} /', s_idx) != -1]
        cat_indices.sort()
        mod_idx = text.find(module_name, s_idx)
        return '不明' if mod_idx == -1 else next((cat for idx, cat in reversed(cat_indices) if idx < mod_idx), '不明')
    
    df['モジュール種類'] = df.apply(get_module_type, axis=1)

    df['DPM_list'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'分間ダメージ / ([\d/ \.]+)HP', x))
    df['DPM(主砲)'] = df['DPM_list'].apply(lambda x: x[0] if len(x) > 0 else "-")
    df['DPM(副砲)'] = df['DPM_list'].apply(lambda x: x[1] if len(x) > 1 else "-")
    df['貫通力_list'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'100 Mでの貫通力 / ([\d/ \.]+)MM', x))
    df['貫通力100m(主砲)'] = df['貫通力_list'].apply(lambda x: x[0] if len(x) > 0 else "-")
    df['貫通力100m(副砲)'] = df['貫通力_list'].apply(lambda x: x[1] if len(x) > 1 else "-")
    df['貫通力500_list'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'500 Mでの貫通力 / ([\d/ \.]+)MM', x))
    df['貫通力500m(主砲)'] = df['貫通力500_list'].apply(lambda x: x[0] if len(x) > 0 else "-")
    df['貫通力500m(副砲)'] = df['貫通力500_list'].apply(lambda x: x[1] if len(x) > 1 else "-")
    df['ダメージ_list'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'ダメージ / ([\d/ \.]+)HP', x))
    df['ダメージ(主砲)'] = df['ダメージ_list'].apply(lambda x: x[0] if len(x) > 0 else "-")
    df['ダメージ(副砲)'] = df['ダメージ_list'].apply(lambda x: x[1] if len(x) > 1 else "-")
    df['装填時間_list'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'装填時間 / ([\d\.]+)秒', x))
    df['装填時間(主砲)'] = df['装填時間_list'].apply(lambda x: x[0] if len(x) > 0 else "-")
    df['装填時間(副砲)'] = df['装填時間_list'].apply(lambda x: x[1] if len(x) > 1 else "-")
    df['射撃速度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'射撃速度 / ([\d\.]+)発', x))
    df['照準時間(秒)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'照準時間 / ([\d\.]+)秒', x))
    df['精度(m)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'精度 / ([\d\.]+)M', x))
    df['モジュールの損傷'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'モジュールの損傷 / ([\d/ \.]+)HP', x))
    df['攻撃半径'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'攻撃半径 / ([\d/ \.]+)M', x))
    df['弾薬の最大速度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'弾薬の最大速度 / ([\d/ \.]+)M', x))
    df['弾薬の最大射程'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'弾薬の最大射程 / ([\d/ \.]+)M', x))
    df['砲弾タイプ'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'砲弾タイプ / ([A-Z/ \.]+)', x))
    df['総弾数'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'総弾数 / (\d+)発', x))
    df['走行中の精度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'走行中の精度.*?([\d\.]+)[ \n]*M', x))
    df['砲塔旋回中の射撃精度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'砲塔旋回中の射撃精度 / ([\d\.]+)M', x))
    df['俯角'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'俯角 / ([\d\.]+)度', x))
    df['仰角'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'仰角 / ([\d\.]+)度', x))
    df['水平可動域'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'水平可動域 / ([\-\d/ \.]+)度', x))
    df['HP'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'HP(\d+)HP', x))
    df['砲塔装甲(mm)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'砲塔装甲 / ([\d/ \.]+)MM', x))
    df['車体装甲(mm)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'車体装甲.*?([\d/ \.]+)MM', x))
    df['視認範囲(m)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'視認範囲 / ([\d\.]+)M', x))
    df['発見可能範囲'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'発見可能範囲[^\d]*([\d\.]+/?[\d\.]*)', x))
    df['通信範囲(m)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'通信範囲 / ([\d\.]+)M', x))
    df['エンジン出力'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'エンジン出力 / (\d+)HP', x))
    df['出力重量比'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'出力重量比 / ([\d\.]+)HP', x))
    df['最大前進速度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'最大速度([\d\.]+)/', x))
    df['最大後進速度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'最大速度[\d\.]+/([\d\.]+)\(', x))
    df['火災発生率'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'火災発生率 / (\d+)パーセント', x))
    df['接地抵抗'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'接地抵抗[^\d]*([\d/ \.]+)', x))

    # === エコノミー・マッチメイキングの正確なパース ===
    df['シルバー獲得レート'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'シルバー獲得レート[^\d]*(\d+)', x))
    def get_exp_rate(text):
        matches = re.findall(r'(.{0,10})EXP\s*獲得レート[^\d]*(\d+)', str(text), re.IGNORECASE)
        for prefix, val in matches:
            if "フリー" not in prefix and "搭乗員" not in prefix:
                return val
        return "-"
    df['EXP獲得レート'] = df['詳細・モジュール生データ'].apply(get_exp_rate)
    df['フリーEXPレート'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'フリー\s*EXP\s*獲得レート[^\d]*(\d+)', x))
    df['搭乗員EXPレート'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'搭乗員\s*EXP\s*レート[^\d]*(\d+)', x))
    df['最大TIER'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'最大\s*TIER[^\dIVX]*([IVX\d]+)', x))

    # ★ここでランキング用の数値を計算してDataFrameに追加しておく（KeyError防止）★
    def get_split_val(val_str, idx):
        if pd.isna(val_str) or val_str == "-": return 0
        parts = str(val_str).split('/')
        if len(parts) > idx:
            num = re.sub(r'[^\d\.]', '', parts[idx])
            try: return float(num)
            except: return 0
        return 0

    df['Rank_DPM_Main'] = df['DPM(主砲)'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Pen_Std'] = df['貫通力100m(主砲)'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Pen_Gold'] = df['貫通力100m(主砲)'].apply(lambda x: get_split_val(x, 1))
    df['Rank_Dmg_Std'] = df['ダメージ(主砲)'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Dmg_HE'] = df['ダメージ(主砲)'].apply(lambda x: get_split_val(x, 2))
    df['Rank_HP'] = df['HP'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Speed'] = df['最大前進速度'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Conceal_Move'] = df['発見可能範囲'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Conceal_Still'] = df['発見可能範囲'].apply(lambda x: get_split_val(x, 1))
    df['Rank_Vision'] = df['視認範囲(m)'].apply(lambda x: get_split_val(x, 0))
    
    return df

df = load_and_parse_data()
if df.empty:
    st.error(f"エラー: データファイル ({CSV_FILE} または {ZIP_FILE}) が見つかりません。")
    st.stop()

# ==========================================
# 拡張シミュレーション & ユーティリティ
# ==========================================
def sim_val(base_str, mult, is_int=False):
    if mult == 1.0: return base_str
    if pd.isna(base_str) or str(base_str).strip() == "-": return "-"
    parts = str(base_str).split('/')
    res = []
    for p in parts:
        try:
            num = float(re.search(r'[\-\d\.]+', p).group(0))
            calc = num * mult
            if is_int: res.append(str(int(round(calc))))
            else: res.append(f"{calc:.2f}")
        except:
            res.append(p.strip())
    return " / ".join(res)

def sim_res_val(base_str, mult_hard, mult_med, mult_soft):
    if pd.isna(base_str) or str(base_str).strip() == "-": return "-"
    parts = str(base_str).split('/')
    res = []
    for i, p in enumerate(parts):
        mult = mult_hard if i == 0 else (mult_med if i == 1 else mult_soft)
        try:
            num = float(re.search(r'[\-\d\.]+', p).group(0))
            calc = num * mult
            res.append(f"{calc:.2f}")
        except:
            res.append(p.strip())
    return " / ".join(res)

def get_camo_bonus_text(tank_type):
    if tank_type in ["中戦車", "軽戦車"]: return "3%"
    if tank_type == "駆逐戦車": return "4%"
    if tank_type in ["重戦車", "自走砲"]: return "2%"
    return "0%"

def get_adv_camo_text(tank_type):
    if tank_type in ["中戦車", "軽戦車"]: return "5%"
    if tank_type == "駆逐戦車": return "7.5%"
    if tank_type in ["重戦車", "自走砲"]: return "2.5%"
    return "0%"

def get_camo_net_text(tank_type):
    if tank_type in ["中戦車", "軽戦車"]: return "10%"
    if tank_type == "駆逐戦車": return "15%"
    if tank_type in ["重戦車", "自走砲"]: return "5%"
    return "0%"

def calc_camo_bonuses(tank_type, apply_camo, apply_adv_camo, apply_camo_net):
    base_bonus = 0.0
    if apply_camo:
        if tank_type in ["中戦車", "軽戦車"]: base_bonus += 0.03
        elif tank_type == "駆逐戦車": base_bonus += 0.04
        elif tank_type in ["重戦車", "自走砲"]: base_bonus += 0.02
        
    adv_camo_bonus = 0.0
    camo_net_bonus = 0.0
    
    if apply_adv_camo:
        if tank_type in ["中戦車", "軽戦車"]: adv_camo_bonus = 0.05
        elif tank_type == "駆逐戦車": adv_camo_bonus = 0.075
        elif tank_type in ["重戦車", "自走砲"]: adv_camo_bonus = 0.025
        
    if apply_camo_net:
        if tank_type in ["中戦車", "軽戦車"]: camo_net_bonus = 0.10
        elif tank_type == "駆逐戦車": camo_net_bonus = 0.15
        elif tank_type in ["重戦車", "自走砲"]: camo_net_bonus = 0.05
        
    move_bonus = base_bonus + adv_camo_bonus
    still_bonus = base_bonus + max(adv_camo_bonus, camo_net_bonus)
    return move_bonus, still_bonus

def calc_crew_and_skill_mult(apply_vents, apply_food_passive, apply_food_active, apply_born_leader):
    bonus_sum = 0.0
    if apply_vents: bonus_sum += 5.0
    if apply_food_passive: bonus_sum += 5.0
    if apply_food_active: bonus_sum += 15.0
    if apply_born_leader: bonus_sum += 5.0
    
    crew_mult = 1.0 + (bonus_sum * 0.0043)
    skill_mult = 1.0 + (bonus_sum / 100.0)
    return crew_mult, skill_mult

def get_conceal_values(conceal_str, tank_type, apply_camo, apply_adv_camo, apply_camo_net, apply_camo_skill, apply_green_thumb, skill_mult):
    move_c = get_split_str(conceal_str, 0)
    still_c = get_split_str(conceal_str, 1)
    if move_c == "-" or still_c == "-":
        return move_c, still_c
        
    move_flat_bonus, still_flat_bonus = calc_camo_bonuses(tank_type, apply_camo, apply_adv_camo, apply_camo_net)
    
    camo_skill_val = 0.0
    if apply_camo_skill: camo_skill_val += (0.075 * skill_mult)
    if apply_green_thumb: camo_skill_val += (0.10 * skill_mult)
    camo_skill_mult_total = 1.0 + camo_skill_val
    
    try:
        base_move = float(move_c)
        base_still = float(still_c)
        
        move_val = 445.0 - ((445.0 - base_move) * camo_skill_mult_total) - (395.0 * move_flat_bonus)
        still_val = 445.0 - ((445.0 - base_still) * camo_skill_mult_total) - (395.0 * still_flat_bonus)
        
        return f"{move_val:.2f}", f"{still_val:.2f}"
    except:
        return move_c, still_c

def get_vision_values(vision_str, apply_optics, apply_binocs, apply_sit_aware, crew_mult, skill_mult):
    if pd.isna(vision_str) or vision_str == "-":
        return "-"
    try:
        base_vision = float(re.search(r'([\d\.]+)', str(vision_str)).group(1))
        bonus = 0.0
        if apply_optics: bonus = max(bonus, 0.10)
        if apply_binocs: bonus = max(bonus, 0.20)
        if apply_sit_aware: bonus += (0.06 * skill_mult)
            
        final_vision = base_vision * (1.0 + bonus) * crew_mult 
            
        if final_vision.is_integer():
            return f"{int(final_vision)}"
        return f"{final_vision:.2f}"
    except:
        return vision_str

def get_crew_exp_str(base_str, apply_food_passive):
    if not apply_food_passive: return base_str
    if base_str == "-": return "-"
    try:
        val = int(re.search(r'\d+', str(base_str)).group())
        return str(val + 10)
    except:
        return base_str

def get_val(tank_data, mod_state, col_name):
    if mod_state and not tank_data[tank_data['モジュール状態'] == mod_state].empty: 
        val = str(tank_data[tank_data['モジュール状態'] == mod_state][col_name].iloc[0])
        if val != "-" and val != "nan": return val
    if col_name in tank_data.columns:
        fallback = tank_data[tank_data[col_name] != "-"]
        if not fallback.empty:
            return str(fallback[col_name].iloc[-1])
    return "-"

def get_hull_traverse(tank_data, s_susp):
    susp_df = tank_data[tank_data['モジュール状態'] == s_susp]
    if not susp_df.empty:
        text = str(susp_df['詳細・モジュール生データ'].iloc[0])
        match = re.search(r'(?:車体)?旋回速度 / ([\d\.]+)度', text)
        if match: return match.group(1)
    
    fallback = tank_data[tank_data['詳細・モジュール生データ'].str.contains(r'(?:車体)?旋回速度 /', na=False)]
    if not fallback.empty:
        text = str(fallback['詳細・モジュール生データ'].iloc[0])
        matches = re.findall(r'(?:車体)?旋回速度 / ([\d\.]+)度', text)
        if matches: return matches[-1]
    return "-"

def get_turret_traverse(tank_data, s_turret):
    turret_df = tank_data[tank_data['モジュール状態'] == s_turret]
    if not turret_df.empty:
        text = str(turret_df['詳細・モジュール生データ'].iloc[0])
        match = re.search(r'(?:砲塔)?旋回速度 / ([\d\.]+)度', text)
        if match: return match.group(1)
    return "-"

def get_ground_resistance(tank_data, s_susp):
    val = get_val(tank_data, s_susp, '接地抵抗')
    if val == "-":
        fallback = tank_data[tank_data['接地抵抗'] != "-"]
        if not fallback.empty:
            val = str(fallback['接地抵抗'].iloc[-1])
            
    if val != "-":
        parts = re.findall(r'[\d\.]+', str(val))
        if len(parts) >= 3:
            return f"{parts[0]} / {parts[1]} / {parts[2]}"
        elif len(parts) > 0:
            return " / ".join(parts)
    return "-"

def get_split_str(val_str, idx):
    if pd.isna(val_str) or val_str == "-": return "-"
    parts = str(val_str).split('/')
    if len(parts) > idx: return parts[idx].strip()
    return "-"

def get_float(val_str):
    try:
        parts = re.findall(r'[\-\d\.]+', str(val_str))
        if parts and parts[0] != '-': return float(parts[0])
        return None
    except: return None

def comp_tr(label, valA, valB, higher_better=True, suffix=""):
    numA = get_float(valA)
    numB = get_float(valB)
    clsA, clsB = "lose-stat", "lose-stat"
    if valA != "-" and valB != "-" and higher_better is not None and numA is not None and numB is not None and numA != numB:
        if (numA > numB and higher_better) or (numA < numB and not higher_better): clsA = "win-stat"
        else: clsB = "win-stat"
    dispA = f"{valA} {suffix}".strip() if valA != "-" else "-"
    dispB = f"{valB} {suffix}".strip() if valB != "-" else "-"
    return f"<tr><td class='comp-label'>{label}</td><td class='{clsA}'>{dispA}</td><td class='{clsB}'>{dispB}</td></tr>"

def render_html_zukan(label, value, suffix="", is_buffed=False):
    """公式サイトのようなフラットリストレイアウト（左ラベル、右バリュー）を出力。バフ適用時は青文字化"""
    val_class = "buffed-text" if is_buffed else ""
    if value and str(value) != "-":
        st.markdown(f"<div class='off-row'><div class='off-label'>{label}</div><div class='off-val {val_class}'>{value} <span class='off-suf'>{suffix}</span></div></div>", unsafe_allow_html=True)


# ==========================================
# サイドバーとメインメニューの連携設定
# ==========================================
if logo_base64:
     logo_html = f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_base64}" class="sidebar-logo"></div>'
else:
     logo_html = ""

st.sidebar.markdown(f"{logo_html}<h3 style='margin-top:0px; text-align:center;'>RECAT Console</h3>", unsafe_allow_html=True)
    
selected_mode = st.sidebar.radio(
    "機能メニュー", 
    PAGES, 
    index=PAGES.index(st.session_state['app_mode'])
)

if selected_mode != st.session_state['app_mode']:
    st.session_state['app_mode'] = selected_mode
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips:** スマホ版は自動で公式アプリ風の最適化レイアウトに切り替わります。")
st.sidebar.caption("⚠️ **注記:** 公式サイトの車両情報を元に作成しておりますので、ゲーム内のデータ(小数点以下のデータ内容等)とほんの少しズレる場合がございます。")

# ==========================================
# 0. ホーム（メインメニュー）
# ==========================================
if st.session_state['app_mode'] == "🏠 ホーム (メインメニュー)":
    
    char1_html = get_character_img_html(CHAR1_FILE, 260, "home-char-left") if CHAR1_FILE else ""
    char2_html = get_character_img_html(CHAR2_FILE, 300, "home-char-right") if CHAR2_FILE else ""
    top_logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="home-top-logo" style="margin: 0 auto 10px auto; display: block; filter: drop-shadow(0px 0px 8px rgba(255,255,255,0.4));">' if logo_base64 else ''

    st.markdown(f"""
    <div class="home-hero-container" style="display: flex; flex-direction: row; justify-content: center; align-items: center; flex-wrap: nowrap; margin-bottom: 40px; padding: 20px 0; max-width: 950px; margin-left: auto; margin-right: auto;">
        <div class="home-char-wrapper" style="flex: 0 0 auto; margin-right: -30px; z-index: 2;">{char1_html}</div>
        <div class="home-text-wrapper" style="flex: 1 1 auto; text-align: center; padding: 0 10px; z-index: 1;">
            {top_logo_html}
            <h1 class="home-title" style='color: #ffffff !important; margin: 0; font-size: 2.5em; text-shadow: 0 0 15px rgba(0,0,0,0.8);'>RECAT 総合データコンソール</h1>
            <p class="home-subtitle" style='color: #8b949e !important; margin-top: 8px; font-size: 1.1em;'>World of Tanks: Modern Armor 専用アナリティクスツール</p>
        </div>
        <div class="home-char-wrapper" style="flex: 0 0 auto; margin-left: -30px; z-index: 2;">{char2_html}</div>
    </div>
    <hr style="border-color: rgba(255,255,255,0.1); margin-bottom: 30px;">
    """, unsafe_allow_html=True)
    
    st.markdown("### 💡 ツールを選択してください")
    
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("📖 車輌図鑑", use_container_width=True):
            st.session_state['app_mode'] = "📖 車輌図鑑"
            st.rerun()
        st.markdown("<p style='text-align: center; color: #8b949e; font-size: 0.85em; margin-top:-10px;'>全ステータスや隠し性能を確認</p>", unsafe_allow_html=True)
    with b2:
        if st.button("⚖️ 車輌比較", use_container_width=True):
            st.session_state['app_mode'] = "⚖️ 車輌比較"
            st.rerun()
        st.markdown("<p style='text-align: center; color: #8b949e; font-size: 0.85em; margin-top:-10px;'>2つの車輌の性能を並べて比較</p>", unsafe_allow_html=True)
    with b3:
        if st.button("🏆 ランキング", use_container_width=True):
            st.session_state['app_mode'] = "🏆 ランキング"
            st.rerun()
        st.markdown("<p style='text-align: center; color: #8b949e; font-size: 0.85em; margin-top:-10px;'>DPMや貫通力などの最強ランキング</p>", unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    b4, b5 = st.columns(2)
    with b4:
        if st.button("🛡️ 装甲計算シミュレーター", use_container_width=True):
            st.session_state['app_mode'] = "🛡️ 装甲計算シミュレーター"
            st.rerun()
        st.markdown("<p style='text-align: center; color: #8b949e; font-size: 0.85em; margin-top:-10px;'>着弾角度を入力して実質装甲厚を計算</p>", unsafe_allow_html=True)
    with b5:
        if st.button("📸 スーパー簡易画像装甲測定", use_container_width=True):
            st.session_state['app_mode'] = "📸 スーパー簡易画像装甲測定"
            st.rerun()
        st.markdown("<p style='text-align: center; color: #8b949e; font-size: 0.85em; margin-top:-10px;'>側面画像をなぞるだけで実装甲厚を測定</p>", unsafe_allow_html=True)


# ==========================================
# 1. 車輌図鑑
# ==========================================
elif st.session_state['app_mode'] == "📖 車輌図鑑":
    
    # === ランキングからのジャンプ処理 ===
    jump_q = ""
    jump_mode_idx = 0
    if 'zukan_jump_tank' in st.session_state:
        jump_q = st.session_state['zukan_jump_tank']
        if st.session_state.get('zukan_jump_mode') == "Cold War":
            jump_mode_idx = 1
        del st.session_state['zukan_jump_tank']

    st.markdown("<div class='panel-box' style='padding-bottom:5px;'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title' style='margin-top:0;'>🔍 車輌の検索・絞り込み</div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    z_mode = c1.radio("モード", ["WWII", "Cold War"], index=jump_mode_idx, horizontal=True, label_visibility="collapsed")
    z_q = c2.text_input("検索", value=jump_q, placeholder="名前で検索...", label_visibility="collapsed")
    f_df = df[df['モード'] == z_mode].copy()
    z_nation = c3.selectbox("国別", ["すべて"] + list(f_df['国'].dropna().unique()), label_visibility="collapsed")
    z_type = c4.selectbox("車種", ["すべて", "軽戦車", "中戦車", "重戦車", "駆逐戦車", "自走砲"], label_visibility="collapsed")
    z_tier = c5.selectbox("Tier / 時代", ["すべて", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "戦後", "エスカレーション", "デタント"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    if z_q: f_df = f_df[f_df['正確な車輌名'].str.contains(z_q, case=False, na=False)]
    if z_nation != "すべて": f_df = f_df[f_df['国'] == z_nation]
    if z_type != "すべて": f_df = f_df[f_df['タイプ'] == z_type]
    if z_tier != "すべて": f_df = f_df[(f_df['Tier'] == z_tier) | (f_df['時代'] == z_tier)]
    
    tank_list = sorted(f_df['正確な車輌名'].unique())
    if not tank_list: 
        st.warning("条件に一致する車輌がありません。")
        st.stop()
    selected_tank = st.selectbox("🎯 車輌を選択", tank_list)
    
    t_data = df[df['正確な車輌名'] == selected_tank]
    tank_type_zukan = t_data['タイプ'].iloc[0] if not t_data.empty else "-"

    # === UIコンテナの定義 ===
    major_stats_placeholder = st.container()
    st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title' style='margin-top:0;'>モジュールのカスタマイズ</div>", unsafe_allow_html=True)
    modules_container = st.container()
    st.markdown("</div>", unsafe_allow_html=True)
    
    sim_container = st.container()
    st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title' style='margin-top:0;'>モジュールの詳細</div>", unsafe_allow_html=True)
    details_container = st.container()
    st.markdown("</div>", unsafe_allow_html=True)

    # === モジュール選択用UIの作成 ===
    guns = t_data[t_data['モジュール種類'] == '主砲']['モジュール状態'].unique()
    turrets = t_data[t_data['モジュール種類'] == '砲塔']['モジュール状態'].unique()
    engines = t_data[t_data['モジュール種類'] == 'エンジン']['モジュール状態'].unique()
    susps = t_data[t_data['モジュール種類'] == 'サスペンション']['モジュール状態'].unique()
    radios = t_data[t_data['モジュール種類'] == '無線']['モジュール状態'].unique()
    
    with modules_container:
        st.markdown("<div class='mobile-grid-anchor'></div>", unsafe_allow_html=True)
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            st.markdown("<div class='mod-header'>主砲</div>", unsafe_allow_html=True)
            s_gun = st.radio("主砲", guns, label_visibility="collapsed") if len(guns) > 0 else None
        with mc2:
            st.markdown("<div class='mod-header'>砲塔</div>", unsafe_allow_html=True)
            s_turret = st.radio("砲塔", turrets, label_visibility="collapsed") if len(turrets) > 0 else None
        with mc3:
            st.markdown("<div class='mod-header'>エンジン</div>", unsafe_allow_html=True)
            s_engine = st.radio("エンジン", engines, label_visibility="collapsed") if len(engines) > 0 else None
        with mc4:
            st.markdown("<div class='mod-header'>サスペンション</div>", unsafe_allow_html=True)
            s_susp = st.radio("履帯", susps, label_visibility="collapsed") if len(susps) > 0 else None
        with mc5:
            st.markdown("<div class='mod-header'>無線</div>", unsafe_allow_html=True)
            s_radio = st.radio("無線", radios, label_visibility="collapsed") if len(radios) > 0 else None

    # === 拡張シミュレーションの設定 ===
    with sim_container:
        st.markdown("<div class='panel-title' style='margin-top:20px; margin-bottom: 10px;'>📊 拡張シミュレーション (タップで設定を展開)</div>", unsafe_allow_html=True)
        camo_txt = get_camo_bonus_text(tank_type_zukan)
        adv_camo_txt = get_adv_camo_text(tank_type_zukan)
        camo_net_txt = get_camo_net_text(tank_type_zukan)
        
        with st.expander("🛠️ 拡張シミュレーション (パーツ・消耗品・スキル)", expanded=True):
            c_sim1, c_sim2, c_sim3, c_sim4 = st.columns(4)
            with c_sim1:
                st.markdown("<div style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>⚙️ パーツ (火力・共通)</div>", unsafe_allow_html=True)
                apply_rammer_zukan = st.checkbox("装填棒 (-7.5%)", key="rammer_zukan")
                apply_vstab_zukan = st.checkbox("砲安定装置 (旋回精度+20%)", key="vstab_zukan")
                apply_gld_zukan = st.checkbox("射撃装置 (照準時間-10%)", key="gld_zukan")
                apply_vents_zukan = st.checkbox("改良型換気装置 (搭乗員+5%)", key="vents_zukan")
            with c_sim2:
                st.markdown("<div style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>⚙️ パーツ (機動/視認/隠蔽)</div>", unsafe_allow_html=True)
                apply_grouser_zukan = st.checkbox("追加グローサー (旋回/抵抗+7.5%)", key="grouser_zukan")
                apply_turbo_zukan = st.checkbox("ターボチャージャー (速度/出力+5%)", key="turbo_zukan")
                apply_optics_zukan = st.checkbox("薄膜レンズ (全車: 10%)", key="optics_zukan")
                apply_binocs_zukan = st.checkbox("双眼鏡 (全車: 20% *静止)", key="binocs_zukan")
                apply_adv_camo_zukan = st.checkbox(f"改良型迷彩 ({adv_camo_txt})", key="adv_zukan")
                apply_camo_net_zukan = st.checkbox(f"迷彩ネット ({camo_net_txt} *静止)", key="net_zukan")
            with c_sim3:
                st.markdown("<div style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>🎨 外観 / 🥩 消耗品</div>", unsafe_allow_html=True)
                apply_camo_zukan = st.checkbox(f"迷彩塗装 ({camo_txt})", key="camo_zukan")
                apply_food_p_zukan = st.checkbox("改良型食料 (常時: 搭乗員+5%)", key="food_p_zukan")
                apply_food_a_zukan = st.checkbox("└ 使用時効果 (さらに+15%)", key="food_a_zukan")
                apply_fuel_p_zukan = st.checkbox("改良型燃料 (常時: 速度+5%/旋回+10%)", key="fuel_p_zukan")
                apply_fuel_a_zukan = st.checkbox("└ 使用時効果 (出力+10%)", key="fuel_a_zukan")
            with c_sim4:
                st.markdown("<div style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>👤 車長スキル</div>", unsafe_allow_html=True)
                apply_born_leader_zukan = st.checkbox("天性のリーダー (搭乗員/スキル+5%)", key="born_leader_zukan")
                apply_camo_skill_zukan = st.checkbox("迷彩の専門知識 (隠蔽+7.5%)", key="camo_skill_zukan")
                apply_green_thumb_zukan = st.checkbox("隠蔽の達人 (+10% ※茂み限定)", key="green_thumb_zukan")
                apply_sit_aware_zukan = st.checkbox("状況判断力 (視認+6%)", key="sit_aware_zukan")
                apply_signal_expert_zukan = st.checkbox("通信エキスパート (通信+30%)", key="signal_expert_zukan")
                apply_clutch_braking_zukan = st.checkbox("クラッチの名手 (車体旋回+7.5%)", key="clutch_braking_zukan")
                apply_rapid_aim_zukan = st.checkbox("迅速な照準 (砲塔旋回+10%)", key="rapid_aim_zukan")
                apply_snap_shot_zukan = st.checkbox("速射 (砲塔旋回精度+10%)", key="snap_shot_zukan")

        sim_warnings = []
        if apply_optics_zukan and apply_binocs_zukan:
            sim_warnings.append("※視認パーツ重複：表記上は効果の大きい双眼鏡が優先表示されます。")
        if apply_adv_camo_zukan and apply_camo_net_zukan:
            sim_warnings.append("※隠蔽パーツ重複：静止時は効果の高い迷彩ネットが優先適用されます。")
        if sim_warnings:
            for w in sim_warnings:
                st.markdown(f"<div style='color:#ff7b72; font-size:0.85em; margin-bottom:15px; margin-top:-10px;'>{w}</div>", unsafe_allow_html=True)

    # === シミュレーション変数の計算 ===
    crew_mult, skill_mult = calc_crew_and_skill_mult(apply_vents_zukan, apply_food_p_zukan, apply_food_a_zukan, apply_born_leader_zukan)
    is_crew_buffed = (apply_vents_zukan or apply_food_p_zukan or apply_food_a_zukan or apply_born_leader_zukan)

    dpm_mult = (1.0 / 0.925) if apply_rammer_zukan else 1.0
    dpm_mult *= crew_mult
    reload_mult = 0.925 if apply_rammer_zukan else 1.0
    reload_mult /= crew_mult
    aim_mult = 0.90 if apply_gld_zukan else 1.0
    aim_mult /= crew_mult
    acc_mult = 1.0 / crew_mult
    rof_mult = 1.0 * crew_mult
    
    speed_mult = 1.05 if apply_turbo_zukan else 1.0
    if apply_fuel_p_zukan: speed_mult *= 1.05
    hp_mult = 1.05 if apply_turbo_zukan else 1.0
    if apply_fuel_a_zukan: hp_mult *= 1.10
    
    tt_mult = 1.0 * crew_mult
    if apply_fuel_p_zukan: tt_mult *= 1.10
    if apply_rapid_aim_zukan: tt_mult *= (1.0 + (0.10 * skill_mult))
    
    trav_mult = 1.0
    if apply_grouser_zukan: trav_mult *= 1.075
    if apply_clutch_braking_zukan: trav_mult *= (1.0 + (0.075 * skill_mult))
    res_mult = 0.925 if apply_grouser_zukan else 1.0
    res_mult /= crew_mult
    
    radio_mult = 1.0 * crew_mult
    if apply_signal_expert_zukan: radio_mult *= (1.0 + (0.30 * skill_mult))
    
    disp_mult = 0.80 if apply_vstab_zukan else 1.0
    if apply_snap_shot_zukan: disp_mult *= (1.0 - (0.10 * skill_mult))
    disp_mult /= crew_mult
    
    move_disp_mult = 1.0 / crew_mult

    # === 基本数値の取得と加工 ===
    sim_dpm = sim_val(get_val(t_data, s_gun, 'DPM(主砲)'), dpm_mult, is_int=True)
    pen_main = get_val(t_data, s_gun, '貫通力100m(主砲)')
    pen_fmt = f"{get_split_str(pen_main, 0)}/{get_split_str(pen_main, 1)}/{get_split_str(pen_main, 2)}"
    dmg_main = get_val(t_data, s_gun, 'ダメージ(主砲)')
    dmg_fmt = f"{get_split_str(dmg_main, 0)}/{get_split_str(dmg_main, 1)}/{get_split_str(dmg_main, 2)}"
    hp_val = get_val(t_data, s_turret, 'HP')
    ammo_type_val = get_val(t_data, s_gun, '砲弾タイプ')
    
    sim_fwd = sim_val(get_val(t_data, s_engine, '最大前進速度'), speed_mult)
    sim_rev = sim_val(get_val(t_data, s_engine, '最大後進速度'), speed_mult)
    speed_fmt = f"{sim_fwd}/{sim_rev}"
    
    vision = get_val(t_data, s_turret, '視認範囲(m)')
    vision_v = get_vision_values(vision, apply_optics_zukan, apply_binocs_zukan, apply_sit_aware_zukan, crew_mult, skill_mult)
    
    conceal = get_val(t_data, s_turret, '発見可能範囲')
    move_v, still_v = get_conceal_values(conceal, tank_type_zukan, apply_camo_zukan, apply_adv_camo_zukan, apply_camo_net_zukan, apply_camo_skill_zukan, apply_green_thumb_zukan, skill_mult)
    camo_fmt = f"{move_v}/{still_v}"

    silver_rate = str(t_data['シルバー獲得レート'].iloc[0]) if not t_data.empty else "-"
    exp_rate = str(t_data['EXP獲得レート'].iloc[0]) if not t_data.empty else "-"
    free_exp_rate = str(t_data['フリーEXPレート'].iloc[0]) if not t_data.empty else "-"
    crew_exp_base = str(t_data['搭乗員EXPレート'].iloc[0]) if not t_data.empty else "-"
    crew_exp_sim = get_crew_exp_str(crew_exp_base, apply_food_p_zukan)
    mm_tier = str(t_data['最大TIER'].iloc[0]) if not t_data.empty else "-"

    # === 「主要性能」トップボードの描画 ===
    with major_stats_placeholder:
        st.markdown("<div class='panel-box' style='padding-top:10px; padding-bottom:5px;'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title' style='margin-top:0;'>主要性能</div>", unsafe_allow_html=True)
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.markdown(f"""
            <div class="major-stat-box">
                <div class="major-stat-title">貫通力</div>
                <div class="major-stat-value">{pen_fmt} <span class="major-stat-unit">MM</span></div>
            </div>
            <div class="major-stat-box">
                <div class="major-stat-title">ダメージ</div>
                <div class="major-stat-value">{dmg_fmt} <span class="major-stat-unit">HP</span></div>
            </div>
            <div class="major-stat-box">
                <div class="major-stat-title">砲弾タイプ</div>
                <div class="major-stat-value" style="font-size: 1.3em;">{ammo_type_val}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_stat2:
            st.markdown(f"""
            <div class="major-stat-box">
                <div class="major-stat-title">HP</div>
                <div class="major-stat-value">{hp_val} <span class="major-stat-unit">HP</span></div>
            </div>
            <div class="major-stat-box">
                <div class="major-stat-title">最大速度 (前進/後退)</div>
                <div class="major-stat-value {'buffed-text' if (apply_turbo_zukan or apply_fuel_p_zukan) else ''}">{speed_fmt} <span class="major-stat-unit">KM/H</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_stat3:
            st.markdown(f"""
            <div class="major-stat-box">
                <div class="major-stat-title">視認範囲</div>
                <div class="major-stat-value {'buffed-text' if (apply_optics_zukan or apply_binocs_zukan or apply_sit_aware_zukan or is_crew_buffed) else ''}">{vision_v} <span class="major-stat-unit">M</span></div>
            </div>
            <div class="major-stat-box">
                <div class="major-stat-title">発見可能範囲 (移動/静止)</div>
                <div class="major-stat-value {'buffed-text' if (apply_camo_zukan or apply_adv_camo_zukan or apply_camo_net_zukan or apply_camo_skill_zukan or apply_green_thumb_zukan) else ''}">{camo_fmt} <span class="major-stat-unit">M</span></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # === モジュール詳細の描画 ===
    with details_container:
        st.markdown("<div class='mobile-grid-anchor'></div>", unsafe_allow_html=True)
        d1, d2, d3, d4, d5 = st.columns(5)
        
        with d1:
            st.markdown(f"<div style='font-weight:bold; margin-bottom:15px; font-size:0.95em; color:#e5e5e5; border-bottom:1px solid #60a5fa; padding-bottom:5px;'>{s_gun if s_gun else '主砲'}</div>", unsafe_allow_html=True)
            sim_reload = sim_val(get_val(t_data, s_gun, '装填時間(主砲)'), reload_mult)
            sim_aim = sim_val(get_val(t_data, s_gun, '照準時間(秒)'), aim_mult)
            sim_acc = sim_val(get_val(t_data, s_gun, '精度(m)'), acc_mult)
            sim_rof = sim_val(get_val(t_data, s_gun, '射撃速度'), rof_mult)
            sim_disp = sim_val(get_val(t_data, s_gun, '砲塔旋回中の射撃精度'), disp_mult)
            pen_500 = get_val(t_data, s_gun, '貫通力500m(主砲)')
            
            render_html_zukan("射撃速度", sim_rof, "発/分", is_buffed=is_crew_buffed)
            render_html_zukan("ダメージ", dmg_fmt, "HP")
            render_html_zukan("モジュールの損傷", get_val(t_data, s_gun, 'モジュールの損傷'), "HP")
            render_html_zukan("攻撃半径", get_val(t_data, s_gun, '攻撃半径'), "M")
            render_html_zukan("分間ダメージ", sim_dpm, "HP/分", is_buffed=(apply_rammer_zukan or is_crew_buffed))
            render_html_zukan("100 Mでの貫通力", pen_fmt, "MM")
            render_html_zukan("500 Mでの貫通力", f"{get_split_str(pen_500, 0)}/{get_split_str(pen_500, 1)}/{get_split_str(pen_500, 2)}", "MM")
            render_html_zukan("弾薬の最大速度", get_val(t_data, s_gun, '弾薬の最大速度'), "M/S")
            render_html_zukan("弾薬の最大射程", get_val(t_data, s_gun, '弾薬の最大射程'), "M")
            render_html_zukan("砲弾タイプ", get_val(t_data, s_gun, '砲弾タイプ'))
            render_html_zukan("装填時間", sim_reload, "秒", is_buffed=(apply_rammer_zukan or is_crew_buffed))
            render_html_zukan("照準時間", sim_aim, "秒", is_buffed=(apply_gld_zukan or is_crew_buffed))
            render_html_zukan("総弾数", get_val(t_data, s_gun, '総弾数'), "発")
            render_html_zukan("精度", sim_acc, "M", is_buffed=is_crew_buffed)
            
            sim_move_disp = sim_val(get_val(t_data, s_gun, '走行中の精度'), move_disp_mult)
            render_html_zukan("走行中の精度", sim_move_disp, "M", is_buffed=is_crew_buffed)
            
            render_html_zukan("砲塔旋回中精度", sim_disp, "M", is_buffed=(apply_vstab_zukan or apply_snap_shot_zukan or is_crew_buffed))
            render_html_zukan("俯角", get_val(t_data, s_gun, '俯角'), "度")
            render_html_zukan("仰角", get_val(t_data, s_gun, '仰角'), "度")
            render_html_zukan("水平可動域", get_val(t_data, s_gun, '水平可動域'), "度")

        with d2:
            st.markdown(f"<div style='font-weight:bold; margin-bottom:15px; font-size:0.95em; color:#e5e5e5; border-bottom:1px solid #60a5fa; padding-bottom:5px;'>{s_turret if s_turret else '砲塔'}</div>", unsafe_allow_html=True)
            turret_armor = get_val(t_data, s_turret, '砲塔装甲(mm)')
            hull_armor = get_val(t_data, s_turret, '車体装甲(mm)')
            sim_tt = sim_val(get_turret_traverse(t_data, s_turret), tt_mult)
            
            render_html_zukan("砲塔装甲", f"{get_split_str(turret_armor, 0)}/{get_split_str(turret_armor, 1)}/{get_split_str(turret_armor, 2)}", "MM")
            render_html_zukan("車体装甲", f"{get_split_str(hull_armor, 0)}/{get_split_str(hull_armor, 1)}/{get_split_str(hull_armor, 2)}", "MM")
            render_html_zukan("旋回速度", sim_tt, "度/秒", is_buffed=(is_crew_buffed or apply_fuel_p_zukan or apply_rapid_aim_zukan))
            render_html_zukan("視認範囲", vision_v, "M", is_buffed=(apply_optics_zukan or apply_binocs_zukan or apply_sit_aware_zukan or is_crew_buffed))
            render_html_zukan("位置", "PRIMARY")
            
        with d3:
            st.markdown(f"<div style='font-weight:bold; margin-bottom:15px; font-size:0.95em; color:#e5e5e5; border-bottom:1px solid #60a5fa; padding-bottom:5px;'>{s_engine if s_engine else 'エンジン'}</div>", unsafe_allow_html=True)
            sim_hp = sim_val(get_val(t_data, s_engine, 'エンジン出力'), hp_mult, is_int=True)
            sim_ptw = sim_val(get_val(t_data, s_engine, '出力重量比'), hp_mult)
            
            render_html_zukan("エンジン出力", sim_hp, "HP", is_buffed=(apply_turbo_zukan or apply_fuel_a_zukan))
            render_html_zukan("出力重量比", sim_ptw, "HP/T", is_buffed=(apply_turbo_zukan or apply_fuel_a_zukan))
            render_html_zukan("最大前進速度", sim_fwd, "KM/H", is_buffed=(apply_turbo_zukan or apply_fuel_p_zukan))
            render_html_zukan("最大後退速度", sim_rev, "KM/H", is_buffed=(apply_turbo_zukan or apply_fuel_p_zukan))
            render_html_zukan("火災発生率", get_val(t_data, s_engine, '火災発生率'), "パーセント")

        with d4:
            st.markdown(f"<div style='font-weight:bold; margin-bottom:15px; font-size:0.95em; color:#e5e5e5; border-bottom:1px solid #60a5fa; padding-bottom:5px;'>{s_susp if s_susp else 'サスペンション'}</div>", unsafe_allow_html=True)
            sim_trav = sim_val(get_hull_traverse(t_data, s_susp), trav_mult)
            sim_res = sim_res_val(get_ground_resistance(t_data, s_susp), res_mult, res_mult, res_mult)
            
            render_html_zukan("旋回速度", sim_trav, "度/秒", is_buffed=(apply_grouser_zukan or apply_clutch_braking_zukan))
            render_html_zukan("接地抵抗", f"{get_split_str(sim_res, 0)}/{get_split_str(sim_res, 1)}/{get_split_str(sim_res, 2)}", "", is_buffed=(apply_grouser_zukan or is_crew_buffed))

        with d5:
            st.markdown(f"<div style='font-weight:bold; margin-bottom:15px; font-size:0.95em; color:#e5e5e5; border-bottom:1px solid #60a5fa; padding-bottom:5px;'>{s_radio if s_radio else '無線'}</div>", unsafe_allow_html=True)
            sim_radio = sim_val(get_val(t_data, s_radio, '通信範囲(m)'), radio_mult)
            render_html_zukan("通信範囲", sim_radio, "M", is_buffed=(is_crew_buffed or apply_signal_expert_zukan))

    # === エコノミー・マッチメイキング情報 ===
    st.markdown("<div class='panel-box' style='margin-top:20px;'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title' style='margin-top:0;'>経済性・マッチメイキング</div>", unsafe_allow_html=True)
    eco1, eco2 = st.columns(2)
    with eco1:
        render_html_zukan("シルバー獲得レート", silver_rate, "%")
        render_html_zukan("車輌EXP獲得レート", exp_rate, "%")
        render_html_zukan("最大マッチメイキング", mm_tier, "")
    with eco2:
        render_html_zukan("フリーEXP獲得レート", free_exp_rate, "%")
        render_html_zukan("搭乗員EXP獲得レート", crew_exp_sim, "%", is_buffed=apply_food_p_zukan)
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 2. 車輌比較
# ==========================================
elif st.session_state['app_mode'] == "⚖️ 車輌比較":
    st.title("⚖️ 究極スペック比較テーブル")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title' style='margin-top:0;'>🟦 車輌 A の検索と設定</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        modeA = c1.radio("モード (A)", ["WWII", "Cold War"], horizontal=True)
        qA = c2.text_input("検索 (A)", placeholder="名前入力...")
        fA = df[df['モード'] == modeA].copy()
        c3, c4, c5 = st.columns(3)
        natA = c3.selectbox("国(A)", ["すべて"] + list(fA['国'].dropna().unique()))
        typA = c4.selectbox("車種(A)", ["すべて", "軽戦車", "中戦車", "重戦車", "駆逐戦車", "自走砲"])
        tierA = c5.selectbox("Tier(A)", ["すべて", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "戦後", "エスカレーション", "デタント"])
        if qA: fA = fA[fA['正確な車輌名'].str.contains(qA, case=False, na=False)]
        if natA != "すべて": fA = fA[fA['国'] == natA]
        if typA != "すべて": fA = fA[fA['タイプ'] == typA]
        if tierA != "すべて": fA = fA[(fA['Tier'] == tierA) | (fA['時代'] == tierA)]
        listA = sorted(fA['正確な車輌名'].unique())
        tankA = st.selectbox("🎯 比較する車輌 A を選択", listA if listA else ["-"])
        
        dfA = df[df['正確な車輌名'] == tankA]
        
        st.markdown("<div class='mobile-grid-anchor'></div>", unsafe_allow_html=True)
        ca1, ca2, ca3 = st.columns(3)
        gA = dfA[dfA['モジュール種類'] == '主砲']['モジュール状態'].unique()
        tA = dfA[dfA['モジュール種類'] == '砲塔']['モジュール状態'].unique()
        eA = dfA[dfA['モジュール種類'] == 'エンジン']['モジュール状態'].unique()
        s_gunA = ca1.selectbox("主砲(A)", gA) if len(gA)>0 else None
        s_turretA = ca2.selectbox("砲塔(A)", tA) if len(tA)>0 else None
        s_engineA = ca3.selectbox("エンジン(A)", eA) if len(eA)>0 else None
        
        st.markdown("<div class='mobile-grid-anchor'></div>", unsafe_allow_html=True)
        ca4, ca5, _ = st.columns(3)
        suspA = dfA[dfA['モジュール種類'] == 'サスペンション']['モジュール状態'].unique()
        rA = dfA[dfA['モジュール種類'] == '無線']['モジュール状態'].unique()
        s_suspA = ca4.selectbox("サスペンション(A)", suspA) if len(suspA)>0 else None
        s_radioA = ca5.selectbox("無線(A)", rA) if len(rA)>0 else None
        
        st.markdown("---")
        with st.expander("🛠️ 拡張シミュレーション (A)", expanded=True):
            tankA_type = dfA['タイプ'].iloc[0] if not dfA.empty else "-"
            
            c_a1, c_a2, c_a3, c_a4 = st.columns(4)
            with c_a1:
                st.markdown("<span style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>⚙️ パーツ (火力/機動)</span>", unsafe_allow_html=True)
                apply_rammer_A = st.checkbox("装填棒(-7.5%)", key="rammer_A")
                apply_vstab_A = st.checkbox("安定装置(+20%)", key="vstab_A")
                apply_gld_A = st.checkbox("射撃装置(-10%)", key="gld_A")
                apply_vents_A = st.checkbox("換気装置(+5%)", key="vents_A")
                apply_grouser_A = st.checkbox("グローサー(+7.5%)", key="grouser_A")
                apply_turbo_A = st.checkbox("ターボ(+5%)", key="turbo_A")
            with c_a2:
                st.markdown("<span style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>⚙️ パーツ (視認/隠蔽)</span>", unsafe_allow_html=True)
                apply_optics_A = st.checkbox("薄膜レンズ", key="optics_A")
                apply_binocs_A = st.checkbox("双眼鏡(*静止)", key="binocs_A")
                apply_adv_camo_A = st.checkbox("改良型迷彩", key="adv_A")
                apply_camo_net_A = st.checkbox("迷彩ネット(*静止)", key="net_A")
            with c_a3:
                st.markdown("<span style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>🎨 外観/消耗品</span>", unsafe_allow_html=True)
                apply_camo_A = st.checkbox("迷彩塗装", key="camo_A")
                apply_food_p_A = st.checkbox("食料(常時)", key="food_p_A")
                apply_food_a_A = st.checkbox("食料(使用)", key="food_a_A")
                apply_fuel_p_A = st.checkbox("燃料(常時)", key="fuel_p_A")
                apply_fuel_a_A = st.checkbox("燃料(使用)", key="fuel_a_A")
            with c_a4:
                st.markdown("<span style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>👤 スキル</span>", unsafe_allow_html=True)
                apply_born_leader_A = st.checkbox("天性のリーダー", key="born_leader_A")
                apply_camo_skill_A = st.checkbox("迷彩の専門知識", key="camo_skill_A")
                apply_green_thumb_A = st.checkbox("隠蔽の達人(*茂み)", key="green_thumb_A")
                apply_sit_aware_A = st.checkbox("状況判断力", key="sit_aware_A")
                apply_snap_shot_A = st.checkbox("速射", key="snap_shot_A")
                apply_rapid_aim_A = st.checkbox("迅速な照準", key="rapid_aim_A")
                apply_clutch_braking_A = st.checkbox("クラッチの名手", key="clutch_braking_A")
                apply_signal_expert_A = st.checkbox("通信エキスパート", key="signal_expert_A")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title' style='margin-top:0;'>🟥 車輌 B の検索と設定</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        modeB = c1.radio("モード (B)", ["WWII", "Cold War"], horizontal=True)
        qB = c2.text_input("検索 (B)", placeholder="名前入力...")
        fB = df[df['モード'] == modeB].copy()
        c3, c4, c5 = st.columns(3)
        natB = c3.selectbox("国(B)", ["すべて"] + list(fB['国'].dropna().unique()))
        typB = c4.selectbox("車種(B)", ["すべて", "軽戦車", "中戦車", "重戦車", "駆逐戦車", "自走砲"])
        tierB = c5.selectbox("Tier(B)", ["すべて", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "戦後", "エスカレーション", "デタント"])
        if qB: fB = fB[fB['正確な車輌名'].str.contains(qB, case=False, na=False)]
        if natB != "すべて": fB = fB[fB['国'] == natB]
        if typB != "すべて": fB = fB[fB['タイプ'] == typB]
        if tierB != "すべて": fB = fB[(fB['Tier'] == tierB) | (fB['時代'] == tierB)]
        listB = sorted(fB['正確な車輌名'].unique())
        tankB = st.selectbox("🎯 比較する車輌 B を選択", listB if listB else ["-"])
        
        dfB = df[df['正確な車輌名'] == tankB]
        
        st.markdown("<div class='mobile-grid-anchor'></div>", unsafe_allow_html=True)
        cb1, cb2, cb3 = st.columns(3)
        gB = dfB[dfB['モジュール種類'] == '主砲']['モジュール状態'].unique()
        tB = dfB[dfB['モジュール種類'] == '砲塔']['モジュール状態'].unique()
        eB = dfB[dfB['モジュール種類'] == 'エンジン']['モジュール状態'].unique()
        s_gunB = cb1.selectbox("主砲(B)", gB) if len(gB)>0 else None
        s_turretB = cb2.selectbox("砲塔(B)", tB) if len(tB)>0 else None
        s_engineB = cb3.selectbox("エンジン(B)", eB) if len(eB)>0 else None
        
        st.markdown("<div class='mobile-grid-anchor'></div>", unsafe_allow_html=True)
        cb4, cb5, _ = st.columns(3)
        suspB = dfB[dfB['モジュール種類'] == 'サスペンション']['モジュール状態'].unique()
        rB = dfB[dfB['モジュール種類'] == '無線']['モジュール状態'].unique()
        s_suspB = cb4.selectbox("サスペンション(B)", suspB) if len(suspB)>0 else None
        s_radioB = cb5.selectbox("無線(B)", rB) if len(rB)>0 else None
        
        st.markdown("---")
        with st.expander("🛠️ 拡張シミュレーション (B)", expanded=True):
            tankB_type = dfB['タイプ'].iloc[0] if not dfB.empty else "-"
            
            c_b1, c_b2, c_b3, c_b4 = st.columns(4)
            with c_b1:
                st.markdown("<span style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>⚙️ パーツ (火力/機動)</span>", unsafe_allow_html=True)
                apply_rammer_B = st.checkbox("装填棒(-7.5%)", key="rammer_B")
                apply_vstab_B = st.checkbox("安定装置(+20%)", key="vstab_B")
                apply_gld_B = st.checkbox("射撃装置(-10%)", key="gld_B")
                apply_vents_B = st.checkbox("換気装置(+5%)", key="vents_B")
                apply_grouser_B = st.checkbox("グローサー(+7.5%)", key="grouser_B")
                apply_turbo_B = st.checkbox("ターボ(+5%)", key="turbo_B")
            with c_b2:
                st.markdown("<span style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>⚙️ パーツ (視認/隠蔽)</span>", unsafe_allow_html=True)
                apply_optics_B = st.checkbox("薄膜レンズ", key="optics_B")
                apply_binocs_B = st.checkbox("双眼鏡(*静止)", key="binocs_B")
                apply_adv_camo_B = st.checkbox("改良型迷彩", key="adv_B")
                apply_camo_net_B = st.checkbox("迷彩ネット(*静止)", key="net_B")
            with c_b3:
                st.markdown("<span style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>🎨 外観/消耗品</span>", unsafe_allow_html=True)
                apply_camo_B = st.checkbox("迷彩塗装", key="camo_B")
                apply_food_p_B = st.checkbox("食料(常時)", key="food_p_B")
                apply_food_a_B = st.checkbox("食料(使用)", key="food_a_B")
                apply_fuel_p_B = st.checkbox("燃料(常時)", key="fuel_p_B")
                apply_fuel_a_B = st.checkbox("燃料(使用)", key="fuel_a_B")
            with c_b4:
                st.markdown("<span style='color:#58a6ff; font-weight:bold; margin-bottom:8px;'>👤 スキル</span>", unsafe_allow_html=True)
                apply_born_leader_B = st.checkbox("天性のリーダー", key="born_leader_B")
                apply_camo_skill_B = st.checkbox("迷彩の専門知識", key="camo_skill_B")
                apply_green_thumb_B = st.checkbox("隠蔽の達人(*茂み)", key="green_thumb_B")
                apply_sit_aware_B = st.checkbox("状況判断力", key="sit_aware_B")
                apply_snap_shot_B = st.checkbox("速射", key="snap_shot_B")
                apply_rapid_aim_B = st.checkbox("迅速な照準", key="rapid_aim_B")
                apply_clutch_braking_B = st.checkbox("クラッチの名手", key="clutch_braking_B")
                apply_signal_expert_B = st.checkbox("通信エキスパート", key="signal_expert_B")
        st.markdown("</div>", unsafe_allow_html=True)

    html = "<table class='comp-table'>"
    html += f"<tr><th style='text-align: left; padding-left: 15px;'>💥 火力・主砲性能</th><th class='comp-val-col'>{tankA}</th><th class='comp-val-col'>{tankB}</th></tr>"
    
    crew_mult_A, skill_mult_A = calc_crew_and_skill_mult(apply_vents_A, apply_food_p_A, apply_food_a_A, apply_born_leader_A)
    crew_mult_B, skill_mult_B = calc_crew_and_skill_mult(apply_vents_B, apply_food_p_B, apply_food_a_B, apply_born_leader_B)
    
    dpm_mult_A = (1.0 / 0.925) if apply_rammer_A else 1.0
    dpm_mult_A *= crew_mult_A
    dpm_mult_B = (1.0 / 0.925) if apply_rammer_B else 1.0
    dpm_mult_B *= crew_mult_B
    
    html += comp_tr("分間ダメージ (主砲)", sim_val(get_val(dfA, s_gunA, 'DPM(主砲)'), dpm_mult_A, True), sim_val(get_val(dfB, s_gunB, 'DPM(主砲)'), dpm_mult_B, True), True, "HP/分")
    html += comp_tr("分間ダメージ (副砲)", sim_val(get_val(dfA, s_gunA, 'DPM(副砲)'), dpm_mult_A, True), sim_val(get_val(dfB, s_gunB, 'DPM(副砲)'), dpm_mult_B, True), True, "HP/分")
    html += comp_tr("100 M 貫通力 (主砲 通常弾)", get_split_str(get_val(dfA, s_gunA, '貫通力100m(主砲)'), 0), get_split_str(get_val(dfB, s_gunB, '貫通力100m(主砲)'), 0), True, "mm")
    html += comp_tr("100 M 貫通力 (主砲 課金弾)", get_split_str(get_val(dfA, s_gunA, '貫通力100m(主砲)'), 1), get_split_str(get_val(dfB, s_gunB, '貫通力100m(主砲)'), 1), True, "mm")
    html += comp_tr("100 M 貫通力 (主砲 HE)", get_split_str(get_val(dfA, s_gunA, '貫通力100m(主砲)'), 2), get_split_str(get_val(dfB, s_gunB, '貫通力100m(主砲)'), 2), True, "mm")
    html += comp_tr("500 M 貫通力 (主砲 通常弾)", get_split_str(get_val(dfA, s_gunA, '貫通力500m(主砲)'), 0), get_split_str(get_val(dfB, s_gunB, '貫通力500m(主砲)'), 0), True, "mm")
    html += comp_tr("500 M 貫通力 (主砲 課金弾)", get_split_str(get_val(dfA, s_gunA, '貫通力500m(主砲)'), 1), get_split_str(get_val(dfB, s_gunB, '貫通力500m(主砲)'), 1), True, "mm")
    html += comp_tr("100 M 貫通力 (副砲)", get_split_str(get_val(dfA, s_gunA, '貫通力100m(副砲)'), 0), get_split_str(get_val(dfB, s_gunB, '貫通力100m(副砲)'), 0), None, "mm")
    html += comp_tr("500 M 貫通力 (副砲)", get_split_str(get_val(dfA, s_gunA, '貫通力500m(副砲)'), 0), get_split_str(get_val(dfB, s_gunB, '貫通力500m(副砲)'), 0), None, "mm")
    html += comp_tr("ダメージ (主砲 通常弾)", get_split_str(get_val(dfA, s_gunA, 'ダメージ(主砲)'), 0), get_split_str(get_val(dfB, s_gunB, 'ダメージ(主砲)'), 0), True, "HP")
    html += comp_tr("ダメージ (主砲 課金弾)", get_split_str(get_val(dfA, s_gunA, 'ダメージ(主砲)'), 1), get_split_str(get_val(dfB, s_gunB, 'ダメージ(主砲)'), 1), True, "HP")
    html += comp_tr("ダメージ (主砲 HE)", get_split_str(get_val(dfA, s_gunA, 'ダメージ(主砲)'), 2), get_split_str(get_val(dfB, s_gunB, 'ダメージ(主砲)'), 2), True, "HP")
    html += comp_tr("ダメージ (副砲)", get_split_str(get_val(dfA, s_gunA, 'ダメージ(副砲)'), 0), get_split_str(get_val(dfB, s_gunB, 'ダメージ(副砲)'), 0), None, "HP")
    
    reload_mult_A = 0.925 if apply_rammer_A else 1.0
    reload_mult_A /= crew_mult_A
    reload_mult_B = 0.925 if apply_rammer_B else 1.0
    reload_mult_B /= crew_mult_B
    html += comp_tr("装填時間 (主砲)", sim_val(get_val(dfA, s_gunA, '装填時間(主砲)'), reload_mult_A), sim_val(get_val(dfB, s_gunB, '装填時間(主砲)'), reload_mult_B), False, "秒")
    html += comp_tr("装填時間 (副砲)", sim_val(get_val(dfA, s_gunA, '装填時間(副砲)'), reload_mult_A), sim_val(get_val(dfB, s_gunB, '装填時間(副砲)'), reload_mult_B), False, "秒")
    
    aim_mult_A = 0.90 if apply_gld_A else 1.0
    aim_mult_A /= crew_mult_A
    aim_mult_B = 0.90 if apply_gld_B else 1.0
    aim_mult_B /= crew_mult_B
    html += comp_tr("照準時間", sim_val(get_val(dfA, s_gunA, '照準時間(秒)'), aim_mult_A), sim_val(get_val(dfB, s_gunB, '照準時間(秒)'), aim_mult_B), False, "秒")
    
    acc_mult_A = 1.0 / crew_mult_A
    acc_mult_B = 1.0 / crew_mult_B
    html += comp_tr("精度", sim_val(get_val(dfA, s_gunA, '精度(m)'), acc_mult_A), sim_val(get_val(dfB, s_gunB, '精度(m)'), acc_mult_B), False, "m")
    
    move_disp_mult_A = 1.0 / crew_mult_A
    move_disp_mult_B = 1.0 / crew_mult_B
    html += comp_tr("走行中の精度 (移動時)", sim_val(get_val(dfA, s_gunA, '走行中の精度'), move_disp_mult_A), sim_val(get_val(dfB, s_gunB, '走行中の精度'), move_disp_mult_B), False, "m")
    
    rof_mult_A = 1.0 * crew_mult_A
    rof_mult_B = 1.0 * crew_mult_B
    html += comp_tr("射撃速度", sim_val(get_val(dfA, s_gunA, '射撃速度'), rof_mult_A), sim_val(get_val(dfB, s_gunB, '射撃速度'), rof_mult_B), True, "発/分")
    
    html += comp_tr("俯角 (マイナス角度)", get_val(dfA, s_gunA, '俯角'), get_val(dfB, s_gunB, '俯角'), True, "度")
    html += comp_tr("仰角", get_val(dfA, s_gunA, '仰角'), get_val(dfB, s_gunB, '仰角'), True, "度")
    html += comp_tr("水平可動域", get_val(dfA, s_gunA, '水平可動域'), get_val(dfB, s_gunB, '水平可動域'), True, "度")
    html += comp_tr("砲弾タイプ", get_val(dfA, s_gunA, '砲弾タイプ'), get_val(dfB, s_gunB, '砲弾タイプ'), None, "")
    html += comp_tr("弾速 (最大/通常弾)", get_split_str(get_val(dfA, s_gunA, '弾薬の最大速度'), 0), get_split_str(get_val(dfB, s_gunB, '弾薬の最大速度'), 0), True, "m/s")
    html += comp_tr("弾速 (金弾/APCR等)", get_split_str(get_val(dfA, s_gunA, '弾薬の最大速度'), 1), get_split_str(get_val(dfB, s_gunB, '弾薬の最大速度'), 1), True, "m/s")
    html += comp_tr("弾薬の最大射程", get_split_str(get_val(dfA, s_gunA, '弾薬の最大射程'), 0), get_split_str(get_val(dfB, s_gunB, '弾薬の最大射程'), 0), True, "m")
    html += comp_tr("総弾数", get_split_str(get_val(dfA, s_gunA, '総弾数'), 0), get_split_str(get_val(dfB, s_gunB, '総弾数'), 0), True, "発")
    
    disp_mult_A = 0.80 if apply_vstab_A else 1.0
    if apply_snap_shot_A: disp_mult_A *= (1.0 - (0.10 * skill_mult_A))
    disp_mult_A /= crew_mult_A
    disp_mult_B = 0.80 if apply_vstab_B else 1.0
    if apply_snap_shot_B: disp_mult_B *= (1.0 - (0.10 * skill_mult_B))
    disp_mult_B /= crew_mult_B
    html += comp_tr("砲塔旋回中の射撃精度", sim_val(get_val(dfA, s_gunA, '砲塔旋回中の射撃精度'), disp_mult_A), sim_val(get_val(dfB, s_gunB, '砲塔旋回中の射撃精度'), disp_mult_B), False, "m")
    
    html += comp_tr("モジュールの損傷", get_val(dfA, s_gunA, 'モジュールの損傷'), get_val(dfB, s_gunB, 'モジュールの損傷'), True, "HP")
    html += comp_tr("攻撃半径 (榴弾爆風)", get_split_str(get_val(dfA, s_gunA, '攻撃半径'), 2), get_split_str(get_val(dfB, s_gunB, '攻撃半径'), 2), True, "m")
    html += f"<tr><th style='text-align: left; padding-left: 15px;'>🛡️ 防御・耐久・視認</th><th></th><th></th></tr>"
    html += comp_tr("耐久値 (HP)", get_val(dfA, s_turretA, 'HP'), get_val(dfB, s_turretB, 'HP'), True, "HP")
    html += comp_tr("車体装甲 (前面)", get_split_str(get_val(dfA, s_turretA, '車体装甲(mm)'), 0), get_split_str(get_val(dfB, s_turretB, '車体装甲(mm)'), 0), True, "mm")
    html += comp_tr("車体装甲 (側面)", get_split_str(get_val(dfA, s_turretA, '車体装甲(mm)'), 1), get_split_str(get_val(dfB, s_turretB, '車体装甲(mm)'), 1), True, "mm")
    html += comp_tr("車体装甲 (背面)", get_split_str(get_val(dfA, s_turretA, '車体装甲(mm)'), 2), get_split_str(get_val(dfB, s_turretB, '車体装甲(mm)'), 2), True, "mm")
    html += comp_tr("砲塔装甲 (前面)", get_split_str(get_val(dfA, s_turretA, '砲塔装甲(mm)'), 0), get_split_str(get_val(dfB, s_turretB, '砲塔装甲(mm)'), 0), True, "mm")
    html += comp_tr("砲塔装甲 (側面)", get_split_str(get_val(dfA, s_turretA, '砲塔装甲(mm)'), 1), get_split_str(get_val(dfB, s_turretB, '砲塔装甲(mm)'), 1), True, "mm")
    html += comp_tr("砲塔装甲 (背面)", get_split_str(get_val(dfA, s_turretA, '砲塔装甲(mm)'), 2), get_split_str(get_val(dfB, s_turretB, '砲塔装甲(mm)'), 2), True, "mm")
    
    tankA_type = dfA['タイプ'].iloc[0] if not dfA.empty else "-"
    tankB_type = dfB['タイプ'].iloc[0] if not dfB.empty else "-"
    
    visionA = get_val(dfA, s_turretA, '視認範囲(m)')
    visionB = get_val(dfB, s_turretB, '視認範囲(m)')
    visionA_val = get_vision_values(visionA, apply_optics_A, apply_binocs_A, apply_sit_aware_A, crew_mult_A, skill_mult_A)
    visionB_val = get_vision_values(visionB, apply_optics_B, apply_binocs_B, apply_sit_aware_B, crew_mult_B, skill_mult_B)
    html += comp_tr("視認範囲", visionA_val, visionB_val, True, "m")
    
    concealA = get_val(dfA, s_turretA, '発見可能範囲')
    concealB = get_val(dfB, s_turretB, '発見可能範囲')
    moveA_val, stillA_val = get_conceal_values(concealA, tankA_type, apply_camo_A, apply_adv_camo_A, apply_camo_net_A, apply_camo_skill_A, apply_green_thumb_A, skill_mult_A)
    moveB_val, stillB_val = get_conceal_values(concealB, tankB_type, apply_camo_B, apply_adv_camo_B, apply_camo_net_B, apply_camo_skill_B, apply_green_thumb_B, skill_mult_B)
    html += comp_tr("発見可能範囲 (移動時)", moveA_val, moveB_val, False, "m")
    html += comp_tr("発見可能範囲 (静止時)", stillA_val, stillB_val, False, "m")
    
    tt_mult_A = 1.0 * crew_mult_A
    tt_mult_B = 1.0 * crew_mult_B
    if apply_fuel_p_A: tt_mult_A *= 1.10
    if apply_rapid_aim_A: tt_mult_A *= (1.0 + (0.10 * skill_mult_A))
    if apply_fuel_p_B: tt_mult_B *= 1.10
    if apply_rapid_aim_B: tt_mult_B *= (1.0 + (0.10 * skill_mult_B))
    html += comp_tr("砲塔旋回速度", sim_val(get_turret_traverse(dfA, s_turretA), tt_mult_A), sim_val(get_turret_traverse(dfB, s_turretB), tt_mult_B), True, "度/秒")
    
    rad_mult_A = 1.0 * crew_mult_A
    rad_mult_B = 1.0 * crew_mult_B
    if apply_signal_expert_A: rad_mult_A *= (1.0 + (0.30 * skill_mult_A))
    if apply_signal_expert_B: rad_mult_B *= (1.0 + (0.30 * skill_mult_B))
    html += comp_tr("通信範囲", sim_val(get_val(dfA, s_radioA, '通信範囲(m)'), rad_mult_A), sim_val(get_val(dfB, s_radioB, '通信範囲(m)'), rad_mult_B), True, "m")
    
    html += f"<tr><th style='text-align: left; padding-left: 15px;'>🚀 機動性・エコノミー</th><th></th><th></th></tr>"
    
    speed_mult_A = 1.05 if apply_turbo_A else 1.0
    if apply_fuel_p_A: speed_mult_A *= 1.05
    speed_mult_B = 1.05 if apply_turbo_B else 1.0
    if apply_fuel_p_B: speed_mult_B *= 1.05
    
    hp_mult_A = 1.05 if apply_turbo_A else 1.0
    if apply_fuel_a_A: hp_mult_A *= 1.10
    hp_mult_B = 1.05 if apply_turbo_B else 1.0
    if apply_fuel_a_B: hp_mult_B *= 1.10
    
    html += comp_tr("最大前進速度", sim_val(get_val(dfA, s_engineA, '最大前進速度'), speed_mult_A), sim_val(get_val(dfB, s_engineB, '最大前進速度'), speed_mult_B), True, "km/h")
    html += comp_tr("最大後進速度", sim_val(get_val(dfA, s_engineA, '最大後進速度'), speed_mult_A), sim_val(get_val(dfB, s_engineB, '最大後進速度'), speed_mult_B), True, "km/h")
    html += comp_tr("エンジン出力", sim_val(get_val(dfA, s_engineA, 'エンジン出力'), hp_mult_A, True), sim_val(get_val(dfB, s_engineB, 'エンジン出力'), hp_mult_B, True), True, "HP")
    html += comp_tr("出力重量比", sim_val(get_val(dfA, s_engineA, '出力重量比'), hp_mult_A), sim_val(get_val(dfB, s_engineB, '出力重量比'), hp_mult_B), True, "hp/t")
    
    html += comp_tr("火災発生率", get_val(dfA, s_engineA, '火災発生率'), get_val(dfB, s_engineB, '火災発生率'), False, "%")
    
    trav_mult_A = 1.0
    if apply_grouser_A: trav_mult_A *= 1.075
    if apply_clutch_braking_A: trav_mult_A *= (1.0 + (0.075 * skill_mult_A))
    trav_mult_B = 1.0
    if apply_grouser_B: trav_mult_B *= 1.075
    if apply_clutch_braking_B: trav_mult_B *= (1.0 + (0.075 * skill_mult_B))
    
    res_mult_A = 0.925 if apply_grouser_A else 1.0
    res_mult_A /= crew_mult_A
    res_mult_B = 0.925 if apply_grouser_B else 1.0
    res_mult_B /= crew_mult_B
    
    res_A = sim_res_val(get_ground_resistance(dfA, s_suspA), res_mult_A, res_mult_A, res_mult_A)
    res_B = sim_res_val(get_ground_resistance(dfB, s_suspB), res_mult_B, res_mult_B, res_mult_B)
    
    html += comp_tr("車体旋回速度", sim_val(get_hull_traverse(dfA, s_suspA), trav_mult_A), sim_val(get_hull_traverse(dfB, s_suspB), trav_mult_B), True, "度/秒")
    html += comp_tr("接地抵抗 (ハード)", get_split_str(res_A, 0), get_split_str(res_B, 0), False, "")
    html += comp_tr("接地抵抗 (ミディアム)", get_split_str(res_A, 1), get_split_str(res_B, 1), False, "")
    html += comp_tr("接地抵抗 (ソフト)", get_split_str(res_A, 2), get_split_str(res_B, 2), False, "")
    
    html += comp_tr("シルバー獲得レート", str(dfA['シルバー獲得レート'].iloc[0]) if not dfA.empty else "-", str(dfB['シルバー獲得レート'].iloc[0]) if not dfB.empty else "-", True, "%")
    html += comp_tr("EXP獲得レート", str(dfA['EXP獲得レート'].iloc[0]) if not dfA.empty else "-", str(dfB['EXP獲得レート'].iloc[0]) if not dfB.empty else "-", True, "%")
    html += comp_tr("フリーEXP獲得レート", str(dfA['フリーEXPレート'].iloc[0]) if not dfA.empty else "-", str(dfB['フリーEXPレート'].iloc[0]) if not dfB.empty else "-", True, "%")
    
    crew_exp_A = get_crew_exp_str(str(dfA['搭乗員EXPレート'].iloc[0]) if not dfA.empty else "-", apply_food_p_A)
    crew_exp_B = get_crew_exp_str(str(dfB['搭乗員EXPレート'].iloc[0]) if not dfB.empty else "-", apply_food_p_B)
    html += comp_tr("搭乗員EXP獲得レート", crew_exp_A, crew_exp_B, True, "%")
    
    html += comp_tr("最大マッチメイキング", str(dfA['最大TIER'].iloc[0]) if not dfA.empty else "-", str(dfB['最大TIER'].iloc[0]) if not dfB.empty else "-", None, "")
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 3. ランキング
# ==========================================
elif st.session_state['app_mode'] == "🏆 ランキング":
    st.title("🏆 戦術アナリティクス・ランキング")
    st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title' style='margin-top:0;'>🔍 抽出条件の指定</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    r_mode = c1.selectbox("モード:", ["WWII", "Cold War"])
    if r_mode == "WWII": r_tier = c2.selectbox("Tier:", ["すべて", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"], index=8)
    else: r_tier = c2.selectbox("時代:", ["すべて", "戦後", "エスカレーション", "デタント"])
    r_type = c3.selectbox("車種:", ["すべて", "軽戦車", "中戦車", "重戦車", "駆逐戦車", "自走砲"])
    
    st.markdown("#### 🏆 ランキング項目")
    rank_target = st.radio("比較対象を選択:", [
        "DPM", "貫通力 (通常弾)", "貫通力 (課金弾)", 
        "単発ダメージ (通常弾)", "単発ダメージ (榴弾 HE)", 
        "HP", "最高速度", "隠蔽率 (発見可能範囲・移動時)", "隠蔽率 (発見可能範囲・静止時)", "視認範囲"
    ], horizontal=True)
    
    st.markdown("#### 📊 集計ルール")
    rank_method = st.radio("集計方法を選択:", [
        "車輌ごとの最大値 (各車輌につき最強構成で1回のみランクイン)", 
        "すべての砲・モジュールを参加させる (同じ車輌でも装備が違えば別々にランクイン)"
    ], horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    col_dict = {
        "DPM": ("Rank_DPM_Main", False),
        "貫通力 (通常弾)": ("Rank_Pen_Std", False),
        "貫通力 (課金弾)": ("Rank_Pen_Gold", False),
        "単発ダメージ (通常弾)": ("Rank_Dmg_Std", False),
        "単発ダメージ (榴弾 HE)": ("Rank_Dmg_HE", False),
        "HP": ("Rank_HP", False),
        "最高速度": ("Rank_Speed", False),
        "隠蔽率 (発見可能範囲・移動時)": ("Rank_Conceal_Move", True),
        "隠蔽率 (発見可能範囲・静止時)": ("Rank_Conceal_Still", True),
        "視認範囲": ("Rank_Vision", False)
    }
    
    sort_col, is_asc = col_dict[rank_target]
    r_df = df[df['モード'] == r_mode].copy()
    if r_tier != "すべて": r_df = r_df[r_df['Tier'] == r_tier if r_mode == "WWII" else r_df['時代'] == r_tier]
    if r_type != "すべて": r_df = r_df[r_df['タイプ'] == r_type]
        
    if r_df.empty: 
        st.warning("条件に一致する車輌がありません。")
    else:
        r_df = r_df[r_df[sort_col] > 0]
        if r_df.empty:
            st.warning("⚠️ 該当するステータスを持つ車輌が存在しません。")
        else:
            if "すべての砲" in rank_method:
                target_mod_types = ['初期装備']
                if rank_target in ["DPM", "貫通力 (通常弾)", "貫通力 (課金弾)", "単発ダメージ (通常弾)", "単発ダメージ (榴弾 HE)"]:
                    target_mod_types.append('主砲')
                elif rank_target in ["HP", "隠蔽率 (発見可能範囲・移動時)", "隠蔽率 (発見可能範囲・静止時)", "視認範囲"]:
                    target_mod_types.append('砲塔')
                elif rank_target == "最高速度":
                    target_mod_types.append('エンジン')
                
                mod_df = r_df[r_df['モジュール種類'].isin(target_mod_types)].copy()
                if mod_df.empty: mod_df = r_df.copy()
                idx = mod_df.groupby(['正確な車輌名', 'モジュール状態'])[sort_col].idxmin() if is_asc else mod_df.groupby(['正確な車輌名', 'モジュール状態'])[sort_col].idxmax()
                ranked = mod_df.loc[idx].copy()
            else:
                idx = r_df.groupby(['正確な車輌名'])[sort_col].idxmin() if is_asc else r_df.groupby(['正確な車輌名'])[sort_col].idxmax()
                ranked = r_df.loc[idx].copy()
                
            ranked = ranked.sort_values(by=sort_col, ascending=is_asc).reset_index(drop=True)
            ranked.index = ranked.index + 1
            
            if "DPM" in rank_target:
                disp_cols = ['正確な車輌名', '国', 'タイプ', 'モジュール状態', sort_col, '貫通力100m(主砲)', 'ダメージ(主砲)', '装填時間(主砲)']
                col_names = ['車輌名', '国', '車種', '使用パッケージ(モジュール)', f'値 ({rank_target})', '貫通力 (通常/金/HE)', 'ダメージ (通常/金/HE)', '装填時間(秒)']
            elif "貫通力" in rank_target or "ダメージ" in rank_target:
                disp_cols = ['正確な車輌名', '国', 'タイプ', 'モジュール状態', sort_col, '貫通力100m(主砲)', 'ダメージ(主砲)', 'DPM(主砲)']
                col_names = ['車輌名', '国', '車種', '使用パッケージ(モジュール)', f'値 ({rank_target})', '貫通力 (通常/金/HE)', 'ダメージ (通常/金/HE)', 'DPM']
            elif "隠蔽率" in rank_target:
                disp_cols = ['正確な車輌名', '国', 'タイプ', 'モジュール状態', sort_col, '発見可能範囲', '視認範囲(m)']
                col_names = ['車輌名', '国', '車種', '使用パッケージ(モジュール)', f'値 (隠蔽率 m)', '発見可能範囲 (移動/静止)', '視認範囲(m)']
            elif rank_target == "視認範囲":
                disp_cols = ['正確な車輌名', '国', 'タイプ', 'モジュール状態', sort_col, '発見可能範囲']
                col_names = ['車輌名', '国', '車種', '使用パッケージ(モジュール)', '値 (視認範囲 m)', '発見可能範囲 (移動/静止)']
            else:
                disp_cols = ['正確な車輌名', '国', 'タイプ', 'モジュール状態', sort_col]
                col_names = ['車輌名', '国', '車種', '使用パッケージ(モジュール)', f'値 ({rank_target})']
                
            display_df = ranked[disp_cols].copy()
            display_df.columns = col_names
            
            st.markdown("---")
            st.markdown(f"### 👑 {r_tier} {r_type} - {rank_target} TOPランキング")
            
            # === Streamlitのバージョン依存を回避した安全なクリックジャンプ機能 ===
            st_version = st.__version__.split('.')
            use_selection = False
            if len(st_version) >= 2 and int(st_version[0]) >= 1 and int(st_version[1]) >= 35:
                use_selection = True
                
            if use_selection:
                st.markdown("<div style='color:#58a6ff; margin-bottom:10px;'>💡 <b>表の行（車輌）をクリックすると、そのまま図鑑のシミュレーション画面へジャンプします！</b></div>", unsafe_allow_html=True)
                event = st.dataframe(
                    display_df.head(100), 
                    use_container_width=True,
                    on_select="rerun",
                    selection_mode="single-row"
                )
                if event.selection.rows:
                    sel_idx = event.selection.rows[0]
                    sel_tank = display_df.iloc[sel_idx]['車輌名']
                    st.session_state['zukan_jump_tank'] = sel_tank
                    st.session_state['zukan_jump_mode'] = r_mode
                    st.session_state['app_mode'] = "📖 車輌図鑑"
                    st.rerun()
            else:
                st.dataframe(display_df.head(100), use_container_width=True)

# ==========================================
# 4. 装甲計算シミュレーター (手動)
# ==========================================
elif st.session_state['app_mode'] == "🛡️ 装甲計算シミュレーター":
    st.title("🛡️ 実質装甲厚 計算シミュレーター (昼飯・豚飯検証)")
    st.write("WOT特有の「標準化（Normalization）」を加味し、入力した角度に対する実質装甲厚を自動計算します。")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title' style='margin-top:0;'>📐 条件設定</div>", unsafe_allow_html=True)
        mode_calc = st.radio("装甲厚の入力方法:", ["手動で数値を入力", "図鑑のデータから引用"], horizontal=True)

        nominal_armor = 250.0 
        
        if mode_calc == "図鑑のデータから引用":
            c1_1, c1_2 = st.columns(2)
            calc_q = c1_1.text_input("車輌検索:", placeholder="名前入力...")
            f_calc = df[df['モード'] == "WWII"].copy()
            if calc_q: f_calc = f_calc[f_calc['正確な車輌名'].str.contains(calc_q, case=False, na=False)]
            calc_list = sorted(f_calc['正確な車輌名'].unique())
            calc_tank = c1_2.selectbox("車輌を選択:", calc_list if calc_list else ["-"])
            
            if calc_tank != "-":
                t_df = df[df['正確な車輌名'] == calc_tank]
                turrets = t_df[t_df['モジュール種類'] == '砲塔']['モジュール状態'].unique()
                s_turret = st.selectbox("砲塔モジュール:", turrets) if len(turrets) > 0 else None
                
                part_choice = st.selectbox("計算する部位:", ["車体前面", "車体側面", "車体背面", "砲塔前面", "砲塔側面", "砲塔背面"])
                hull_str = get_val(t_df, s_turret, '車体装甲(mm)')
                turret_str = get_val(t_df, s_turret, '砲塔装甲(mm)')
                
                if "車体" in part_choice:
                    idx = ["前面", "側面", "背面"].index(part_choice.replace("車体", ""))
                    val_str = get_split_str(hull_str, idx)
                else:
                    idx = ["前面", "側面", "背面"].index(part_choice.replace("砲塔", ""))
                    val_str = get_split_str(turret_str, idx)
                
                extracted_val = get_float(val_str)
                if extracted_val:
                    nominal_armor = float(extracted_val)
                    st.success(f"✅ {calc_tank} の {part_choice}装甲: **{nominal_armor} mm** をセットしました。")
                else:
                    st.warning("装甲値が取得できませんでした。手動入力に切り替えてください。")
        else:
            nominal_armor = st.number_input("基本装甲厚 (mm):", min_value=1.0, max_value=1500.0, value=250.0, step=1.0)

        st.markdown("---")
        angle_deg = st.slider("着弾角度 (度) ※0度が真正面からの直撃、70度以上は跳弾危険域", min_value=0.0, max_value=89.0, value=20.0, step=1.0)
        
        # WOT特有の弾種による標準化をワンクリックでセット
        ammo_type = st.radio("被弾する弾種 (標準化の自動適用):", ["AP弾 (標準化 5度)", "APCR弾 (標準化 2度)", "HEAT / HE弾 (標準化 0度)", "カスタム (手動入力)"])
        
        if "AP弾" in ammo_type: default_norm = 5.0
        elif "APCR" in ammo_type: default_norm = 2.0
        elif "HEAT" in ammo_type: default_norm = 0.0
        else: default_norm = 0.0
        
        normalization = st.number_input("標準化角度 (度):", min_value=0.0, max_value=20.0, value=default_norm, step=1.0)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='panel-box' style='height: 100%;'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title' style='margin-top:0;'>🛡️ 計算結果</div>", unsafe_allow_html=True)
        calc_angle = max(0.0, angle_deg - normalization)
        
        if angle_deg >= 70.0 and ("HEAT" not in ammo_type and "HE" not in ammo_type):
            st.markdown("<div class='armor-result-bounce'>跳弾 (Ricochet)</div>", unsafe_allow_html=True)
            st.info("※APおよびAPCR弾は、着弾角度が70度以上の場合、装甲厚に関わらず強制跳弾（Auto-Bounce）となります。（3倍ルール適応時を除く）")
        elif angle_deg >= 85.0 and "HEAT" in ammo_type:
            st.markdown("<div class='armor-result-bounce'>跳弾 (Ricochet)</div>", unsafe_allow_html=True)
            st.info("※HEAT弾は着弾角度が85度以上で強制跳弾となります。")
        else:
            if calc_angle >= 89.9: eff_armor = float('inf')
            else: eff_armor = nominal_armor / math.cos(math.radians(calc_angle))
            
            st.markdown(f"<div class='armor-result'>{eff_armor:.1f} MM</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='armor-subtext'>基本装甲 <b>{nominal_armor}mm</b> / 実効角度 <b>{calc_angle:.1f}°</b></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 💡 WOTの計算式メカニズム")
        st.latex(r"実質装甲 = \frac{基本装甲厚}{\cos(着弾角度 - 標準化)}")
        st.write("""
        * **標準化 (Normalization):** 砲弾が装甲に食い込む際に、角度を垂直に近づけようとする力。AP弾は5度、APCR弾は2度有利に判定されます。
        * **跳弾 (Ricochet):** WOTでは、AP/APCRは70度以上、HEATは85度以上で着弾すると、貫通力に関係なく弾かれます（3倍ルール適応時を除く）。
        """)
        st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 5. 📸 スーパー簡易画像装甲測定
# ==========================================
elif st.session_state['app_mode'] == "📸 スーパー簡易画像装甲測定":
    st.title("📸 スーパー簡易画像装甲測定 (弾道指定版)")
    
    st.info("💡 **使い方**\n\n"
            "1. 側面からの画像をアップロードします。\n"
            "2. 画像上で調べたい装甲の**「上端」**と**「下端」**をクリックします。\n"
            "3. 最後に**「弾が飛んでくる方向（発射元）」**をクリックすると実装甲厚が出ます。")

    if not HAS_IMG_COORD:
        st.error("⚠️ この機能を使用するには追加ライブラリが必要です。コマンドプロンプト等で以下のコマンドを実行し、アプリを再起動してください。")
        st.code("pip install streamlit-image-coordinates pillow")
        st.stop()

    col_settings, col_image = st.columns([1.5, 2.5])

    with col_settings:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title' style='margin-top:0;'>⚙️ 条件設定</div>", unsafe_allow_html=True)
        nominal_armor = st.number_input("基本装甲厚 (mm):", min_value=1.0, max_value=1500.0, value=100.0, step=1.0)
        
        st.markdown("---")
        ammo_type = st.radio("被弾する弾種 (標準化の自動適用):", ["AP弾 (標準化 5度)", "APCR弾 (標準化 2度)", "HEAT / HE弾 (標準化 0度)"])
        
        if "AP弾" in ammo_type: default_norm = 5.0
        elif "APCR" in ammo_type: default_norm = 2.0
        else: default_norm = 0.0
        
        normalization = st.number_input("標準化角度 (度):", min_value=0.0, max_value=20.0, value=default_norm, step=1.0)
        
        st.markdown("---")
        horizontal_angle = st.slider("車体を斜めにする (昼飯・豚飯角)", min_value=0.0, max_value=89.0, value=0.0, step=1.0)
        
        st.markdown("---")
        if st.button("🔄 クリック位置をリセット", use_container_width=True):
            st.session_state['img_clicks'] = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
        # --- 3点クリック計算結果エリア ---
        if len(st.session_state.get('img_clicks', [])) == 3:
            x1, y1 = st.session_state['img_clicks'][0]
            x2, y2 = st.session_state['img_clicks'][1]
            x3, y3 = st.session_state['img_clicks'][2]
            
            M_x = (x1 + x2) / 2.0
            M_y = (y1 + y2) / 2.0
            
            Nx = -(y2 - y1)
            Ny = (x2 - x1)
            Sx = M_x - x3
            Sy = M_y - y3
            
            mag_N = math.hypot(Nx, Ny)
            mag_S = math.hypot(Sx, Sy)
            
            if mag_N == 0 or mag_S == 0:
                angle_deg = 0.0
            else:
                dp = (Sx * Nx) + (Sy * Ny)
                cos_theta = abs(dp) / (mag_S * mag_N)
                cos_theta = max(0.0, min(1.0, cos_theta))
                angle_deg = math.degrees(math.acos(cos_theta))

            compound_angle_rad = math.acos(math.cos(math.radians(angle_deg)) * math.cos(math.radians(horizontal_angle)))
            compound_angle_deg = math.degrees(compound_angle_rad)

            st.markdown("<div class='panel-box' style='border-color: #58a6ff; background-color: rgba(88, 166, 255, 0.05);'>", unsafe_allow_html=True)
            st.markdown("<div class='panel-title' style='color: #58a6ff !important; margin-top:0;'>🛡️ 計算結果</div>", unsafe_allow_html=True)
            
            calc_angle = max(0.0, compound_angle_deg - normalization)
            
            if compound_angle_deg >= 70.0 and ("HEAT" not in ammo_type and "HE" not in ammo_type):
                st.markdown("<div class='armor-result-bounce'>跳弾 (Ricochet)</div>", unsafe_allow_html=True)
                st.info("※APおよびAPCR弾は、着弾角度が70度以上の場合、強制跳弾（Auto-Bounce）となります。")
            elif compound_angle_deg >= 85.0 and "HEAT" in ammo_type:
                st.markdown("<div class='armor-result-bounce'>跳弾 (Ricochet)</div>", unsafe_allow_html=True)
                st.info("※HEAT弾は着弾角度が85度以上で強制跳弾となります。")
            else:
                if calc_angle >= 89.9: eff_armor = float('inf')
                else: eff_armor = nominal_armor / math.cos(math.radians(calc_angle))
                
                st.markdown(f"<div class='armor-result'>{eff_armor:.1f} MM</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='armor-subtext'>基本装甲 <b>{nominal_armor}mm</b> / 最終実効角度 <b>{calc_angle:.1f}°</b></div>", unsafe_allow_html=True)
                st.success(f"🎯 測定角度: 約 **{compound_angle_deg:.1f} 度**")
            st.markdown("</div>", unsafe_allow_html=True)

    with col_image:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title' style='margin-top:0;'>📸 画像測定ボード</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("側面から撮影したスクリーンショットをアップロード", type=["png", "jpg", "jpeg"])
        
        target_image = None
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if uploaded_file is not None:
            target_image = Image.open(uploaded_file).convert("RGB")
        else:
            if SAMPLE_IMG_FILE:
                sample_path = os.path.join(base_dir, SAMPLE_IMG_FILE)
                target_image = Image.open(sample_path).convert("RGB")
            else:
                st.warning("⚠️ サンプル画像が見つかりません。画像をアップロードしてください。")

        if 'img_clicks' not in st.session_state:
            st.session_state['img_clicks'] = []
            
        if target_image is not None:
            target_image.thumbnail((800, 800))
            
            draw_image = target_image.copy()
            draw = ImageDraw.Draw(draw_image)
            clicks = st.session_state.get('img_clicks', [])
            
            r = 6 
            for i, pt in enumerate(clicks):
                color = "red" if i < 2 else "cyan"
                draw.ellipse((pt[0]-r, pt[1]-r, pt[0]+r, pt[1]+r), fill=color, outline="white", width=2)
                
            if len(clicks) >= 2:
                x1, y1 = clicks[0]
                x2, y2 = clicks[1]
                draw.line([(x1, y1), (x2, y2)], fill="lime", width=4)
                
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                
                if len(clicks) == 3:
                    x3, y3 = clicks[2]
                    draw.line([(x3, y3), (mid_x, mid_y)], fill="cyan", width=3)
                    
                    arrow_angle = math.atan2(mid_y - y3, mid_x - x3)
                    head_len = 15
                    head_angle = math.pi / 6 
                    hx1 = mid_x - head_len * math.cos(arrow_angle - head_angle)
                    hy1 = mid_y - head_len * math.sin(arrow_angle - head_angle)
                    hx2 = mid_x - head_len * math.cos(arrow_angle + head_angle)
                    hy2 = mid_y - head_len * math.sin(arrow_angle + head_angle)
                    draw.polygon([(mid_x, mid_y), (hx1, hy1), (hx2, hy2)], fill="cyan")

            # ユーザーへの案内テキスト
            if len(clicks) == 0:
                st.warning("👆 画像上で、測定したい装甲の「片端」をクリックしてください。")
            elif len(clicks) == 1:
                st.warning("👆 次に、同じ装甲の「もう一端」をクリックしてください。")
            elif len(clicks) == 2:
                st.warning("🎯 最後に、「弾が飛んでくる方向（発射元）」をクリックしてください。")
            else:
                st.success("✅ 測定完了！結果は左側に表示されています。やり直す場合は再度画像をクリックしてください。")
            
            value = streamlit_image_coordinates(draw_image, key="armor_img")
            
            if value is not None:
                pt = (value["x"], value["y"])
                if len(st.session_state['img_clicks']) < 3 and pt not in st.session_state['img_clicks']:
                    st.session_state['img_clicks'].append(pt)
                    st.rerun() 
            
        st.markdown("</div>", unsafe_allow_html=True)
