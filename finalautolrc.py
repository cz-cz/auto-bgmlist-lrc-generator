import requests
import json
import time
import sys
import os,base64
from scrapy.selector import Selector
from  binascii import hexlify
from Crypto.Cipher import AES
class Encrypyed():
    '''传入歌曲的ID，加密生成'params'、'encSecKey 返回'''
    def __init__(self):
        self.pub_key = '010001'
        self.modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        self.nonce = '0CoJUm6Qyw8W8jud'

    def create_secret_key(self, size):
        return hexlify(os.urandom(size))[:16].decode('utf-8')

    def aes_encrypt(self,text, key):
        iv = '0102030405060708'
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8")) 
        result = encryptor.encrypt(text.encode("utf-8"))
        result_str = base64.b64encode(result).decode('utf-8')
        return result_str

    def rsa_encrpt(self,text, pubKey, modulus):
        text = text[::-1]
        rs = pow(int(hexlify(text.encode('utf-8')), 16), int(pubKey, 16), int(modulus, 16))
        return format(rs, 'x').zfill(256)

    def work(self,ids,br=128000):
        text = {'ids': [ids], 'br': br, 'csrf_token': ''}
        text = json.dumps(text)
        i=self.create_secret_key(16)
        encText =self.aes_encrypt(text, self.nonce)
        encText=self.aes_encrypt(encText,i)
        encSecKey=self.rsa_encrpt(i,self.pub_key,self.modulus)
        data = {'params': encText, 'encSecKey': encSecKey}
        return data

    def search(self,text):
        text = json.dumps(text)
        i = self.create_secret_key(16)
        encText = self.aes_encrypt(text, self.nonce)
        encText = self.aes_encrypt(encText, i)
        encSecKey = self.rsa_encrpt(i, self.pub_key, self.modulus)
        data = {'params': encText, 'encSecKey': encSecKey}
        return data


class search():
    '''跟歌单直接下载的不同之处，1.就是headers的referer
                              2.加密的text内容不一样！
                              3.搜索的URL也是不一样的
        输入搜索内容，可以根据歌曲ID进行下载，大家可以看我根据跟单下载那章，自行组合
                                '''
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/search/'} ###!!注意，搜索跟歌单的不同之处！！
        self.main_url='http://music.163.com/'
        self.session = requests.Session()
        self.session.headers=self.headers
        self.ep=Encrypyed()

    def search_song(self, search_content,search_type=1, limit=9):
        """
        根据音乐名搜索
      :params search_content: 音乐名
      :params search_type: 不知
      :params limit: 返回结果数量
      return: 可以得到id 再进去歌曲具体的url
        """
        url = 'http://music.163.com/weapi/cloudsearch/get/web?csrf_token='
        text = {'s': search_content, 'type': search_type, 'offset': 0, 'sub': 'false', 'limit': limit}
        data = self.ep.search(text)
        resp = self.session.post(url, data=data)
        result = resp.json()
        if result['result']['songCount']<= 0:
            print('搜不到！！')
        else:
            songs = result['result']['songs']
            for idx0,song in enumerate(songs):
                song_id,song_name,singer,alia = song['id'],song['name'],song['ar'][0]['name'],song['al']['name']
                print(idx0,song_id,song_name,singer,alia)
            music_id0=input("请输入正确的歌id：" )or '0'
            if(len(music_id0)>=5):
                return music_id0
            for idx0,song in enumerate(songs):
                if(idx0==int(music_id0)):
                    song_id= song['id']
                    return song_id
            
        



def delete_first_lines(filename, count):
    fin = open(filename, 'r')
    a = fin.readlines()
    fout = open(filename, 'w')
    b = ''.join(a[count:])
    fout.write(b)
