from rx import Observable
from rx.core import Scheduler
from rx.concurrency import ThreadPoolScheduler
import re
import requests
from threading import current_thread
import multiprocessing
from datetime import datetime
from pyquery import PyQuery as pq
from config import USERNAME, PASSWORD, DB_HOST, DB_PORT, FORUM_IDS, YEARS, FORUM_URL
from entities import Post, User, Forum, Thread

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
    Post.init("posts")
  except Exception as e:
    print(e)

def run2():
  s = requests.Session()
  r = s.post(f"{FORUM_URL}/account.php", data={
    "action": "login",
    "next": "/",
    "username": USERNAME,
    "password": PASSWORD
  })
  if "TEMPORARY LOCKOUT!" in r.text:
    print("Too many wrong logins...")
    exit(0)
  elif """<div id="notregistered">""" in r.text:
    print(r.text)
    print("Login failed")
    exit(0)
  def on_complete():
    print(f"Done! {current_thread().name}")
  def on_error(e):
    print(f"Error! {e} {current_thread().name}")
  def on_next(_):
    pass
  def get_page_urls_from_forum(s_, a):
    year, f_id = a
    url = f"{FORUM_URL}/forumdisplay.php?forumid={f_id}"
    if year == 2018:
      resp = s_.post(url, data={"rem": "Remove", "ac_year": year, "ac_day": "", "ac_month": ""})
    else:
      resp = s_.post(url, data={"set": "GO", "ac_year": year, "ac_day": "", "ac_month": ""})
    d = pq(resp.text)
    if """<div id="notregistered">""" in resp.text:
      print("Login failed")
      exit(0)
      s_.post(url, data={"rem": "Remove", "ac_year": year, "ac_day": "", "ac_month": ""})
    pages = d.find(".pages a[title=\"Last page\"]").text()
    pages = re.match("(\d+)", pages)
    i = int(pages.group(1)) if pages else 1
    if i == 1:
      with open("log.html", "wb") as f:
        f.write(resp.content)
    return list(map(lambda z: (s_, f"{url}&pagenumber={z}", f_id, year), range(1,i)))
  def get_threads_from_page(s_, a):
    s_, url, f_id, year = a
    resp = s.post(url, data={"ac_year": year})
    d2 = pq(resp.text)
    threads = []
    for h in d2.find(".thread_title"):
      t_id = int(re.search("threadid=(\d+)", h.get("href")).group(1))
      threads += [(f_id, t_id, year)]
    return threads
  def get_page_urls_from_thread(s_, x):
    f_id, t_id, year = x
    u = f"{FORUM_URL}/showthread.php?threadid={t_id}"
    resp_ = s_.get(u)
    d = pq(resp_.text)
    pages = d.find(".pages a[title=\"Last page\"]").text()
    pages = re.match("(\d+)", pages)
    i = int(pages.group(1)) if pages else 1
    return list(map(lambda z: (f"{u}&pagenumber={z}", f_id, t_id, year), range(1, i)))
  def get_posts(s_, g):
    url, forum_id, t_id, year = g
    if year == 2018:
      resp = s_.post(url, data={"rem": "Remove", "ac_year": year, "ac_day": "", "ac_month": ""})
    else:
      resp = s_.post(url, data={"set": "GO", "ac_year": year, "ac_day": "", "ac_month": ""})
    d = pq(resp.text)
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

  scheduler = ThreadPoolScheduler(multiprocessing.cpu_count())
  scheduler2 = ThreadPoolScheduler(multiprocessing.cpu_count())
  scheduler3 = ThreadPoolScheduler(multiprocessing.cpu_count())
  scheduler4 = ThreadPoolScheduler(multiprocessing.cpu_count())

  forumids = Observable.from_([1, 25, 26, 154, 273, 21])
  years = Observable.from_(range(2017, 2019))

  forumids \
    .flat_map(lambda g: years.map(lambda h: (h, g))) \
    .flat_map(lambda z: Observable.just(z, scheduler).flat_map(lambda a: get_page_urls_from_forum(s, a))) \
    .flat_map(lambda z: Observable.just(z, scheduler2).flat_map(lambda a: get_threads_from_page(s, a))) \
    .flat_map(lambda z: Observable.just(z, scheduler3).flat_map(lambda a: get_page_urls_from_thread(s, a))) \
    .flat_map(lambda z: Observable.just(z, scheduler4).flat_map(lambda a: get_posts(s, a))) \
    .subscribe(on_next=on_next,
               on_error=on_error,
               on_completed=on_complete)
  scheduler.executor.shutdown()
  scheduler2.executor.shutdown()
  scheduler3.executor.shutdown()
  scheduler4.executor.shutdown()

if __name__ == '__main__':
  print("Starting spider...")
  run2()