import streamlit as st
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

# ページ設定
st.set_page_config(page_title="RECAT 総合データコンソール", layout="wide", initial_sidebar_state="expanded")

# === セッションステートの初期化 (ページ遷移用) ===
if 'app_mode' not in st.session_state:
    st.session_state['app_mode'] = "🏠 ホーム (メインメニュー)"

# === ファイル名とパスの自動解決 ===
base_dir = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = "wot_wwii_all_tanks_modules.csv"
ZIP_FILE = "wot_wwii_all_tanks_modules.zip"

LOGO_FILE = None
for potential_logo in ["1782708565492 (1)-Photoroom_2.png", "1782708565492 (1)-Photoroom.png"]:
    if os.path.exists(os.path.join(base_dir, potential_logo)):
        LOGO_FILE = potential_logo
        break

SAMPLE_IMG_FILE = "Screenshot 2026-07-17 23-00-25_3.jpg"

def get_base64_of_bin_file(bin_file):
    if bin_file:
        full_path = os.path.join(base_dir, bin_file)
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
    return None

logo_base64 = get_base64_of_bin_file(LOGO_FILE)

# === 全体デザイン設定 (完全ダークモード) ===
css = """
<style>
/* メイン画面とサイドバーの背景を黒/ダークグレーに固定 */
.stApp { background-color: #0d1117 !important; }
[data-testid="stSidebar"] { background-color: #161b22 !important; }

/* 全体の文字色を白系に固定 */
h1, h2, h3, h4, h5, h6, p, span, label, div { color: #e6edf3 !important; }

/* タブ（ドロップダウン）展開時のメニューも強制ダークモード化 */
div[data-baseweb="select"] > div { background-color: #1c2128 !important; color: #ffffff !important; border-color: #30363d !important; }
div[data-baseweb="popover"] { background-color: #1c2128 !important; }
div[data-baseweb="popover"] * { color: #e6edf3 !important; }
ul[role="listbox"] { background-color: #1c2128 !important; }
li[role="option"] { background-color: #1c2128 !important; color: #ffffff !important; }
li[role="option"]:hover { background-color: #30363d !important; color: #58a6ff !important; }
input { background-color: #1c2128 !important; color: #ffffff !important; border: 1px solid #30363d !important; }

/* ⚠️追加: ボタンの完全ダーク化設定 */
div[data-testid="stButton"] button { background-color: #21262d !important; color: #58a6ff !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
div[data-testid="stButton"] button:hover { background-color: #30363d !important; color: #ffffff !important; border: 1px solid #58a6ff !important; }
div[data-testid="stButton"] button p { color: inherit !important; }

/* サイドバーのロゴ画像を不透明度15%に設定 */
[data-testid="stSidebar"] img { opacity: 0.15 !important; }

/* パネルとテーブルのデザイン */
.block-container { max-width: 1600px; padding-top: 1.5rem; }
.panel-box { padding: 20px; background-color: #161b22; border-radius: 12px; margin-bottom: 20px; border: 1px solid #30363d; box-shadow: 0 4px 6px rgba(0,0,0,0.5); }
.panel-title { font-size: 1.2em; color: #58a6ff !important; margin-top: 10px; margin-bottom: 15px; border-bottom: 2px solid #30363d; padding-bottom: 5px; }
.comp-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.95em; background-color: #161b22; border-radius: 8px; overflow: hidden; }
.comp-table th { background-color: #21262d; padding: 12px; border-bottom: 2px solid #30363d; text-align: center; font-size: 1.1em; color: #ffffff !important; }
.comp-table td { padding: 8px 12px; border-bottom: 1px solid #30363d; text-align: center; color: #e6edf3 !important;}
.comp-label { text-align: left !important; color: #8b949e !important; width: 26%; font-weight: 500; background-color: #0d1117; }
.win-stat { color: #58a6ff !important; font-weight: bold; background-color: rgba(88, 166, 255, 0.1); }
.stat-label { font-size: 0.8em; color: #8b949e !important; margin-bottom: -4px; margin-top: 8px; text-align: center; }
.stat-value { font-size: 1.1em; font-weight: bold; margin-bottom: 4px; text-align: center; color: #e6edf3 !important; }
.armor-result { font-size: 3.5em; font-weight: bold; color: #ff7b72 !important; text-align: center; margin-top: 10px; margin-bottom: 5px; line-height: 1.1;}
.armor-result-bounce { font-size: 2.8em; font-weight: bold; color: #8b949e !important; text-align: center; margin-top: 10px; margin-bottom: 5px; }
.armor-subtext { text-align: center; color: #8b949e !important; font-size: 0.9em; margin-bottom: 15px;}
</style>
"""

