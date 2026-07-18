import streamlit as st
import pandas as pd
import re
import math
import os # 追加

# ページ設定
st.set_page_config(page_title="WOT 総合データコンソール", layout="wide")

# === UIデザイン・テーブルのCSS設定 ===
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
    
    /* 計算機用のデザイン */
    .armor-result { font-size: 3em; font-weight: bold; color: #ff4b4b; text-align: center; margin-top: 15px; margin-bottom: 5px; }
    .armor-result-bounce { font-size: 2.5em; font-weight: bold; color: #a0a0a0; text-align: center; margin-top: 15px; margin-bottom: 5px; }
    /* RNG表示用 */
    .rng-text { font-size: 0.85em; color: #888; font-weight: normal; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_parse_data():
    try:
        # ZIP対応修正
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

    # === 真の全ステータス徹底抽出 ===
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

    df['Rank_DPM'] = df['DPM(主砲)'].apply(lambda x: get_split_val(x, 0))
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

# === RNG対応ヘルパー関数 ===
def get_float(val):
    nums = re.findall(r'[\d\.]+', str(val))
    return float(nums[0]) if nums else None

def get_rng_str(val_str):
    # 分割されている場合は各パーツに適用
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

# ... (中略：図鑑・ランキング・計算機は既存のものと完全に一致)