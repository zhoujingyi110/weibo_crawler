from json import load
import pymysql

class DB(object):
    def __init__(self):
        self.get_json()
        # print(self.db_config)
        self.connect()

    def get_json(self):
        with open("config_db.json") as f:
            self.db_config = load(f)

    def execute_sql(self,sql):
        cur = self.connection.cursor()
        cur.execute(sql)
        self.connection.commit()
        cur.close()

    def connect(self):
        self.connection =pymysql.connect(charset = 'utf8mb4',database=self.db_config['DATABASE'],user=self.db_config["USER"],password=self.db_config['PASSWORD'],host=self.db_config["HOST"],port=self.db_config["PORT"])

    def disconnect(self):
        self.connection.close()
# d = DB()
