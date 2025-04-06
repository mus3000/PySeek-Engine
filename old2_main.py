import math
import documents
import os


class VectorCompare:
    # 'magnitude' 主要指的是向量的長度或大小
    def magnitude(self,concordance):
        if type(concordance) != dict:
            raise ValueError('Supplied Argument should be of type dict')
        
        total = 0
        
        
        # 這個字典表示 'hello' 出現了 2 次，'world' 出現了 3 次。要計算這個字典的 "magnitude"，我們首先計算每個單詞計數的平方：
        # 然後計算它們的總和：13 = 4 + 9
        # 最後，取總和的平方根：根號13 = 3.605
        for word, count in concordance.items():
            total += count ** 2
            
        return math.sqrt(total)



    def relation(self,concordance1, concordance2):
        if type(concordance1) != dict:
            raise ValueError('Supplied Argument 1 should be of type dict')
        if type(concordance2) != dict:
            raise ValueError('Supplied Argument 2 should be of type dict')

        relevance = 0
        topvalue = 0
        
        for word, count in concordance1.items():
            if word in concordance2:  
                topvalue += count * concordance2[word]
        # 在這部分代碼中，首先計算 concordance1 和 concordance2 的 magnitude（大小）。
        # 如果兩個字典的向量大小都不為 0（即兩個向量不為零向量），則餘弦相似度可以計算為
        # cosine similarity=topvalue/magnitude(concordance1) x magnitude(concordance2)
        #這個公式表示兩個向量之間的餘弦角度，越接近 1 表示兩個向量越相似，越接近 0 表示它們越不相似。
        #如果其中任一個向量的大小為 0（即空向量），則返回 0，表示無法計算相似度。
        if (self.magnitude(concordance1) * self.magnitude(concordance2)) != 0:
            return topvalue / (self.magnitude(concordance1) * self.magnitude(concordance2))
        else:
            return 0



    def concordance(self,document):
        # document = "hello world hello"
        # {'hello': 2, 'world': 1}
        if type(document) != str:
            raise ValueError('Supplied Argument should be of type string')
        con = {}
        for word in document.split(' '):
            if word in con:  
                con[word] = con[word] + 1
            else:
                con[word] = 1
        return con


class DocumentDatabase:
    def __init__(self, db_file='documents.db'):
        """初始化SQLite數據庫"""
        self.conn = sqlite3.connect(db_file)
        self._init_db()
        
    def _init_db(self):
        """創建數據表結構"""
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS structured_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,  # 對應原始documents的ID
            title TEXT,
            author TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()
        
    def add_structured_doc(self, doc_id, title=None, author=None, category=None):
        """添加結構化文檔信息"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO structured_docs (doc_id, title, author, category)
        VALUES (?, ?, ?, ?)
        ''', (doc_id, title, author, category))
        self.conn.commit()
        return cursor.lastrowid

    def sql_query(self, conditions=None, fields=None, limit=5):
        """SQL式查詢"""
        if not fields:
            fields = ['doc_id', 'title', 'author', 'category']
        
        query = f"SELECT {', '.join(fields)} FROM structured_docs"
        params = []
        
        if conditions:
            where_clause = []
            for key, value in conditions.items():
                if isinstance(value, (list, tuple)):
                    placeholders = ', '.join(['?'] * len(value))
                    where_clause.append(f"{key} IN ({placeholders})")
                    params.extend(value)
                else:
                    where_clause.append(f"{key} = ?")
                    params.append(value)
            query += " WHERE " + " AND ".join(where_clause)
        
        query += f" LIMIT {limit}"
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()


#初始化
v = VectorCompare()
db = DocumentDatabase()


def save_documents_to_file():
    """將當前 documents 字典保存回 documents.py 文件"""
    with open('documents.py', 'w', encoding='utf-8') as f:
        f.write('documents = {\n')
        for key, value in documents.documents.items():
            # 處理特殊字符以確保正確儲存
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





# 開始查詢
# 主程序循環
while True:
    print("\n1. Search documents")
    print("2. Add new document")
    print("3. Exit")
    choice = input("Choose an option (1-3): ")
    
    if choice == '1':
        # 搜索功能
        searchterm = input('Enter Search Term: ')
        matches = []
        
        for doc_id, content in documents.documents.items():
            if isinstance(content, str):
                doc_vector = v.concordance(content.lower())
                query_vector = v.concordance(searchterm.lower())
                relation = v.relation(query_vector, doc_vector)
                if relation > 0:
                    matches.append((relation, doc_id, content[:100]))
        
        matches.sort(reverse=True)

        if matches:
            for match in matches[:5]:
                print(f"\nSimilarity: {match[0]:.4f}")
                print(f"Document ID: {match[1]}")
                print(f"Snippet: {match[2]}")
                print("-" * 50)
        else:
            print("No matches found.")
    
    elif choice == '2':
        # 新增文檔功能
        print("\nEnter new document content (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == '' and len(lines) > 0 and lines[-1] == '':
                break
            lines.append(line)
        content = '\n'.join(lines[:-1])  # 移除最後的空行
        
        if content.strip():
            new_id = add_new_document(content)
            print(f"Successfully added document ID: {new_id}")
        else:
            print("Error: Content cannot be empty")
    
    elif choice == '3':
        print("Exiting program.")
        break
    
    else:
        print("Invalid choice. Please try again.")



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