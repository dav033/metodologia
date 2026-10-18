import sqlite3
from contextlib import closing, contextmanager

_JOBS = ("CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,payload TEXT NOT NULL,"
         "state TEXT NOT NULL DEFAULT 'pending',token INTEGER NOT NULL DEFAULT 0,"
         "lease_until INTEGER,attempts INTEGER NOT NULL DEFAULT 0,depends_on TEXT,result TEXT)")
_OUTBOX = ("CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY,body TEXT NOT NULL,"
           "delivered INTEGER NOT NULL DEFAULT 0)")
_INBOX = "CREATE TABLE IF NOT EXISTS inbox(id TEXT PRIMARY KEY,body TEXT NOT NULL)"


def _connect(path):
    c = sqlite3.connect(path, timeout=60, isolation_level=None)
    c.execute("PRAGMA busy_timeout=60000")
    return c


@contextmanager
def _tx(path):
    """Connection with an IMMEDIATE write transaction; commit on success, rollback on error."""
    with closing(_connect(path)) as c:
        c.execute("BEGIN IMMEDIATE")
        try:
            yield c
        except BaseException:
            c.execute("ROLLBACK")
            raise
        c.execute("COMMIT")


def init(path):
    with _tx(path) as c:
        for ddl in (_JOBS, _OUTBOX, _INBOX):
            c.execute(ddl)


def enqueue(path, id, payload, depends_on=None):
    with _tx(path) as c:
        c.execute("INSERT OR IGNORE INTO jobs(id,payload,depends_on) VALUES(?,?,?)",
                  (id, payload, depends_on))


def claim(path, now, ttl):
    if ttl <= 0:
        raise ValueError("ttl must be positive")
    with _tx(path) as c:
        row = c.execute(
            "SELECT j.id,j.payload FROM jobs j WHERE "
            "(j.state='pending' OR (j.state='running' AND j.lease_until<=?)) AND "
            "(j.depends_on IS NULL OR EXISTS(SELECT 1 FROM jobs p WHERE p.id=j.depends_on AND p.state='done')) "
            "ORDER BY j.id LIMIT 1", (now,)).fetchone()
        if row is None:
            return None
        c.execute("UPDATE jobs SET state='running',lease_until=?,attempts=attempts+1,"
                  "token=token+1 WHERE id=?", (now + ttl, row[0]))
        token = c.execute("SELECT token FROM jobs WHERE id=?", (row[0],)).fetchone()[0]
        return (row[0], row[1], token)


_VALID = "id=? AND state='running' AND token=? AND lease_until>?"


def complete(path, id, token, result, now, fault=None):
    with _tx(path) as c:
        if c.execute("SELECT 1 FROM jobs WHERE " + _VALID, (id, token, now)).fetchone() is None:
            return False
        c.execute("UPDATE jobs SET state='done',result=?,lease_until=NULL WHERE id=?", (result, id))
        if fault:
            fault('after_result')
        c.execute("INSERT INTO outbox(id,body) VALUES(?,?)", (id, result))
        if fault:
            fault('before_commit')
        return True


def inspect(path, id):
    with closing(_connect(path)) as c:
        c.row_factory = sqlite3.Row
        r = c.execute("SELECT * FROM jobs WHERE id=?", (id,)).fetchone()
        return dict(r) if r else None


def retry(path, id, token, now):
    with _tx(path) as c:
        cur = c.execute("UPDATE jobs SET state='pending',lease_until=NULL WHERE " + _VALID,
                        (id, token, now))
        return cur.rowcount == 1


def publish(path, deliver):
    count = 0
    last = None
    while True:
        # Read the next row and release the connection before calling back.
        with closing(_connect(path)) as c:
            row = c.execute(
                "SELECT id,body FROM outbox WHERE delivered=0 AND (? IS NULL OR id>?) "
                "ORDER BY id LIMIT 1", (last, last)).fetchone()
        if row is None:
            return count
        deliver(row[0], row[1])
        with _tx(path) as c:
            c.execute("UPDATE outbox SET delivered=1 WHERE id=?", (row[0],))
        last = row[0]
        count += 1


def consume(path, id, body):
    with _tx(path) as c:
        return c.execute("INSERT OR IGNORE INTO inbox(id,body) VALUES(?,?)", (id, body)).rowcount == 1
