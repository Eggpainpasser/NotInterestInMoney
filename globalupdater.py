import json
import time
import threading
import requests
from retrying import retry

def retry_request(url, timeout = 5.0, max_retry_time=9999):
    text = None
    retry_times = 0
    while retry_times < max_retry_time:
        try:
            text = requests.get(url).text
            return text
        except Exception as e:
            retry_times += 1
    return text

def request_codes(codes, timeout = 0.5):
    urlappend = ''
    for code in codes:
        warp_code = code
        if code.startswith('0') or code.startswith('3'):
            warp_code = 'sz'+code
        if code.startswith('6'):
            warp_code = 'sh'+code
        urlappend  += '%s,'%(warp_code)
    if urlappend[-1] == ',':
        urlappend      = urlappend[:-1]
    url = 'http://hq.sinajs.cn/list=%s' %(urlappend)
    try:
        text = requests.get(url, timeout=timeout).text
    except Exception as e:
        return None
    return text

def request_index(timeout=0.5):
    url = 'http://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006'
    try:
        text = requests.get(url, timeout=timeout).text
    except Exception as e:
        return None
    return text

def analyze_js_code(line):
    effective_words = line[21:-3]
    datapart = effective_words.split(',')
    st_name  = datapart[0]
    st_open  = float(datapart[1])
    st_preclose = float(datapart[2])
    st_price    = float(datapart[3])
    st_high     = float(datapart[4])
    st_low      = float(datapart[5])
    st_invbuy   = float(datapart[6])
    st_invsell  = float(datapart[7])
    st_vol      = float(datapart[8])
    st_amount   = float(datapart[9])
    buy_1_vol   = float(datapart[10])
    buy_1       = float(datapart[11])
    buy_2_vol   = float(datapart[12])
    buy_2       = float(datapart[13])
    buy_3_vol   = float(datapart[14])
    buy_3       = float(datapart[15])
    buy_4_vol   = float(datapart[16])
    buy_4       = float(datapart[17])
    buy_5_vol   = float(datapart[18])
    buy_5       = float(datapart[19])
    sell_1_vol  = float(datapart[20])
    sell_1      = float(datapart[21])
    sell_2_vol  = float(datapart[22])
    sell_2      = float(datapart[23])
    sell_3_vol  = float(datapart[24])
    sell_3      = float(datapart[25])
    sell_4_vol  = float(datapart[26])
    sell_4      = float(datapart[27])
    sell_5_vol  = float(datapart[28])
    sell_5      = float(datapart[29])

    return st_name, st_open, st_preclose, st_price, st_high, \
        st_low, st_invbuy, st_invsell, st_vol, st_amount, \
        buy_1_vol, buy_1, buy_2_vol, buy_2, buy_3_vol, buy_3, buy_4_vol, buy_4, \
        buy_5_vol, buy_5, sell_1_vol, sell_1, sell_2_vol, sell_2, sell_3_vol, sell_3, \
        sell_4_vol, sell_4, sell_5_vol, sell_5

def analyze_js_index(line):
    effective_words = line[23:-3]
    datapart = effective_words.split(',')
    index_name = datapart[0]
    index_index= float(datapart[1])
    index_chg  = float(datapart[2])
    index_pctchg=float(datapart[3])
    index_volume=float(datapart[4])
    index_amount=float(datapart[5])
    return index_name, index_index, index_chg, index_pctchg, index_volume, index_amount

def mean(sequence):
    nsize = len(sequence)
    sums  = sum(sequence)
    return sums/nsize

class ConceptInfo(object):
    def __init__(self):
        self.Reset()
    
    def Reset(self):
        self.pct_chgs = []
        self.amounts  = 0.0
        self.pct_chg  = 0.0
        self.amount   = 0.0

    def Info(self):
        return self.pct_chg, self.amount

    def NewInfo(self, pct_chg, amount):
        self.pct_chgs.append(pct_chg)
        self.amounts += amount
        self.pct_chg = 0.0 if len(self.pct_chgs)==0 else mean(self.pct_chgs)
        self.amount  = 0.0 if len(self.pct_chgs)==0 else self.amounts/len(self.pct_chgs)

    def __str__(self):
        return 'pct_chg=%f\tamount=%f' %(self.pct_chg, self.amount)
    
    def __repr__(self):
        return str(self)

