import urllib.request
import os
import re
import ssl
import time
import random
from bs4 import BeautifulSoup
from time import strftime

# 忽略 SSL 证书校验
ssl_context = ssl._create_unverified_context()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://blog.sina.com.cn/'
}

def sanitize_filename(name):
    """清理文件名非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()[:100]

def open_url(url):
    """请求网页并返回解析后的 BeautifulSoup 对象"""
    if url.startswith('http://'):
        url = url.replace('http://', 'https://', 1)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl_context) as response:
            content = response.read().decode('utf-8', errors='ignore')
            return BeautifulSoup(content, 'html.parser')
    except Exception as e:
        print(f"请求失败: {url}, 错误: {e}")
        return None

def fetch_blog_task(blog_url):
    # 1. 获取博主信息和第一页
    soup = open_url(blog_url)
    if not soup: return

    # 提取 UID
    uid = ""
    scripts = soup.find_all('script')
    for s in scripts:
        match = re.search(r'\$uid\s*:\s*"(\d+)"', s.text)
        if match:
            uid = match.group(1)
            break
    
    if not uid:
        print("无法获取 UID，请检查 URL 是否正确。")
        return

    blog_name = soup.find('span', id='blognamespan').text if soup.find('span', id='blognamespan') else "新浪博主"
    print(f"正在准备抓取博主: {blog_name} (UID: {uid})")

    # 2. 获取所有文章 ID (简化版逻辑)
    # 实际应用中需要循环抓取目录页，这里示范核心抓取过程
    # 假设我们已经得到了文章列表，进入单篇抓取
    
    # 获取文章 ID 列表 (从目录页解析)
    list_url = f"https://blog.sina.com.cn/s/articlelist_{uid}_0_1.html"
    list_soup = open_url(list_url)
    
    # 匹配文章 ID
    article_links = list_soup.find_all('a', href=re.compile(r"blog_([a-zA-Z0-9]+)\.html"))
    article_ids = []
    for a in article_links:
        aid = re.search(r"blog_([a-zA-Z0-9]+)\.html", a['href'])
        if aid: article_ids.append(aid.group(1))
    
    article_ids = list(set(article_ids)) # 去重
    print(f"本页发现 {len(article_ids)} 篇文章，开始解析正文...")

    if not os.path.exists("images"): os.mkdir("images")

    # 3. 逐篇解析正文
    for i, aid in enumerate(article_ids):
        art_url = f"https://blog.sina.com.cn/s/blog_{aid}.html"
        art_soup = open_url(art_url)
        if not art_soup: continue

        # --- 核心修复：使用 BeautifulSoup 提取 ---
        title = art_soup.find('h2', class_='titName').get_text(strip=True) if art_soup.find('h2', class_='titName') else f"Post_{aid}"
        
        # 针对您提供的源码，定位 id="sina_keyword_ad_area2"
        content_div = art_soup.find('div', id='sina_keyword_ad_area2')
        
        if content_div:
            # 修正图片懒加载
            for img in content_div.find_all('img'):
                real_src = img.get('real_src')
                if real_src:
                    img['src'] = real_src
                # 修复图片协议
                if img.get('src') and img['src'].startswith('//'):
                    img['src'] = 'https:' + img['src']

            content_html = str(content_div)
        else:
            content_html = "<p>正文提取失败</p>"

        # 保存文件
        pub_time = art_soup.find('span', class_='time').get_text(strip=True) if art_soup.find('span', class_='time') else ""
        
        safe_title = sanitize_filename(title)
        filename = f"Post_{i+1}_{safe_title}.html"

        html_out = f"""<html>
<head><meta charset="utf-8"/><title>{title}</title>
<style>body{{max-width:800px; margin:auto; line-height:1.8; padding:20px;}} img{{max-width:100%;}}</style>
</head>
<body>
    <h2>{title}</h2>
    <p style="color:#666">时间: {pub_time}</p>
    <div class="content">{content_html}</div>
</body></html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_out)
        
        print(f"成功导出: {filename}")
        time.sleep(random.uniform(1, 2))

if __name__ == "__main__":
    target_url = "https://blog.sina.com.cn/u/2871229797"
    fetch_blog_task(target_url)
