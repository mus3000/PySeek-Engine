import math
import documents
import sqlite3
from datetime import datetime
import redis
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# 連接到 Redis (預設在本機的 6379 port)
r = redis.Redis(host='localhost', port=6379, db=0)
# ==================== 原有向量搜索功能 ====================
class VectorCompare:
    def magnitude(self, concordance):
        if type(concordance) != dict:
            raise ValueError('Supplied Argument should be of type dict')
        total = sum(count**2 for word, count in concordance.items())
        return math.sqrt(total)

    def relation(self, concordance1, concordance2):
        if type(concordance1) != dict or type(concordance2) != dict:
            return 0
        topvalue = sum(count * concordance2.get(word, 0) for word, count in concordance1.items())
        mag = (self.magnitude(concordance1) * self.magnitude(concordance2))
        return topvalue / mag if mag != 0 else 0

    def concordance(self, document):
        if type(document) != str:
            raise ValueError('Supplied Argument should be of type string')
        con = {}
        for word in document.split():
            con[word] = con.get(word, 0) + 1
        return con

def perform_tfidf_search(searchterm, documents_dict):
    doc_ids = list(documents_dict.keys())
    doc_texts = list(documents_dict.values())

    all_texts = [searchterm] + doc_texts  # 把搜尋字串放在第一個
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # 計算第一個（searchterm）對所有文檔的相似度
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    matches = []
    for i, score in enumerate(cosine_similarities):
        if score > 0:
            matches.append((score, doc_ids[i], doc_texts[i][:100], doc_texts[i]))

    matches.sort(reverse=True)
    return matches

# ==================== 快取實現 ==================== #

def get_from_cache(searchterm):
    data = r.get(searchterm.lower())
    if data:
        return json.loads(data)
    return None


def add_to_cache(searchterm, matches):
    r.set(searchterm.lower(), json.dumps(matches))

def clear_all_cache():
    r.flushdb()  # 清空當前資料庫的所有快取
    print("快取清除完畢！")


# ==================== 快取實現結束 ================== #

def save_documents_to_file():
    with open('documents.py', 'w', encoding='utf-8') as f:
        f.write('documents = {\n')
        for key, value in documents.documents.items():
            cleaned_value = value.replace("'", "\\'").replace("\n", "\\n")
            f.write(f"    {key}: '{cleaned_value}',\n")
        f.write('}\n')

def add_new_document(content):
    if not isinstance(content, str):
        print("Error: Content must be a string")
        return
    new_index = max(documents.documents.keys()) + 1 if documents.documents else 0
    documents.documents[new_index] = content
    save_documents_to_file()
    print(f"New document added with index: {new_index}")
    return new_index

def vector_search_interface():
    v = VectorCompare()
    while True:
        print("\n=== 向量搜索模式 ===")
        print("1. 進行向量搜索")
        print("2. 寫入新文檔")
        print("3. 清除所有快取")
        print("4. 返回主選單")
        choice = input("請選擇操作 (1-4): ")
        
        if choice == '1':
            searchterm = input('輸入搜索關鍵字 (或輸入"back"返回): ')
            if searchterm.lower() == 'back':
                break
            
            # 嘗試從快取中讀取結果
            matches = get_from_cache(searchterm)
            # matches = []
            
            if matches is None:
                matches = []
                matches = perform_tfidf_search(searchterm, documents.documents)

                # for doc_id, content in documents.documents.items():
                #     if isinstance(content, str):
                #         relation = v.relation(
                #             v.concordance(searchterm.lower()),
                #             v.concordance(content.lower())
                #         )
                #         if relation > 0:
                #             matches.append((relation, doc_id, content[:100], content))
                        
                        
                # 儲存結果到快取中
                add_to_cache(searchterm, matches)
                
            matches.sort(reverse=True)
            
            if matches:
                # 先顯示所有匹配結果
                print("\n找到以下匹配文檔:")
                for i, (score, doc_id, snippet, full_content) in enumerate(matches[:5], 1):
                    print(f"\n結果 {i}:")
                    print(f"相似度: {score:.4f}")
                    print(f"文檔ID: {doc_id}")
                    print(f"摘要: {snippet}")
                    print("-" * 50)
                
                # 統一詢問用戶要查看哪個文檔
                while True:
                    doc_choice = input("\n輸入要查看完整內容的文檔ID (或輸入 'back' 返回): ")
                    if doc_choice.lower() == 'back':
                        break
                        
                    try:
                        doc_choice = int(doc_choice)
                        matching_docs = {doc_id: full_content for _, doc_id, _, full_content in matches}
                        
                        if doc_choice in matching_docs:
                            print("\n完整內容：")
                            print(matching_docs[doc_choice])
                            break  # 顯示完後退出循環
                        else:
                            print("無效的文檔ID，請從顯示的結果中選擇")
                    except ValueError:
                        print("請輸入有效的文檔ID數字")
            else:
                print("沒有找到匹配的文檔")
        elif choice == '2':
            content = input("輸入文檔內容 (或輸入'back'返回): ")
            if content.lower() == 'back':
                break
            add_new_document(content)
        elif choice == '3':
            clear_all_cache()
        elif choice == '4':
            break
        else:
            print("無效選擇，請重新輸入")