class GlobalUpdater(object):
    def __init__(self):
        self.requestcode_once = 850
        self.started = False
        self.updatetaskthread = threading.Thread(target=self.TaskUpdate)
        self.datalock= threading.Lock()
        self.GenerateIndex()
        self.GenerateCodes()
        self.GenerateConcepts()
        self.BuildRelationShip()

    def GenerateIndex(self):
        self.index = []
        for i in range(3):
            self.index.append({'name':'', 'index':0.0, 'chg':0.0, 'pct_chg':0.0, 'amount':0.0, 'vol':0.0, 'amount':0.0})

    def GenerateCodes(self):
        codefp = open('codes.txt','rt')
        self.codes = []
        self.codes_info = {}
        for line in codefp:
            code = line.split('\n')[0]
            self.codes.append(code)
            self.codes_info[code] = {'pct_chg':0.0, 'amount':0.0, 'price':0.0, 'preclose':0.0, 'vol':0.0, 'high':0.0, 'low':0.0, 'open':0.0}
        self.ncode = len(self.codes)
        self.codes_concepts = {}
        codefp.close()

    def GenerateConcepts(self):
        conceptfp = open('concept.json','rt')
        self.concept_content = json.load(conceptfp)
        conceptfp.close()
    
    def BuildRelationShip(self):
        self.concept_objs   = {}
        for concept, content_codes in self.concept_content.items():
            self.concept_objs[concept] = ConceptInfo()
            for content_code in content_codes:
                if content_code not in self.codes_concepts:
                    self.codes_concepts[content_code] = []
                self.codes_concepts[content_code].append(concept)

    def start(self):
        self.started = True
        self.updatetaskthread.start()

    def stop(self):
        self.started = False
        self.updatetaskthread.join()

    def TaskUpdate(self, interval=1):
        nloop = self.ncode // self.requestcode_once + 1 if self.ncode % self.requestcode_once > 0 else self.ncode // self.requestcode_once
        while(self.started):
            next_time = time.time() + interval
            text = ''
            while(self.started):
                info_text = request_index()
                if info_text is None:
                    continue
                text = text + info_text
                break
            for iloop in range(nloop):
                deal_codes = self.codes[iloop * self.requestcode_once: min(self.ncode, (iloop + 1) * self.requestcode_once)]
                while(self.started):
                    info_text = request_codes(deal_codes)
                    if info_text is None:
                        continue
                    text = text + info_text
                    break
            lines = text.split('\n')
            indexlines = lines[0:3]
            infolines  = lines[3:]
            self.UpdateIndex(indexlines)
            self.UpdateCode(infolines)
            while(time.time() < next_time):
                time.sleep(0.33)

    def UpdateCode(self, lines):
        self.datalock.acquire()
        for concept,obj in self.concept_objs.items():
            obj.Reset()
        for line in lines:
            if len(line) <= 0:
                continue
            code = line[13:19]

            st_name, st_open, st_preclose, st_price, st_high, \
                st_low, st_invbuy, st_invsell, st_vol, st_amount, \
                buy_1_vol, buy_1, buy_2_vol, buy_2, buy_3_vol, buy_3, buy_4_vol, buy_4, \
                buy_5_vol, buy_5, sell_1_vol, sell_1, sell_2_vol, sell_2, sell_3_vol, sell_3, \
                sell_4_vol, sell_4, sell_5_vol, sell_5 = analyze_js_code(line)
            self.codes_info[code]['price']    = st_price
            self.codes_info[code]['preclose'] = st_preclose
            self.codes_info[code]['open']     = st_open
            self.codes_info[code]['vol']      = st_vol
            self.codes_info[code]['amount']   = st_amount
            self.codes_info[code]['low']      = st_low
            self.codes_info[code]['high']     = st_high
            self.codes_info[code]['pct_chg']  = (st_price - st_preclose) / st_preclose * 100

            if code not in self.codes_concepts:
                continue
            concepts = self.codes_concepts[code]
            for concept in concepts:
                self.concept_objs[concept].NewInfo((st_price - st_preclose) / st_preclose * 100, st_amount/100000000)
        self.datalock.release()

    def UpdateIndex(self, lines):
        self.datalock.acquire()
        iindex = 0
        for line in lines:
            if line == '':
                continue
            index_name, index_index, index_chg, index_pctchg, index_volume, index_amount = analyze_js_index(line)
            self.index[iindex]['name'] = index_name
            self.index[iindex]['index']= index_index
            self.index[iindex]['chg']  = index_chg
            self.index[iindex]['pct_chg'] = index_pctchg
            self.index[iindex]['vol']  = index_volume
            self.index[iindex]['amount'] = index_amount
            iindex += 1
        self.datalock.release()

    def IndexInfo(self):
        self.datalock.acquire()
        indexinfo = self.index.copy()
        self.datalock.release()
        return indexinfo

    def CodesInfo(self, codes):
        self.datalock.acquire()
        info_dict = {}
        for code in codes:
            if code not in self.codes_info:
                continue
            info_dict[code] = self.codes_info[code].copy()
            if code not in self.codes_concepts:
                continue
            info_dict[code]['concepts'] = self.codes_concepts[code]
        self.datalock.release()
        return info_dict
    
    def ConceptsInfo(self, concepts):
        self.datalock.acquire()
        info_dict = {}
        for concept in concepts:
            if concept not in self.concept_content:
                continue
            info_dict[concept] = {}
            pct_chg, amount = self.concept_objs[concept].Info()
            info_dict[concept]['codes']= self.concept_content[concept].copy()
            info_dict[concept]['pct_chg'] = pct_chg
            info_dict[concept]['amount'] = amount
        self.datalock.release()
        return info_dict

    def SortConceptsByPctchg(self):
        self.datalock.acquire()
        sorted_concepts = sorted(self.concept_objs.items(),key = lambda x:x[1].pct_chg, reverse=True)
        self.datalock.release()
        return sorted_concepts

    def SortConceptCodesByPctchg(self, concept):
        self.datalock.acquire()
        if concept not in self.concept_content:
            self.datalock.release()
            return []
        concept_codes = self.concept_content[concept]
        exist_codes   = []
        for code in concept_codes:
            if code in self.codes:
                exist_codes.append(code)
        sorted_codes = sorted(exist_codes, key=lambda code:self.codes_info[code]['pct_chg'], reverse=True)
        self.datalock.release()
        return sorted_codes
        

if __name__ == '__main__':
    '''
    gu = GlobalUpdater(3)
    gu.UpdateIndex()
    #text = request_codes(['000066'],True)
    #lines = text.split('\n')
    #analyze_js_index(lines[0])
    '''
    gu = GlobalUpdater()
    gu.start()
    time.sleep(10)
    #info = gu.CodesInfo(['000066','000662'])
    #print(gu.ConceptsInfo(['中韩自贸区']))
    #print(gu.SortConceptsByPctchg())
    #print(gu.SortConceptCodesByPctchg('工业大麻'))
    gu.stop()