"""Create users table

Revision ID: 6094c6ce6075
Revises: 
Create Date: 2024-09-10 17:59:09.834033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6094c6ce6075'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    create table users(
        id bigserial primary key,
        username text,
        full_name text,
        hashed_password text
    )
    """)

def downgrade():
    op.execute("drop table todos;")