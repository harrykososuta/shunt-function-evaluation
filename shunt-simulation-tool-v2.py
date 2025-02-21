import streamlit as st

# **他の Streamlit コマンドの前に set_page_config() を記述**
if "is_configured" not in st.session_state:
    st.set_page_config(page_title="シャント機能評価", layout="wide")
    st.session_state.is_configured = True

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# 日本語フォント設定
matplotlib.rcParams['font.family'] = 'MS Gothic'

# 初期設定（基準値）
baseline_FV = 380  # ml/min
baseline_RI = 0.68
baseline_diameter = 5.0  # 血管径 (mm)

# PSV・EDV・TAV・TAMV の計算に使用する係数（血管径の影響を考慮）
coefficients = {
    "PSV": [37.664, 0.0619, 52.569, -1.2],
    "EDV": [69.506, 0.0305, -74.499, -0.8],
    "TAV": [43.664, 0.0298, -35.760, -0.6],
    "TAMV": [50.123, 0.0452, -30.789, -1.0]
}

# 指定した FV, RI, 血管径 に応じた各パラメータの計算関数
def calculate_parameter(FV, RI, diameter, coeffs):
    return coeffs[0] + coeffs[1] * float(FV) + coeffs[2] * float(RI) + coeffs[3] * float(diameter)

# シャント機能不全の診断基準
def evaluate_shunt_function(TAV, RI, PI, EDV):
    score = 0
    comments = []

    # TAV 評価
    if TAV <= 34.5:
        score += 1
        comments.append("TAVが34.5 cm/s以下 → 低血流が疑われる")

    # RI 評価
    if RI >= 0.68:
        score += 1
        comments.append("RIが0.68以上 → 高抵抗が疑われる")

    # PI 評価
    if PI >= 1.3:
        score += 1
        comments.append("PIが1.3以上 → 脈波指数が高い")

    # EDV 評価
    if EDV <= 40.4:
        score += 1
        comments.append("EDVが40.4 cm/s以下 → 拡張期血流速度が低い")

    return score, comments

# **サイドバーでページ選択**
st.sidebar.title("ページ選択")
page = st.sidebar.radio("表示するページ", ["シミュレーションツール", "評価フォーム"])

# **シミュレーションツールのページ**
if page == "シミュレーションツール":
    st.title("シャント機能評価シミュレーションツール")

    # ユーザー入力
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        FV = st.slider("血流量 FV (ml/min)", min_value=100, max_value=2000, value=int(baseline_FV), step=10, key="fv_slider")
        RI = st.slider("抵抗指数 RI", min_value=0.4, max_value=1.0, value=float(baseline_RI), step=0.01, key="ri_slider")
        diameter = st.slider("血管径 (mm)", min_value=3.0, max_value=7.0, value=baseline_diameter, step=0.1)

    # VAIVT ボタン（右側に配置）
    with col3:
        st.write("")
        st.write("")
        toggle_vaivt = st.button("VAIVTを実施")

    # VAIVTを適用する場合の処理（FV増加、RI減少）
    def apply_vaivt(FV, RI):
        return FV * 1.15, RI * 0.8

    if toggle_vaivt:
        FV, RI = apply_vaivt(FV, RI)
        st.write("**VAIVT後の数値:**")
        st.write(f"FV: {FV:.2f} ml/min")
        st.write(f"RI: {RI:.2f}")

    # PSV・EDV・TAV・TAMV の計算（血管径を追加）
    PSV = calculate_parameter(FV, RI, diameter, coefficients["PSV"])
    EDV = calculate_parameter(FV, RI, diameter, coefficients["EDV"])
    TAV = calculate_parameter(FV, RI, diameter, coefficients["TAV"])
    TAMV = calculate_parameter(FV, RI, diameter, coefficients["TAMV"])

    # **TAV/TAMV の自動計算と表示**
    TAV_TAMV_ratio = TAV / TAMV if TAMV != 0 else 0

    # PIの計算: (PSV - EDV) / TAMV
    PI = (PSV - EDV) / TAMV if TAMV != 0 else 0

    # 主要パラメータの表示
    st.subheader("主要パラメータ")
    st.write(f"PSV: {PSV:.2f} cm/s")
    st.write(f"EDV: {EDV:.2f} cm/s")
    st.write(f"PI: {PI:.2f}")
    st.write(f"TAV: {TAV:.2f} cm/s")
    st.write(f"TAMV: {TAMV:.2f} cm/s")
    st.write(f"TAV/TAMV: {TAV_TAMV_ratio:.2f}")
    st.write(f"血管径: {diameter:.1f} mm")  # **血管径の表示**

    # **波形分類**
    if TAV_TAMV_ratio > 0.95:
        wave_comment = "Ⅰ・Ⅱ型はシャント機能は問題なし"
    elif TAV_TAMV_ratio <= 0.95 and TAV_TAMV_ratio > 0.6:
        wave_comment = "Ⅲ型は50％程度の狭窄があるため細かく精査"
    elif TAV_TAMV_ratio <= 0.6 and TAV_TAMV_ratio > 0.3:
        wave_comment = "Ⅳ型はVAIVTを提案を念頭に精査"
    else:
        wave_comment = "Ⅴ型はシャント閉塞している可能性が高い"

    st.write(f"### 波形分類")
    st.write(wave_comment)

    # **TAVR算出（仮定）**
    TAVR = 0.5 * FV / (RI * diameter)
    st.write(f"### TAVRの算出")
    st.write(f"TAVR: {TAVR:.2f} (仮定値)")

    # **RI/PI算出**
    RI_PI = RI / PI if PI != 0 else 0
    st.write(f"### RI/PI の算出")
    st.write(f"RI/PI: {RI_PI:.2f}")

# **評価フォームのページ**
elif page == "評価フォーム":
    st.title("シャント機能評価フォーム")

    # 入力フォーム
    fv = st.number_input("FV（血流量, ml/min）", min_value=0.0, value=400.0)
    ri = st.number_input("RI（抵抗指数）", min_value=0.0, value=0.6)
    pi = st.number_input("PI（脈波指数）", min_value=0.0, value=1.2)
    tav = st.number_input("TAV（時間平均流速, cm/s）", min_value=0.0, value=60.0)
    tamv = st.number_input("TAMV（時間平均最大速度, cm/s）", min_value=0.0, value=100.0)
    psv = st.number_input("PSV（収縮期最大速度, cm/s）", min_value=0.0, value=120.0)
    edv = st.number_input("EDV（拡張期末速度, cm/s）", min_value=0.0, value=50.0)

    # シャント機能評価の実行
    score, comments = evaluate_shunt_function(tav, ri, pi, edv)

    # スコアとコメントの表示
    st.write("### 評価結果")
    st.write(f"評価スコア: {score} / 4")

    if score == 0:
        st.success("シャント機能は正常です。経過観察が推奨されます。")
    elif score == 1 or score == 2:
        st.warning("シャント機能は要注意です。追加評価が必要です。")
    else:
        st.error("シャント不全のリスクが高いです。専門的な評価が必要です。")

    # コメントの表示
    if comments:
        st.write("### 評価コメント")
        for comment in comments:
            st.write(f"- {comment}")
