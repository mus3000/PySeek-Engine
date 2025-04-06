import requests
from bs4 import BeautifulSoup
import math
import documents

url = 'https://www.gutenberg.org/cache/epub/75778/pg75778-images.html'  # 替換成你要抓的網址
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# 找出所有 <p> 標籤
paragraphs = soup.find_all('p')

# 將每個 <p> 標籤的文字組合成一個完整的文章字串
article = '\n\n'.join([p.get_text() for p in paragraphs])

# 保存到檔案中
with open('article.txt', 'w', encoding='utf-8') as f:
    f.write(article)
    
# 讀取新抓取的文章
with open('article.txt', 'r', encoding='utf-8') as f:
    new_article = f.read()

chunk_size = 100
chunks = [new_article[i:i+chunk_size] for i in range(0, len(new_article), chunk_size)]


# 更新 documents 字典，並加入新抓取的文章
new_index = len(documents.documents)
for i, chunk in enumerate(chunks):
    documents.documents[new_index + i] = chunk

# documents.documents[new_index] = new_article

# 儲存修改後的 documents 字典回 documents.py

# 儲存修改後的 documents 字典回 documents.py
with open('documents.py', 'w', encoding='utf-8') as f:
    f.write('documents = {\n')
    for key, value in documents.documents.items():
        # 替換單引號和換行符，避免儲存時格式錯誤
        cleaned_value = value.replace("'", "\\'").replace("\n", "\\n")
        f.write(f"    {key}: '{cleaned_value}',\n")
    f.write('}\n')

print(f"New article added and split into {len(chunks)} chunks. documents.py updated.")