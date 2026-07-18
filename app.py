import streamlit as st
import pandas as pd
import re
import math
import os

# ページ設定
st.set_page_config(page_title="WOT 総合データコンソール", layout="wide")

# === CSS設定 ===
st.markdown("""
    <style>
    .block-container { max-width: 1550px; padding-top: 1.5rem; }
    .comp-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.95em; background-color: #1e1e1e; border-radius: 8px; overflow: hidden; }
    .comp-table th { background-color: #2b2b2b; padding: 12px; border-bottom: 2px solid #444; text-align: center; font-size: 1.1em; color: #ffffff; }
    .comp-table td { padding: 8px 12px; border-bottom: 1px solid #333; text-align: center; }
    .comp-label { text-align: left !important; color: #a0a0a0; width: 26%; font-weight: 500; background-color: #252525; }
    .comp-val-col { width: 37%; }
    .win-stat { color: #4dabf7; font-weight: bold; background-color: rgba(77, 171, 247, 0.15); }
    .lose-stat { color: #e0e0e0; }
    .stat-label { font-size: 0.75em; color: #a0a0a0; margin-bottom: -4px; margin-top: 6px; text-align: center; }
    .stat-value { font-size: 1.05em; font-weight: bold; margin-bottom: 4px; text-align: center; }
    .search-box { padding: 10px; background-color: #1e1e1e; border-radius: 8px; margin-bottom: 15px; }
    .rng-text { font-size: 0.85em; color: #888; font-weight: normal; margin-left: 5px; }
    .armor-result { font-size: 3em; font-weight: bold; color: #ff4b4b; text-align: center; margin-top: 15px; margin-bottom: 5px; }
    .armor-result-bounce { font-size: 2.5em; font-weight: bold; color: #a0a0a0; text-align: center; margin-top: 15px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_parse_data():
    try:
        # ZIPとCSVの両方に対応
        if os.path.exists("wot_wwii_all_tanks_modules.csv.zip"):
            df = pd.read_csv("wot_wwii_all_tanks_modules.csv.zip", encoding="utf-8-sig", compression="zip")
        else:
            df = pd.read_csv("wot_wwii_all_tanks_modules.csv", encoding="utf-8-sig")
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

    # 全データ抽出
    df['DPM(主砲)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'分間ダメージ / ([\d/ \.]+)HP', x)[0] if len(get_match_all(r'分間ダメージ / ([\d/ \.]+)HP', x)) > 0 else "-")
    df['DPM(副砲)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'分間ダメージ / ([\d/ \.]+)HP', x)[1] if len(get_match_all(r'分間ダメージ / ([\d/ \.]+)HP', x)) > 1 else "-")
    df['貫通力100m(主砲)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'100 Mでの貫通力 / ([\d/ \.]+)MM', x)[0] if len(get_match_all(r'100 Mでの貫通力 / ([\d/ \.]+)MM', x)) > 0 else "-")
    df['ダメージ(主砲)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'ダメージ / ([\d/ \.]+)HP', x)[0] if len(get_match_all(r'ダメージ / ([\d/ \.]+)HP', x)) > 0 else "-")
    df['装填時間(主砲)'] = df['詳細・モジュール生データ'].apply(lambda x: get_match_all(r'装填時間 / ([\d\.]+)秒', x)[0] if len(get_match_all(r'装填時間 / ([\d\.]+)秒', x)) > 0 else "-")
    
    # 項目補完
    cols = ['射撃速度', '照準時間(秒)', '精度(m)', 'モジュールの損傷', '攻撃半径', '弾薬の最大速度', '弾薬の最大射程', '砲弾タイプ', '総弾数', '砲塔旋回中の射撃精度', '俯角', '仰角', '水平可動域', 'HP', '砲塔装甲(mm)', '車体装甲(mm)', '視認範囲(m)', '発見可能範囲', '旋回速度', '通信範囲(m)', 'エンジン出力', '出力重量比', '最大前進速度', '最大後進速度', '火災発生率', '接地抵抗', '最大TIER', 'シルバー獲得レート', 'EXP獲得レート', 'フリーEXPレート', '搭乗員EXPレート']
    for c in cols:
        df[c] = df['詳細・モジュール生データ'].apply(lambda x: get_match(rf'{c} / ([\d/ \.\-]+)', x))
    return df

df = load_and_parse_data()

# RNG対応ヘルパー
def get_float(val):
    nums = re.findall(r'[\d\.]+', str(val))
    return float(nums[0]) if nums else None

def get_rng_str(val_str):
    parts = str(val_str).split('/')
    res = []
    for p in parts:
        num = get_float(p)
        if num: res.append(f"{p}<span class='rng-text'>({int(num*0.8)}-{int(num*1.2)})</span>")
        else: res.append(p)
    return " / ".join(res)

def get_val(tank_data, mod_state, col_name):
    if mod_state and not tank_data[tank_data['モジュール状態'] == mod_state].empty:
        return str(tank_data[tank_data['モジュール状態'] == mod_state][col_name].iloc[0])
    return "-"

def get_split_str(val_str, idx):
    if pd.isna(val_str) or val_str == "-": return "-"
    parts = str(val_str).split('/')
    if len(parts) > idx: return parts[idx].strip()
    return "-"

def comp_tr(label, valA, valB, higher_better=True, suffix="", is_rng=False):
    numA = get_float(valA)
    numB = get_float(valB)
    clsA, clsB = "lose-stat", "lose-stat"
    if valA != "-" and valB != "-" and higher_better is not None and numA and numB and numA != numB:
        if (numA > numB and higher_better) or (numA < numB and not higher_better): clsA = "win-stat"
        else: clsB = "win-stat"
    dispA = get_rng_str(valA) if is_rng else f"{valA} {suffix}"
    dispB = get_rng_str(valB) if is_rng else f"{valB} {suffix}"
    return f"<tr><td class='comp-label'>{label}</td><td class='{clsA}'>{dispA}</td><td class='{clsB}'>{dispB}</td></tr>"

# サイドバー
app_mode = st.sidebar.radio("機能メニュー", ["📖 車輌図鑑", "⚖️ 車輌比較", "🏆 ランキング", "🛡️ 装甲計算シミュレーター"])

# メイン処理 (各モード)
if app_mode == "📖 車輌図鑑":
    st.title("📖 車輌図鑑")
    t_name = st.selectbox("車輌選択", sorted(df['正確な車輌名'].unique()))
    t_data = df[df['正確な車輌名'] == t_name]
    st.markdown(f"### {t_name}")
    st.dataframe(t_data, use_container_width=True)

elif app_mode == "⚖️ 車輌比較":
    st.title("⚖️ 車輌比較")
    c1, c2 = st.columns(2)
    tankA = c1.selectbox("車輌A", sorted(df['正確な車輌名'].unique()))
    tankB = c2.selectbox("車輌B", sorted(df['正確な車輌名'].unique()))
    dA = df[df['正確な車輌名'] == tankA].iloc[0]
    dB = df[df['正確な車輌名'] == tankB].iloc[0]
    
    html = f"<table class='comp-table'><tr><th>項目</th><th>{tankA}</th><th>{tankB}</th></tr>"
    html += comp_tr("DPM(主砲)", dA['DPM(主砲)'], dB['DPM(主砲)'], True, "HP/分", True)
    html += comp_tr("貫通力(100m)", dA['貫通力100m(主砲)'], dB['貫通力100m(主砲)'], True, "mm", True)
    html += comp_tr("ダメージ", dA['ダメージ(主砲)'], dB['ダメージ(主砲)'], True, "HP", True)
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

elif app_mode == "🏆 ランキング":
    st.title("🏆 ランキング")
    target = st.radio("項目", ["DPM(主砲)", "貫通力100m(主砲)", "ダメージ(主砲)"], horizontal=True)
    ranked = df.sort_values(by=target, ascending=False)
    st.dataframe(ranked[['正確な車輌名', target]], use_container_width=True)

elif app_mode == "🛡️ 装甲計算シミュレーター":
    st.title("🛡️ 装甲計算シミュレーター")
    thick = st.number_input("基本装甲厚(mm)", value=250)
    angle = st.slider("着弾角度(度)", 0, 89, 20)
    res = thick / math.cos(math.radians(angle))
    st.markdown(f"<div class='armor-result'>{res:.1f} MM</div>", unsafe_allow_html=True)
