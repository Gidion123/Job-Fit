"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Created: ${create_date}
"""
from alembic import op

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    raise NotImplementedError('write raw SQL with op.execute')


def downgrade() -> None:
    raise NotImplementedError('destructive downgrades are guarded; see 0001 and 0002')
