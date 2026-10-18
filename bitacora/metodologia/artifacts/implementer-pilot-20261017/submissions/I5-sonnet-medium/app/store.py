import contextlib
import sqlite3

def init(path):
    with _tx(path) as c:
        c.execute("CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,payload TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending',token INTEGER NOT NULL DEFAULT 0,lease_until INTEGER,attempts INTEGER NOT NULL DEFAULT 0,depends_on TEXT,result TEXT)")
def enqueue(path,id,payload,depends_on=None):
    with _tx(path) as c:c.execute('INSERT OR IGNORE INTO jobs(id,payload,depends_on) VALUES(?,?,?)',(id,payload,depends_on))
@contextlib.contextmanager
def _conn(path):
    c=sqlite3.connect(path,timeout=30,isolation_level=None)
    try:
        yield c
    finally:
        c.close()
@contextlib.contextmanager
def _tx(path):
    """BEGIN IMMEDIATE transaction: serializes writers; commits on success, rolls back on error."""
    with _conn(path) as c:
        c.execute('BEGIN IMMEDIATE')
        try:
            yield c
        except BaseException:
            c.execute('ROLLBACK')
            raise
        c.execute('COMMIT')
def claim(path,now,ttl):
    if ttl<=0:raise ValueError('ttl must be positive')
    with _tx(path) as c:
        r=c.execute("SELECT id,payload,token FROM jobs WHERE state='pending' OR (state='running' AND lease_until<=?) ORDER BY id LIMIT 1",(now,)).fetchone()
        if r is None:return None
        t=r[2]+1
        c.execute("UPDATE jobs SET state='running',token=?,lease_until=?,attempts=attempts+1 WHERE id=?",(t,now+ttl,r[0]))
        return (r[0],r[1],t)
def complete(path,id,token,result,now,fault=None):
    with _tx(path) as c:
        cur=c.execute("UPDATE jobs SET state='done',result=?,lease_until=NULL WHERE id=? AND state='running' AND token=? AND lease_until>?",(result,id,token,now))
        if cur.rowcount!=1:return False
        if callable(fault):fault()
        return True
def inspect(path,id):
    with _conn(path) as c:
        c.row_factory=sqlite3.Row;r=c.execute('SELECT * FROM jobs WHERE id=?',(id,)).fetchone();return dict(r) if r else None
def retry(path,id,token,now):return False
def publish(path,deliver):return 0
def consume(path,id,body):return False
