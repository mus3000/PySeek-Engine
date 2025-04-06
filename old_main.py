import math
import documents

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





v = VectorCompare()






index = {

0:v.concordance(documents.documents[0].lower()),

1:v.concordance(documents.documents[1].lower()),

2:v.concordance(documents.documents[2].lower()),

3:v.concordance(documents.documents[3].lower()),

4:v.concordance(documents.documents[4].lower()),

5:v.concordance(documents.documents[5].lower()),

6:v.concordance(documents.documents[6].lower()),

}



# 開始查詢
while True:
    searchterm = input('Enter Search Term: ')
    # 存儲匹配結果
    matches = []
    
    # 計算所有文檔的餘弦相似度
    for i in range(len(index)):
        relation = v.relation(v.concordance(searchterm.lower()), index[i])
        if relation != 0:
            matches.append((relation, documents.documents[i][:100]))
  
    # 排序並顯示匹配結果
    matches.sort(reverse=True)

    # 輸出結果
    if matches:
        for match in matches:
            print(f"Similarity: {match[0]:.4f}")
            print(f"Document ID: {match[1]}")
            print(f"Snippet: {match[1]}")
            print("-" * 50)
    else:
        print("No matches found.")
    
    # 詢問是否繼續查詢
    continue_search = input("Would you like to search again? (y/n): ")
    if continue_search.lower() != 'y':
        break

print("Exiting program.")



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