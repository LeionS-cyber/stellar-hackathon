"""Initial auth + files migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Enum
    user_role = postgresql.ENUM('creator', 'verifier', 'license_buyer', 'admin', name='user_role')
    user_role.create(op.get_bind())
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('wallet_address', sa.String(56), unique=True, nullable=False),
        sa.Column('role', postgresql.ENUM('creator', 'verifier', 'license_buyer', 'admin', name='user_role'), server_default='creator'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_users_wallet', 'users', ['wallet_address'])
    
    # Auth challenges table
    op.create_table(
        'auth_challenges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('wallet_address', sa.String(56), nullable=False),
        sa.Column('challenge_text', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_challenges_wallet', 'auth_challenges', ['wallet_address', 'used'])
    
    # Files table
    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('wallet_address', sa.String(56), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('file_location', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('ix_files_user_id', 'files', ['user_id'])
    op.create_index('ix_files_hash', 'files', ['file_hash'])

def downgrade():
    op.drop_index('ix_files_hash', table_name='files')
    op.drop_index('ix_files_user_id', table_name='files')
    op.drop_table('files')
    op.drop_index('idx_challenges_wallet', table_name='auth_challenges')
    op.drop_table('auth_challenges')
    op.drop_index('ix_users_wallet', table_name='users')
    op.drop_table('users')
    op.execute('DROP TYPE user_role')
