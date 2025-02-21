import streamlit as st
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

    # 追加評価ロジック
    # TAV/TAMV の評価
    if TAV_TAMV_ratio > 0.95:
        stenosis_comment = "TAV/TAMV ≈ 1 に近い → 層流で安定 → 狭窄リスク低"
    elif TAV_TAMV_ratio < 0.6:
        stenosis_comment = "TAV/TAMV < 0.6 → 乱流増加 → 狭窄の可能性"
    else:
        stenosis_comment = "TAV/TAMV は正常範囲"

    # RI/PI の評価
    if RI / PI <= 0.5:
        blood_flow_comment = "RI/PI が 0.5 以下 → PSV に対して TAMV が極端に低い → 血流変動が大きく、狭窄の可能性"
    else:
        blood_flow_comment = "RI/PI は正常範囲"

    # 評価結果の表示
    st.subheader("評価結果")
    st.write(f"TAV/TAMV: {TAV_TAMV_ratio:.2f}")
    st.write(stenosis_comment)

    st.write(f"RI/PI: {RI/PI:.2f}")
    st.write(blood_flow_comment)

    # **スコアと追加評価コメント**
    score, comments = evaluate_shunt_function(TAV, RI, PI, EDV)

    # スコアの表示
    st.write("### スコア")
    st.write(f"評価スコア: {score} / 4")

    # コメントの表示
    st.write("### 評価コメント")
    for comment in comments:
        st.write(f"- {comment}")

# シャント機能不全の診断基準を評価する関数
def evaluate_shunt_function(TAV, RI, PI, EDV):
    # スコアの初期化
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
