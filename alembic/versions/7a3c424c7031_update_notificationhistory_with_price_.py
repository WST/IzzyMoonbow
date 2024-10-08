"""Update NotificationHistory with price status and timeframe

Revision ID: 7a3c424c7031
Revises: 87c9cb439e3c
Create Date: 2024-09-29 18:59:33.560005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a3c424c7031'
down_revision: Union[str, None] = '87c9cb439e3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notification_history', sa.Column('notification_type', sa.Enum('price', 'fvg', 'oi'), nullable=False))
    op.add_column('notification_history', sa.Column('price_status', sa.Enum('high', 'low'), nullable=True))
    op.add_column('notification_history', sa.Column('timeframe', sa.Enum('15m', '4h'), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('notification_history', 'timeframe')
    op.drop_column('notification_history', 'price_status')
    op.drop_column('notification_history', 'notification_type')
    # ### end Alembic commands ###
