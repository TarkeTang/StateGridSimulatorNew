"""
数据库迁移脚本

将旧的消息表结构迁移到新的连接会话模型

运行方式：
    cd backend
    python scripts/migrate_db.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy import text
from src.core.config import settings
from src.db.session import engine
from src.utils.logger import get_logger

log = get_logger("migrate")

# 获取数据库类型
DB_DRIVER = settings.database.driver


async def table_exists(conn, table_name: str) -> bool:
    """检查表是否存在"""
    if DB_DRIVER == "sqlite":
        result = await conn.execute(text(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{table_name}'
        """))
    else:
        result = await conn.execute(text(f"""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = '{table_name}'
        """))
    return result.fetchone() is not None


async def column_exists(conn, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    if DB_DRIVER == "sqlite":
        result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]
    else:
        result = await conn.execute(text(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = '{table_name}' AND column_name = '{column_name}'
        """))
        columns = [row[0] for row in result.fetchall()]
    return column_name in columns


async def migrate():
    """执行数据库迁移"""
    log.info(f"开始数据库迁移... (数据库类型: {DB_DRIVER})")
    
    async with engine.begin() as conn:
        # 检查连接会话表是否已存在
        if await table_exists(conn, 'sys_connection_session'):
            log.info("连接会话表已存在，跳过创建")
        else:
            log.info("创建连接会话表...")
            
            # 创建连接会话表
            if DB_DRIVER == "sqlite":
                await conn.execute(text("""
                    CREATE TABLE sys_connection_session (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_id INTEGER NOT NULL,
                        session_id VARCHAR(50) NOT NULL UNIQUE,
                        status VARCHAR(20) NOT NULL DEFAULT 'connected',
                        local_address VARCHAR(50),
                        local_port INTEGER,
                        remote_address VARCHAR(50),
                        remote_port INTEGER,
                        connected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        disconnected_at DATETIME,
                        send_count INTEGER DEFAULT 0,
                        receive_count INTEGER DEFAULT 0,
                        error_message TEXT,
                        remark TEXT,
                        FOREIGN KEY (config_id) REFERENCES sys_session_config(id) ON DELETE CASCADE
                    )
                """))
            else:
                await conn.execute(text("""
                    CREATE TABLE sys_connection_session (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        config_id INT NOT NULL,
                        session_id VARCHAR(50) NOT NULL UNIQUE,
                        status VARCHAR(20) NOT NULL DEFAULT 'connected',
                        local_address VARCHAR(50),
                        local_port INT,
                        remote_address VARCHAR(50),
                        remote_port INT,
                        connected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        disconnected_at DATETIME,
                        send_count INT DEFAULT 0,
                        receive_count INT DEFAULT 0,
                        error_message TEXT,
                        remark TEXT,
                        FOREIGN KEY (config_id) REFERENCES sys_session_config(id) ON DELETE CASCADE,
                        INDEX ix_config_id (config_id),
                        INDEX ix_session_id (session_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """))
            
            # SQLite 需要单独创建索引
            if DB_DRIVER == "sqlite":
                await conn.execute(text("CREATE INDEX ix_sys_connection_session_config_id ON sys_connection_session(config_id)"))
                await conn.execute(text("CREATE INDEX ix_sys_connection_session_session_id ON sys_connection_session(session_id)"))
            
            log.info("连接会话表创建完成")
        
        # 检查消息表是否有旧数据
        result = await conn.execute(text("SELECT COUNT(*) FROM sys_session_message"))
        count = result.fetchone()[0]
        
        if count == 0:
            log.info("消息表为空，跳过数据迁移")
        else:
            log.info(f"开始迁移 {count} 条消息记录...")
            
            # 检查是否需要迁移
            if await column_exists(conn, 'sys_session_message', 'connection_id'):
                log.info("消息表已包含 connection_id 字段，检查是否需要迁移数据...")
                result = await conn.execute(text("SELECT COUNT(*) FROM sys_session_message WHERE connection_id IS NULL"))
                null_count = result.fetchone()[0]
                if null_count == 0:
                    log.info("数据已迁移，跳过")
                else:
                    await migrate_data(conn)
            else:
                # 添加新字段
                log.info("添加新字段...")
                try:
                    if DB_DRIVER == "sqlite":
                        await conn.execute(text("ALTER TABLE sys_session_message ADD COLUMN connection_id INTEGER"))
                        await conn.execute(text("ALTER TABLE sys_session_message ADD COLUMN config_id INTEGER"))
                    else:
                        await conn.execute(text("ALTER TABLE sys_session_message ADD COLUMN connection_id INT"))
                        await conn.execute(text("ALTER TABLE sys_session_message ADD COLUMN config_id INT"))
                    log.info("新字段添加完成")
                except Exception as e:
                    log.warning(f"添加字段时出错（可能已存在）: {e}")
                
                await migrate_data(conn)
        
        # 创建索引
        log.info("创建索引...")
        try:
            if DB_DRIVER == "sqlite":
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sys_session_message_connection_id ON sys_session_message(connection_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sys_session_message_config_id ON sys_session_message(config_id)"))
            else:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_sys_session_message_connection_id 
                    ON sys_session_message(connection_id)
                """))
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_sys_session_message_config_id 
                    ON sys_session_message(config_id)
                """))
        except Exception as e:
            log.warning(f"创建索引时出错: {e}")
        
        log.info("数据库迁移完成！")


async def migrate_data(conn):
    """迁移数据"""
    # 获取所有唯一的 session_id
    result = await conn.execute(text("SELECT DISTINCT session_id FROM sys_session_message"))
    session_ids = [row[0] for row in result.fetchall()]
    
    log.info(f"发现 {len(session_ids)} 个会话需要迁移")
    
    for old_session_id in session_ids:
        # 为每个 session_id 创建一个连接记录
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        new_session_id = f"{old_session_id}_{now}"
        
        # 插入连接记录
        if DB_DRIVER == "sqlite":
            await conn.execute(text("""
                INSERT INTO sys_connection_session (config_id, session_id, status, connected_at, send_count, receive_count)
                SELECT :config_id, :session_id, 'disconnected', 
                       COALESCE((SELECT MIN(timestamp) FROM sys_session_message WHERE session_id = :old_session_id), datetime('now')),
                       (SELECT COUNT(*) FROM sys_session_message WHERE session_id = :old_session_id AND direction = 'send'),
                       (SELECT COUNT(*) FROM sys_session_message WHERE session_id = :old_session_id AND direction = 'receive')
            """), {"config_id": old_session_id, "session_id": new_session_id, "old_session_id": old_session_id})
        else:
            await conn.execute(text("""
                INSERT INTO sys_connection_session (config_id, session_id, status, connected_at, send_count, receive_count)
                SELECT :config_id, :session_id, 'disconnected', 
                       COALESCE((SELECT MIN(timestamp) FROM sys_session_message WHERE session_id = :old_session_id), NOW()),
                       (SELECT COUNT(*) FROM sys_session_message WHERE session_id = :old_session_id AND direction = 'send'),
                       (SELECT COUNT(*) FROM sys_session_message WHERE session_id = :old_session_id AND direction = 'receive')
            """), {"config_id": old_session_id, "session_id": new_session_id, "old_session_id": old_session_id})
        
        # 获取新创建的连接记录 ID
        connection_result = await conn.execute(text(
            "SELECT id FROM sys_connection_session WHERE session_id = :session_id"
        ), {"session_id": new_session_id})
        connection_id = connection_result.fetchone()[0]
        
        # 更新消息表
        await conn.execute(text("""
            UPDATE sys_session_message 
            SET connection_id = :connection_id, 
                config_id = :config_id
            WHERE session_id = :old_session_id
        """), {"connection_id": connection_id, "config_id": old_session_id, "old_session_id": old_session_id})
    
    log.info("数据迁移完成")


async def main():
    try:
        await migrate()
        print("\n✅ 迁移成功！请重启后端服务。")
    except Exception as e:
        log.error(f"迁移失败: {e}")
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())