#删除前三行
#保存BGM列表
def getbgmlist(filename):
    with open(filename+'.edl', "r") as f:  # 打开文件
        count=0
        final='BGM列表：\n'
        for line in f.readlines():
            count=count+1
            if(count%4==1):
                line = line.strip('\n') #去掉列表中每一个元素的换行符
                timebegin=line[53:61]
                print(timebegin)
                final=final+timebegin
                
            if(count%4==2):
                line = line.strip('\n') #去掉列表中每一个元素的换行符
                timebegin=line[18:-4]
                print(timebegin)
                final=final+' '+timebegin+'\n'
        #print(final)
        with open(filename+'BGM'+'.txt', "w") as f2: 
            f2.write(final)
#歌曲时间相加，输入两个时间，输出和
#前者为歌在序列中的时间基线00:00:00
#后者为歌词的时间线
# [mm:ss.xx]歌词正文，mm表示从开始到现在的分钟数，
# ss表示从开始到现在的描述，xx表示n*10毫秒，精度是10毫秒。
#返回str mm:ss.xx

def songtimeadd(songtime1,songtime2):
    reslut=''
    minisecond=songtime2[6:8] #从0数，第六个开始取，第八个不取
    second=int(songtime1[6:8])+int(songtime2[3:5])
    minute=int(songtime1[3:5])+int(songtime2[0:2])
    if(second>=60): 
        second=second-60
        minute=minute+1
    if(int(songtime1[0:2])>0):
        minute=60*int(songtime1[0:2])+minute
    reslut=str(minute).zfill(2)+':'+str(second).zfill(2)+'.'+minisecond  
    # print(reslut)
    return   reslut    
def songtimeadd2(songtime1,songtime2):
    reslut=''
    minisecond=songtime2[6:9] #从0数，第六个开始取，第八个不取
    second=int(songtime1[6:8])+int(songtime2[3:5])
    minute=int(songtime1[3:5])+int(songtime2[0:2])
    if(second>=60): 
        second=second-60
        minute=minute+1
    if(int(songtime1[0:2])>0):
        minute=60*int(songtime1[0:2])+minute
    reslut=str(minute).zfill(2)+':'+str(second).zfill(2)+'.'+minisecond  
    # print(reslut)
    return   reslut 
# [mm:ss.xx]两个相加 只关注MM,SS值
def songtimeadd3(songtime1,songtime2):
    reslut=''
    minisecond=songtime2[6:] #从0数，第六个开始取，第八个不取
    second=int(songtime1[3:5])+int(songtime2[3:5])
    minute=int(songtime1[0:2])+int(songtime2[0:2])
    if(second>=60): 
        second=second-60
        minute=minute+1
    reslut=str(minute).zfill(2)+':'+str(second).zfill(2)+'.'+minisecond  
    # print(reslut)
    return   reslut 

