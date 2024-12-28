import sqlite3
from config import *
import random
from googletrans import Translator
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
plt.switch_backend('agg')

translator = Translator()


class DB_Manager:
    def __init__(self, database):
        self.database = database
        self.used_cities = set()


    def create_user_table(self):
        conn = sqlite3.connect(self.database) 
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER,
                            username TEXT,
                            score INTEGER,
                            max_score INTEGER
                         )''')
            conn.commit()

    def add_user(self, user_id, user_name):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (user_id, user_name, 0, 0))
            conn.commit()
    
    def get_users(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users')
            return [x[0] for x in cur.fetchall()] 

    def get_city(self, last_city, used_cities):
        conn = sqlite3.connect(self.database)
        if last_city == '':
            last_letter = ''
        else:
            last_letter = last_city[-1].upper()
            if last_letter in ['Ь', 'Ы', 'Ъ']:
                last_letter = last_city[-2].upper()
        with conn:
            cur = conn.cursor()
            while True:
                cur.execute("SELECT city FROM cities WHERE city LIKE ? ORDER BY RANDOM() LIMIT 1", (last_letter + '%',))
                city = cur.fetchone()[0]
                if not city:
                    return None
                if city not in used_cities:
                    if city == []:
                        return None
                    else:
                        return city
    

    def check_city(self, last_city):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT city FROM cities WHERE city = ?", (last_city, ))
            exist_city = [x[0] for x in cur.fetchall()]
        if exist_city == []:
            return False
        else:
            return True
        
    def new_score(self, score, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT score FROM users WHERE user_id = ?', (user_id,))
            old_score = [x[0] for x in cur.fetchall()][0]
            new_score = score + old_score
            conn.execute("UPDATE users SET score = ? WHERE user_id = ?", (new_score, user_id))

    def get_score(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT score FROM users WHERE user_id = ?', (user_id,))
            return [x[0] for x in cur.fetchall()][0] 
        


    def get_user_rating(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            score = self.get_score(user_id)
            cur.execute('SELECT count(*) FROM users WHERE score > ?', (score,))
            result = cur.fetchone()[0] + 1
            return(result)

    def get_max_score(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT max_score FROM users WHERE user_id = ?', (user_id,))
            return cur.fetchall()[0][0]

    def new_max_score(self, user_id, max_score):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("UPDATE users SET max_score = ? WHERE user_id = ?", (max_score, user_id))

    def get_total_rating(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users ORDER BY score DESC LIMIT 5')
            return cur.fetchall()
    
    def get_max_rating(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users ORDER BY max_score DESC LIMIT 5')
            return cur.fetchall()
        
    def get_coordinates(self, city_name):
        conn = sqlite3.connect('data.db')
        with conn:
            cur = conn.cursor()
            if self.check_city(city_name):
                cur.execute('''SELECT lat, lon FROM cities WHERE city = ?''', (city_name,))
                coordinates = cur.fetchone()
                return coordinates
            else:
                return None
        
    def create_grapf(self, city, user_id):
        fig = plt.figure()

        ax = fig.add_subplot(1,1,1, projection=ccrs.Mercator())

        ax.stock_img()
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS)

        lat1, lon1, lat2, lon2 = 10, 180, 40, 80
        ax.set_extent([lat1, lon1, lat2, lon2], crs=ccrs.PlateCarree())
        path = f'images/{user_id}.png'
        if self.get_coordinates(city):
            lat, lon = self.get_coordinates(city)

            plt.plot([lon], [lat],
                color='blue', linewidth=1, marker='o',
                transform=ccrs.Geodetic(),
                )
            plt.text(lon + 5 if lon < 90 else lon -5, lat + 1, city,
                horizontalalignment='right',
                transform=ccrs.Geodetic())
            plt.savefig(path)
            plt.show()
            return True
        else:
            return False

if __name__ == "__main__":
    manager = DB_Manager('database.db')
    manager.create_user_table()
    manager.get_city('Анадырь', [])
