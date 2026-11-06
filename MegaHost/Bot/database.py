import sqlite3

conn = sqlite3.connect('database.db')
print('База данных создана и подключена')

cursor = conn.cursor()



if cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="users"').fetchone() is None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            stars REAL DEFAULT 0.0,
            count_refs INTEGER DEFAULT 0,
            referral_id INTEGER DEFAULT NULL,
            hikka INTEGER DEFAULT 0,
            heroku INTEGER DEFAULT 0,
            server_hikka INTEGER DEFAULT 0,
            server_heroku INTEGER DEFAULT 0
        )
    ''')
    print('Таблица "users" создана')
else:
    print('Выполнено подключение к таблице "users".')

if cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="creat_ub"').fetchone() is None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS creat_ub (
            id INTEGER PRIMARY KEY,
            tarif INTEGER DEFAULT 0,
            ub INTEGER DEFAULT 0,
            server INTEGER DEFAULT 0
        )
    ''')
    print('Таблица "creat_ub" создана')
else:
    print('Выполнено подключение к таблице "creat_ub".')

if cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="promocodes"').fetchone() is None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promocodes (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            stars REAL NOT NULL,
            max_uses INTEGER NOT NULL,
            current_uses INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    print('Таблица "promocodes" создана')
else:
    print('Выполнено подключение к таблице "promocodes".')

if cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="promocode_uses"').fetchone() is None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promocode_uses (
            id INTEGER PRIMARY KEY,
            promocode_id INTEGER,
            user_id INTEGER,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (promocode_id) REFERENCES promocodes(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(promocode_id, user_id)
        )
    ''')
    print('Таблица "promocode_uses" создана')
else:
    print('Выполнено подключение к таблице "promocode_uses".')
conn.commit()
conn.close()
print('База данных успешно инициализирована.')


def add_promocode(code, stars, max_uses):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO promocodes (code, stars, max_uses) VALUES (?, ?, ?)',
                       (code, stars, max_uses))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def use_promocode(code, user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        promo = cursor.execute('''
            SELECT * FROM promocodes 
            WHERE code = ? AND is_active = TRUE 
            AND current_uses < max_uses
        ''', (code,)).fetchone()

        if not promo:
            return False, "Промокод недействителен или закончились использования"

        used = cursor.execute('''
            SELECT 1 FROM promocode_uses 
            WHERE promocode_id = ? AND user_id = ?
        ''', (promo[0], user_id)).fetchone()

        if used:
            return False, "Вы уже использовали этот промокод"

        # Увеличиваем количество использований промокода
        cursor.execute('''
            UPDATE promocodes 
            SET current_uses = current_uses + 1 
            WHERE code = ?
        ''', (code,))

        # Записываем использование промокода
        cursor.execute('''
            INSERT INTO promocode_uses (promocode_id, user_id) 
            VALUES (?, ?)
        ''', (promo[0], user_id))

        # Начисляем звезды пользователю
        cursor.execute('''
            UPDATE users 
            SET stars = stars + ? 
            WHERE id = ?
        ''', (promo[2], user_id))

        conn.commit()
        return True, promo[2]  # Возвращаем True и количество начисленных звезд
    except Exception as e:
        conn.rollback()
        return False, f"❌ {str(e)}"
    finally:
        conn.close()


def deactivate_promocode(code):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE promocodes SET is_active = FALSE WHERE code = ?', (code,))
    conn.commit()
    conn.close()


def add_user(user_id, username, referral_id=None):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (id, username, stars, count_refs, referral_id, hikka, heroku, server_hikka, server_heroku) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (user_id, username, 0.0, 0, referral_id, 0, 0, 0, 0))
    conn.commit()
    conn.close()


def user_exists(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return bool(result)


def increment_stars(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET stars = stars + ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()


def deincrement_stars(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET stars = stars - ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()


def get_user_zero_referrals():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM users WHERE count_refs = 0').fetchall()
    conn.close()
    return result


def withdraw_stars(user_id, stars_to_withdraw):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET stars = stars - ?, withdrawn = withdrawn + ? WHERE id = ?',
                   (stars_to_withdraw, stars_to_withdraw, user_id))
    conn.commit()
    conn.close()


def increment_referrals(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET count_refs = count_refs + 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_user_count():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT COUNT(*) FROM users').fetchone()
    conn.close()
    return result[0] if result else 0


def get_total_withdrawn():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT SUM(withdrawn) FROM users').fetchone()
    conn.close()
    return result[0] if result else 0.0


def get_user(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return result


def get_users():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM users').fetchall()
    conn.close()
    return result

# UserBots

# Hikka
def add_hikka(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET hikka = hikka + ? WHERE id = ?', (1, user_id))
    conn.commit()
    conn.close()

def minus_hikka(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET hikka = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_hikka(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return result

# ServerHikka
def add_server_hikka(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET server_hikka = ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()

def minus_server_hikka(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET server_hikka = ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()

def get_server_hikka(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return result

# Heroku

def add_heroku(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET heroku = ? WHERE id = ?', (1, user_id))
    conn.commit()
    conn.close()


def minus_heroku(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET heroku = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_heroku(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return result

# ServerHeroku

def add_server_heroku(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET server_heroku = ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()


def minus_server_heroku(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET server_heroku = ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()


def get_server_heroku(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return result


# Функции связанные с созданием юб

def add_user_creat_ub(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO creat_ub (id, tarif, ub, server) VALUES (?, ?, ?, ?)',
                   (user_id, 0, 0, 0))
    conn.commit()
    conn.close()

def add_tarif_ub_add(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE creat_ub SET tarif = ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()

def add_ub_obraz(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE creat_ub SET ub = ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()

def add_server_ub_add(user_id, stars):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE creat_ub SET server = ? WHERE id = ?', (stars, user_id))
    conn.commit()
    conn.close()

def get_creat_ub(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    result = cursor.execute('SELECT * FROM creat_ub WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return result