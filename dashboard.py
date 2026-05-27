import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# ================= 页面设置 =================
st.set_page_config(page_title="AutoStat 稳定版", layout="wide")

st.title("🚗 俄罗斯汽车行业情报系统（稳定版）")


# ================= 获取新闻列表 =================
def get_news():
    url = "https://eng.autostat.ru/news/"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", href=True)

    news = []
    seen = set()

    for a in links:
        title = a.get_text(strip=True)
        href = a["href"]

        if len(title) < 20:
            continue
        if "news" not in href:
            continue

        full = "https://eng.autostat.ru" + href

        if full in seen:
            continue
        seen.add(full)

        news.append({
            "title": title,
            "link": full
        })

        if len(news) >= 20:
            break

    return news


# ================= 获取详情 =================
def get_detail(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # 时间提取
        date = ""

        meta = soup.find("meta", {"property": "article:published_time"})
        if meta:
            date = meta.get("content", "")[:10]

        if not date:
            t = soup.find("time")
            if t:
                date = t.get_text(strip=True)

        if not date:
            m = re.search(r"\d{4}-\d{2}-\d{2}", soup.text)
            if m:
                date = m.group()

        # 正文
        ps = soup.find_all("p")
        text = " ".join([p.get_text() for p in ps])

        return date if date else "未知", text

    except:
        return "未知", ""


# ================= 中文摘要（无翻译版本） =================
def make_summary(text):

    if not text:
        return "暂无内容"

    sentences = re.split(r"[.。]", text)

    clean = [s.strip() for s in sentences if len(s.strip()) > 30]

    return "。".join(clean[:3])


# ================= UI控制 =================
if st.button("🔄 更新数据"):
    st.rerun()


# ================= 主流程 =================
news = get_news()

rows = []

for n in news:

    date, content = get_detail(n["link"])

    rows.append({
        "日期": date,
        "英文标题": n["title"],
        "摘要": make_summary(content),
        "原文链接": n["link"]
    })


df = pd.DataFrame(rows)


# ================= 展示 =================
st.dataframe(df, use_container_width=True)


# ================= 可展开详情 =================
for i, row in df.iterrows():
    with st.expander(row["英文标题"]):
        st.write("📅 日期：", row["日期"])
        st.write("📝 摘要：", row["摘要"])
        st.markdown(f"[👉 查看原文]({row['原文链接']})")
        st.markdown(f"[查看原文]({row['原文链接']})")
