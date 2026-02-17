"""Utility migration: drop & recreate columns on `order_history`.

User requirement:
- Remove (if present) the columns: loyalty_applied, discount_amount, final_price,
  return_status, return_reason, return_initiated_time, feedback
- Recreate loyalty_applied/discount_amount/final_price as FLOAT/REAL (NULL)
- Recreate return_status/return_reason/return_initiated_time/feedback as TEXT (NULL)

Important SQLite note:
- SQLite cannot reliably ALTER COLUMN types. The safe way is: rebuild the table.
- This script preserves:
  - all other columns + data
  - foreign key constraints
  - indexes (recreated from sqlite_master)
"""

from typing import Any, Dict, List, Tuple
from sqlalchemy import create_engine, inspect, text
from database import DATABASE_URL
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


TARGET_TABLE = "order_history"
DROP_AND_RECREATE = {"loyalty_applied", "discount_amount", "final_price",
                     "return_status", "return_reason", "return_initiated_time", "feedback"}


def _fetchall(conn, sql: str, params: Dict[str, Any] | None = None) -> List[Tuple[Any, ...]]:
    if params is None:
        return conn.exec_driver_sql(sql).fetchall()
    return conn.exec_driver_sql(sql, params).fetchall()


def _table_exists(conn) -> bool:
    row = conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:t",
        {"t": TARGET_TABLE},
    ).fetchone()
    return row is not None


def _get_table_info(conn) -> List[Tuple[Any, ...]]:
    # (cid, name, type, notnull, dflt_value, pk)
    return _fetchall(conn, f"PRAGMA table_info({TARGET_TABLE})")


def _get_foreign_keys(conn) -> List[Tuple[Any, ...]]:
    # (id, seq, table, from, to, on_update, on_delete, match)
    return _fetchall(conn, f"PRAGMA foreign_key_list({TARGET_TABLE})")


def _get_indexes_sql(conn) -> List[str]:
    rows = _fetchall(
        conn,
        """
        SELECT sql
        FROM sqlite_master
        WHERE type='index'
          AND tbl_name=:t
          AND sql IS NOT NULL
        """,
        {"t": TARGET_TABLE},
    )
    return [r[0] for r in rows if r and r[0]]


def _quote_ident(name: str) -> str:
    # Minimal quoting for identifiers.
    return '"' + name.replace('"', '""') + '"'


