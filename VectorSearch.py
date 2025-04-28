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
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"



            
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
        for word in re.findall(r'(?u)\b\w+\b', document):
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
    vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b')
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
# def save_documents_to_file():
#     with open('documents.py', 'w', encoding='utf-8') as f:
#         f.write('documents = {\n')
#         for key, value in documents.documents.items():
#             cleaned_value = value.replace("'", "\\'").replace("\n", "\\n")
#             f.write(f"    {key}: '{cleaned_value}',\n")
#         f.write('}\n')
def save_documents_to_file():
    """優化批量保存性能"""
    try:
        with open('documents.py', 'w', encoding='utf-8') as f:
            f.write('documents = {\n')
            for key, value in documents.documents.items():
                # 使用 repr() 自動處理轉義字符
                f.write(f"    {key}: {repr(value)},\n")
            f.write('}\n')
    except Exception as e:
        print(f"Error saving documents: {str(e)}")
        raise
    
    
def add_new_document(content):
    if not isinstance(content, str):
        print("Error: Content must be a string")
        return
    new_index = max(documents.documents.keys()) + 1 if documents.documents else 0
    documents.documents[new_index] = content
    save_documents_to_file()
    print(f"New document added with index: {new_index}")
    return new_index

def add_new_documents_batch(contents: list):
    """批量添加多個文檔"""
    if not isinstance(contents, list):
        print("Error: Input must be a list of strings")
        return []
    
    new_ids = []
    for content in contents:
        if not isinstance(content, str):
            print(f"Warning: Skipping non-string content: {content}")
            continue
        new_id = add_new_document(content)
        new_ids.append(new_id)
        
    return new_ids


def delete_document(doc_id):
    """刪除指定文檔"""
    try:
        doc_id = int(doc_id)
    except ValueError:
        print(f"{RED}錯誤：文檔ID必須是整數{RESET}")
        return
    if doc_id not in documents.documents:
        print(f"{RED}錯誤：找不到ID為 {doc_id} 的文檔{RESET}")
        return
    del documents.documents[doc_id]
    save_documents_to_file()
    print(f"{GREEN}文檔 ID {doc_id} 已成功刪除{RESET}")
        
        
def delete_document_batch(doc_ids):
    """批量刪除指定文檔"""
    not_found_ids = []  # 用於儲存找不到的文檔 ID
    for doc_id in doc_ids:
        try:
            doc_id = int(doc_id)
        except ValueError:
            print(f"{RED}錯誤：文檔ID必須是整數{RESET}")
            not_found_ids.append(doc_id)
            continue  # 如果文檔ID無法轉換為整數，跳過當前的ID
            
        if doc_id not in documents.documents:
            print(f"{RED}錯誤：找不到ID為 {doc_id} 的文檔{RESET}")
            not_found_ids.append(doc_id)
            continue  # 如果找不到該ID的文檔，跳過當前的ID

        del documents.documents[doc_id]
        print(f"{GREEN}文檔 ID {doc_id} 已成功刪除{RESET}")

    save_documents_to_file()

    if not_found_ids:
        return f"未找到文檔ID：{', '.join(map(str, not_found_ids))}"
    return "所有指定的文檔已成功刪除"


def boolean_search_interface():
    inverted_index = create_inverted_index(documents.documents)

    while True:
        print("\n=== 布林查詢模式 ===")
        print("提示：你可以使用 AND / OR / NOT，例如：apple AND banana NOT cherry")
        searchterm = input("輸入布林查詢語句 (或輸入 'back' 返回): ")
        if searchterm.lower() == 'back':
            break

        matches = perform_boolean_search(searchterm, documents.documents, inverted_index)

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

def perform_boolean_search(query, documents_dict, inverted_index):
    def tokenize(query):
        return re.findall(r'\b(?:AND|OR|NOT)\b|[\w\d]+|[()]', query.upper())

    def to_postfix(tokens):
        precedence = {'NOT': 3, 'AND': 2, 'OR': 1}
        output = []
        stack = []

        for token in tokens:
            if token not in precedence and token not in {'(', ')'}:
                output.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()  # remove '('
            else:
                while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence[token]:
                    output.append(stack.pop())
                stack.append(token)

        while stack:
            output.append(stack.pop())

        return output

    def eval_postfix(postfix_tokens):
        stack = []

        for token in postfix_tokens:
            if token not in {'AND', 'OR', 'NOT'}:
                stack.append(inverted_index.get(token.lower(), set()))
            elif token == 'NOT':
                operand = stack.pop()
                result = set(documents_dict.keys()) - operand
                stack.append(result)
            else:
                right = stack.pop()
                left = stack.pop()
                if token == 'AND':
                    stack.append(left & right)
                elif token == 'OR':
                    stack.append(left | right)

        return stack[0] if stack else set()

    tokens = tokenize(query)
    postfix = to_postfix(tokens)
    matched_doc_ids = eval_postfix(postfix)

    if not matched_doc_ids:
        return []
    
    excluded_terms = set()
    i = 0
    while i < len(tokens):
        if tokens[i] == 'NOT':
            excluded_terms.add(tokens[i+1].lower())
            i += 2
        else:
            i += 1
            
    # 過濾結果：確保最終結果中不包含被排除的詞
    filtered_docs = []
    for doc_id in matched_doc_ids:
        doc_text = documents_dict[doc_id]
        # 檢查文檔是否包含任何被排除的詞
        if not any(excluded_term in doc_text.lower() for excluded_term in excluded_terms):
            filtered_docs.append(doc_id)

    if not filtered_docs:
        return []
    
    
    # 提取用於相似度計算的詞（非NOT詞）
    query_terms = [token.lower() for token in tokens 
                  if token not in {'AND', 'OR', 'NOT', '(', ')'} 
                  and token.lower() not in excluded_terms]

    relevant_doc_texts = [documents_dict[doc_id] for doc_id in filtered_docs]
    
    # 計算相似度（僅使用非NOT詞）
    if query_terms:
        query_for_similarity = ' '.join(query_terms)
        all_texts = [query_for_similarity] + relevant_doc_texts
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    else:
        cosine_similarities = [0.5] * len(filtered_docs)

    matches = []
    for i, doc_id in enumerate(filtered_docs):
        # 確保摘要不顯示被排除的詞
        snippet = relevant_doc_texts[i][:100]
        # 可以選擇性地過濾摘要中的排除詞
        for term in excluded_terms:
            snippet = snippet.replace(term, '[FILTERED]')
        matches.append((
            cosine_similarities[i],
            doc_id,
            snippet,
            relevant_doc_texts[i]
        ))

    matches.sort(reverse=True)
    return matches



