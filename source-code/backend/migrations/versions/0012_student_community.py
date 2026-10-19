"""Add opt-in Student Community and private connection events.

Revision ID: 0012_student_community
Revises: 0011_student_avatar

Frozen PostgreSQL DDL: no imports from changing application models.
"""
from alembic import op

revision = '0012_student_community'
down_revision = '0011_student_avatar'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE TABLE community_profiles (
	student_id UUID NOT NULL,
	public_ref VARCHAR(56) NOT NULL,
	public_name VARCHAR(32) NOT NULL,
	name_key VARCHAR(96),
	enabled BOOLEAN DEFAULT 'false' NOT NULL,
	visible_subject_ids JSON NOT NULL,
	name_change_required BOOLEAN DEFAULT 'false' NOT NULL,
	action_window TIMESTAMP WITH TIME ZONE,
	action_count INTEGER DEFAULT '0' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (student_id),
	FOREIGN KEY(student_id) REFERENCES student_profiles (student_id) ON DELETE CASCADE,
	UNIQUE (public_ref),
	UNIQUE (name_key)
)""")
    op.execute("""CREATE TABLE community_follows (
	follower_id UUID NOT NULL,
	followed_id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (follower_id, followed_id),
	CONSTRAINT ck_community_no_self_follow CHECK (follower_id <> followed_id),
	FOREIGN KEY(follower_id) REFERENCES community_profiles (student_id) ON DELETE CASCADE,
	FOREIGN KEY(followed_id) REFERENCES community_profiles (student_id) ON DELETE CASCADE
)""")
    op.execute("""CREATE INDEX ix_community_follows_followed_id ON community_follows (followed_id)""")
    op.execute("""CREATE TABLE community_blocks (
	blocker_id UUID NOT NULL,
	blocked_id UUID NOT NULL,
	PRIMARY KEY (blocker_id, blocked_id),
	CONSTRAINT ck_community_no_self_block CHECK (blocker_id <> blocked_id),
	FOREIGN KEY(blocker_id) REFERENCES community_profiles (student_id) ON DELETE CASCADE,
	FOREIGN KEY(blocked_id) REFERENCES community_profiles (student_id) ON DELETE CASCADE
)""")
    op.execute("""CREATE INDEX ix_community_blocks_blocked_id ON community_blocks (blocked_id)""")
    op.execute("""CREATE TABLE community_notifications (
	id UUID NOT NULL,
	public_ref VARCHAR(56) NOT NULL,
	recipient_id UUID NOT NULL,
	actor_id UUID NOT NULL,
	event_type VARCHAR(40) DEFAULT 'follow.v1' NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	read BOOLEAN DEFAULT 'false' NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_community_notification_pair UNIQUE (recipient_id, actor_id, event_type),
	UNIQUE (public_ref),
	FOREIGN KEY(recipient_id) REFERENCES community_profiles (student_id) ON DELETE CASCADE,
	FOREIGN KEY(actor_id) REFERENCES community_profiles (student_id) ON DELETE CASCADE
)""")
    op.execute("""CREATE INDEX ix_community_notifications_created_at ON community_notifications (created_at)""")
    op.execute("""CREATE INDEX ix_community_notifications_recipient_id ON community_notifications (recipient_id)""")
    op.execute("""CREATE TABLE community_reports (
	id UUID NOT NULL,
	public_ref VARCHAR(56) NOT NULL,
	reporter_id UUID NOT NULL,
	target_id UUID NOT NULL,
	reason VARCHAR(40) NOT NULL,
	reported_name VARCHAR(32) NOT NULL,
	status VARCHAR(24) DEFAULT 'open' NOT NULL,
	reviewed_by UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_community_report_pair UNIQUE (reporter_id, target_id),
	CONSTRAINT ck_community_report_status CHECK (status IN ('open','dismissed','name_change_required')),
	CONSTRAINT ck_community_report_reason CHECK (reason IN ('inappropriate_name','impersonation','other_concern')),
	UNIQUE (public_ref),
	FOREIGN KEY(reporter_id) REFERENCES community_profiles (student_id) ON DELETE CASCADE,
	FOREIGN KEY(target_id) REFERENCES community_profiles (student_id) ON DELETE CASCADE,
	FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE SET NULL
)""")
    op.execute("""CREATE INDEX ix_community_reports_status ON community_reports (status)""")
    op.execute("""CREATE INDEX ix_community_reports_target_id ON community_reports (target_id)""")


def downgrade():
    op.drop_table('community_reports')
    op.drop_table('community_notifications')
    op.drop_table('community_blocks')
    op.drop_table('community_follows')
    op.drop_table('community_profiles')
