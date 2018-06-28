from sanic import Sanic
from sanic.response import json
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search as S, Q, SF
from pyquery import PyQuery as pq
from config import DB_HOST, DB_PORT

es = Elasticsearch([f"http://{DB_HOST}:{DB_PORT}"], timeout=60)
app = Sanic()

#todo: most quoted posts

@app.route('/search',  methods=['POST'])
async def search(request):
  try:
    args = request.json["query"]
    args = args.split(" ")
  except KeyError as e:
    return json({"response": "Bad query"})
  s = S(using=es, index="posts")
  for arg in [a for a in args if ":" in a]:
    k, v = arg.split(":")[0], arg.split(":")[1]
    if k in ["user_id", "thread_id"]:
      d = {k: v}
      s = s.query("match", **d)
  g = " ".join([a for a in args if ":" not in a])
  qs = Q('match_phrase', post_body=g)
  s = s.query(qs)
  s = s.sort('post_date')[0:100]
  resp = s.execute()
  z = []
  print(args)
  for hit in resp:
    print(hit)
    d = pq(hit.post_body)
    z += [{
      "post_id": hit.meta.id,
      "user_id": hit.user_id,
      "post_date": hit.post_date,
      "post_body": d.text(),
    }]
  return json({"response": z})

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000)