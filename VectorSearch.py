import math
import documents
import sqlite3
from datetime import datetime

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
        print("3. 返回主選單")
        choice = input("請選擇操作 (1-3): ")
        
        if choice == '1':
            searchterm = input('輸入搜索關鍵字 (或輸入"back"返回): ')
            if searchterm.lower() == 'back':
                break
            matches = []
            for doc_id, content in documents.documents.items():
                if isinstance(content, str):
                    relation = v.relation(
                        v.concordance(searchterm.lower()),
                        v.concordance(content.lower())
                    )
                    if relation > 0:
                        matches.append((relation, doc_id, content[:100], content))
            
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
            break
        else:
            print("無效選擇，請重新輸入")
