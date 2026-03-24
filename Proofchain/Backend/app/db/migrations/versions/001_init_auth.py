"""Initial auth migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create enum type
    user_role = postgresql.ENUM('creator', 'verifier', 'license_buyer', 'admin', name='user_role')
    user_role.create(op.get_bind())
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('wallet_address', sa.String(56), unique=True, nullable=False, index=True),
        sa.Column('role', sa.Enum('creator', 'verifier', 'license_buyer', 'admin', name='user_role'), nullable=False, server_default='creator'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(), nullable=True)
    )
    
    # Auth challenges table
    op.create_table(
        'auth_challenges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('wallet_address', sa.String(56), nullable=False),
        sa.Column('challenge_text', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Index for faster lookups
    op.create_index('idx_challenges_wallet', 'auth_challenges', ['wallet_address', 'used'])

def downgrade():
    op.drop_index('idx_challenges_wallet', table_name='auth_challenges')
    op.drop_table('auth_challenges')
    op.drop_table('users')
    op.execute('DROP TYPE user_role')