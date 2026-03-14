import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import io

# --- 設定 ---
st.set_page_config(page_title="企業電話番号 検索ツール (Excel対応)", layout="wide")

st.title("📞 企業電話番号 自動検索ツール")
st.write("Excelファイルをアップロードすると、Google検索から電話番号を自動で抽出します。")

# --- 関数: Google検索から電話番号を抽出 ---
def search_phone_number(company_name, address):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    # 検索精度を上げるため、会社名と住所を組み合わせる
    query = f"{company_name} {address} 電話番号"
    url = f"https://www.google.com/search?q={query}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        
        # 日本の電話番号パターン
        phone_pattern = r'(\d{2,4}-\d{2,4}-\d{4})'
        match = re.search(phone_pattern, text)
        
        return match.group(1) if match else "見つかりませんでした"
    except Exception as e:
        return f"エラー"

# --- メインUI ---
uploaded_file = st.file_uploader("Excelファイルをアップロードしてください", type=['xlsx'])

if uploaded_file:
    # Excelの読み込み
    df = pd.read_excel(uploaded_file)
    st.write("### アップロードされたデータ (先頭5件)")
    st.dataframe(df.head())
    
    col_name = st.selectbox("「会社名」の列を選択してください", df.columns)
    col_addr = st.selectbox("「住所」の列を選択してください", df.columns)
    
    if st.button("検索を開始する"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        total = len(df)
        
        for i, row in df.iterrows():
            status_text.text(f"検索中 ({i+1}/{total}): {row[col_name]}")
            
            # 検索実行
            phone = search_phone_number(row[col_name], row[col_addr])
            results.append(phone)
            
            # ブロック対策の待機
            time.sleep(2) 
            progress_bar.progress((i + 1) / total)
            
        df['抽出電話番号'] = results
        
        st.success("全ての検索が完了しました！")
        st.dataframe(df)
        
        # Excelとしてダウンロードするための処理
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        st.download_button(
            label="結果をExcelでダウンロード",
            data=output.getvalue(),
            file_name="search_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
