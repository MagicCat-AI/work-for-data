import sqlite3
import os
from typing import Optional, Dict, Any
import logging
from contextlib import contextmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理类，封装SQLite操作"""

    def __init__(self, db_path: str = 'chat_app.db'):
        """
        初始化数据库管理器
        :param db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建用户表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )''')

            # 创建用户配置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                theme TEXT DEFAULT 'light',
                language TEXT DEFAULT 'en',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )''')

            # 创建聊天记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )''')

            # 创建索引提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp)')

            conn.commit()
            logger.info("数据库初始化完成")

    @contextmanager
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接上下文管理器"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 设置行工厂为字典模式
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"数据库连接错误: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False) -> Optional[Any]:
        """
        执行SQL查询
        :param query: SQL查询语句
        :param params: 查询参数
        :param fetch_one: 是否只获取一条记录
        :return: 查询结果
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()
            except sqlite3.Error as e:
                logger.error(f"查询执行失败: {str(e)}")
                raise

    def add_user(self, username: str, password: str) -> int:
        """
        添加新用户
        :param username: 用户名
        :param password: 密码(应预先加密)
        :return: 新用户ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password)
                user_id = cursor.lastrowid
                # 为用户创建默认设置
                cursor.execute(
                    "INSERT INTO user_settings (user_id) VALUES (?)",
                    (user_id,))
                conn.commit()
                return user_id
        except sqlite3.IntegrityError:
            logger.warning(f"用户名已存在: {username}")
            raise ValueError("用户名已存在")
        except sqlite3.Error as e:
            logger.error(f"添加用户失败: {str(e)}")
            raise

    def add_chat_message(self, user_id: int, message: str, response: str) -> int:
        """
        添加聊天记录
        :param user_id: 用户ID
        :param message: 用户消息
        :param response: 系统回复
        :return: 新记录ID
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)",
                    (user_id, message, response))
                record_id = cursor.lastrowid
                conn.commit()
                return record_id
        except sqlite3.Error as e:
            logger.error(f"添加聊天记录失败: {str(e)}")
            raise

    def get_user_chat_history(self, user_id: int, limit: int = 20) -> list:
        """
        获取用户聊天历史
        :param user_id: 用户ID
        :param limit: 返回记录数限制
        :return: 聊天记录列表
        """
        try:
            return self.execute_query(
                "SELECT * FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit))
        except sqlite3.Error as e:
            logger.error(f"获取聊天历史失败: {str(e)}")
            raise


# 初始化数据库实例
db_manager = DatabaseManager()

if __name__ == "__main__":
    # 测试代码
    try:
        # 添加测试用户
        user_id = db_manager.add_user("test_user", "hashed_password")
        print(f"添加用户成功，ID: {user_id}")

        # 添加测试聊天记录
        chat_id = db_manager.add_chat_message(user_id, "你好", "你好，有什么可以帮您？")
        print(f"添加聊天记录成功，ID: {chat_id}")

        # 查询聊天历史
        history = db_manager.get_user_chat_history(user_id)
        print("聊天历史:")
        for record in history:
            print(f"{record['timestamp']}: {record['message']} -> {record['response']}")

    except Exception as e:
        print(f"测试失败: {str(e)}")