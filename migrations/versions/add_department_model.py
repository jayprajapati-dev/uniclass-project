"""Add department model and user relationships

Revision ID: add_department_model
Revises: 
Create Date: 2024-04-04 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_department_model'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create department table
    op.create_table('department',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('name')
    )

    # Add department_id and teaching_department_id columns to user table
    op.add_column('user',
        sa.Column('department_id', sa.Integer(), nullable=True)
    )
    op.add_column('user',
        sa.Column('teaching_department_id', sa.Integer(), nullable=True)
    )

    # Add foreign key constraints
    op.create_foreign_key(
        'fk_user_department_id', 'user', 'department',
        ['department_id'], ['id']
    )
    op.create_foreign_key(
        'fk_user_teaching_department_id', 'user', 'department',
        ['teaching_department_id'], ['id']
    )

def downgrade():
    # Remove foreign key constraints
    op.drop_constraint('fk_user_teaching_department_id', 'user', type_='foreignkey')
    op.drop_constraint('fk_user_department_id', 'user', type_='foreignkey')

    # Remove department_id and teaching_department_id columns from user table
    op.drop_column('user', 'teaching_department_id')
    op.drop_column('user', 'department_id')

    # Drop department table
    op.drop_table('department') 