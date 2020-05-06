import requests
import time
import threading
import datetime
from globalupdater import GlobalUpdater, mean

begin = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')
today = (datetime.datetime.now()).strftime('%Y%m%d')

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

def timeratio():
    ratio = 1.0
    reftoday = datetime.datetime.today()
    minutes = ((datetime.datetime.now() - datetime.datetime(reftoday.year,reftoday.month,reftoday.day, 0, 0, 0)).total_seconds()//60)
    if minutes < 570:
        ratio = 1.0
    if 570 <= minutes <= 690:
        ratio = (minutes - 570) / 240
    if 690 < minutes < 780:
        ratio = 0.5
    if 780 <= minutes <= 900:
        ratio = 0.5 + (minutes - 780) / 240
    if 900 < minutes:
        ratio = 1.0
    return ratio

timeratio()

def request_volume(code):
    warp_code = code
    if code.startswith('0') or code.startswith('3'):
        warp_code = '1'+code
    if code.startswith('6'):
        warp_code = '0'+code
    url = 'http://quotes.money.163.com/service/chddata.html?code=%s&start=%s&end=%s&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP' %(warp_code,begin,today)
    info_request = retry_request(url)
    if not info_request:
        return None, None
    latest_vols = []
    lines = info_request.split('\n')
    if len(lines) >= 1:
        for line in lines[1:6]:
            args = line.split(',')
            if len(args) == 1:
                continue
            latest_vols.append(float(args[-4]))
        latest_args = lines[1].split(',')
        circulation_volume = float(latest_args[-4])/float(latest_args[-5])
        mean_volume = mean(latest_vols)
    else:
        circulation_volume = None
        mean_volume = None
    return circulation_volume, mean_volume

def is_Chinese(ch):
    if '\u4e00' <= ch <= '\u9fff':
            return True
    return False

def ChineseCount(instr):
    count = 0
    for ch in instr:
        if is_Chinese(ch):
            count += 1
    return count

def ljust_fmt(data, length=12):
    if type(data) is float:
        str_data = '%.2f'%(data)
    else:
        str_data = str(data)
        nChinese = ChineseCount(str_data)
        length -= nChinese * 1
    str_data = str_data.ljust(length)
    return str_data

class Binder(object):
    def __init__(self, codes, time_interval, pct_chg_limit, tov_limit, vor_limit, listall=True, keys=['price', 'tov', 'tor']):
        self.gu = GlobalUpdater()
        self.codes = codes
        self.timeinterval = time_interval
        self.pct_chg_limit= pct_chg_limit
        self.tov_limit    = tov_limit
        self.vor_limit    = vor_limit
        self.listall      = listall
        self.limit_keys   = ['price', 'vol', 'amount', 'pct_chg', 'tov', 'vor']
        self.started      = False
        self.timeinterval = time_interval
        self.ststr        = ''
        self.conceptstr   = ''
        self.indexstr     = ''
        self.taskthread   = None

        self.GenerateKeys(keys)
        threading.Thread(target=self.GenerateOverview,args=[self.codes,]).start()

    def GenerateOverview(self, codes):
        self.codes_overview = {}
        for code in codes:
            circulation_volume, mean_volume = request_volume(code)
            if circulation_volume is None or mean_volume is None:
                continue
            code_msg_dic = {'mean_volume':mean_volume, 'num_vol':circulation_volume}
            self.codes_overview[code] = code_msg_dic

    def GenerateKeys(self, keys):
        self.key_order     = {}
        for key in self.limit_keys:
            self.key_order[key] = -1
        self.order_key     = []  
        self.nkey          = 0
        for key in keys:
            if key in self.key_order:
                self.key_order[key] = self.nkey
                self.order_key.append(key)
                self.nkey += 1
        self.content_fmt = '%s\t' + '%.2f\t' * self.nkey
        self.content_fmt  = self.content_fmt[:-1] + '\n'
        self.title = 'code\n'
        for key in self.order_key:
            self.title = self.title[:-1] + '\t' + key + '\n'
    
    def start(self):
        if self.started:
            return
        self.started=True
        self.gu.start()
        self.taskthread = threading.Thread(target=self.update_task)
        self.taskthread.start()

    def stop(self):
        if not self.started:
            return
        self.started = False
        self.taskthread.join()
        self.gu.stop()

    def update_task(self):
        while(self.started):
            nexttime = time.time() + self.timeinterval
            self.UpdateST()
            self.UpdateConcept()
            self.UpdateIndex()

            while(time.time() < nexttime):
                time.sleep(0.33)

    def UpdateST(self):
        ratio = timeratio()
        divide_ratio = 1.0 if ratio==0.0 else 1.0/ratio
        codesinfo = self.gu.CodesInfo(self.codes)
        content   = ''
        for code in self.codes:
            if code not in codesinfo:
                continue
            tov = codesinfo[code]['vol'] / self.codes_overview[code]['num_vol'] if code in self.codes_overview else 0.0
            vor = codesinfo[code]['vol'] / self.codes_overview[code]['mean_volume'] * divide_ratio if code in self.codes_overview else 0.0
            codesinfo[code]['tov'] = tov
            codesinfo[code]['vor'] = vor
            if self.listall or \
              (not (self.pct_chg_limit[0] <= codesinfo[code]['pct_chg'] <= self.pct_chg_limit[1]) or \
              tov >= self.tov_limit or vor >= self.vor_limit):
                content_list= [0.0] * self.nkey
                for key in self.limit_keys:
                    if self.key_order[key] >= 0:
                        content_list[self.key_order[key]] = codesinfo[code][key]
                content += self.content_fmt % (code, *content_list)
        self.ststr = self.title + content

    def UpdateConcept(self):
        alighconcept= 16
        alignsize   = 12
        title = '%s%s%s\n' %(ljust_fmt('Concept',alighconcept),ljust_fmt('pct_chg',alignsize),ljust_fmt('amount',alignsize))
        ctfmt = '%s%s%s\n'
        content=''
        sorted_concepts = self.gu.SortConceptsByPctchg()
        for concept, obj in sorted_concepts[:10]:
            content += ctfmt%(ljust_fmt(concept,alighconcept),ljust_fmt(obj.pct_chg,alignsize),ljust_fmt(obj.amount,alignsize))
        self.conceptstr = title + content

    def UpdateIndex(self):
        alignsize = 14
        title = '%s%s%s\n'%(ljust_fmt(' ',alignsize),ljust_fmt('index',alignsize),ljust_fmt('pct_chg',alignsize))
        ctfmt = '%s%s%s\n'
        content=''
        indexinfo = self.gu.IndexInfo()
        if indexinfo is None:
            return
        for info in indexinfo:
            content += ctfmt%(ljust_fmt(info['name'],alignsize),ljust_fmt(info['index'],alignsize),ljust_fmt(info['pct_chg'],alignsize))
        self.indexstr = title + content

    def ConceptListStr(self, concept):
        if not self.gu:
            return ''
        alignsize = 8
        title = '%s%s%s%s\n'%(ljust_fmt('',alignsize),ljust_fmt('price',alignsize),ljust_fmt('pct_chg',alignsize),ljust_fmt('amount',alignsize))
        code_list = self.gu.SortConceptCodesByPctchg(concept)
        codes_info= self.gu.CodesInfo(code_list)
        content = ''
        nline   = 1
        for code in code_list:
            if code not in codes_info:
                continue
            content += '%s%s%s%s\n'%(ljust_fmt(code,alignsize),ljust_fmt(codes_info[code]['price'],alignsize),ljust_fmt(codes_info[code]['pct_chg'],alignsize),ljust_fmt(codes_info[code]['amount']/100000000,alignsize))
            nline += 1
        return title + content, nline
            


if __name__ == '__main__':
    bd = Binder(['000066'],1,0,0,0,True)
    bd.start()