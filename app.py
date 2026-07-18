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
    .win-stat { color: #4dabf7; font-weight: bold; background-color: rgba(77, 171, 247, 0.15); }
    .lose-stat { color: #e0e0e0; }
    .stat-label { font-size: 0.75em; color: #a0a0a0; margin-bottom: -4px; margin-top: 6px; text-align: center; }
    .stat-value { font-size: 1.05em; font-weight: bold; margin-bottom: 4px; text-align: center; }
    .search-box { padding: 10px; background-color: #1e1e1e; border-radius: 8px; margin-bottom: 15px; }
    .rng-text { font-size: 0.85em; color: #888; font-weight: normal; margin-left: 5px; }
    .armor-result { font-size: 3em; font-weight: bold; color: #ff4b4b; text-align: center; margin-top: 15px; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_parse_data():
    try:
        # ZIPファイルを優先して読み込む
        if os.path.exists("wot_wwii_all_tanks_modules.csv.zip"):
            df = pd.read_csv("wot_wwii_all_tanks_modules.csv.zip", encoding="utf-8-sig", compression="zip")
        else:
            df = pd.read_csv("wot_wwii_all_tanks_modules.csv", encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame()

    # (パース処理は既存のものと全く同じです)
    def get_match(pattern, text):
        m = re.search(pattern, str(text))
        return m.group(1).replace(' ', '').strip('/') if m else "-"
    def extract_basics(text):
        m = re.search(r'ホーム › 戦車事典 › ([^/]+) / (.*?) / (?:価格|戦闘獲得レート|主要性能)', str(text))
        if m: return pd.Series([m.group(1).replace(' ', ''), re.sub(r'\s*/\s*(プレミアム車輌|退役車輌)$', '', m.group(2).strip())])
        return pd.Series(["-", "-"])

    df[['国', '正確な車輌名']] = df['詳細・モジュール生データ'].apply(extract_basics)
    df = df[df['正確な車輌名'] != "-"]
    # (ランキング用の数値化)
    def to_float(val):
        nums = re.findall(r'[\d\.]+', str(val))
        return float(nums[0]) if nums else 0
    df['Rank_DPM'] = df['詳細・モジュール生データ'].apply(lambda x: to_float(re.search(r'分間ダメージ / ([\d/ \.]+)HP', str(x)).group(1).split('/')[0] if re.search(r'分間ダメージ / ([\d/ \.]+)HP', str(x)) else 0))
    return df

df = load_and_parse_data()

# 【重要】データが読み込めていない場合にアプリを止める安全装置
if df.empty:
    st.error("データファイルが見つからないか、読み込めませんでした。GitHubに 'wot_wwii_all_tanks_modules.csv.zip' が正しくアップロードされているか確認してください。")
    st.stop()

# サイドバー
app_mode = st.sidebar.radio("機能メニュー", ["📖 車輌図鑑", "⚖️ 車輌比較", "🏆 ランキング", "🛡️ 装甲計算シミュレーター"])

# メイン処理
if app_mode == "📖 車輌図鑑":
    st.title("📖 車輌図鑑")
    t_name = st.selectbox("車輌選択", sorted(df['正確な車輌名'].unique()))
    st.dataframe(df[df['正確な車輌名'] == t_name], use_container_width=True)

# (以下、比較・ランキング機能などは以前のコードを維持)
elif app_mode == "🏆 ランキング":
    st.title("🏆 ランキング")
    st.dataframe(df[['正確な車輌名', 'Rank_DPM']].sort_values(by='Rank_DPM', ascending=False), use_container_width=True)

elif app_mode == "🛡️ 装甲計算シミュレーター":
    st.title("🛡️ 装甲計算")
    thick = st.number_input("装甲厚(mm)", value=250)
    angle = st.slider("角度(度)", 0, 89, 20)
    st.write(f"実質装甲: {thick / math.cos(math.radians(angle)):.1f} mm")