#拼接一首歌词的时间
#歌词名字，歌ID,歌在序列中开始的时间，歌的名字
def songlrctime(filename,songid,time,songname):
    music_id=str(songid)
    headers={"User-Agent" : "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language" : "en-us",
    "Connection" : "keep-alive",
    "Accept-Charset" : "GB2312,utf-8;q=0.7,*;q=0.7"}
    url = 'http://music.163.com/api/song/lyric?'+ 'id=' + music_id+ '&lv=1&kv=1&tv=-1'
    r = requests.get(url,headers=headers,allow_redirects=False)
    #allow_redirects设置为重定向的参数
    #headers=headers添加请求头的参数，冒充请求头
    # time.sleep(0.01)
    json_obj = r.text
    # print(json_obj)
    j = json.loads(json_obj)#进行json解析
    # print(j)
    if 'nolyric' in j or 'uncollected' in j:  #纯音乐处理
        timeadded0=songtimeadd(time,'00:01.00')#加1秒
        temp='['+timeadded0+']'+songname.strip('\n')+r'\n'+'纯音乐，请欣赏'+'\n'
        # temp='['+time[3:8]+'.'+'00'+']'+songname.strip('\n')+r'\n'+'纯音乐，请欣赏'+'\n'
        timeadded=songtimeadd(time,'00:05.00')#加五秒
        temp=temp+'['+timeadded+']'+'\n'
        print(temp)
        with open(filename+'.lrc', "a",encoding='utf-8') as f3: 
            f3.write(temp)
        return 
    #print(j['lrc']['lyric'])
    #print(j['tlyric']['lyric'])
    lrc=j['lrc']['lyric']
    lrc=lrc.splitlines()  #原语言字幕
    lrc_t=j['tlyric']['lyric']
    lrc_t=lrc_t.splitlines()  #翻译语言字幕
    lrc_after=[]
    lrc_t_after=[]
    for line in lrc:  #删除原语言字幕不正常元素
        #print(line[9])
        if(len(line)>=11):
            if(line[9]==']'or line[10]==']'):
                lrc_after.append(line)
            # print(lrc_after)
    for line in lrc_t:  #删除翻译语言字幕不正常元素
        if(len(line)>=11):
            if(line[9]==']'or line[10]==']'):
                lrc_t_after.append(line)
            # print(lrc_t_after)
    if(int(j['tlyric']['version'])==0): #单语言处理
        reslut=''
        reslut=reslut+'['+songtimeadd(time,'00:00.10')+']'+songname.strip('\n')+'\n'
        for idx1,line in enumerate(lrc_after):
            if(line[9]==']'):
                timeadded=songtimeadd(time,str(lrc_after[idx1])[1:9])
                reslut=reslut+'['+timeadded+']'+str(lrc_after[idx1])[10:]+'\n'
            if(line[10]==']'):
                timeadded=songtimeadd2(time,str(lrc_after[idx1])[1:10])
                reslut=reslut+'['+timeadded+']'+str(lrc_after[idx1])[11:]+'\n'
        with open(filename+'.lrc', "a",encoding='utf-8') as f2: 
            f2.write(reslut)
        print (reslut)
        return
    reslut=''
    reslut=reslut+'['+songtimeadd(time,'00:00.10')+']'+songname.strip('\n')+'\n'
    for idx1,line in enumerate(lrc_after):
        for idx2,line2 in enumerate(lrc_t_after):
            #line = line.strip('\n') #去掉列表中每一个元素的换行符
            if(idx1<=len(lrc_t_after) and
            str(lrc_after[idx1])[:10]==str(lrc_t_after[idx2])[:10]):
                if(line[9]==']'):
                    timeadded=songtimeadd(time,str(lrc_t_after[idx2])[1:9])
                    reslut=reslut+'['+timeadded+']'+str(lrc_t_after[idx2])[10:]+r'\n'+str(lrc_after[idx1])[10:]+'\n'
                    print(idx1,(len(lrc_after)-1))
                    if(idx1==(len(lrc_after)-1)):
                        timeadded=songtimeadd3(timeadded,'00:02.00')
                        reslut=reslut+'['+timeadded+']'+'\n'
                if(line[10]==']'):
                    timeadded=songtimeadd2(time,str(lrc_t_after[idx2])[1:10])
                    reslut=reslut+'['+timeadded+']'+str(lrc_t_after[idx2])[11:]+r'\n'+str(lrc_after[idx1])[11:]+'\n'
                    if(idx1==(len(lrc_after)-1)):
                        timeadded=songtimeadd3(timeadded,'00:02.000')
                        reslut=reslut+'['+timeadded+']'+'\n'
    print(reslut)
    with open(filename+'.lrc', "a",encoding='utf-8') as f2: 
            f2.write(reslut)
        
if __name__ == '__main__':
    filename="扬溧高速"    #在这里输入你的文件名哦
    delete_first_lines(filename+'.edl',3)   #删除前三行
    getbgmlist(filename)                    #提取出BGM列表
                                            #
    with open(filename+'BGM'+'.txt', "r") as f3:
         for idx0,line in enumerate(f3.readlines()):
            if(idx0==0):                #因为第一行是‘BGM列表：’
                continue
            else:                   #从第二行开始搜索
                print(line[9:])     #‘00:00:00 Aspiration’取歌名
                time.sleep(0.01)        
                d=search()
                songid=d.search_song(line[9:])#得到歌曲的ID
                songlrctime(filename,songid,line[:8],line[9:])
                
                
    