# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 17:20:34 2016

@author: Rohan Kulkarni
@email : rohan.kulkarni@columbia.edu

"""


from flask import Flask,render_template
from mechanize import Browser
from goose import Goose
from multiprocessing import Pool,cpu_count
import math


app = Flask(__name__,static_url_path='/static')


class HackerNews():
    def __init__(self,browser,goose):
        self.browser_obj = browser
        self.browser_obj.set_handle_robots(False)
        self.browser_obj.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        self.browser_obj.open('https://news.ycombinator.com/')
        self.text_map = list()
        self.goose = goose
    
    def set_filters(self,filter_words):
        self.filters = filter_words
        
    def get_links(self):
        landing_page_links = list()
        for link in self.browser_obj.links(url_regex="^http{1}"):
            landing_page_links.append(link)
        self.news_links = landing_page_links
        
    def strip_inlinks(self):
        self.news_links=self.news_links[1:-2]
   
    def print_textmap(self):
        for i,tup in enumerate(self.text_map):
            print tup

browser = Browser()
goose = Goose()
hn = HackerNews(browser,goose) 

def extract_link(link):
    global hn
    global browser
    global goose
    try:
        browser.follow_link(link)
        url = browser.geturl()
        article = goose.extract(url=url)
        browser.back()
        return (url,article.title,article.cleaned_text[:500])
    except:
        return None
      
@app.route('/')
def loadInitialResults():
    filter_words = ['python','Ocaml','Linux']
    filter_words = map(lambda x:x.lower(), filter_words)
    
    hn.set_filters(filter_words)
    hn.get_links()
    hn.strip_inlinks()
    numProc = cpu_count()*2
    pool = Pool(processes=numProc)
    initial_res = pool.map(extract_link,hn.news_links)
    result = [x for x in initial_res if x is not None]
    news = [{'title':x[1],'url':x[0],'text':x[2]+'...'} for x in result]
    obj=dict()
    obj['link_data'] = news
    obj['num_pages'] = range(2,int(math.ceil((float(len(result))/10.0)+1)))
    return render_template('homepage.html',returnObj=obj)

@app.route('/next_page')
def loadNewPage():
    pass

if __name__ == '__main__':
    app.debug = True
    app.run(host='localhost',port=8086)