def rebuild_order_history_columns() -> None:
    engine = create_engine(
        DATABASE_URL,
        echo=True,
        connect_args={"check_same_thread": False},
    )

    with engine.begin() as conn:
        # Ensure FK enforcement on.
        conn.exec_driver_sql("PRAGMA foreign_keys=ON")

        if not _table_exists(conn):
            raise RuntimeError(f"Table '{TARGET_TABLE}' not found.")

        # Capture table schema info.
        table_info = _get_table_info(conn)
        existing_cols = [r[1] for r in table_info]
        print(f"\n📋 Existing columns in {TARGET_TABLE}: {existing_cols}\n")

        # Save index DDL to recreate later.
        index_sql_list = _get_indexes_sql(conn)

        # Build new column definitions (preserve everything except the 3 columns).
        kept_cols_info = [r for r in table_info if r[1]
                          not in DROP_AND_RECREATE]

        # Primary key columns (supports composite keys)
        pk_cols = [(r[1], int(r[5]))
                   for r in kept_cols_info if int(r[5] or 0) > 0]
        pk_cols_sorted = [name for name, _pos in sorted(
            pk_cols, key=lambda x: x[1])]

        def col_def(row) -> str:
            _cid, name, col_type, notnull, dflt_value, pk = row
            parts = [_quote_ident(name)]
            parts.append(col_type or "TEXT")
            if len(pk_cols_sorted) == 1 and pk_cols_sorted[0] == name:
                parts.append("PRIMARY KEY")
            if int(notnull or 0) == 1:
                parts.append("NOT NULL")
            if dflt_value is not None:
                parts.append(f"DEFAULT {dflt_value}")
            return " ".join(parts)

        new_cols_ddl = [col_def(r) for r in kept_cols_info]

        # Add the three columns back as REAL (float) and blank (NULL by default)
        new_cols_ddl.append('"loyalty_applied" REAL')
        new_cols_ddl.append('"discount_amount" REAL')
        new_cols_ddl.append('"final_price" REAL')

        # Add four new optional TEXT columns (NULL by default)
        new_cols_ddl.append('"return_status" TEXT')
        new_cols_ddl.append('"return_reason" TEXT')
        new_cols_ddl.append('"return_initiated_time" TEXT')
        new_cols_ddl.append('"feedback" TEXT')

        # Foreign keys (preserve)
        fk_rows = _get_foreign_keys(conn)
        fk_by_id: Dict[int, List[Tuple[Any, ...]]] = {}
        for r in fk_rows:
            fk_by_id.setdefault(int(r[0]), []).append(r)

        fk_constraints: List[str] = []
        for _id, group in fk_by_id.items():
            group_sorted = sorted(group, key=lambda x: int(x[1]))
            ref_table = group_sorted[0][2]
            from_cols = [_quote_ident(g[3]) for g in group_sorted]
            to_cols = [_quote_ident(g[4]) for g in group_sorted]
            on_update = group_sorted[0][5]
            on_delete = group_sorted[0][6]
            clause = f"FOREIGN KEY ({', '.join(from_cols)}) REFERENCES {_quote_ident(ref_table)} ({', '.join(to_cols)})"
            if on_update and str(on_update).upper() != "NO ACTION":
                clause += f" ON UPDATE {on_update}"
            if on_delete and str(on_delete).upper() != "NO ACTION":
                clause += f" ON DELETE {on_delete}"
            fk_constraints.append(clause)

        # Composite primary key as table constraint if needed
        table_constraints: List[str] = []
        if len(pk_cols_sorted) > 1:
            table_constraints.append(
                f"PRIMARY KEY ({', '.join(_quote_ident(c) for c in pk_cols_sorted)})")
        table_constraints.extend(fk_constraints)

        tmp_table = f"{TARGET_TABLE}__rebuild_tmp"
        conn.exec_driver_sql(f"DROP TABLE IF EXISTS {_quote_ident(tmp_table)}")

        create_stmt = f"CREATE TABLE {_quote_ident(tmp_table)} (\n  " + \
            ",\n  ".join(new_cols_ddl)
        if table_constraints:
            create_stmt += ",\n  " + ",\n  ".join(table_constraints)
        create_stmt += "\n);"

        print("\n🔨 Rebuilding table to drop & recreate columns as REAL...")
        conn.exec_driver_sql(create_stmt)

        # Copy old data into tmp (new 3 columns stay NULL/blank)
        kept_col_names = [r[1] for r in kept_cols_info]
        cols_csv = ", ".join(_quote_ident(c) for c in kept_col_names)
        insert_stmt = (
            f"INSERT INTO {_quote_ident(tmp_table)} ({cols_csv}) "
            f"SELECT {cols_csv} FROM {_quote_ident(TARGET_TABLE)}"
        )
        conn.exec_driver_sql(insert_stmt)

        # Swap tables
        conn.exec_driver_sql(f"DROP TABLE {_quote_ident(TARGET_TABLE)}")
        conn.exec_driver_sql(
            f"ALTER TABLE {_quote_ident(tmp_table)} RENAME TO {_quote_ident(TARGET_TABLE)}")

        # Recreate indexes
        for idx_sql in index_sql_list:
            try:
                conn.exec_driver_sql(idx_sql)
            except Exception as e:
                print(f"⚠️ Could not recreate index: {e}\nSQL: {idx_sql}")

    # Verify
    inspector = inspect(engine)
    cols_after = inspector.get_columns(TARGET_TABLE)
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    for c in cols_after:
        if c["name"] in DROP_AND_RECREATE:
            print(f"  • {c['name']:<18} type={str(c['type'])}")

    print("\n✅ Done. Columns were recreated as REAL (float) and left blank (NULL).")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ORDER HISTORY TABLE - DROP & RECREATE COLUMNS")
    print("="*60)
    print("\nThis script will DROP and recreate these columns:")
    print("  1. loyalty_applied        (REAL) - blank/NULL")
    print("  2. discount_amount        (REAL) - blank/NULL")
    print("  3. final_price            (REAL) - blank/NULL")
    print("  4. return_status          (TEXT) - blank/NULL")
    print("  5. return_reason          (TEXT) - blank/NULL")
    print("  6. return_initiated_time  (TEXT) - blank/NULL")
    print("  7. feedback               (TEXT) - blank/NULL")
    print("\n" + "="*60 + "\n")

    try:
        rebuild_order_history_columns()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
