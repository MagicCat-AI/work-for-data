import sqlite3
from typing import List, Tuple, Optional
import csv
from datetime import datetime

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

    # ===== 新增常用管理功能 =====
    def update_username(self, user_id: int, new_username: str) -> bool:
        """
        更新指定用户的用户名
        :param user_id: 用户ID
        :param new_username: 新用户名
        :return: 是否更新成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET username = ? WHERE id = ?",
            (new_username, user_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def count_users(self) -> int:
        """
        统计用户总数
        :return: 用户数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM users")
        count = cursor.fetchone()['cnt']
        conn.close()
        return count

    def count_chat_records(self) -> int:
        """
        统计聊天记录总数
        :return: 聊天记录数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM chat_history")
        count = cursor.fetchone()['cnt']
        conn.close()
        return count

    def search_chats(self, keyword: str, limit: int = 50) -> List[Tuple[int, int, str, str, str]]:
        """
        根据关键词搜索聊天记录（模糊匹配）
        :param keyword: 搜索关键词
        :param limit: 返回记录数上限
        :return: 匹配的聊天记录列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        pattern = f"%{keyword}%"
        cursor.execute(
            "SELECT id, user_id, message, response, timestamp FROM chat_history "
            "WHERE message LIKE ? OR response LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (pattern, pattern, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [(r['id'], r['user_id'], r['message'], r['response'], r['timestamp']) for r in rows]

    def delete_chats_older_than(self, date_str: str) -> int:
        """
        删除指定日期之前的聊天记录
        :param date_str: 日期字符串，如 '2025-05-01'
        :return: 删除的记录数
        """
        # 验证并格式化日期
        datetime.strptime(date_str, '%Y-%m-%d')
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chat_history WHERE DATE(timestamp) < DATE(?)",
            (date_str,)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def export_user_chat_to_csv(self, user_id: int, file_path: str) -> None:
        """
        导出指定用户的聊天记录到 CSV 文件
        :param user_id: 用户ID
        :param file_path: CSV 文件路径
        """
        chats = self.get_all_chat_history(limit=10000)
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'user_id', 'message', 'response', 'timestamp'])
            for record in chats:
                if record[1] == user_id:
                    writer.writerow(record)

# 使用示例
if __name__ == '__main__':
    db = ChatAppDB()
    print(f"总用户数: {db.count_users()}")
    print(f"总聊天数: {db.count_chat_records()}")
    # 搜索包含关键字的聊天
    results = db.search_chats('你好')
    print("搜索结果:", results)
    # 导出用户1的聊天到CSV
    db.export_user_chat_to_csv(1, 'user1_chats.csv')
