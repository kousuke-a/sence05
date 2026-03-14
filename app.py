import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import base64

# --- 設定 ---
st.set_page_config(page_title="企業電話番号 検索ツール", layout="wide")

st.title("📞 企業電話番号 自動検索ツール")
st.write("CSVをアップロードすると、Google検索の結果から電話番号を自動で推測してリスト化します。")

# --- 関数: Google検索から電話番号を抽出 ---
def search_phone_number(company_name, address):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    query = f"{company_name} {address} 電話番号"
    url = f"https://www.google.com/search?q={query}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # ページ全体のテキストから電話番号のパターンを探す
        text = soup.get_text()
        # 日本の電話番号パターン（携帯・固定・フリーダイヤル対応）
        phone_pattern = r'(\d{2,4}-\d{2,4}-\d{4})'
        match = re.search(phone_pattern, text)
        
        return match.group(1) if match else "見つかりませんでした"
    except Exception as e:
        return f"エラー: {e}"

# --- メインUI ---
uploaded_file = st.file_uploader("会社名と住所が含まれるCSVファイルをアップロードしてください", type=['csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
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
            # 進捗更新
            status_text.text(f"検索中 ({i+1}/{total}): {row[col_name]}")
            
            # 検索実行
            phone = search_phone_number(row[col_name], row[col_addr])
            results.append(phone)
            
            # Googleにブロックされないよう待機（重要）
            time.sleep(2) 
            progress_bar.progress((i + 1) / total)
            
        df['抽出電話番号'] = results
        
        st.success("全ての検索が完了しました！")
        st.dataframe(df)
        
        # ダウンロードボタン
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="結果をCSVでダウンロード",
            data=csv,
            file_name="company_list_with_phone.csv",
            mime="text/csv",
        )
