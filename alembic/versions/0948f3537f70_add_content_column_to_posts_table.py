"""add content column to posts table

Revision ID: 0948f3537f70
Revises: ec02e6925b50
Create Date: 2025-12-17 15:40:31.289174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0948f3537f70'
down_revision: Union[str, Sequence[str], None] = 'ec02e6925b50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('posts',sa.Column('content',sa.String(),nullable=False))
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('posts','content')
    pass
