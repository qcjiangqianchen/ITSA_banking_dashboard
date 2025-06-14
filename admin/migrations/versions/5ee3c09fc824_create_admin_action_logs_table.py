"""Create admin_action_logs table

Revision ID: 5ee3c09fc824
Revises: 
Create Date: 2025-04-12 21:16:38.280191

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5ee3c09fc824'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_action_logs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('admin_name', sa.String(length=100), nullable=False),
    sa.Column('target_name', sa.String(length=100), nullable=False),
    sa.Column('target_role', sa.String(length=20), nullable=False),
    sa.Column('action_type', sa.String(length=20), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index('email')

    op.drop_table('user')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', mysql.VARCHAR(length=36), nullable=False),
    sa.Column('first_name', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('last_name', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('email', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('role', mysql.VARCHAR(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='MyISAM'
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index('email', ['email'], unique=True)

    op.drop_table('admin_action_logs')
    # ### end Alembic commands ###
