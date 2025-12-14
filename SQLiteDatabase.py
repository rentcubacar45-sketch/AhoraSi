import sqlite3
import json
import os

class SQLiteDatabase(object):
    def __init__(self, path='database'):
        self.db_path = f'{path}.db'
        self.conn = None
        self.cursor = None
        self.create_table()

    def create_table(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                dir TEXT,
                cloudtype TEXT,
                moodle_host TEXT,
                moodle_repo_id INTEGER,
                moodle_user TEXT,
                moodle_password TEXT,
                isadmin INTEGER,
                zips INTEGER,
                uploadtype TEXT,
                proxy TEXT,
                tokenize INTEGER
            )
        ''')
        self.conn.commit()

    def check_create(self):
        # Table is created in __init__, no need for separate check
        pass

    def save(self):
        # No need to save manually, changes are committed immediately
        pass

    def create_user(self, name):
        data = {
            'dir': '',
            'cloudtype': 'moodle',
            'moodle_host': '---',
            'moodle_repo_id': 4,
            'moodle_user': '---',
            'moodle_password': '---',
            'isadmin': 0,
            'zips': 100,
            'uploadtype': 'evidence',
            'proxy': '',
            'tokenize': 0
        }
        self.save_data_user(name, data)

    def create_admin(self, name):
        data = {
            'dir': '',
            'cloudtype': 'moodle',
            'moodle_host': '---',
            'moodle_repo_id': 4,
            'moodle_user': '---',
            'moodle_password': '---',
            'isadmin': 1,
            'zips': 100,
            'uploadtype': 'evidence',
            'proxy': '',
            'tokenize': 0
        }
        self.save_data_user(name, data)

    def remove(self, name):
        self.cursor.execute('DELETE FROM users WHERE username = ?', (name,))
        self.conn.commit()

    def get_user(self, name):
        self.cursor.execute('SELECT * FROM users WHERE username = ?', (name,))
        row = self.cursor.fetchone()
        if row:
            return {
                'dir': row[1],
                'cloudtype': row[2],
                'moodle_host': row[3],
                'moodle_repo_id': row[4],
                'moodle_user': row[5],
                'moodle_password': row[6],
                'isadmin': row[7],
                'zips': row[8],
                'uploadtype': row[9],
                'proxy': row[10],
                'tokenize': row[11]
            }
        return None

    def save_data_user(self, user, data):
        self.cursor.execute('''
            INSERT OR REPLACE INTO users (
                username, dir, cloudtype, moodle_host, moodle_repo_id,
                moodle_user, moodle_password, isadmin, zips, uploadtype, proxy, tokenize
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user, data['dir'], data['cloudtype'], data['moodle_host'], data['moodle_repo_id'],
            data['moodle_user'], data['moodle_password'], data['isadmin'], data['zips'],
            data['uploadtype'], data['proxy'], data['tokenize']
        ))
        self.conn.commit()

    def is_admin(self, user):
        user_data = self.get_user(user)
        if user_data:
            return user_data['isadmin'] == 1
        return False

    def load(self):
        # Data is loaded on demand, no need to load all into memory
        pass

    def migrate_from_json(self, json_db_path):
        if os.path.exists(json_db_path):
            with open(json_db_path, 'r') as f:
                lines = f.read().split('\n')
                for line in lines:
                    if line:
                        tokens = line.split('=')
                        if len(tokens) == 2:
                            user = tokens[0]
                            data = json.loads(tokens[1].replace("'", '"'))
                            self.save_data_user(user, data)
            print("Migration from JSON database completed.")

    def close(self):
        if self.conn:
            self.conn.close()