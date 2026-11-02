"""Initial schema from specs/004-hotelsystem/plan.md, section 3.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}


def upgrade():
    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("code", name="uq_countries_code"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "room_types",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("room_count", sa.Integer(), nullable=False),
        sa.Column("max_guests", sa.Integer(), nullable=False),
        sa.Column("demo_data", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("code", name="uq_room_types_code"),
        sa.CheckConstraint("room_count >= 0", name="ck_room_types_room_count"),
        sa.CheckConstraint("max_guests BETWEEN 1 AND 4", name="ck_room_types_max_guests"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "room_type_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("room_type_id", sa.Integer(), sa.ForeignKey("room_types.id", name="fk_room_type_prices_room_type"), nullable=False),
        sa.Column("season", sa.String(10), nullable=False),
        sa.Column("suggested_nightly_rate", sa.Numeric(12, 2), nullable=False),
        sa.UniqueConstraint("room_type_id", "season", name="uq_room_type_prices_type_season"),
        sa.CheckConstraint("season IN ('low', 'mid', 'high')", name="ck_room_type_prices_season"),
        sa.CheckConstraint("suggested_nightly_rate > 0", name="ck_room_type_prices_rate"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guest_name", sa.String(200), nullable=False),
        sa.Column("country_id", sa.Integer(), sa.ForeignKey("countries.id", name="fk_bookings_country"), nullable=False),
        sa.Column("room_type_id", sa.Integer(), sa.ForeignKey("room_types.id", name="fk_bookings_room_type"), nullable=False),
        sa.Column("arrival", sa.Date(), nullable=False),
        sa.Column("departure", sa.Date(), nullable=False),
        sa.Column("guest_count", sa.Integer(), nullable=False),
        sa.Column("nightly_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("demo_data", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("departure > arrival", name="ck_bookings_dates"),
        sa.CheckConstraint("guest_count > 0", name="ck_bookings_guest_count"),
        sa.CheckConstraint("nightly_rate > 0", name="ck_bookings_nightly_rate"),
        sa.CheckConstraint("status IN ('active', 'cancelled')", name="ck_bookings_status"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_bookings_type_status_dates", "bookings", ["room_type_id", "status", "arrival", "departure"])
    op.create_table(
        "drinks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(10), nullable=False),
        sa.Column("suggested_unit_price", sa.Numeric(12, 2), nullable=False),
        sa.UniqueConstraint("name", name="uq_drinks_name"),
        sa.CheckConstraint("category IN ('cocktail', 'coffee')", name="ck_drinks_category"),
        sa.CheckConstraint("suggested_unit_price > 0", name="ck_drinks_price"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("code", name="uq_employees_code"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "bar_sales",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("drink_id", sa.Integer(), sa.ForeignKey("drinks.id", name="fk_bar_sales_drink"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", name="fk_bar_sales_employee"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("demo_data", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("quantity > 0", name="ck_bar_sales_quantity"),
        sa.CheckConstraint("unit_price > 0", name="ck_bar_sales_unit_price"),
        sa.CheckConstraint("status IN ('active', 'cancelled')", name="ck_bar_sales_status"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_bar_sales_employee_status_date", "bar_sales", ["employee_id", "status", "sale_date"])
    op.create_table(
        "idempotency_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("http_method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(100), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("http_method", "path", "idempotency_key", name="uq_idempotency_requests_key"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "seed_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("source_checksums", sa.JSON(), nullable=False),
        sa.Column("anchor_date", sa.Date(), nullable=False),
        sa.Column("anchor_year", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("version", name="uq_seed_runs_version"),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "import_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("catalog_count", sa.Integer(), nullable=False),
        sa.Column("reference_count", sa.Integer(), nullable=False),
        sa.Column("omitted_count", sa.Integer(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        **TABLE_OPTIONS,
    )
    op.create_table(
        "historical_reference_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("original_values", sa.JSON(), nullable=False),
        sa.UniqueConstraint("source", "row_number", name="uq_historical_reference_records_row"),
        **TABLE_OPTIONS,
    )


def downgrade():
    for table in (
        "historical_reference_records",
        "import_reports",
        "seed_runs",
        "idempotency_requests",
        "bar_sales",
        "employees",
        "drinks",
        "bookings",
        "room_type_prices",
        "room_types",
        "countries",
    ):
        op.drop_table(table)
