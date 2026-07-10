import sqlite3
import os
import json
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'finlyze.db')

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create watchlist table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE NOT NULL,
            company_name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create analysis history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            ticker TEXT NOT NULL,
            company_name TEXT,
            rating TEXT,
            target_price TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            results_json TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("SQLite Database initialized successfully")

def add_to_watchlist(ticker, company_name=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO watchlist (ticker, company_name) VALUES (?, ?)",
            (ticker.upper(), company_name)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error adding to watchlist: {str(e)}")
        return False

def remove_from_watchlist(ticker):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error removing from watchlist: {str(e)}")
        return False

def get_watchlist():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, company_name, added_at FROM watchlist ORDER BY added_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting watchlist: {str(e)}")
        return []

def is_watchlisted(ticker):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM watchlist WHERE ticker = ?", (ticker.upper(),))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    except Exception as e:
        logger.error(f"Error checking watchlist: {str(e)}")
        return False

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle NumPy types like int64/float64 and convert them to standard Python types"""
    def default(self, obj):
        if hasattr(obj, 'item') and callable(getattr(obj, 'item')):
            return obj.item()
        elif hasattr(obj, 'tolist') and callable(getattr(obj, 'tolist')):
            return obj.tolist()
        try:
            return super(CustomJSONEncoder, self).default(obj)
        except TypeError:
            return str(obj)

def save_analysis(task_id, ticker, company_name, rating, target_price, results_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        results_json = json.dumps(results_dict, cls=CustomJSONEncoder)
        cursor.execute('''
            INSERT OR REPLACE INTO analysis_history 
            (task_id, ticker, company_name, rating, target_price, results_json) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_id, ticker.upper(), company_name, rating, str(target_price), results_json))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving analysis history: {str(e)}")
        return False

def get_analysis_history(limit=10):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT task_id, ticker, company_name, rating, target_price, generated_at 
            FROM analysis_history 
            ORDER BY generated_at DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting analysis history: {str(e)}")
        return []

def get_saved_analysis_results(task_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT results_json FROM analysis_history WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row['results_json'])
        return None
    except Exception as e:
        logger.error(f"Error retrieving saved analysis results: {str(e)}")
        return None
