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
                        matches.append((relation, doc_id, content[:100]))
            
            matches.sort(reverse=True)
            
            if matches:
                for score, doc_id, snippet in matches[:5]:
                    print(f"\n相似度: {score:.4f}")
                    print(f"文檔ID: {doc_id}")
                    print(f"摘要: {snippet}")
                    print("-" * 50)
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

# ==================== 獨立SQL功能 ====================
class SQLDocumentSystem:
    def __init__(self, db_file='sql_documents.db'):
        self.conn = sqlite3.connect(db_file)
        self._init_db()
    
    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()
    
    def add_document(self, title, content, author=None, category=None):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO documents (title, content, author, category)
        VALUES (?, ?, ?, ?)
        ''', (title, content, author, category))
        self.conn.commit()
        return cursor.lastrowid
    
    def search_documents(self, field, keyword, limit=5):
        cursor = self.conn.cursor()
        cursor.execute(f'''
        SELECT id, title, author, substr(content, 1, 100) as snippet 
        FROM documents 
        WHERE {field} LIKE ? 
        ORDER BY created_at DESC 
        LIMIT ?
        ''', (f'%{keyword}%', limit))
        return cursor.fetchall()
    
    def advanced_search(self, conditions, limit=5):
        cursor = self.conn.cursor()
        query = "SELECT id, title, author, substr(content, 1, 100) as snippet FROM documents"
        params = []
        
        if conditions:
            query += " WHERE " + " AND ".join(f"{k} LIKE ?" for k in conditions.keys())
            params = [f'%{v}%' for v in conditions.values()]
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()

def sql_interface():
    sql_db = SQLDocumentSystem()
    try:
        while True:
            print("\n=== SQL文檔系統 ===")
            print("1. 添加文檔")
            print("2. 標題搜索")
            print("3. 內容搜索")
            print("4. 作者搜索")
            print("5. 高級搜索")
            print("6. 返回主選單")
            choice = input("請選擇操作 (1-6): ")
            
            if choice == '1':
                print("\n添加新文檔:")
                title = input("標題: ")
                print("輸入內容 (空行結束):")
                content_lines = []
                while True:
                    line = input()
                    if line == "":
                        break
                    content_lines.append(line)
                content = "\n".join(content_lines)
                author = input("作者 (可選): ")
                category = input("分類 (可選): ")
                
                doc_id = sql_db.add_document(title, content, author or None, category or None)
                print(f"文檔已添加，ID: {doc_id}")
            
            elif choice in ['2', '3', '4']:
                field = {
                    '2': 'title',
                    '3': 'content',
                    '4': 'author'
                }[choice]
                keyword = input(f"輸入{field}搜索關鍵字: ")
                results = sql_db.search_documents(field, keyword)
                
                if results:
                    print("\n搜索結果:")
                    for doc_id, title, author, snippet in results:
                        print(f"\nID: {doc_id}")
                        print(f"標題: {title}")
                        print(f"作者: {author or '未知'}")
                        print(f"摘要: {snippet}")
                        print("-" * 50)
                else:
                    print("沒有找到匹配的文檔")
            
            elif choice == '5':
                print("\n高級搜索 (留空表示不限制)")
                conditions = {}
                if title := input("標題包含: "):
                    conditions['title'] = title
                if content := input("內容包含: "):
                    conditions['content'] = content
                if author := input("作者: "):
                    conditions['author'] = author
                if category := input("分類: "):
                    conditions['category'] = category
                    
                results = sql_db.advanced_search(conditions)
                
                if results:
                    print("\n搜索結果:")
                    for doc_id, title, author, snippet in results:
                        print(f"\nID: {doc_id}")
                        print(f"標題: {title}")
                        print(f"作者: {author or '未知'}")
                        print(f"摘要: {snippet}")
                        print("-" * 50)
                else:
                    print("沒有找到匹配的文檔")
            
            elif choice == '6':
                break
            
            else:
                print("無效選擇，請重新輸入")
    finally:
        sql_db.close()

# ==================== 主選單 ====================
def main():
    while True:
        print("\n=== 主選單 ===")
        print("1. 向量空間文檔搜索")
        print("2. SQL文檔系統")
        print("3. 退出程序")
        choice = input("請選擇模式 (1-3): ")
        
        if choice == '1':
            vector_search_interface()
        elif choice == '2':
            sql_interface()
        elif choice == '3':
            print("程序已退出")
            break
        else:
            print("無效選擇，請重新輸入")

if __name__ == "__main__":
    main()
    
    
    
# 我認為結果還不錯！現在這項技術存在一些問題。
# 首先，它不支援布林搜索，這可能是一個問題，
# 儘管大多數人傾向於只輸入一些術語。其次，它在處理較大的文件時有問題。
# 向量空間的工作方式偏向較小的文檔，因為它們更接近搜尋字詞空間。
# 您可以透過將較大的文件分成較小的文件來解決這個問題。
# 但最後也是最大的問題是它非常耗費 CPU 資源。
# 我已經使用 50,000 個文件測試了這樣的搜索，並且它是可行的，
# 但您不會想要進行更進一步的搜索。但這是一個相當幼稚的實現。
# 透過一些快取並檢查哪些文件值得比較，您可以將其擴展到數百萬個文件。

# 我記得在某處讀過（抱歉沒有來源）Altavista 
# 和其他一些早期搜尋引擎使用類似於上述的技術來計算排名，因此看來這個想法確實可以大規模推廣。

# 現在我確信有人會想，「等等，如果這麼簡單，
# 那為什麼打造下一個谷歌這麼難？」。嗯，答案是，
# 索引 10,000 到 100,000,000 個頁面相當容易，
# 但索引 1,000,000,000 個以上的頁面則要困難得多。
# 您必須將其分片到多台計算機，並且出錯的幅度非常低。
# 您可以閱讀安娜·帕特森（ Cuil的聯合創始人之一）撰寫的這篇文章
# 《為什麼編寫搜尋引擎很難》，它很好地解釋了這個問題。

# 有些人表示難以運作上述內容。要做到這一點，只需將其全部複製到一個文件中並運行它。