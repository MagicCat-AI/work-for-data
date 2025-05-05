import sqlite3
from typing import List, Tuple

DB_PATH = 'chat_app.db'

class ChatAppDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def delete_users(self, user_ids: List[int]) -> int:
        """
        批量删除指定用户
        :param user_ids: 用户ID列表
        :return: 删除的记录数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM users WHERE id IN ({','.join(['?']*len(user_ids))})",
            user_ids
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def delete_all_users(self) -> int:
        """
        删除所有用户记录
        :return: 删除的记录数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def delete_chat_records(self, record_ids: List[int]) -> int:
        """
        批量删除指定聊天记录
        :param record_ids: 聊天记录ID列表
        :return: 删除的记录数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM chat_history WHERE id IN ({','.join(['?']*len(record_ids))})",
            record_ids
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def delete_chat_by_user(self, user_id: int) -> int:
        """
        删除某个用户的所有聊天记录
        :param user_id: 用户ID
        :return: 删除的记录数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chat_history WHERE user_id = ?",
            (user_id,)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def clear_all_chat_history(self) -> int:
        """
        删除所有聊天记录
        :return: 删除的记录数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def get_all_users(self) -> List[Tuple[int, str]]:
        """
        获取所有用户列表
        :return: 用户ID和用户名列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [(r['id'], r['username']) for r in rows]

    def get_all_chat_history(self, limit: int = 100) -> List[Tuple[int, int, str, str, str]]:
        """
        获取所有聊天记录（或指定数量）
        :param limit: 最多返回记录数
        :return: 聊天记录列表(id, user_id, message, response, timestamp)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, message, response, timestamp FROM chat_history "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [(r['id'], r['user_id'], r['message'], r['response'], r['timestamp']) for r in rows]

# 使用示例
if __name__ == '__main__':
    db = ChatAppDB()
    # 批量删除用户
    deleted_users = db.delete_users([2, 3])
    print(f"已删除用户数: {deleted_users}")

    # 删除所有聊天记录
    deleted_chats = db.clear_all_chat_history()
    print(f"已删除聊天记录数: {deleted_chats}")
