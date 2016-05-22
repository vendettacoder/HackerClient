# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 17:20:34 2016

@author: Rohan Kulkarni
@email : rohan.kulkarni@columbia.edu

"""

from __future__ import print_function
import sys

from flask import Flask,render_template
from mechanize import Browser
from goose import Goose
from multiprocessing import Pool,cpu_count
import math
import praw
from espncricinfo.summary import Summary
from bs4 import BeautifulSoup
from urllib import urlopen


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
            print(tup,file=sys.stderr)

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
        print(url, file=sys.stderr)
        browser.back()
        return (url,article.title,article.cleaned_text[:500])
    except:
        return None

def extract_reddit_link(x):
    return {'title':x.title,'url':x.url,'text':goose.extract(url=x.url).cleaned_text[:500]+'...'}
        
class AppStatus():
    def __init__(self,page_number):
        self.current_page=page_number
        
@app.route('/')
def loadInitialResults():
    hn.get_links()
    hn.strip_inlinks()
    numProc = cpu_count()*2
    pool = Pool(processes=numProc)
    initial_res = pool.map(extract_link,hn.news_links[:25])
    result = [x for x in initial_res if x is not None]
    news = [{'title':x[1],'url':x[0],'text':x[2]+'...'} for x in result]
    obj = dict()
    obj['link_data'] = news
    obj['num_pages'] = range(2,int(math.ceil((float(len(result))/10.0)+1)))
    return render_template('homepage.html',returnObj=obj)

@app.route('/reddit_page/')
def loadRedditResults():
    reddit = praw.Reddit(user_agent='rohan_news_client')
    submissions = reddit.get_subreddit('worldnews').get_hot(limit=15)
    numProc = cpu_count()*2
    pool = Pool(processes=numProc)
    news = pool.map(extract_reddit_link,submissions)
    obj = dict()
    obj['link_data'] = news
    obj['num_pages'] = range(2,int(math.ceil((float(len(news))/10.0)+1)))
    return render_template('homepage.html',returnObj=obj)

@app.route('/live_cricket/')
def loadCricketResults():
    s = Summary()
    obj = dict()
    match_list = list()
    for match in s.all_matches:
        match_list.append(match)
    grouped_list = [match_list[i:i+4] for i in range(0, len(match_list), 4)]
    obj['match_data'] = grouped_list
    return render_template('cricketpage.html',returnObj = obj)

@app.route('/live_football/') 
def loadFootballResults():
    football_page = urlopen("http://www.livescores.com").read()
    football_soup=BeautifulSoup(football_page,'lxml')
    teams = set(map(lambda x:x.lower(),["Arsenal","Chelsea","Liverpool","Manchester City","Manchester United","Tottenham","Napoli","Juventus","Inter","AC Milan","Barcelona","Athletico Madrid","Real Madrid","Bayern Munich","Borussia Dortmund","Bayer Leverkusen","Monaco","Paris Saint Germain","Marseille","Spain","Germany","Argentina","Colombia","Belgium","Uruguay","Switzerland","Netherlands","Italy","England","Brazil","Chile","United States","Portugal","Greece","Bosnia and Herzegovina","Ivory Coast","Croatia","Russia","Ukraine","Cote d'Ivoire"]))
    match_list = list()
    obj = dict()
    for data in football_soup.findAll('div',class_="row-gray"):
        data_string = data.text.strip()
        if any(team.lower() in data_string.lower() for team in teams):
            match_list.append(data_string)
    grouped_list = [match_list[i:i+4] for i in range(0, len(match_list), 4)]
    obj['match_data'] = grouped_list
    return render_template('footballpage.html',returnObj = obj)
    

if __name__ == '__main__':
    app.debug = True
    app.run(host='localhost',port=8078)