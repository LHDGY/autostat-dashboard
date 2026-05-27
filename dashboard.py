import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from googletrans import Translator

# ================= 初始化 =================
st.set_page_config(page_title="AutoStat V2", layout="wide")
st.title("🚗 俄罗斯汽车情报系统 V2（中文增强版）")

translator = Translator()

def to_cn(text):
    try:
        return translator.translate(text, dest="zh-cn").text
    except:
        return text


# ================= 抓新闻 =================
def get_news():
    url = "https://eng.autostat.ru/news/"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.find_all("a", href=True)

    seen = set()
    news = []

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


# ================= 抓详情 =================
def get_detail(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # 时间
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


# ================= 信息抽取 =================
def extract(text):
    t = text.lower()

    brands = []
    for b in ["geely", "byd", "lada", "haval", "chery", "toyota"]:
        if b in t:
            brands.append(b)

    model = []
    if "suv" in t:
        model.append("SUV")
    if "electric" in t or "ev" in t:
        model.append("EV")
    if "sedan" in t:
        model.append("Sedan")

    numbers = re.findall(r"\d+\.?\d*\s?(kw|hp|kwh|rub|usd|million)", t)

    return {
        "brands": ", ".join(set(brands)) if brands else "Unknown",
        "model": ", ".join(set(model)) if model else "Unknown",
        "numbers": ", ".join(numbers[:3]) if numbers else ""
    }


# ================= 中文摘要（升级版） =================
def summary(title, text):

    raw = (title + " " + text)[:500]

    sentences = re.split(r"[.。]", raw)
    clean = [s.strip() for s in sentences if len(s.strip()) > 30]

    base = "。".join(clean[:3])

    return to_cn(base)


# ================= 中文标题 =================
def cn_title(title):
    return to_cn(title)


# ================= UI =================
if st.button("🔄 更新数据"):
    st.rerun()


# ================= 主流程 =================
news = get_news()

data = []

for n in news:

    date, text = get_detail(n["link"])
    info = extract(text)

    data.append({
        "日期": date,
        "中文标题": cn_title(n["title"]),
        "品牌": info["brands"],
        "车型": info["model"],
        "中文摘要": summary(n["title"], text),
        "原文链接": n["link"]
    })


df = pd.DataFrame(data)


# ================= 展示 =================
st.dataframe(df, use_container_width=True)

for i, row in df.iterrows():
    with st.expander(row["中文标题"]):
        st.write("📅 日期：", row["日期"])
        st.write("🚗 品牌：", row["品牌"])
        st.write("⚙️ 车型：", row["车型"])
        st.write("📝 摘要：", row["中文摘要"])
        st.markdown(f"[查看原文]({row['原文链接']})")
