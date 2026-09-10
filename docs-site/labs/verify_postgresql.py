import argparse,pathlib,subprocess,re,os,tempfile,time
parser=argparse.ArgumentParser(description="Verify documented SQL in a fresh local PostgreSQL cluster; TCP disabled.")
parser.add_argument("--bin",required=True,help="Directory containing a complete PostgreSQL 18 server and client installation")
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parents[2];p=pathlib.Path(tempfile.mkdtemp(prefix='study-pg-review-'));bin=pathlib.Path(args.bin).resolve()
env=os.environ.copy();env.update(PGHOST=str(p),PGPORT='55487',PGDATABASE='postgres',PGUSER=os.environ['USER'])
def run(name,*args,**kw):return subprocess.run([str(bin/name),*map(str,args)],env=env,text=True,capture_output=True,check=True,**kw).stdout
def sql(q,db='postgres'):return run('psql','-X','-A','-t','-v','ON_ERROR_STOP=1','-d',db,'-c',q).strip()
def blocks(path):return re.findall(r'^```sql\n(.*?)^```',(root/path).read_text(),re.M|re.S)
version=run('postgres','--version').strip()
if not re.search(r'\b18\.', version):
 raise SystemExit('This fixture requires a PostgreSQL 18 server: '+version)
print(version)
print(run('initdb','-D',p/'data','-A','trust','--no-locale'))
started=False
try:
 print(run('pg_ctl','-D',p/'data','-l',p/'server.log','-o',f"-k {p} -p 55487 -h ''",'-w','start'));started=True
 b=blocks('docs-site/content/backend-engineering/02-domain-data-transaction.md')
 out=sql(b[0]+b[1]+b[1]+b[2]+b[3])
 assert out.endswith('0\n1'),out
 print('Backend: PASS conditional inventory decrement and outbox foreign-key/payload match')
 b=blocks('docs-site/content/messaging/02-duplicate-dlq-replay-lab.md')
 script=b[0]+b[1]+b[1]+b[2]+b[1].replace('evt-00042','evt-00043').replace('COMMIT;','ROLLBACK;')+b[2]+b[1].replace('evt-00042','evt-00043')+b[2]
 out=sql(script);assert out.count('1|1')==2 and '2|2' in out;print('Messaging:',out)
 run('createdb','study_source');b=blocks('docs-site/content/postgresql/02-lock-backup-restore-lab.md');sql(b[0],'study_source')
 # A holds the documented update until the test sends COMMIT.
 A=subprocess.Popen([str(bin/'psql'),'-X','-A','-t','-v','ON_ERROR_STOP=1','-d','study_source'],env=env,text=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 A.stdin.write(b[1]+'\n');A.stdin.flush()
 deadline=time.monotonic()+8
 while 'idle in transaction' not in sql("SELECT state FROM pg_stat_activity WHERE datname='study_source' AND query LIKE 'UPDATE accounts SET balance = balance - 10%' AND pid<>pg_backend_pid()"):
  if time.monotonic()>deadline:raise RuntimeError('A did not acquire row lock')
  time.sleep(.05)
 B=subprocess.Popen([str(bin/'psql'),'-X','-A','-t','-v','ON_ERROR_STOP=1','-d','study_source','-c',b[2]],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 deadline=time.monotonic()+8
 while True:
  obs=sql(b[3]);
  if '|Lock|' in obs:break
  if time.monotonic()>deadline:raise RuntimeError('no blocked B')
  time.sleep(.05)
 print('Lock observer: PASS waiter, Lock, blocker')
 A.stdin.write('COMMIT;\n\\q\n');A.stdin.flush();A.communicate(timeout=5)
 bo,be=B.communicate(timeout=5);assert B.returncode==0,(bo,be)
 assert sql('SELECT balance FROM accounts WHERE id=1','study_source')=='100.00'
 run('pg_dump','--format=custom','--file',p/'accounts.dump','study_source');run('createdb','study_restore');run('pg_restore','--exit-on-error','--dbname=study_restore',p/'accounts.dump')
 assert sql('SELECT count(*),sum(balance) FROM accounts','study_restore')=='2|200.00'
 # Constraint is restored too: reject invalid balance rather than silently storing it.
 r=subprocess.run([str(bin/'psql'),'-X','-v','ON_ERROR_STOP=1','-d','study_restore','-c','UPDATE accounts SET balance=-1 WHERE id=1'],env=env,text=True,capture_output=True)
 assert r.returncode!=0 and 'check constraint' in r.stderr
 print('PostgreSQL: PASS lock, commit, dump/restore 2|200.00, restored constraint rejects negative')
finally:
 if started:print(run('pg_ctl','-D',p/'data','-m','fast','-w','stop'))
 print('isolated receipt directory:',p)