def vector_search_interface():
    inverted_index = create_inverted_index(documents.documents)

    while True:
        print(f"\n{BOLD}{CYAN}=== 向量搜索模式 ==={RESET}")
        print(f"{YELLOW}1.{RESET} 進行向量搜索")
        print(f"{YELLOW}2.{RESET} 寫入新文檔")
        print(f"{YELLOW}3.{RESET} 批量寫入新文檔")
        print(f"{YELLOW}4.{RESET} 刪除文檔")
        print(f"{YELLOW}5.{RESET} 批量刪除文檔")
        print(f"{YELLOW}6.{RESET} 清除所有快取")
        print(f"{YELLOW}7.{RESET} 布林查詢模式")
        print(f"{YELLOW}8.{RESET} 返回主選單")

        choice = input(f"{BOLD}請選擇操作 (1-5): {RESET}")

        if choice == '1':
            searchterm = input(f'{BOLD}輸入搜索關鍵字 (或輸入"back"返回): {RESET}')
            if searchterm.lower() == 'back':
                break

            matches = get_from_cache(searchterm)

            if matches is None:
                matches = perform_tfidf_search(searchterm, documents.documents, inverted_index)
                add_to_cache(searchterm, matches)

            matches.sort(reverse=True)

            if matches:
                print(f"\n{GREEN}找到以下匹配文檔:{RESET}")
                for i, (score, doc_id, snippet, full_content) in enumerate(matches[:5], 1):
                    print(f"\n{BOLD}結果 {i}:{RESET}")
                    print(f"{CYAN}相似度:{RESET} {score:.4f}")
                    print(f"{CYAN}文檔ID:{RESET} {doc_id}")
                    highlighted_snippet = highlight_keywords(snippet, searchterm.split())
                    print(f"{CYAN}摘要:{RESET} {highlighted_snippet}")
                    print("-" * 50)

                while True:
                    doc_choice = input(f"\n{BOLD}輸入要查看完整內容的文檔ID (或輸入 'back' 返回): {RESET}")
                    if doc_choice.lower() == 'back':
                        break
                    try:
                        doc_choice = int(doc_choice)
                        matching_docs = {doc_id: full_content for _, doc_id, _, full_content in matches}

                        if doc_choice in matching_docs:
                            print(f"\n{GREEN}完整內容：{RESET}")
                            print(matching_docs[doc_choice])
                            break
                        else:
                            print(f"{RED}無效的文檔ID，請從顯示的結果中選擇{RESET}")
                    except ValueError:
                        print(f"{RED}請輸入有效的文檔ID數字{RESET}")
            else:
                print(f"{RED}沒有找到匹配的文檔{RESET}")
        elif choice == '2':
            content = input(f"{BOLD}輸入文檔內容 (或輸入'back'返回): {RESET}")
            if content.lower() == 'back':
                break
            add_new_document(content)
        elif choice == '3':
            batch_content = input(f"{BOLD}輸入批量文檔內容 (使用JSON格式，如[\"文檔1\",\"文檔2\"])(或輸入'back'返回): {RESET}")
            if batch_content.lower() == 'back':
                break
            try:
                # 解析輸入的JSON字符串為Python列表
                import json
                documents_list = json.loads(batch_content)
                if isinstance(documents_list, list):
                    new_ids = add_new_documents_batch(documents_list)
                    print(f"{GREEN}成功添加{len(new_ids)}個文檔，ID為：{new_ids}{RESET}")
                else:
                    print(f"{RED}輸入必須是JSON格式的列表{RESET}")
            except json.JSONDecodeError:
                print(f"{RED}輸入格式錯誤，無法解析為JSON列表。請使用格式如：[\"文檔1\", \"文檔2\"]{RESET}")
        elif choice == '4':
            doc_id = input(f"{BOLD}輸入要刪除的文檔ID (或輸入'back'返回): {RESET}")
            if doc_id.lower() == 'back':
                continue
            delete_document(doc_id)
        elif choice == '5':
            doc_ids_input = input(f"{BOLD}輸入要刪除的文檔ID列表 (以逗號分隔，如 1,2,3) (或輸入'back'返回): {RESET}")
            if doc_ids_input.lower() == 'back':
                continue
            try:
                doc_ids = list(map(int, doc_ids_input.split(',')))
                result = delete_document_batch(doc_ids)
                print(result)
            except ValueError:
                print(f"{RED}無效的文檔ID列表，請確保輸入的是以逗號分隔的數字列表。{RESET}")
        elif choice == '6':
            clear_all_cache()
            print(f"{GREEN}快取已清除{RESET}")
        elif choice == '7':
            boolean_search_interface()
        elif choice == '8':
            break
        else:
            print(f"{RED}無效選擇，請重新輸入{RESET}")



