from config import DB_HOST, DB_PORT
from pyquery import PyQuery as pq
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, Keyword, Text, Integer

from elasticsearch_dsl import connections
connections.create_connection(hosts=[f"{DB_HOST}"])

html_strip = analyzer('html_strip',
    tokenizer="standard",
    filter=["standard", "lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)


class User(DocType):
  user_name = Keyword()
  user_id = Integer()
  reg_date = Date()

  @staticmethod
  def insert(user_id, user_name, reg_date):
    #todo: posts, posts_counted, profile_text, avatar, last_post, contact_info, rapsheet, banned, probated, cancerous
    u = User(meta={'id':user_id}, user_id=user_id, user_name=user_name, reg_date=reg_date)
    u.save(index="users")
    return u

class Post(DocType):
  post_body = Text(
        analyzer=html_strip,
        fields={'raw': Keyword()}
  )
  user_id = Integer()
  thread_id = Integer()
  post_date = Date()

  @staticmethod
  def insert(post_id, user_id, post_body, thread_id, post_date, is_edited=False, quoting=[None]):
    p = Post(meta={'id':post_id}, user_id=user_id, post_body=post_body, thread_id=thread_id, post_date=post_date)
    p.save(index="posts")
    return p

  def __str__(self):
    d = pq(self.post_body)
    t = d.text() if d.text() else self.post_body
    return f"\n" \
           f"{('#'*20)}" \
           f"UserID: {self.user_id}" \
           f"ThreadID: {self.thread_id}" \
           f"\n" \
           f"{t}" \
           f"\n" \
           f"{('#'*20)}"

class Thread(DocType):
  title = Text()
  user_id = Integer()
  post_id = Integer()
  forum_id = Integer()
  post_body = Text(
        analyzer=html_strip,
        fields={'raw': Keyword()}
  )
  post_date = Date()

  def __str__(self):
    d = pq(self.post_body)
    t = d.text() if d.text() else self.post_body
    return f"\n" \
           f"{('#'*20)}" \
           f"Thread: {self.title}" \
           f"Id: {self.thread_id}" \
           f"By: {self.user_id}" \
           f"\n" \
           f"{('#'*20)}"

  @staticmethod
  def insert(thread_id, title, user_id, post_id, post_date, post_body, forum_id):
    #todo: replies, views, rating, icon, forumid, postdate, is_edited, quoting
    t = Thread(
      meta={'id':thread_id},
      title=title,
      user_id=user_id,
      post_date=post_date,
      post_id=post_id,
      post_body=post_body,
      forum_id=forum_id
    )
    t.save(index="threads")
    return t

class Forum:
  def __init__(self, forum_id, title, thread_ids):
    pass