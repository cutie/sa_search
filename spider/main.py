import random
from rx import Observable
from rx.core import Scheduler
from rx.concurrency import ThreadPoolScheduler
import re
import requests
from datetime import datetime
from pyquery import PyQuery as pq
from config import USERNAME, PASSWORD
from config import DB_HOST, DB_PORT
from config import FORUM_IDS, YEARS, FORUM_URL
from entities import Post, User, Forum, Thread

from elasticsearch_dsl import connections
connections.create_connection(hosts=[f"{DB_HOST}:{DB_PORT}"], timeout=60)

"""
goals: 
most empty quoted(?)
most linked threads(?)
imitate stuff from posting gloryhole


intitle:"dog breath" userid:41043 grap
"police explosion" since:"last monday" before:"2 days ago"
threadid:4987552 quoting:Lowtax username:"Toxic Dude" tree


"""

def init():
  try:
    Post.init("saforums")
  except Exception as e:
    print(e)

def get_page_number(html) -> int:
  d = pq(html)
  pages = d.find(".pages a[title=\"Last page\"]").text()
  pages = re.match("(\d+)", pages)
  return int(pages.group(1)) if pages else 1

user_cache = {}
def handle_posts(html, t_id):
  d = pq(html)
  found_posts = []
  z = d.find(".post")
  for h in z:
    post_id = int(re.match("post(\d+)", d(h).attr("id")).group(1))
    user_id = int(re.search("userid-(\d+)", d(h).find(".userinfo").attr("class")).group(1))
    post_body = d(h).find(".postbody").html()
    fail = ["<!-- google_ad_section_start -->", "<!-- google_ad_section_end -->"]
    for f in fail:
      post_body = post_body.replace(f, "")
    post_date_str = d(h).find(".postdate").text().replace("#", "").replace("?", "").strip()
    post_date = datetime.strptime(post_date_str, '%b %d, %Y %H:%M')
    p = Post.insert(post_id, user_id, post_body, t_id, post_date)
    found_posts += [p]
  return found_posts

def run():
  s = requests.Session()
  s.post(f"{FORUM_URL}/account.php", data={
    "action": "login",
    "next": "/",
    "password": PASSWORD,
    "username": USERNAME,
  })

  init()

  threads = []
  c = 0
  for f_id in FORUM_IDS.keys():
    for year in range(2017,2019):
      url = f"{FORUM_URL}/forumdisplay.php?forumid={f_id}"
      if year == 2018:
        resp = s.post(url, data={"rem": "Remove", "ac_year": year, "ac_day": "", "ac_month": ""})
      else:
        resp = s.post(url, data={"set": "GO", "ac_year": year, "ac_day": "", "ac_month": ""})
      #reset
      s.post(url, data={"rem": "Remove", "ac_year": year, "ac_day": "", "ac_month": ""})
      pages = get_page_number(resp.text)
      print(f"Forum ID {f_id} in {year} has {pages} pages")
      for page_num in range(1,10):
        print(f"Forum: {f_id} | Page {page_num}/{pages}")
        url = f"{FORUM_URL}/forumdisplay.php?forumid={f_id}&pagenumber={page_num}"
        resp = s.post(url, data={"ac_year": year})
        d2 = pq(resp.text)
        for h in d2.find(".thread_title"):
          t_id = int(re.search("threadid=(\d+)", h.get("href")).group(1))
          c += 1
          threads += [(c, f_id, t_id)]
  scheduler = ThreadPoolScheduler(25)
  def work(x):
    i, f_id_, t_id_ = x
    resp_ = s.get(f"{FORUM_URL}/showthread.php?threadid={t_id_}")
    pages_ = get_page_number(resp_.text)
    print(f"Forum: {f_id_}  Thread:{t_id_}")
    print(f"{i}/{len(threads)}")
    for page_num_ in range(1, pages_+1):
      resp2 = s.get(f"{FORUM_URL}/showthread.php?threadid={t_id_}&pagenumber={page_num_}")
      handle_posts(resp2.text, t_id_)

  def printthread(val):
    pass
    #print("{}, thread: {}".format(val, current_thread().name))

  Observable.from_(threads) \
    .select_many(lambda i: Observable.start(lambda: work(i), scheduler=scheduler)) \
    .observe_on(Scheduler.event_loop) \
    .subscribe(
    on_next=lambda x: printthread("on_next: {}".format(x)),
    on_completed=lambda: printthread("on_completed"),
    on_error=lambda err: printthread("on_error: {}".format(err)))

  printthread("\nAll done")
  scheduler.executor.shutdown()


if __name__ == '__main__':
  #print("Pretending to run Spider")
  #print(USERNAME, PASSWORD)
  run()