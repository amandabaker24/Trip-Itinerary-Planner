"""create core tables

Revision ID: 0001_create_core_tables
Revises: 
Create Date: 2025-11-20 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_create_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("destination", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
    )
    op.create_index("ix_trips_id", "trips", ["id"])
    op.create_index("ix_trips_owner_id", "trips", ["owner_id"])

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
    )
    op.create_index("ix_locations_id", "locations", ["id"])

    op.create_table(
        "trip_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
    )
    op.create_index("ix_trip_members_id", "trip_members", ["id"])
    op.create_index("ix_trip_members_trip_id", "trip_members", ["trip_id"])
    op.create_index("ix_trip_members_user_id", "trip_members", ["user_id"])

    op.create_table(
        "trip_destinations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_trip_destinations_id", "trip_destinations", ["id"])
    op.create_index("ix_trip_destinations_trip_id", "trip_destinations", ["trip_id"])
    op.create_index("ix_trip_destinations_location_id", "trip_destinations", ["location_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_events_id", "events", ["id"])
    op.create_index("ix_events_trip_id", "events", ["trip_id"])
    op.create_index("ix_events_location_id", "events", ["location_id"])

    op.create_table(
        "budget_envelopes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("planned_amount", sa.Float(), nullable=False),
    )
    op.create_index("ix_budget_envelopes_id", "budget_envelopes", ["id"])
    op.create_index("ix_budget_envelopes_trip_id", "budget_envelopes", ["trip_id"])

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("envelope_id", sa.Integer(), sa.ForeignKey("budget_envelopes.id"), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=True),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("spent_at_date", sa.Date(), nullable=False),
    )
    op.create_index("ix_expenses_id", "expenses", ["id"])
    op.create_index("ix_expenses_trip_id", "expenses", ["trip_id"])
    op.create_index("ix_expenses_envelope_id", "expenses", ["envelope_id"])
    op.create_index("ix_expenses_event_id", "expenses", ["event_id"])

    op.create_table(
        "weather_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("provider_payload", sa.JSON(), nullable=True),
    )
    op.create_index("ix_weather_alerts_id", "weather_alerts", ["id"])
    op.create_index("ix_weather_alerts_trip_id", "weather_alerts", ["trip_id"])


def downgrade() -> None:
    op.drop_index("ix_weather_alerts_trip_id", table_name="weather_alerts")
    op.drop_index("ix_weather_alerts_id", table_name="weather_alerts")
    op.drop_table("weather_alerts")

    op.drop_index("ix_expenses_event_id", table_name="expenses")
    op.drop_index("ix_expenses_envelope_id", table_name="expenses")
    op.drop_index("ix_expenses_trip_id", table_name="expenses")
    op.drop_index("ix_expenses_id", table_name="expenses")
    op.drop_table("expenses")

    op.drop_index("ix_budget_envelopes_trip_id", table_name="budget_envelopes")
    op.drop_index("ix_budget_envelopes_id", table_name="budget_envelopes")
    op.drop_table("budget_envelopes")

    op.drop_index("ix_events_location_id", table_name="events")
    op.drop_index("ix_events_trip_id", table_name="events")
    op.drop_index("ix_events_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_trip_destinations_location_id", table_name="trip_destinations")
    op.drop_index("ix_trip_destinations_trip_id", table_name="trip_destinations")
    op.drop_index("ix_trip_destinations_id", table_name="trip_destinations")
    op.drop_table("trip_destinations")

    op.drop_index("ix_trip_members_user_id", table_name="trip_members")
    op.drop_index("ix_trip_members_trip_id", table_name="trip_members")
    op.drop_index("ix_trip_members_id", table_name="trip_members")
    op.drop_table("trip_members")

    op.drop_index("ix_locations_id", table_name="locations")
    op.drop_table("locations")

    op.drop_index("ix_trips_owner_id", table_name="trips")
    op.drop_index("ix_trips_id", table_name="trips")
    op.drop_table("trips")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
