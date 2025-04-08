import math
import documents
import sqlite3
from datetime import datetime
from VectorSearch import *
from SQLDocumentSystem import *


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
