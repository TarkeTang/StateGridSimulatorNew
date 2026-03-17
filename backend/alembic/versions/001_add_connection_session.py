"""add connection session table

Revision ID: 001
Revises: 
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库"""
    
    # 1. 创建连接会话表
    op.create_table(
        'sys_connection_session',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('config_id', sa.Integer(), nullable=False, comment='会话配置ID'),
        sa.Column('session_id', sa.String(50), nullable=False, unique=True, comment='会话标识'),
        sa.Column('status', sa.String(20), nullable=False, server_default='connected', comment='连接状态'),
        sa.Column('local_address', sa.String(50), nullable=True, comment='本地地址'),
        sa.Column('local_port', sa.Integer(), nullable=True, comment='本地端口'),
        sa.Column('remote_address', sa.String(50), nullable=True, comment='远程地址'),
        sa.Column('remote_port', sa.Integer(), nullable=True, comment='远程端口'),
        sa.Column('connected_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='连接时间'),
        sa.Column('disconnected_at', sa.DateTime(), nullable=True, comment='断开时间'),
        sa.Column('send_count', sa.Integer(), server_default='0', comment='发送消息数'),
        sa.Column('receive_count', sa.Integer(), server_default='0', comment='接收消息数'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('remark', sa.Text(), nullable=True, comment='备注'),
        sa.ForeignKeyConstraint(['config_id'], ['sys_session_config.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_sys_connection_session_config_id', 'sys_connection_session', ['config_id'])
    op.create_index('ix_sys_connection_session_session_id', 'sys_connection_session', ['session_id'])
    
    # 2. 为消息表添加新字段
    op.add_column('sys_session_message', sa.Column('connection_id', sa.Integer(), nullable=True, comment='连接会话ID'))
    op.add_column('sys_session_message', sa.Column('config_id', sa.Integer(), nullable=True, comment='会话配置ID'))
    
    # 3. 添加新的 session_id 字段（字符串类型）
    op.add_column('sys_session_message', sa.Column('session_id_new', sa.String(50), nullable=True, comment='会话标识'))
    
    # 4. 迁移数据：为每个会话创建一个连接记录，并更新消息
    # 使用原生 SQL 进行数据迁移
    conn = op.get_bind()
    
    # 获取所有唯一的 session_id
    result = conn.execute(sa.text("SELECT DISTINCT session_id FROM sys_session_message"))
    session_ids = [row[0] for row in result.fetchall()]
    
    for old_session_id in session_ids:
        # 为每个 session_id 创建一个连接记录
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        new_session_id = f"{old_session_id}_{now}"
        
        # 插入连接记录
        conn.execute(sa.text("""
            INSERT INTO sys_connection_session (config_id, session_id, status, connected_at, send_count, receive_count)
            SELECT :config_id, :session_id, 'disconnected', 
                   COALESCE((SELECT MIN(timestamp) FROM sys_session_message WHERE session_id = :old_session_id), NOW()),
                   (SELECT COUNT(*) FROM sys_session_message WHERE session_id = :old_session_id AND direction = 'send'),
                   (SELECT COUNT(*) FROM sys_session_message WHERE session_id = :old_session_id AND direction = 'receive')
        """), {"config_id": old_session_id, "session_id": new_session_id, "old_session_id": old_session_id})
        
        # 获取新创建的连接记录 ID
        connection_result = conn.execute(sa.text(
            "SELECT id FROM sys_connection_session WHERE session_id = :session_id"
        ), {"session_id": new_session_id})
        connection_id = connection_result.fetchone()[0]
        
        # 更新消息表
        conn.execute(sa.text("""
            UPDATE sys_session_message 
            SET connection_id = :connection_id, 
                config_id = :config_id,
                session_id_new = :new_session_id
            WHERE session_id = :old_session_id
        """), {"connection_id": connection_id, "config_id": old_session_id, 
               "new_session_id": new_session_id, "old_session_id": old_session_id})
    
    # 5. 删除旧的 session_id 列，重命名新列
    op.drop_column('sys_session_message', 'session_id')
    op.drop_column('sys_session_message', 'session_name')
    op.alter_column('sys_session_message', 'session_id_new', new_column_name='session_id')
    
    # 6. 设置新字段为非空
    op.alter_column('sys_session_message', 'connection_id', nullable=False)
    op.alter_column('sys_session_message', 'config_id', nullable=False)
    op.alter_column('sys_session_message', 'session_id', nullable=False)
    
    # 7. 添加外键和索引
    op.create_foreign_key('fk_session_message_connection', 'sys_session_message', 
                          'sys_connection_session', ['connection_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_sys_session_message_connection_id', 'sys_session_message', ['connection_id'])
    op.create_index('ix_sys_session_message_config_id', 'sys_session_message', ['config_id'])
    op.create_index('ix_sys_session_message_session_id', 'sys_session_message', ['session_id'])
    
    # 8. 删除不再需要的统计表（如果存在）
    # 保留表结构，但数据不再使用


def downgrade() -> None:
    """降级数据库"""
    # 删除索引和外键
    op.drop_index('ix_sys_session_message_session_id', 'sys_session_message')
    op.drop_index('ix_sys_session_message_config_id', 'sys_session_message')
    op.drop_index('ix_sys_session_message_connection_id', 'sys_session_message')
    op.drop_constraint('fk_session_message_connection', 'sys_session_message', type_='foreignkey')
    
    # 恢复旧字段
    op.add_column('sys_session_message', sa.Column('session_id', sa.Integer(), nullable=True))
    op.add_column('sys_session_message', sa.Column('session_name', sa.String(100), nullable=True))
    
    # 迁移数据回旧结构
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE sys_session_message m
        SET session_id = m.config_id,
            session_name = (SELECT name FROM sys_session_config WHERE id = m.config_id)
    """))
    
    # 删除新字段
    op.drop_column('sys_session_message', 'connection_id')
    op.drop_column('sys_session_message', 'config_id')
    
    # 删除连接会话表
    op.drop_index('ix_sys_connection_session_session_id', 'sys_connection_session')
    op.drop_index('ix_sys_connection_session_config_id', 'sys_connection_session')
    op.drop_table('sys_connection_session')