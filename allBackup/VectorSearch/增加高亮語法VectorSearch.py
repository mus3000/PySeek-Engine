import math
import documents
import redis
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from rapidfuzz import fuzz, process


#syntax highlight
HIGHLIGHT_COLOR = "\033[1;34m"  # 藍色 + 粗體
RESET_COLOR = "\033[0m"




            
def highlight_keywords(text, keywords):
    for word in keywords:
        pattern = re.compile(rf'\b({re.escape(word)})\b', re.IGNORECASE)
        text = pattern.sub(f"{HIGHLIGHT_COLOR}\\1{RESET_COLOR}", text)
    return text


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

# ==================== 建立倒排索引 ==================== #

def create_inverted_index(documents_dict):
    inverted_index = {}
    for doc_id, doc_text in documents_dict.items():
        for word in set(doc_text.split()):
            if word not in inverted_index:
                inverted_index[word] = set()
            inverted_index[word].add(doc_id)
    return inverted_index



# ==================== 計算TF-IDF並根據倒排索引檢索文檔 ==================== #
def perform_tfidf_search(searchterm, documents_dict, inverted_index):
    doc_ids = list(documents_dict.keys())
    doc_texts = list(documents_dict.values())

    # 先根據倒排索引過濾出可能包含搜索詞的文檔
    relevant_doc_ids = set()
    for word in searchterm.split():
        if word in inverted_index:
            relevant_doc_ids.update(inverted_index[word])

    # 如果沒有相關文檔，返回空
    if not relevant_doc_ids:
        return []

    relevant_doc_texts = [documents_dict[doc_id] for doc_id in relevant_doc_ids]
    relevant_doc_ids = list(relevant_doc_ids)

    # 計算TF-IDF矩陣，將搜索詞和文檔文本合併
    all_texts = [searchterm] + relevant_doc_texts
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # 計算搜索詞和所有相關文檔的餘弦相似度
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # 選出相似度大於0的文檔
    matches = []
    for i, score in enumerate(cosine_similarities):
        if score > 0:
            matches.append((score, relevant_doc_ids[i], relevant_doc_texts[i][:100], relevant_doc_texts[i]))

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
    inverted_index = create_inverted_index(documents.documents)
  
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
            
            if matches is None:
                matches = perform_tfidf_search(searchterm, documents.documents, inverted_index)
                add_to_cache(searchterm, matches)
                
            matches.sort(reverse=True)
            
            if matches:
                print("\n找到以下匹配文檔:")
                for i, (score, doc_id, snippet, full_content) in enumerate(matches[:5], 1):
                    print(f"\n結果 {i}:")
                    print(f"相似度: {score:.4f}")
                    print(f"文檔ID: {doc_id}")
                    highlighted_snippet = highlight_keywords(snippet, searchterm.split())
                    print(f"摘要: {highlighted_snippet}")
                    print("-" * 50)
                
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
                            break
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
