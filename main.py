import math
import documents
import sqlite3
from datetime import datetime
from VectorSearch import *
from SQLDocumentSystem import *

# ANSI 顏色碼
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"

# ==================== 主選單 ====================
def main():
    while True:
        print(f"\n{BOLD}{CYAN}=== 主選單 ==={RESET}")
        print(f"{YELLOW}1.{RESET} 向量空間文檔搜索")
        print(f"{YELLOW}2.{RESET} SQL文檔系統")
        print(f"{YELLOW}3.{RESET} 退出程序")
        choice = input(f"{BOLD}請選擇模式 (1-3): {RESET}")
        
        if choice == '1':
            vector_search_interface()
        elif choice == '2':
            sql_interface()
        elif choice == '3':
            print(f"{GREEN}程序已退出{RESET}")
            break
        else:
            print(f"{RED}無效選擇，請重新輸入{RESET}")

if __name__ == "__main__":
    main()
