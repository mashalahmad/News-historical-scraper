 
import requests
import re
import errno
from bs4 import BeautifulSoup
from tld import get_fld
from datetime import datetime
import urllib.request
import pymysql
import socket
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from socket import error as SocketError
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from sys import platform



# Database details - host, user, password, database name

#DBHOST = "xxx"
#DBUSER = "root"
#DBPASSWORD = "xxx^5$"
#DBNAME = "xxxxxx"

# create database connection
con = pymysql.connect(host='xxxx',user='root',password='xxxxx',database='xxxxxx') 


# computer's ip
hostname = socket.gethostname()   
ip_address = socket.gethostbyname(hostname)

date = datetime.today().strftime('%Y-%m-%d')
email = 'admin@biasmonitor.com'


# create mysql cursor
with con.cursor() as cursor:
    
    #cursor.execute('select * from `bias_master`')
    cursor.execute('select * from `bias_master`')
    bias_master_records = cursor.fetchall()
    #print(bias_master_records)

    cursor.execute('select * from `focused_search`')
    focused_search=cursor.fetchall()
    
    # fetch previous urls to prevent duplicates
    article_urls = []
    cursor.execute('select article_url from `bias_detail`')
    [article_urls.append(url[0]) for url in cursor.fetchall()]
    
    # ignore domains variables
    ignore_domains = []
    cursor.execute('select domain from `ignore_domain`')
    [ignore_domains.append(url[0]) for url in cursor.fetchall()]
    ignore_domains = ','.join(ignore_domains)
        
    new_urls = []
    def get_sunshinedata(article_pages,bias_id):
            page_text = ''
            for article in article_pages:
                if not ((article in article_urls) or (article in new_urls)):
                        new_urls.append(article)
                        print(article)
                        if ("submissions" in article):
                            continue
                        else:   
                          response = urllib.request.urlopen(article)
                          article_html = BeautifulSoup(response, 'html.parser')
                          article_title = article_html.find('div', {'class' : 'scn_acf_field'})
                          article_pub_date = article_html.find('time', {'class' : 'entry-date updated td-module-date'})
                          article_pub_date = datetime.strptime((article_pub_date.text), '%d %B %Y')
                          published_date = article_pub_date.strftime('%Y-%m-%d')
                          cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,published_date,article,article_title.text,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))
                          con.commit() 
                          cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                          bias_detail_id = cursor.fetchall()[0][0]
                          con.commit() 
                          article_text = article_html.find_all('div', class_='tdb-block-inner td-fix-index')
                          for text in article_text:
                              for child in text.children:
                                    if not child.name:
                                        continue
                                    if child.name =='p':
                                          page_text = child.get_text()
                                          #print(page_text)   
                                          cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                          con.commit() 
                          print("record inserted");

    def get_abcdata(article_links,biasid):
        #print(article_urls)
        page_text = ''
        for link in article_links:
            if not ((link in article_urls)  or (link in new_urls)):
                new_urls.append(link)
                print(link)
                response = urllib.request.urlopen(link)
                soup = BeautifulSoup(response, 'html.parser')
                article_title = soup.select('h1')[0].text.strip()
                #print(article_title)
                if ("VIDEO" in article_title) or ("AUDIO" in article_title) or ("video" in link) or ("7:30" in link) or ("audio" in link) :
                       continue
                else:    
                    if soup.find('div', {'data-component' : 'Dateline'}) is not None:
                        article_pub_date = soup.find('time', {'data-component' : 'Text'})
                        article_pub_date=article_pub_date.text.split(" ")
                        article_pub_date = article_pub_date[:-2]
                        article_pub_date = " ".join(article_pub_date)
                        article_pub_date = datetime.strptime((article_pub_date), '%a %d %b %Y')
                        published_date = article_pub_date.strftime('%Y-%m-%d')
                        cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,published_date,link,article_title,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))
                        con.commit()
                    cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                    bias_detail_id = cursor.fetchall()[0][0]
                    con.commit()                        
                    if soup.find('div', {'id' : 'body'}) is not None:
                        if soup.find('div',{'id': 'body'}).find('p') is not None:
                            article_text = soup.find('div', {'id' : 'body'}).find_all("p")
                        else:
                            article_text = soup.find('div', {'id' : 'body'}).select("span")[0]
                    elif soup.find('div',{'data-component' : 'GridRow'}) is not None:
                            article_text = soup.find('div', {'data-component' : 'GridRow'}).find_all('p')
                    elif soup.find('div', {'class' :'comp-rich-text clearfix'}) is not None:
                            article_text = soup.find('div', {'class' : 'comp-rich-text clearfix'}).find_all('p')
                    elif soup.find('div', {'class' : 'DetailLayout_inner__BwjPC'}) is not None:
                           article_text = soup.find('div', {'class' : 'DetailLayout_inner__BwjPC'}).find_all('p')  
                    elif soup.find('div', {'class' : 'article section'}) is not None:
                           article_text = soup.find('div', {'class' : 'article section'}).find_all('p')                                   
                                        
                    for text in  article_text:
                            page_text = text.get_text() 
                            cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                            con.commit()
                    print("record inserted")
        driver.close()                        
    #couriermail
    
    def getcouriermail_data(article_links,biasid):
            try:  
                for url in article_links:
                  if url :
                    if not ((url in article_urls)  or (url in new_urls)) :
                        new_urls.append(url)
                        print(url)
                        driver.get(url)
                        time.sleep(10)
                        article_html = BeautifulSoup(driver.page_source, 'html.parser')
                        if  article_html.find('h1', {'id' : 'story-headline'}) is not None:
                            article_title = article_html.find('h1', {'id' : 'story-headline'})
                        else:
                            continue
                        if  article_html.find('div', {'class' : 'date-live'}) is not None:     
                            e = datetime.now()
                            article_pub_date=e.strftime("%B %d, %Y")
                            article_pub_date= datetime.strptime(article_pub_date, '%B %d, %Y').strftime('%Y-%m-%d')
                        elif article_html.find('div', {'id' : 'publish-date'}) is not None:
                            article_pub_date= article_html.find('div', {'id' : 'publish-date'})
                        else:
                          continue  

                        article_pub_date=article_pub_date.text.split(" ")
                        article_pub_date = article_pub_date[:-2]
                        article_pub_date = " ".join(article_pub_date)
                        article_pub_date= datetime.strptime(article_pub_date, '%B %d, %Y').strftime('%Y-%m-%d')
                        cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,article_pub_date,url,article_title.text,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))    
                        con.commit()
                        cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                        bias_detail_id = cursor.fetchall()[0][0]
                        con.commit()


                        if article_html.find('div', attrs={'class' : 'video-body'}) is not None:
                            article_text = article_html.find('div', attrs={'class' : 'video-body'}).select("p")[0]
                            page_text = article_text.text
                            cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                            con.commit()                          
                        elif article_html.find_all('div', attrs={'id' : 'story-primary'}) is not None:   
                                article_text = article_html.find_all('div', attrs={'id' : 'story-primary'})
                                for text in article_text:
                                    for child in text.children:
                                        if not child.name:
                                                continue
                                        if child.name == 'p':
                                                page_text = child.get_text()
                                                cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                                con.commit() 
                        print("record inserted")
                driver.close()              
            except SocketError as e:
                    if e.errno == errno.ECONNRESET:
                        pass
                    else:
                        pass

    def getmyweekly_data(article_pages,bias_id):
        for article in article_pages:
            if not ((article in article_urls)  or (article in new_urls)):
                new_urls.append(article)
                print(article)
                response = urllib.request.urlopen(article)
                article_html = BeautifulSoup(response, 'html.parser')
                article_title = article_html.find('h1', {'class' : 'mvp-post-title entry-title'})
                article_pub_date = article_html.find('time', {'class' : 'post-date updated'})
                article_pub_date = datetime.strptime((article_pub_date.text), '%B %d, %Y')
                published_date = article_pub_date.strftime('%Y-%m-%d')
                cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,published_date,article,article_title.text,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))
                con.commit() 
                cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                bias_detail_id = cursor.fetchall()[0][0]
                con.commit()
                article_text = article_html.find_all('div', class_='theiaPostSlider_preloadedSlide') 
                for text in article_text:
                    for child in text.children:
                        if not child.name:
                              continue
                        if child.name =='p':
                            page_text = child.get_text()
                            if page_text.strip():
                                cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                con.commit() 
                            #print(page_text)      
                        elif child.name =='div':
                                article_subtext = text.find_all('div', class_='wire-column__preview__text') 
                                for subtext in article_subtext:
                                        if subtext is not None:
                                            page_text= subtext.get_text()
                                            if page_text.strip():
                                                cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                                con.commit()   
                print("record inserted")
    
    def getgcnews_data(article_pages,bias_id):
        for article in article_pages:
            if not ((article in article_urls)  or (article in new_urls)):
                print(article)
                response = urllib.request.urlopen(article)
                article_html = BeautifulSoup(response, 'html.parser')
                article_title = article_html.find('h1', {'class' : 'entry-title'})
                article_pub_date = article_html.find_all('div', {'class' : 'date'})[1].text.strip()
                article_pub_date = datetime.strptime((article_pub_date), '%B %d, %Y')
                published_date = article_pub_date.strftime('%Y-%m-%d')

                cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,published_date,article,article_title.text,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))
                con.commit() 
                cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                bias_detail_id = cursor.fetchall()[0][0]
                con.commit()
                article_text = article_html.find_all('div', class_='entry-content') 
                for text in article_text:
                    for child in text.children:
                        if not child.name:
                              continue
                        if child.name =='p':
                            page_text = child.get_text()
                            if page_text.strip():
                                    cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                    con.commit() 
                print("record inserted")  
    
    #Seniors Today
    def getseniorstoday_data(article_pages,bias_id):
        for article in article_pages:
            if not ((article in article_urls)  or (article in new_urls)):
                print(article)
                response = urllib.request.urlopen(article)
                article_html = BeautifulSoup(response, 'html.parser')
                article_title = article_html.find('h1', {'class' : 'entry-title'})
                article_pub_date = article_html.find('span', {'class' : 'td-post-date'})
                article_pub_date = datetime.strptime((article_pub_date.text), '%d/%m/%Y')
                published_date = article_pub_date.strftime('%Y-%m-%d')
                cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,published_date,article,article_title.text,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))
                con.commit() 
                cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                bias_detail_id = cursor.fetchall()[0][0]
                con.commit()
                article_text = article_html.find_all('div', class_='td-post-content tagdiv-type')
                for text in article_text:
                    for child in text.children:
                        if not child.name:
                              continue
                        if child.name =='p':
                            page_text = child.get_text()
                            if page_text.strip():
                                    cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                    con.commit() 
                print("record inserted")
    def getbisbanetimes_data(article_pages,bias_id):
        for article in article_pages:
            if not ((article in article_urls)  or (article in new_urls)) :
                new_urls.append(article)
                print(article)
                response = urllib.request.urlopen(article)
                article_html = BeautifulSoup(response, 'html.parser')
                if(article_html.find('h1', {'data-testid' : 'headline'})) is not None:
                      article_title = article_html.find('h1', {'data-testid' : 'headline'})
                else:
                      article_title = article_html.find('h1', {'itemprop' : 'headline'})
                article_pub_date = article_html.find('time', {'data-testid' : 'datetime'})
                article_pub_date = article_pub_date["datetime"][:-15]
                cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,article_pub_date,article,article_title.text,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))    
                con.commit()
                cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                bias_detail_id = cursor.fetchall()[0][0]
                con.commit()
                article_text = article_html.find_all('div', {'data-testid' : 'body-content'}) 
                for text in article_text:
                    for child in text.children:
                            if not child.name:
                                  continue
                            if child.name =='p':
                                page_text = child.get_text()
                                cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                con.commit() 
                print("record inserted")                

    def getnews_data(article_pages,bias_id):
            try:  
                for url in article_pages:
                    if url :
                        if not ((url in article_urls)  or (url in new_urls)) :
                            new_urls.append(url)
                            print(url)
                            driver.get(url)
                            time.sleep(10)
                            article_html = BeautifulSoup(driver.page_source, 'html.parser')
                            if  article_html.find('h1', {'id' : 'story-headline'}) is not None:
                                article_title = article_html.find('h1', {'id' : 'story-headline'})
                            else:
                                continue
                            if  article_html.find('div', {'class' : 'date-live'}) is not None:     
                                e = datetime.now()
                                article_pub_date=e.strftime("%B %d, %Y")
                                article_pub_date= datetime.strptime(article_pub_date, '%B %d, %Y').strftime('%Y-%m-%d')
                            elif article_html.find('div', {'id' : 'publish-date'}) is not None:
                                article_pub_date= article_html.find('div', {'id' : 'publish-date'})
                            else:
                              continue    

                            article_pub_date=article_pub_date.text.split(" ")
                            article_pub_date = article_pub_date[:-2]
                            article_pub_date = " ".join(article_pub_date)
                            article_pub_date= datetime.strptime(article_pub_date, '%B %d, %Y').strftime('%Y-%m-%d')
                            cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,article_pub_date,url,article_title.text,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))    
                            con.commit()
                            cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                            bias_detail_id = cursor.fetchall()[0][0]
                            con.commit()
                            if article_html.find_all('div', attrs={'id' : 'story-primary'}) is not None:   
                                    article_text = article_html.find_all('div', attrs={'id' : 'story-primary'})
                                    for text in article_text:
                                        for child in text.children:
                                            if not child.name:
                                                    continue
                                            if child.name == 'p':
                                                    page_text = child.get_text()
                                                    if page_text.strip():
                                                        cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                                        con.commit() 
                            print("record inserted")
            except SocketError as e:
                        if e.errno == errno.ECONNRESET:
                            pass
                        else:
                            pass
    
    def get_ausarticledata(article_pages,bias_id):
        try:  
              for url in article_pages[1:]:
                  if not ((url in article_urls)  or (url in new_urls)) :
                      new_urls.append(url)
                      if ("the-oz" in url) or ("arts" in url) or ("weekend-australian-magazine" in url) or ("sport" in url):
                          continue
                      else:    
                          print(url)
                          driver.get(url)
                          time.sleep(10)
                          article_html = BeautifulSoup(driver.page_source, 'html.parser')
                          if  article_html.find('h1', {'id' : 'story-headline'}) is not None:
                              article_title = article_html.find('h1', {'id' : 'story-headline'})
                          if  article_html.find('time', {'class' : 'date-and-time'}) is not None:  
                                  article_pub_date = article_html.find('time', {'class' : 'date-and-time'})
                                  if(len(article_pub_date) == 24):
                                        article_pub_date = article_pub_date["datetime"][:-14]
                                  else:
                                        article_pub_date = article_pub_date["datetime"].split(" ")
                                        article_pub_date = article_pub_date[1:]
                                        article_pub_date = " ".join(article_pub_date)
                                        article_pub_date= datetime.strptime(article_pub_date, '%B %d, %Y').strftime('%Y-%m-%d')      
                                                                               
                          cursor.execute("INSERT INTO `bias_detail` VALUES (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(bias_id,date,article_pub_date,url,article_title.text,' ',' ',' ',ip_address,email,0,1,'NULL','NULL',0,1,'unset'))    
                          con.commit()
                          cursor.execute(u"select id from bias_detail order by id desc limit 1;")
                          bias_detail_id = cursor.fetchall()[0][0]
                          con.commit()
                          if article_html.find_all('p', attrs={'class' : 'selectionShareable'}) is not None:   
                                  article_text = article_html.find_all('p', attrs={'class' : 'selectionShareable'})[:-1]
                                  for text in article_text:
                                          page_text = text.get_text()
                                          cursor.execute("INSERT INTO `article_sentences` VALUES (default,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,default);",(bias_id,bias_detail_id,page_text,0,0,0.00,0.00,0.00,' ',' ',' ',0.00,0,0,0,'bias_2',0,'unset'))
                                          con.commit() 
                                  print("record inserted")   
                  
        except SocketError as e:
              if e.errno == errno.ECONNRESET:
                    pass
              else:
                    pass
                        

    for  url in focused_search:
                cursor.execute(u"select * from bias_master order by id desc limit 1;")
                bias_id = cursor.fetchall()[0][0]
                cursor.execute(u"select * from bias_master order by id desc limit 1;")
                record = cursor.fetchall()[0][1]
                query = record.replace(" ","+")
                query = "Jason+Hunt"
                print(url[1])
                if url[1] == 'https://search-beta.abc.net.au/#/':
                   continue
                   try:
                        options = webdriver.ChromeOptions()
                        options.add_argument('--ignore-certificate-errors')
                        options.add_argument('--incognito')
                        options.add_argument('--headless')
                        options.add_argument('--no-sandbox')
                        options.add_argument('--window-size=1420,1080')
                        options.add_argument('--disable-gpu')
                        options.add_experimental_option('excludeSwitches', ['enable-automation'])
                        driver = webdriver.Chrome("chromedriver", options=options)
                        driver.get(url[1])
                        time.sleep(5)
                        elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,'//input[@placeholder="Search the ABC"]')))
                        elem.clear()
                        print(query)
                        elem.send_keys(query)                                                                                                                                                                                 
                        elem.submit()
                        time.sleep(5)
                        page_num = 0
                        article_links = []

                        while True :
                            try:
                                WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH,"//button[@data-component='Pagination__Next']")))
                                driver.find_element(by=By.XPATH,value="//button[@data-component='Pagination__Next']").click()
                                time.sleep(5)
                                page_num += 1
                                print("getting page number "+str(page_num))         
                                links = driver.find_elements(by=By.XPATH,value='//div[@data-testid="search-hit-content"]/a')
                                for link in links:
                                     article = link.get_attribute('href')
                                     article_links.append(article)
                            except:
                                print("No more pages")
                                break
                        get_abcdata(article_links,bias_id)        
                               
                   except SocketError as e:
                                if e.errno == errno.ECONNRESET:
                                    pass
                                else:
                                    pass

                elif url[1] == 'https://www.sunshinecoastnews.com.au/':
                    continue
                    try:
                        query2 = url[1]+"?s="+query
                        print(query2)
                        options = webdriver.ChromeOptions()
                        options.add_argument('--ignore-certificate-errors')
                        options.add_argument('--incognito')
                        options.add_argument('--headless')
                        options.add_argument('--no-sandbox')
                        options.add_argument('--window-size=1420,1080')
                        options.add_argument('--disable-gpu')
                        options.add_experimental_option('excludeSwitches', ['enable-automation'])
                        driver = webdriver.Chrome("chromedriver", options=options)
                        driver.get(query2)
                        time.sleep(10)
                        page_num = 0
                        try:
                              while (True and page_num !=20) :
                                        WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR,".td-load-more-wrap")))
                                        nextpage=driver.find_element(by=By.XPATH,value="//div[@class='td-load-more-wrap']/a")
                                        classname= nextpage.get_attribute("class")
                                        if "disabled" in classname:
                                            print("No more pages")
                                            break
                                        else:
                                            driver.find_element(by=By.CSS_SELECTOR,value=".td-load-more-wrap").click()
                                            page_num += 1
                                            print("getting page number "+str(page_num))
                                            time.sleep(4)
                                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                                            article_pages = []
                                            [article_pages.append(x['href']) for x in soup.select('div.td-module-meta-info h3 > a')]
                              get_sunshinedata(article_pages,bias_id)        
                              driver.close() 
                        except TimeoutException as e:  
                                pass
                                 
                    except SocketError as e:
                            if e.errno == errno.ECONNRESET:
                                pass
                            else:
                                pass
                #Couriermail         
                
                elif url[1] == 'https://www.couriermail.com.au/':
                    continue
                    query = query.replace("+"," ")
                    options = webdriver.ChromeOptions()
                    options.add_argument("start-maximized")
                    options.add_argument('--no-sandbox')
                    options.add_argument('--headless')
                    options.add_argument('--window-size=1420,1080')
                    options.add_argument('--disable-gpu')
                    # Chrome is controlled by automated test software
                    options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    options.add_experimental_option('useAutomationExtension', False)         
                    driver = webdriver.Chrome("chromedriver", options=options)

                    # Selenium Steialth settings
                    stealth(driver,
                          languages=["en-US", "en"],
                          vendor="Google Inc.",
                          platform="Win32",
                          webgl_vendor="Intel Inc.",
                          renderer="Intel Iris OpenGL Engine",
                          fix_hairline=True,
                      )
                       
                    driver.get(url[1])   
                    time.sleep(10)
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/header/div[2]/div[1]/a[2]"))).click()
                    # login 
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[id='1-email']"))).send_keys("ben.goudie.park@gmail.com")
                    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("hjBVs&8$111")
                    login = driver.find_element(by=By.NAME,value='submit')
                    login.click();
                    time.sleep(5)
                    # sending in search phrase
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@class='navigation']//button[@name='Search']"))).click()
                    input_text = driver.find_element(by=By.XPATH, value="//form[contains(@class, 'navigation_search')]//input")
                    
                    input_text.send_keys(query)
                    print(input_text.get_attribute('value'))
                    time.sleep(2)
                    driver.find_element(By.XPATH, "//*[@class='navigation']//button[@name='Search']").click()
                    time.sleep(5)
                    input_text = driver.find_element(by=By.XPATH, value="//form[contains(@class, 'navigation_search')]//input")
                    input_text.clear()
                    input_text.send_keys(query)
                    driver.find_element(By.XPATH, "//*[@class='navigation']//button[@name='Search']").click()
                    time.sleep(10)
                    
                    all_articles = driver.find_elements(By.XPATH, "//*[@class='storyblock_title']/a")
                    article_headers = [article.get_attribute('href') for article in all_articles]
       
                  
                    # All articles scraping
                    page_num = 0
                    while ((WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.XPATH,"//li[@class= 'ais-Pagination-item ais-Pagination-item--nextPage']")))) and page_num != 25):
                        driver.find_element(by=By.XPATH,value="//li[@class= 'ais-Pagination-item ais-Pagination-item--nextPage']").click()
                        page_num += 1
                        print("getting page number "+str(page_num))
                        time.sleep(10)
                        all_articles = driver.find_elements(By.XPATH, "//*[@class='storyblock_title']/a")
                        article_headers += [article.get_attribute('href') for article in all_articles]
                    getcouriermail_data(article_headers, bias_id)
                
                elif url[1] == 'https://www.myweeklypreview.com.au/':
                    continue
                    query2 = url[1]+"?s="+query
                    print(query2)
                    response = urllib.request.urlopen(query2)
                    article_html = BeautifulSoup(response, 'html.parser')
                    article_pages = []
                    [article_pages.append(x.find('a').get('href')) for x in article_html.find_all('div', attrs={'class' : 'mvp-blog-col-text left relative'})]
                    getmyweekly_data(article_pages,bias_id)

                elif url[1] == 'https://gcnews.com.au/':
                    continue
                    page_num = 1
                    article_pages = []
                    print(url[1]+'/'+ query)
                    while True:
                        url = "https://gcnews.com.au/page/"+format(page_num)+"/?s="+query
                        #print(url)
                        response = requests.get(url)
                        article_html = BeautifulSoup(response.content, 'html.parser')
                        if response.status_code == 404: # break once the page is not found
                            break
                        if article_html.find('header', attrs={'class' : 'entry-header'}).text.strip() == "Nothing Found":
                            print("No Result Found")
                            break
                        else:  
                            [article_pages.append(x.find('a').get('href')) for x in article_html.find_all('header', attrs={'class' : 'entry-header'})]
                            print("getting page number {}".format(page_num))
                            page_num += 1
                    getgcnews_data(article_pages,bias_id)

                elif url[1] == 'https://seniorstoday.com.au/':
                    continue
                    page_num = 1
                    article_pages = []
                    print(url[1]+'/'+ query)

                    while True :
                        url = 'https://seniorstoday.com.au/page/'+format(page_num)+'/?s='+query
                        response = requests.get(url)
                        article_html = BeautifulSoup(response.content, 'html.parser')
                        if response.status_code == 404: 
                            break
                        if article_html.find('div', attrs={'class' : 'no-results td-pb-padding-side'}) is not None:
                            if article_html.find('div', attrs={'class' : 'no-results td-pb-padding-side'}).text.strip() == "No results for your search":
                                print("No Result Found")
                                break      
                        [article_pages.append(x.find('a').get('href')) for x in article_html.find_all('div', attrs={'class' : 'item-details'})]
                        print("getting page number {}".format(page_num))
                        page_num += 1  
                    getseniorstoday_data(article_pages,bias_id)

                elif url[1] == 'https://www.brisbanetimes.com.au/':
                    continue
                    query = query.replace("+"," ")
                    print(query)
                    options = webdriver.ChromeOptions()
                    prefs = {"profile.managed_default_content_settings.images": 2}
                    options.add_experimental_option("prefs", prefs)
                    options.add_argument('--ignore-certificate-errors')
                    options.add_argument('--incognito')
                    options.add_argument('--headless')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--window-size=1420,1080')
                    options.add_argument('--disable-gpu')
                    options.add_experimental_option('excludeSwitches', ['enable-automation'])
                    driver = webdriver.Chrome("chromedriver", options=options)
                    driver.get(url[1])
                    time.sleep(5)
                    elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="sections"]'))).click()
                    elem = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="site-search"]')))
                    elem.send_keys(query)
                    elem.submit()

                    article_pages = []
                    page_num =0
                    try:
                        while ((WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.XPATH,'//button[@data-testid="show-more-button"]'))))):    
                                driver.find_element(by=By.XPATH,value='//button[@data-testid="show-more-button"]').click()
                                page_num += 1
                                print("getting page number "+str(page_num))
                                all_articles = WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, '//*[@id="content"]//h3[@data-testid="article-headline"]/a')))
                                article_pages += [article.get_attribute('href') for article in all_articles]

                    except TimeoutException as e:  
                                print("No more pages")
                                pass
                    urls_list = list(dict.fromkeys(article_pages))
                    getbisbanetimes_data(urls_list,bias_id)
      

                elif url[1] == 'https://news.com.au/':
                      continue
                      query = query.replace("+"," ")
                      options = webdriver.ChromeOptions()
                      options.add_argument("start-maximized")
                      options.add_argument('--no-sandbox')
                      options.add_argument('--headless')
                      options.add_argument('--window-size=1420,1080')
                      options.add_argument('--disable-gpu')
                      # Chrome is controlled by automated test software
                      options.add_experimental_option("excludeSwitches", ["enable-automation"])
                      options.add_experimental_option('useAutomationExtension', False)         
                      driver = webdriver.Chrome("chromedriver", options=options)

                      # Selenium Steialth settings
                      stealth(driver,
                            languages=["en-US", "en"],
                            vendor="Google Inc.",
                            platform="Win32",
                            webgl_vendor="Intel Inc.",
                            renderer="Intel Iris OpenGL Engine",
                            fix_hairline=True,
                        )
                        
                      driver.get(url[1])   
                      time.sleep(10)
                      WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//a[@class="header_log-in"]'))).click()
                      # login 
                      WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[id='1-email']"))).send_keys("ben.goudie.park@gmail.com")
                      driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("hjBVs&8$111")
                      login = driver.find_element(by=By.NAME,value='submit')
                      login.click();
                      time.sleep(5)
                      # sending in search phrase
                      WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@class='navigation']//button[@name='Search']"))).click()
                      input_text = driver.find_element(by=By.XPATH, value="//form[contains(@class, 'navigation_search')]//input")
                      input_text.send_keys(query)
                      print(input_text.get_attribute('value'))
                      time.sleep(2)
                      driver.find_element(By.XPATH, "//*[@class='navigation']//button[@name='Search']").click()
                      time.sleep(5)
                      input_text = driver.find_element(by=By.XPATH, value="//form[contains(@class, 'navigation_search')]//input")
                      input_text.clear()
                      input_text.send_keys(query)
                      driver.find_element(By.XPATH, "//*[@class='navigation']//button[@name='Search']").click()
                      time.sleep(10)
                      article_pages = []
                      
                      all_articles = driver.find_elements(By.XPATH, "//*[@class='storyblock']//h4[@class='storyblock_title']/a")
                      article_pages += [article.get_attribute('href') for article in all_articles]
                      
                      page_num = 0
                      while (WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.XPATH,"//li[@class= 'ais-Pagination-item ais-Pagination-item--nextPage']"))) and page_num != 15 ):
                          driver.find_element(by=By.XPATH,value="//li[@class= 'ais-Pagination-item ais-Pagination-item--nextPage']").click()
                          page_num += 1
                          print("getting page number "+str(page_num))
                          time.sleep(10)
                          all_articles = driver.find_elements(By.XPATH, "//*[@class='storyblock']//h4[@class='storyblock_title']/a")
                          article_pages += [article.get_attribute('href') for article in all_articles]

                      getnews_data(article_pages,bias_id)
                      driver.close()  
                
                elif url[1] == 'https://www.theaustralian.com.au/':
                    
                      query = query.replace("+"," ")
                      print(query)
                      options = Options()
                      prefs = {"credentials_enable_service": False,
                          "profile.password_manager_enabled": False,
                            "profile.managed_default_content_settings.images": 2  
                              }

                      options.add_experimental_option("prefs", prefs)
                      options.add_argument("start-maximized")
                      options.add_argument('--no-sandbox')
                      options.add_argument('--headless')
                      options.add_argument('--window-size=1420,1080')
                      options.add_argument('--disable-gpu')
                      # Chrome is controlled by automated test software
                      options.add_experimental_option("excludeSwitches", ["enable-automation"])
                      options.add_experimental_option('useAutomationExtension', False)         


                      webdriver_service = Service('chromedriver')
                      driver = webdriver.Chrome(options=options, service=webdriver_service)
                      wait = WebDriverWait(driver, 20)

                      stealth(driver,
                              languages=["en-US", "en"],
                              vendor="Google Inc.",
                              platform="Win32",
                              webgl_vendor="Intel Inc.",
                              renderer="Intel Iris OpenGL Engine",
                              fix_hairline=True,)
                      driver.get(url[1])
                      time.sleep(10)
                      WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header"]/div[2]/div[1]/div/div[3]/div/div[1]/a[2]'))).click()
                      # login 
                      WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[id='1-email']"))).send_keys("ben.goudie.park@gmail.com")
                      driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("hjBVs&8$111")
                      login = driver.find_element(by=By.NAME,value='submit')
                      login.click();
                      time.sleep(20)
                      text_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".header__search #search__input")))
                      text_input.click()
                      text_input.send_keys(query + Keys.ENTER)
                      time.sleep(10)
                      text_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".header__search #search__input")))
                      text_input.clear()
                      text_input.click()
                      text_input.send_keys(query + Keys.ENTER)
                      time.sleep(20)

                      article_pages = []    
                      page_num = 0
                      while (WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="algolia-pagination"]//a[@class="page-numbers next"]'))) and page_num != 5):
                          driver.find_element(by=By.XPATH,value='//*[@id="algolia-pagination"]//a[@class="page-numbers next"]').click()
                          page_num += 1
                          print("getting page number "+str(page_num))
                          time.sleep(10)
                          all_articles = driver.find_elements(By.XPATH, '//h3[@class="story-block__heading"]//a')
                          article_pages += [article.get_attribute('href') for article in all_articles[1:]]                      
                      get_ausarticledata(article_pages,bias_id)
                      driver.close()  


             

    
    
                                                                      
con.close()
