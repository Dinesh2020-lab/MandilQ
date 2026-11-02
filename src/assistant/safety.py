"""SQL safety validator (FR-21). Parses with sqlglot; rejects anything but one allowlisted SELECT."""
from __future__ import annotations
from dataclasses import dataclass
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

ALLOWED_TABLES = {"v_prices", "v_monthly_prices", "v_seasonality", "v_volatility", "v_anomalies"}
ALLOWED_FUNCS = {
    "avg", "count", "sum", "min", "max", "stddev", "stddev_samp", "stddev_pop", "variance", "median",
    "percentile_cont", "abs", "round", "coalesce", "nullif", "greatest", "least", "lag", "lead", "rank",
    "dense_rank", "row_number", "ntile", "first_value", "last_value", "date_trunc", "date_part", "extract",
    "to_char", "make_date", "lower", "upper", "length", "sqrt", "ln", "power", "floor", "ceil", "ceiling",
    "cast", "case", "if", "concat", "trim", "cume_dist", "percent_rank", "mod",
}
MAX_ROWS = 1000


@dataclass
class Verdict:
    ok: bool
    sql: str = ""
    message: str = ""


def _fn_name(n: exp.Expression) -> str:
    return (n.name if isinstance(n, exp.Anonymous) else n.sql_name()).lower()


def validate_sql(sql: str, max_rows: int = MAX_ROWS) -> Verdict:
    try:
        stmts = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except SqlglotError as e:
        return Verdict(False, message=f"Could not parse SQL: {str(e)[:150]}")
    if len(stmts) != 1:
        return Verdict(False, message="Exactly one statement is allowed.")
    tree = stmts[0]
    if not isinstance(tree, (exp.Select, exp.Union)):
        return Verdict(False, message="Only SELECT queries are allowed.")
    banned = (exp.Into, exp.Lock, exp.Command, exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
              exp.Alter, exp.Copy, exp.Set)
    if any(tree.find(b) for b in banned):
        return Verdict(False, message="Statement contains a disallowed clause.")
    ctes = {c.alias.lower() for c in tree.find_all(exp.CTE)}
    for t in tree.find_all(exp.Table):
        if t.args.get("db") or t.args.get("catalog"):
            return Verdict(False, message="Schema-qualified tables are not allowed.")
        if isinstance(t.this, exp.Func):
            return Verdict(False, message="Table functions are not allowed.")
        if t.name.lower() not in ALLOWED_TABLES | ctes:
            return Verdict(False, message=f"Table '{t.name}' is not allowed.")
    for f in tree.find_all(exp.Func):
        if _fn_name(f) not in ALLOWED_FUNCS:
            return Verdict(False, message=f"Function '{_fn_name(f)}' is not allowed.")
    lim = tree.args.get("limit")
    n = None
    if lim is not None and isinstance(lim.expression, exp.Literal) and lim.expression.is_int:
        n = int(lim.expression.this)
    if lim is None or n is None or n > max_rows:
        tree = tree.limit(max_rows)
    return Verdict(True, sql=tree.sql(dialect="postgres"))
