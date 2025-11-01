from rq import Worker, Queue, Connection
from redis import Redis

listen = ['default']
conn = Redis(host="redis", port=6379)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()