"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("wallet_address", sa.String(56), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("wallet_address"),
    )
    op.create_index("idx_user_email_active", "users", ["email", "is_active"])
    op.create_index("idx_user_created_at", "users", ["created_at"])

    # Create licenses table
    op.create_table(
        "licenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "license_type",
            postgresql.ENUM("EXCLUSIVE", "NON_EXCLUSIVE", "PERSONAL", name="license_types"),
            nullable=False,
            server_default="PERSONAL",
        ),
        sa.Column("price", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("blockchain_tx_hash", sa.String(66), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_license_creator", "licenses", ["creator_id"])
    op.create_index("idx_license_owner", "licenses", ["owner_id"])
    op.create_index("idx_license_created_at", "licenses", ["created_at"])

    # Create assets table
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Numeric(15, 0), nullable=False),
        sa.Column("phash", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("width", sa.Numeric(10, 0), nullable=True),
        sa.Column("height", sa.Numeric(10, 0), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_asset_phash", "assets", ["phash"])

    # Create transaction_history table
    op.create_table(
        "transaction_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "tx_type",
            postgresql.ENUM("MINT", "EXCLUSIVE", "NON_EXCLUSIVE", name="tx_types"),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(18, 2), nullable=False),
        sa.Column("blockchain_tx_hash", sa.String(66), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"]),
        sa.ForeignKeyConstraint(["buyer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_txn_license", "transaction_history", ["license_id"])
    op.create_index("idx_txn_buyer", "transaction_history", ["buyer_id"])
    op.create_index("idx_txn_seller", "transaction_history", ["seller_id"])
    op.create_index("idx_txn_created_at", "transaction_history", ["created_at"])


def downgrade():
    op.drop_index("idx_txn_created_at", table_name="transaction_history")
    op.drop_index("idx_txn_seller", table_name="transaction_history")
    op.drop_index("idx_txn_buyer", table_name="transaction_history")
    op.drop_index("idx_txn_license", table_name="transaction_history")
    op.drop_table("transaction_history")
    op.drop_index("idx_asset_phash", table_name="assets")
    op.drop_table("assets")
    op.drop_index("idx_license_created_at", table_name="licenses")
    op.drop_index("idx_license_owner", table_name="licenses")
    op.drop_index("idx_license_creator", table_name="licenses")
    op.drop_table("licenses")
    op.drop_index("idx_user_created_at", table_name="users")
    op.drop_index("idx_user_email_active", table_name="users")
    op.drop_table("users")