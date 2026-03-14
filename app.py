import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import io

# ページ設定
st.set_page_config(page_title="企業電話番号 検索くん", page_icon="📞")

st.title("📞 企業電話番号 自動検出ツール")
st.markdown("""
アップロードされたExcelの「会社名」と「住所」から、Google検索を使って電話番号を自動で特定します。
※大量のデータを一度に処理するとGoogleからブロックされる可能性があるため、1件ごとに数秒の待機時間を設けています。
""")

def extract_phone_number(text):
    """テキストから日本の電話番号（固定・携帯・フリーダイヤル）を抽出"""
    patterns = [
        r'\d{2,4}-\d{2,4}-\d{4}',    # 03-1234-5678 等
        r'\(0\d\)\d{4}-\d{4}',        # (03)1234-5678 等
        r'0\d{9,10}'                  # 09012345678 (ハイフンなし) 等
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None

def fetch_phone_number(company, address):
    """Google検索結果から電話番号を特定する"""
    # 検索精度を高めるため、会社名と住所の一部（市区町村まで）を組み合わせる
    clean_address = address[:10] if isinstance(address, str) else ""
    query = f"{company} {clean_address} 電話番号"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    
    try:
        url = f"https://www.google.com/search?q={query}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return "アクセス制限中"

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 検索結果のスニペット（説明文）部分を全スキャン
        search_results = soup.find_all(['span', 'div'])
        for res in search_results:
            found = extract_phone_number(res.get_text())
            if found:
                return found
        
        return "見つかりませんでした"
    except Exception:
        return "通信エラー"

# ファイルアップローダー
uploaded_file = st.file_uploader("Excelファイルをアップロード (.xlsx)", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("ファイルを読み込みました。")
    
    # 列選択
    cols = df.columns.tolist()
    col1, col2 = st.columns(2)
    with col1:
        target_col = st.selectbox("会社名の列", cols)
    with col2:
        addr_col = st.selectbox("住所の列", cols)

    if st.button("🔍 検出を開始する"):
        results = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        total = len(df)
        for i, (index, row) in enumerate(df.iterrows()):
            company = row[target_col]
            address = row[addr_col]
            
            status.info(f"検索中 ({i+1}/{total}): {company}")
            
            # 検索実行
            phone = fetch_phone_number(company, address)
            results.append(phone)
            
            # Googleブロック対策：1件ごとに3秒待機
            time.sleep(3)
            progress_bar.progress((i + 1) / total)
            
        df['検出電話番号'] = results
        st.balloons()
        st.write("### 検索結果")
        st.dataframe(df)

        # Excelダウンロードボタン
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="✅ 結果をExcelでダウンロード",
            data=output.getvalue(),
            file_name="detected_phone_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
