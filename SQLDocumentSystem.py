import math
import documents
import sqlite3
from datetime import datetime


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
    
    def delete_document(self, doc_id):
        """根據文檔ID刪除文檔"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
        self.conn.commit()
        return cursor.rowcount  # 返回受影響的行數
    
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
            print("6. 刪除文檔")  
            print("7. 返回主選單") 
            choice = input("請選擇操作 (1-7): ")
            
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
            
            elif choice == '6':  # 新增的刪除功能
                print("\n刪除文檔")
                doc_id = input("輸入要刪除的文檔ID: ")
                try:
                    doc_id = int(doc_id)
                    affected_rows = sql_db.delete_document(doc_id)
                    if affected_rows > 0:
                        print(f"文檔ID {doc_id} 已成功刪除")
                    else:
                        print(f"找不到文檔ID {doc_id}")
                except ValueError:
                    print("請輸入有效的文檔ID數字")
            
            elif choice == '7':  # 原來的6改為7
                break
            
            else:
                print("無效選擇，請重新輸入")
    finally:
        sql_db.close()