# === ⚠️修正: ホーム画面のみロゴの透かしを表示 (スペースなしで左詰めに配置) ===
if logo_base64 and st.session_state.get('sidebar_radio', "🏠 ホーム (メインメニュー)") == "🏠 ホーム (メインメニュー)":
    css += f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/png;base64,{logo_base64}");
    background-position: center;
    background-repeat: no-repeat;
    background-size: 450px;
    background-attachment: fixed;
}}
[data-testid="stAppViewContainer"]::before {{
    content: ""; position: absolute; top: 0; right: 0; bottom: 0; left: 0;
    background-color: rgba(13, 17, 23, 0.88); z-index: -1;
}}
</style>
"""

st.markdown(css, unsafe_allow_html=True)

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
        m = re.search(pattern, str(text))
        return m.group(1).replace(' ', '').strip('/') if m else "-"
        
    def get_match_all(pattern, text):
        return [m.replace(' ', '').strip('/') for m in re.findall(pattern, str(text))]

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
    df['砲塔旋回中の射撃精度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'砲塔旋回中の射撃精度 / ([\d\.]+)M', x))
    df['俯角'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'俯角 / ([\d\.]+)度', x))
    df['仰角'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'仰角 / ([\d\.]+)度', x))
    df['水平可動域'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'水平可動域 / ([\-\d/ \.]+)度', x))
    df['HP'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'HP(\d+)HP', x))
    df['砲塔装甲(mm)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'砲塔装甲 / ([\d/ \.]+)MM', x))
    df['車体装甲(mm)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'車体装甲.*?([\d/ \.]+)MM', x))
    df['視認範囲(m)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'視認範囲 / ([\d\.]+)M', x))
    df['発見可能範囲'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'発見可能範囲[^\d]*([\d\.]+/?[\d\.]*)', x))
    df['旋回速度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'旋回速度 / ([\d\.]+)度', x))
    df['通信範囲(m)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'通信範囲 / ([\d\.]+)M', x))
    df['エンジン出力'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'エンジン出力 / (\d+)HP', x))
    df['出力重量比'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'出力重量比 / ([\d\.]+)HP', x))
    df['最大前進速度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'最大速度([\d\.]+)/', x))
    df['最大後進速度'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'最大速度[\d\.]+/([\d\.]+)\(', x))
    df['火災発生率'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'火災発生率 / (\d+)パーセント', x))
    df['接地抵抗'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'接地抵抗 / ([\d/ \.]+)', x))
    df['最大TIER'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'最大TIER[^\d]*([IVX]+)', x))
    df['シルバー獲得レート'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'シルバー獲得レート[^\d]*(\d+)', x))
    df['EXP獲得レート'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'EXP獲得レート[^\d]*(\d+)', x))
    df['フリーEXPレート'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'フリーEXP獲得レート[^\d]*(\d+)', x))
    df['搭乗員EXPレート'] = df['詳細・モジュール生データ'].apply(lambda x: get_match(r'搭乗員EXPレート[^\d]*(\d+)', x))

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
    df['Rank_Dmg_Std'] = df['ダメージ(主砲)'].apply(lambda x: get_split_val(x, 0))
    df['Rank_HP'] = df['HP'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Speed'] = df['最大前進速度'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Conceal_Move'] = df['発見可能範囲'].apply(lambda x: get_split_val(x, 0))
    df['Rank_Vision'] = df['視認範囲(m)'].apply(lambda x: get_split_val(x, 0))
    return df

df = load_and_parse_data()
if df.empty:
    st.error(f"エラー: データファイル ({CSV_FILE} または {ZIP_FILE}) が見つかりません。")
    st.stop()

# ==========================================
# サイドバーとメインメニューの設定
# ==========================================
if LOGO_FILE:
    logo_path = os.path.join(base_dir, LOGO_FILE)
    st.sidebar.image(logo_path, use_container_width=True) 
else:
    st.sidebar.title("RECAT Console")
    
st.session_state['app_mode'] = st.sidebar.radio("機能メニュー", [
    "🏠 ホーム (メインメニュー)", 
    "📖 車輌図鑑", 
    "⚖️ 車輌比較", 
    "🏆 ランキング", 
    "🛡️ 装甲計算シミュレーター", 
    "📸 スーパー簡易画像装甲測定"
], key="sidebar_radio")
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips:** PC環境では画面幅を広げるとより見やすくなります。")

def get_val(tank_data, mod_state, col_name):
    if mod_state and not tank_data[tank_data['モジュール状態'] == mod_state].empty: return str(tank_data[tank_data['モジュール状態'] == mod_state][col_name].iloc[0])
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

def render_html_zukan(label, value, suffix=""):
    if value and str(value) != "-":
        st.markdown(f"<div class='stat-label'>{label}</div><div class='stat-value'>{value} <span style='font-size:0.7em; color:#8b949e;'>{suffix}</span></div>", unsafe_allow_html=True)


# ==========================================
# 0. ホーム（メインメニュー）
# ==========================================
if st.session_state['app_mode'] == "🏠 ホーム (メインメニュー)":
    if LOGO_FILE:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image(logo_path, use_container_width=True)
            
    st.markdown("<h1 style='text-align: center; color: #58a6ff !important;'>RECAT 総合データコンソール</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e !important;'>World of Tanks: Modern Armor 専用アナリティクスツール</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 💡 ツールを選択してください")
    
    # ジャンプ用ボタンの配置
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("📖 車輌図鑑\n\n全ステータスや隠し性能を確認", use_container_width=True):
            st.session_state['sidebar_radio'] = "📖 車輌図鑑"
            st.rerun()
    with b2:
        if st.button("⚖️ 車輌比較\n\n2つの車輌の性能を並べて比較", use_container_width=True):
            st.session_state['sidebar_radio'] = "⚖️ 車輌比較"
            st.rerun()
    with b3:
        if st.button("🏆 ランキング\n\nDPMや貫通力などの最強ランキング", use_container_width=True):
            st.session_state['sidebar_radio'] = "🏆 ランキング"
            st.rerun()
            
    b4, b5 = st.columns(2)
    with b4:
        if st.button("🛡️ 装甲計算シミュレーター\n\n昼飯・豚飯時の実質装甲厚を手動計算", use_container_width=True):
            st.session_state['sidebar_radio'] = "🛡️ 装甲計算シミュレーター"
            st.rerun()
    with b5:
        if st.button("📸 スーパー簡易画像装甲測定\n\nスクショから自動的に実装甲厚を計算", use_container_width=True):
            st.session_state['sidebar_radio'] = "📸 スーパー簡易画像装甲測定"
            st.rerun()


# ==========================================
# 1. 車輌図鑑
# ==========================================
elif st.session_state['app_mode'] == "📖 車輌図鑑":
    st.title("📖 車輌図鑑")
    st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>🔍 車輌の検索・絞り込み</div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    z_mode = c1.radio("モード", ["WWII", "Cold War"], horizontal=True)
    z_q = c2.text_input("名前で検索 (フリーワード):", placeholder="例: Tiger")
    f_df = df[df['モード'] == z_mode].copy()
    z_nation = c3.selectbox("国別", ["すべて"] + list(f_df['国'].dropna().unique()))
    z_type = c4.selectbox("車種", ["すべて", "軽戦車", "中戦車", "重戦車", "駆逐戦車", "自走砲"])
    z_tier = c5.selectbox("Tier / 時代", ["すべて", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "戦後", "エスカレーション", "デタント"])
    if z_q: f_df = f_df[f_df['正確な車輌名'].str.contains(z_q, case=False, na=False)]
    if z_nation != "すべて": f_df = f_df[f_df['国'] == z_nation]
    if z_type != "すべて": f_df = f_df[f_df['タイプ'] == z_type]
    if z_tier != "すべて": f_df = f_df[(f_df['Tier'] == z_tier) | (f_df['時代'] == z_tier)]
    tank_list = sorted(f_df['正確な車輌名'].unique())
    if not tank_list: 
        st.warning("条件に一致する車輌がありません。")
        st.stop()
    selected_tank = st.selectbox("🎯 抽出対象の車輌を選択", tank_list)
    st.markdown("</div>", unsafe_allow_html=True)
    
    t_data = df[df['正確な車輌名'] == selected_tank]
    st.markdown("---")
    st.markdown(f"<div class='panel-title'>⚙️ モジュール構成 - {selected_tank}</div>", unsafe_allow_html=True)
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    guns = t_data[t_data['モジュール種類'] == '主砲']['モジュール状態'].unique()
    turrets = t_data[t_data['モジュール種類'] == '砲塔']['モジュール状態'].unique()
    engines = t_data[t_data['モジュール種類'] == 'エンジン']['モジュール状態'].unique()
    susps = t_data[t_data['モジュール種類'] == 'サスペンション']['モジュール状態'].unique()
    radios = t_data[t_data['モジュール種類'] == '無線']['モジュール状態'].unique()
    s_gun = mc1.selectbox("主砲", guns) if len(guns) > 0 else None
    s_turret = mc2.selectbox("砲塔", turrets) if len(turrets) > 0 else None
    s_engine = mc3.selectbox("エンジン", engines) if len(engines) > 0 else None
    s_susp = mc4.selectbox("履帯", susps) if len(susps) > 0 else None
    s_radio = mc5.selectbox("無線", radios) if len(radios) > 0 else None
    
    st.markdown("---")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>💥 攻撃性能 (主砲)</div>", unsafe_allow_html=True)
        render_html_zukan("分間ダメージ", get_val(t_data, s_gun, 'DPM(主砲)'), "HP/分")
        pen_main = get_val(t_data, s_gun, '貫通力100m(主砲)')
        render_html_zukan("100M 貫通力 (通常/金/HE)", f"{get_split_str(pen_main, 0)} / {get_split_str(pen_main, 1)} / {get_split_str(pen_main, 2)}", "MM")
        pen_500 = get_val(t_data, s_gun, '貫通力500m(主砲)')
        render_html_zukan("500M 貫通力 (通常/金)", f"{get_split_str(pen_500, 0)} / {get_split_str(pen_500, 1)}", "MM")
        dmg_main = get_val(t_data, s_gun, 'ダメージ(主砲)')
        render_html_zukan("ダメージ (通常/金/HE)", f"{get_split_str(dmg_main, 0)} / {get_split_str(dmg_main, 1)} / {get_split_str(dmg_main, 2)}", "HP")
        render_html_zukan("装填時間", get_val(t_data, s_gun, '装填時間(主砲)'), "秒")
        render_html_zukan("照準時間", get_val(t_data, s_gun, '照準時間(秒)'), "秒")
        render_html_zukan("精度", get_val(t_data, s_gun, '精度(m)'), "M")
        render_html_zukan("射撃速度", get_val(t_data, s_gun, '射撃速度'), "発/分")
        st.markdown("</div>", unsafe_allow_html=True)
    with d2:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>💥 攻撃・砲弾特性</div>", unsafe_allow_html=True)
        dpm_sub = get_val(t_data, s_gun, 'DPM(副砲)')
        if dpm_sub != "-":
            render_html_zukan("分間ダメージ (副砲)", dpm_sub, "HP/分")
            render_html_zukan("100M 貫通力 (副砲)", get_split_str(get_val(t_data, s_gun, '貫通力100m(副砲)'), 0), "MM")
            render_html_zukan("ダメージ (副砲)", get_split_str(get_val(t_data, s_gun, 'ダメージ(副砲)'), 0), "HP")
            render_html_zukan("装填時間 (副砲)", get_val(t_data, s_gun, '装填時間(副砲)'), "秒")
            st.markdown("<hr style='border-color:#333; margin:10px 0;'>", unsafe_allow_html=True)
        render_html_zukan("俯角 / 仰角", f"{get_val(t_data, s_gun, '俯角')} / {get_val(t_data, s_gun, '仰角')}", "度")
        render_html_zukan("水平可動域", get_val(t_data, s_gun, '水平可動域'), "度")
        render_html_zukan("砲弾タイプ", get_val(t_data, s_gun, '砲弾タイプ'))
        render_html_zukan("弾薬の最大速度", get_val(t_data, s_gun, '弾薬の最大速度'), "M/S")
        render_html_zukan("弾薬の最大射程", get_val(t_data, s_gun, '弾薬の最大射程'), "M")
        render_html_zukan("総弾数", get_val(t_data, s_gun, '総弾数'), "発")
        render_html_zukan("砲塔旋回中の射撃精度", get_val(t_data, s_gun, '砲塔旋回中の射撃精度'), "M")
        render_html_zukan("攻撃半径 (榴弾)", get_val(t_data, s_gun, '攻撃半径'), "M")
        st.markdown("</div>", unsafe_allow_html=True)
    with d3:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>🛡️ 防御・視認</div>", unsafe_allow_html=True)
        render_html_zukan("耐久値 (HP)", get_val(t_data, s_turret, 'HP'), "HP")
        hull_armor = get_val(t_data, s_turret, '車体装甲(mm)')
        render_html_zukan("車体装甲 (前/側/背)", f"{get_split_str(hull_armor, 0)} / {get_split_str(hull_armor, 1)} / {get_split_str(hull_armor, 2)}", "MM")
        turret_armor = get_val(t_data, s_turret, '砲塔装甲(mm)')
        render_html_zukan("砲塔装甲 (前/側/背)", f"{get_split_str(turret_armor, 0)} / {get_split_str(turret_armor, 1)} / {get_split_str(turret_armor, 2)}", "MM")
        render_html_zukan("視認範囲", get_val(t_data, s_turret, '視認範囲(m)'), "M")
        conceal = get_val(t_data, s_turret, '発見可能範囲')
        render_html_zukan("発見可能範囲 (移動/静止)", f"{get_split_str(conceal, 0)} / {get_split_str(conceal, 1)}", "M")
        render_html_zukan("砲塔旋回速度", get_val(t_data, s_turret, '旋回速度'), "度/秒")
        render_html_zukan("通信範囲", get_val(t_data, s_radio, '通信範囲(m)'), "M")
        render_html_zukan("モジュールの損傷", get_val(t_data, s_gun, 'モジュールの損傷'), "HP")
        st.markdown("</div>", unsafe_allow_html=True)
    with d4:
        st.markdown("<div class='panel-box'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>🚀 機動性・エコノミー</div>", unsafe_allow_html=True)
        render_html_zukan("最大前進 / 後進速度", f"{get_val(t_data, s_engine, '最大前進速度')} / {get_val(t_data, s_engine, '最大後進速度')}", "KM/H")
        render_html_zukan("エンジン出力", get_val(t_data, s_engine, 'エンジン出力'), "HP")
        render_html_zukan("出力重量比", get_val(t_data, s_engine, '出力重量比'), "HP/T")
        render_html_zukan("車体旋回速度", get_val(t_data, s_susp, '旋回速度'), "度/秒")
        ground_res = get_val(t_data, s_susp, '接地抵抗')
        render_html_zukan("接地抵抗 (ハード/ミド/ソフト)", f"{get_split_str(ground_res, 0)} / {get_split_str(ground_res, 1)} / {get_split_str(ground_res, 2)}", "")
        render_html_zukan("火災発生率", get_val(t_data, s_engine, '火災発生率'), "%")
        render_html_zukan("シルバー獲得レート", get_val(t_data, s_turret, 'シルバー獲得レート'), "%")
        render_html_zukan("EXP獲得レート", get_val(t_data, s_turret, 'EXP獲得レート'), "%")
        render_html_zukan("フリー / 搭乗員EXPレート", f"{get_val(t_data, s_turret, 'フリーEXPレート')}% / {get_val(t_data, s_turret, '搭乗員EXPレート')}%", "")
        render_html_zukan("最大マッチメイキング", get_val(t_data, s_turret, '最大TIER'), "")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 2. 車輌比較
# ==========================================
elif st.session_state['app_mode'] == "⚖️ 車輌比較":
    st.title("⚖️ 究極スペック比較テーブル")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("<div class='panel-title'>🟦 車輌 A の検索と設定</div>", unsafe_allow_html=True)
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
        ca1, ca2, ca3 = st.columns(3)
        gA = dfA[dfA['モジュール種類'] == '主砲']['モジュール状態'].unique()
        tA = dfA[dfA['モジュール種類'] == '砲塔']['モジュール状態'].unique()
        eA = dfA[dfA['モジュール種類'] == 'エンジン']['モジュール状態'].unique()
        s_gunA = ca1.selectbox("主砲(A)", gA) if len(gA)>0 else None
        s_turretA = ca2.selectbox("砲塔(A)", tA) if len(tA)>0 else None
        s_engineA = ca3.selectbox("エンジン(A)", eA) if len(eA)>0 else None
        ca4, ca5, _ = st.columns(3)
        suspA = dfA[dfA['モジュール種類'] == 'サスペンション']['モジュール状態'].unique()
        rA = dfA[dfA['モジュール種類'] == '無線']['モジュール状態'].unique()
        s_suspA = ca4.selectbox("サスペンション(A)", suspA) if len(suspA)>0 else None
        s_radioA = ca5.selectbox("無線(A)", rA) if len(rA)>0 else None

    with colB:
        st.markdown("<div class='panel-title'>🟥 車輌 B の検索と設定</div>", unsafe_allow_html=True)
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
        cb1, cb2, cb3 = st.columns(3)
        gB = dfB[dfB['モジュール種類'] == '主砲']['モジュール状態'].unique()
        tB = dfB[dfB['モジュール種類'] == '砲塔']['モジュール状態'].unique()
        eB = dfB[dfB['モジュール種類'] == 'エンジン']['モジュール状態'].unique()
        s_gunB = cb1.selectbox("主砲(B)", gB) if len(gB)>0 else None
        s_turretB = cb2.selectbox("砲塔(B)", tB) if len(tB)>0 else None
        s_engineB = cb3.selectbox("エンジン(B)", eB) if len(eB)>0 else None
        cb4, cb5, _ = st.columns(3)
        suspB = dfB[dfB['モジュール種類'] == 'サスペンション']['モジュール状態'].unique()
        rB = dfB[dfB['モジュール種類'] == '無線']['モジュール状態'].unique()
        s_suspB = cb4.selectbox("サスペンション(B)", suspB) if len(suspB)>0 else None
        s_radioB = cb5.selectbox("無線(B)", rB) if len(rB)>0 else None

    html = "<table class='comp-table'>"
    html += f"<tr><th style='text-align: left; padding-left: 15px;'>💥 火力・主砲性能</th><th class='comp-val-col'>{tankA}</th><th class='comp-val-col'>{tankB}</th></tr>"
    html += comp_tr("分間ダメージ (主砲)", get_val(dfA, s_gunA, 'DPM(主砲)'), get_val(dfB, s_gunB, 'DPM(主砲)'), True, "HP/分")
    html += comp_tr("分間ダメージ (副砲)", get_val(dfA, s_gunA, 'DPM(副砲)'), get_val(dfB, s_gunB, 'DPM(副砲)'), True, "HP/分")
    html += comp_tr("100 M 貫通力 (主砲 通常弾)", get_split_str(get_val(dfA, s_gunA, '貫通力100m(主砲)'), 0), get_split_str(get_val(dfB, s_gunB, '貫通力100m(主砲)'), 0), True, "mm")
    html += comp_tr("100 M 貫通力 (主砲 課金弾)", get_split_str(get_val(dfA, s_gunA, '貫通力100m(主砲)'), 1), get_split_str(get_val(dfB, s_gunB, '貫通力100m(主砲)'), 1), True, "mm")
    html += comp_tr("100 M 貫通力 (主砲 HE)", get_split_str(get_val(dfA, s_gunA, '貫通力100m(主砲)'), 2), get_split_str(get_val(dfB, s_gunB, '貫通力100m(主砲)'), 2), True, "mm")
    html += comp_tr("100 M 貫通力 (副砲)", get_split_str(get_val(dfA, s_gunA, '貫通力100m(副砲)'), 0), get_split_str(get_val(dfB, s_gunB, '貫通力100m(副砲)'), 0), None, "mm")
    html += comp_tr("ダメージ (主砲 通常弾)", get_split_str(get_val(dfA, s_gunA, 'ダメージ(主砲)'), 0), get_split_str(get_val(dfB, s_gunB, 'ダメージ(主砲)'), 0), True, "HP")
    html += comp_tr("ダメージ (主砲 課金弾)", get_split_str(get_val(dfA, s_gunA, 'ダメージ(主砲)'), 1), get_split_str(get_val(dfB, s_gunB, 'ダメージ(主砲)'), 1), True, "HP")
    html += comp_tr("ダメージ (主砲 HE)", get_split_str(get_val(dfA, s_gunA, 'ダメージ(主砲)'), 2), get_split_str(get_val(dfB, s_gunB, 'ダメージ(主砲)'), 2), True, "HP")
    html += comp_tr("ダメージ (副砲)", get_split_str(get_val(dfA, s_gunA, 'ダメージ(副砲)'), 0), get_split_str(get_val(dfB, s_gunB, 'ダメージ(副砲)'), 0), None, "HP")
    html += comp_tr("装填時間 (主砲)", get_val(dfA, s_gunA, '装填時間(主砲)'), get_val(dfB, s_gunB, '装填時間(主砲)'), False, "秒")
    html += comp_tr("装填時間 (副砲)", get_val(dfA, s_gunA, '装填時間(副砲)'), get_val(dfB, s_gunB, '装填時間(副砲)'), False, "秒")
    html += comp_tr("照準時間", get_val(dfA, s_gunA, '照準時間(秒)'), get_val(dfB, s_gunB, '照準時間(秒)'), False, "秒")
    html += comp_tr("精度", get_val(dfA, s_gunA, '精度(m)'), get_val(dfB, s_gunB, '精度(m)'), False, "m")
    html += comp_tr("射撃速度", get_val(dfA, s_gunA, '射撃速度'), get_val(dfB, s_gunB, '射撃速度'), True, "発/分")
    html += comp_tr("俯角 (マイナス角度)", get_val(dfA, s_gunA, '俯角'), get_val(dfB, s_gunB, '俯角'), True, "度")
    html += comp_tr("仰角", get_val(dfA, s_gunA, '仰角'), get_val(dfB, s_gunB, '仰角'), True, "度")
    html += comp_tr("水平可動域", get_val(dfA, s_gunA, '水平可動域'), get_val(dfB, s_gunB, '水平可動域'), True, "度")
    html += comp_tr("砲弾タイプ", get_val(dfA, s_gunA, '砲弾タイプ'), get_val(dfB, s_gunB, '砲弾タイプ'), None, "")
    html += comp_tr("弾速 (最大/通常弾)", get_split_str(get_val(dfA, s_gunA, '弾薬の最大速度'), 0), get_split_str(get_val(dfB, s_gunB, '弾薬の最大速度'), 0), True, "m/s")
    html += comp_tr("弾速 (金弾/APCR等)", get_split_str(get_val(dfA, s_gunA, '弾薬の最大速度'), 1), get_split_str(get_val(dfB, s_gunB, '弾薬の最大速度'), 1), True, "m/s")
    html += comp_tr("弾薬の最大射程", get_split_str(get_val(dfA, s_gunA, '弾薬の最大射程'), 0), get_split_str(get_val(dfB, s_gunB, '弾薬の最大射程'), 0), True, "m")
    html += comp_tr("総弾数", get_val(dfA, s_gunA, '総弾数'), get_val(dfB, s_gunB, '総弾数'), True, "発")
    html += comp_tr("砲塔旋回中の射撃精度", get_val(dfA, s_gunA, '砲塔旋回中の射撃精度'), get_val(dfB, s_gunB, '砲塔旋回中の射撃精度'), False, "m")
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
    html += comp_tr("視認範囲", get_val(dfA, s_turretA, '視認範囲(m)'), get_val(dfB, s_turretB, '視認範囲(m)'), True, "m")
    html += comp_tr("発見可能範囲 (移動時)", get_split_str(get_val(dfA, s_turretA, '発見可能範囲'), 0), get_split_str(get_val(dfB, s_turretB, '発見可能範囲'), 0), False, "m")
    html += comp_tr("発見可能範囲 (静止時)", get_split_str(get_val(dfA, s_turretA, '発見可能範囲'), 1), get_split_str(get_val(dfB, s_turretB, '発見可能範囲'), 1), False, "m")
    html += comp_tr("砲塔旋回速度", get_val(dfA, s_turretA, '旋回速度'), get_val(dfB, s_turretB, '旋回速度'), True, "度/秒")
    html += comp_tr("通信範囲", get_val(dfA, s_radioA, '通信範囲(m)'), get_val(dfB, s_radioB, '通信範囲(m)'), True, "m")
    html += f"<tr><th style='text-align: left; padding-left: 15px;'>🚀 機動性・エコノミー</th><th></th><th></th></tr>"
    html += comp_tr("最大前進速度", get_val(dfA, s_engineA, '最大前進速度'), get_val(dfB, s_engineB, '最大前進速度'), True, "km/h")
    html += comp_tr("最大後進速度", get_val(dfA, s_engineA, '最大後進速度'), get_val(dfB, s_engineB, '最大後進速度'), True, "km/h")
    html += comp_tr("エンジン出力", get_val(dfA, s_engineA, 'エンジン出力'), get_val(dfB, s_engineB, 'エンジン出力'), True, "HP")
    html += comp_tr("出力重量比", get_val(dfA, s_engineA, '出力重量比'), get_val(dfB, s_engineB, '出力重量比'), True, "hp/t")
    html += comp_tr("火災発生率", get_val(dfA, s_engineA, '火災発生率'), get_val(dfB, s_engineB, '火災発生率'), False, "%")
    html += comp_tr("車体旋回速度", get_val(dfA, s_suspA, '旋回速度'), get_val(dfB, s_suspB, '旋回速度'), True, "度/秒")
    html += comp_tr("接地抵抗 (ハード)", get_split_str(get_val(dfA, s_suspA, '接地抵抗'), 0), get_split_str(get_val(dfB, s_suspB, '接地抵抗'), 0), False, "")
    html += comp_tr("接地抵抗 (ミディアム)", get_split_str(get_val(dfA, s_suspA, '接地抵抗'), 1), get_split_str(get_val(dfB, s_suspB, '接地抵抗'), 1), False, "")
    html += comp_tr("接地抵抗 (ソフト)", get_split_str(get_val(dfA, s_suspA, '接地抵抗'), 2), get_split_str(get_val(dfB, s_suspB, '接地抵抗'), 2), False, "")
    html += comp_tr("シルバー獲得レート", get_val(dfA, s_turretA, 'シルバー獲得レート'), get_val(dfB, s_turretB, 'シルバー獲得レート'), True, "%")
    html += comp_tr("EXP獲得レート", get_val(dfA, s_turretA, 'EXP獲得レート'), get_val(dfB, s_turretB, 'EXP獲得レート'), True, "%")
    html += comp_tr("最大マッチメイキング", get_val(dfA, s_turretA, '最大TIER'), get_val(dfB, s_turretB, '最大TIER'), None, "")
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 3. ランキング
# ==========================================
elif st.session_state['app_mode'] == "🏆 ランキング":
    st.title("🏆 戦術アナリティクス・ランキング")
    st.markdown("<div class='panel-title'>🔍 抽出条件の指定</div>", unsafe_allow_html=True)
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
            st.dataframe(display_df.head(100), use_container_width=True)

# ==========================================
# 4. 装甲計算シミュレーター (手動)
# ==========================================
elif st.session_state['app_mode'] == "🛡️ 装甲計算シミュレーター":
    st.title("🛡️ 実質装甲厚 計算シミュレーター (昼飯・豚飯検証)")
    st.write("WOT特有の「標準化（Normalization）」を加味し、入力した角度に対する実質装甲厚を自動計算します。")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='panel-title'>📐 条件設定</div>", unsafe_allow_html=True)
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

    with col2:
        st.markdown("<div class='panel-title'>🛡️ 計算結果</div>", unsafe_allow_html=True)
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

# ==========================================
# 5. 📸 スーパー簡易画像装甲測定
# ==========================================
elif st.session_state['app_mode'] == "📸 スーパー簡易画像装甲測定":
    st.title("📸 スーパー簡易画像装甲測定 (3点クリック弾道計算)")
    
    st.info("💡 **使い方 (3ステップで完了！)**\n\n"
            "1. **画像を用意:** 調べたい戦車を**真横**から見た画像をアップロードします。（※現在はサンプル画像が表示されています）\n"
            "2. **装甲を指定 (2回クリック):** 画像上で、調べたい装甲の**「上端」**と**「下端」**をクリックします。（緑色の線が引かれます）\n"
            "3. **弾道を指定 (1回クリック):** 最後に、**「弾が飛んでくる位置（発射元）」**をクリックすると、自動で計算結果が表示されます！")

    if not HAS_IMG_COORD:
        st.error("⚠️ この機能を使用するには追加ライブラリが必要です。コマンドプロンプト等で以下のコマンドを実行し、アプリを再起動してください。")
        st.code("pip install streamlit-image-coordinates pillow")
        st.stop()

    col_settings, col_image = st.columns([1.5, 2.5])

    with col_settings:
        st.markdown("<div class='panel-title'>⚙️ 条件設定</div>", unsafe_allow_html=True)
        nominal_armor = st.number_input("基本装甲厚 (mm):", min_value=1.0, max_value=1500.0, value=100.0, step=1.0)
        
        st.markdown("---")
        ammo_type = st.radio("被弾する弾種 (標準化の自動適用):", ["AP弾 (標準化 5度)", "APCR弾 (標準化 2度)", "HEAT / HE弾 (標準化 0度)"])
        
        if "AP弾" in ammo_type: default_norm = 5.0
        elif "APCR" in ammo_type: default_norm = 2.0
        else: default_norm = 0.0
        
        normalization = st.number_input("標準化角度 (度):", min_value=0.0, max_value=20.0, value=default_norm, step=1.0)
        
        st.markdown("---")
        if st.button("🔄 クリック位置をリセット", use_container_width=True):
            st.session_state['img_clicks'] = []
            st.session_state['last_click'] = None
            st.rerun()
            
        # --- 計算結果エリア ---
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

            st.markdown("---")
            st.markdown("<div class='panel-title' style='color: #ff7b72 !important;'>🛡️ 計算結果</div>", unsafe_allow_html=True)
            
            calc_angle = max(0.0, angle_deg - normalization)
            
            if angle_deg >= 70.0 and ("HEAT" not in ammo_type and "HE" not in ammo_type):
                st.markdown("<div class='armor-result-bounce'>跳弾 (Ricochet)</div>", unsafe_allow_html=True)
                st.info("※APおよびAPCR弾は、着弾角度が70度以上の場合、強制跳弾（Auto-Bounce）となります。")
            elif angle_deg >= 85.0 and "HEAT" in ammo_type:
                st.markdown("<div class='armor-result-bounce'>跳弾 (Ricochet)</div>", unsafe_allow_html=True)
                st.info("※HEAT弾は着弾角度が85度以上で強制跳弾となります。")
            else:
                if calc_angle >= 89.9: eff_armor = float('inf')
                else: eff_armor = nominal_armor / math.cos(math.radians(calc_angle))
                
                st.markdown(f"<div class='armor-result'>{eff_armor:.1f} MM</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='armor-subtext'>基本装甲 <b>{nominal_armor}mm</b> / 実効角度 <b>{calc_angle:.1f}°</b></div>", unsafe_allow_html=True)
                st.success(f"🎯 測定された着弾角度: 約 **{angle_deg:.1f}** 度")

    with col_image:
        st.markdown("<div class='panel-title'>📸 画像測定ボード</div>", unsafe_allow_html=True)
        
        # ⚠️余分な空欄を防ぐために、アップローダーの配置をシンプル化
        uploaded_file = st.file_uploader("真横から撮影したスクリーンショットをアップロード (任意)", type=["png", "jpg", "jpeg"])
        
        target_image = None
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if uploaded_file is not None:
            target_image = Image.open(uploaded_file).convert("RGB")
        else:
            sample_path = os.path.join(base_dir, SAMPLE_IMG_FILE)
            if os.path.exists(sample_path):
                target_image = Image.open(sample_path).convert("RGB")
            else:
                st.warning(f"⚠️ サンプル画像が見つかりません。({sample_path}) 画像をアップロードしてください。")

        if 'img_clicks' not in st.session_state:
            st.session_state['img_clicks'] = []
            
        if target_image is not None:
            target_image.thumbnail((1000, 1000))
            
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
                st.warning("👆 画像上で、測定したい装甲の「上端」をクリックしてください。")
            elif len(clicks) == 1:
                st.warning("👆 次に、同じ装甲の「下端」をクリックしてください。")
            elif len(clicks) == 2:
                st.warning("🎯 最後に、「弾が飛んでくる位置（発射元）」をクリックしてください。")
            else:
                st.success("✅ 測定完了！結果は左側に表示されています。やり直す場合は再度画像をクリックしてください。")
            
            value = streamlit_image_coordinates(draw_image, key="armor_img")
            
            if value is not None:
                pt = (value["x"], value["y"])
                if pt != st.session_state.get('last_click'):
                    st.session_state['last_click'] = pt
                    if len(st.session_state['img_clicks']) >= 3:
                        st.session_state['img_clicks'] = [] 
                    st.session_state['img_clicks'].append(pt)
                    st.rerun()
