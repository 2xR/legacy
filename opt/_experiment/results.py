import sqlite3


class ResultsDB(object):
    """This database provides a base set of tables that allow resuming an experiment from the point 
    where it was left off before. Base tables includes 'instances', 'methods', 'replications', and 
    a 'completed' table to mark things that were already run. 
    This database is meant to store the results from an experiment, while at the same time 
    providing the basic infrastructure to allow pausing and later resuming an experiment without 
    having to start over."""
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.connection = None
        self.cursor = None
        
    def connect(self, filepath=None):
        if filepath is not None:
            self.filepath = filepath
        if self.filepath is None:
            raise Exception("no file path provided for database")
        self.connection = sqlite3.connect(self.filepath)
        self.cursor = self.connection.cursor()
        self.init()
        
    def init(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS instances (descr TEXT UNIQUE);")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS methods (descr TEXT UNIQUE);")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS replications (descr TEXT UNIQUE);")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS completed "
                            "(instance REFERENCES instances(rowid),"
                            " method REFERENCES methods(rowid),"
                            " replication REFERENCES replications(rowid),"
                            " UNIQUE (instance, method, replication));")
        
    def close(self):
        self.cursor.close()
        self.connection.commit()
        self.connection.close()
        
    def get_completed(self, instance=None, method=None, replication=None):
        self.cursor.execute("SELECT 1 FROM completed AS c" 
                            " JOIN instances AS i ON i.rowid=c.instance AND i.descr=?"
                            " JOIN methods AS m ON m.rowid=c.method AND m.descr=?"
                            " JOIN replications AS r ON r.rowid=c.replication AND r.descr=?;",
                            self._parse_args_completed(instance, method, replication))
        return self.cursor.fetchone() is not None
        
    def set_completed(self, instance=None, method=None, replication=None):
        instance, method, replication = self._parse_args_completed(instance, method, replication)
        self.cursor.execute("INSERT OR IGNORE INTO instances VALUES (?);", (instance,))
        self.cursor.execute("INSERT OR IGNORE INTO methods VALUES (?);", (method,))
        self.cursor.execute("INSERT OR IGNORE INTO replications VALUES (?);", (replication,))
        self.cursor.execute("INSERT OR FAIL INTO completed"
                            " SELECT i.rowid, m.rowid, r.rowid"
                            " FROM instances AS i JOIN methods AS m JOIN replications AS r"
                            " WHERE i.descr=? AND m.descr=? AND r.descr=?;", 
                            (instance, method, replication))
        
    def _parse_args_completed(self, instance, method, replication):
        if instance is None:
            assert method is None
            instance = "*"
        if method is None: 
            assert replication is None
            method = "*"
        if replication is None:
            replication = "*"
        return str(instance), str(method), str(replication)    
        
    def iter_table(self, table):
        for row in self.cursor.execute("SELECT * FROM %s" % table):
            yield row
            
    def iter_instances(self):
        return self.iter_table("instances")
        
    def iter_methods(self):
        return self.iter_table("methods")
        
    def iter_replications(self):
        return self.iter_table("replications")
        
        