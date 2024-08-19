# make_drill_chart.py

import re

import pandas as pd
import polars as pl
from numpy import arange
from fractions import Fraction

out_file = "drill_chart.md"


def lrange(*args):
    """list range - can be added to other lrange"""
    return list(arange(*args))


def make_inches_table() -> pl.DataFrame:
    df_inch = pl.DataFrame(
        [
            {
                "Inches (Frac)": str(Fraction(i, 64)) + '"',
                "Inches (Dec)": i / 64,
                "mm": i / 64 * 25.4,
                "Source": "Inch Fractions",
            }
            for i in lrange(1, 66) + lrange(66, 128, 2)
        ]
    )
    return df_inch


def make_mm_table() -> pl.DataFrame:
    df_mm = pl.DataFrame(
        [
            {"mm": mm, "Inches (Dec)": mm / 25.4, "Source": "mm"}
            for mm in lrange(0.5, 24, 0.5) + lrange(24, 50, 1)
        ]
    )
    return df_mm


def make_drill_letters_table() -> pl.DataFrame:
    # This table is from https://en.wikipedia.org/wiki/Drill_bit_sizes#:~:text=Drill%20bit%20conversion%20table%5Bedit%5D
    df_read = pd.read_html("source/Drill_Letters.html")
    assert len(df_read) == 1
    df_pd = df_read[0]
    df = pl.from_pandas(df_pd)

    df = df.rename({"gauge": "Drill Bit Letter", "in": "Inches (Dec)", "mm": "mm"})
    df = df.with_columns(Source=pl.lit("Drill Bit Letters"))
    return df


def make_uts_screw_table() -> pl.DataFrame:
    """Loads a Unified Thread Standard (UTS) imperial table."""
    df_read = pd.read_html("source/Unified_Thread_Standard_UTS.html")
    assert len(df_read) == 1
    df_pd = df_read[0]
    df = pl.from_pandas(df_pd)

    # Promote headers:
    df = df.rename(df.head(1).to_dicts().pop())
    df = df.slice(1)  # Remove first row.

    # Clean col names:
    df = df.rename({col: re.sub(r"\s+", " ", col) for col in df.columns})

    # Fix misreading 1" sizes.
    df = df.with_columns(
        pl.col("Thread Designation").replace(
            {
                "1-8": None,
                "1-14": None,
            }
        ),
        # Threads Per Inch Info (like 'UNC=40 TPI')
        tpi_info=(
            pl.col("UNF / UNC")
            + pl.lit("=")
            + pl.col("Threads per Inch").str.replace(" 1/2", ".5", literal=True)
            + pl.lit(" TPI")
        ),
    ).with_columns(
        (
            pl.lit("(#")
            + pl.col("Thread Designation").str.extract(r"^(\d+)-")
            + pl.lit(")")
        ).alias("Thread Designation")
    )

    df = (
        df.group_by(["Basic Major Diameter (External Threads)"], maintain_order=True)
        .agg(
            pl.col("Thread Designation").drop_nulls().first(),
            pl.col("tpi_info"),
        )
        .with_columns(pl.col("tpi_info").list.join(", "))
    )

    df = df.select(
        **{
            "Inches (Frac)": pl.lit(None, pl.String),
            "Inches (Dec)": pl.col("Basic Major Diameter (External Threads)").cast(
                pl.Float64
            ),
            "mm": (
                pl.col("Basic Major Diameter (External Threads)").cast(pl.Float64)
                * pl.lit(25.4)
            ),
            "Unified Thread Standard": (
                pl.when(pl.col("Thread Designation").is_null())
                .then(pl.col("tpi_info"))
                .otherwise(
                    pl.col("Thread Designation") + pl.lit(" ") + pl.col("tpi_info")
                )
            ),
            "Source": pl.lit("Unified Thread Standard (UTS)"),
        }
    ).unique(maintain_order=True)

    return df


def polars_to_markdown(df: pl.DataFrame) -> str:
    # with pl.Config() as cfg:
    #     cfg.set_tbl_formatting("ASCII_MARKDOWN")
    #     cfg.set_tbl_rows(10000)
    #     cfg.set_tbl_hide_dataframe_shape(True)
    #     cfg.set_tbl_hide_column_data_types(True)
    #     cfg.set_tbl_width_chars(140)
    #     return str(df)
    return df.to_pandas().to_markdown(index=False)


def cast_final_table(df: pl.DataFrame) -> pl.DataFrame:
    assert df["mm"].dtype == pl.Float64
    df = df.with_columns(
        pl.col("mm").map_elements(
            lambda mm: f"{mm:.03f} mm",
            return_dtype=pl.String,
        ),
        # Add 'mm_float' col
        mm_float=pl.col("mm"),
    )

    if df["Inches (Dec)"].dtype != pl.String:
        df = df.with_columns(
            pl.col("Inches (Dec)").map_elements(
                lambda x: f'{x:.03f}"', return_dtype=pl.String
            ),
        )
    return df


def main() -> None:
    dfs = [
        cast_final_table(make_mm_table()),
        cast_final_table(make_inches_table()),
        cast_final_table(make_drill_letters_table()),
        cast_final_table(make_uts_screw_table()),
    ]
    df = pl.concat(
        dfs,
        how="diagonal",
    )
    df = df.sort(["mm_float", "Source"]).drop("mm_float")

    # Group up, and order the output cols.
    df = df.group_by(["mm", "Inches (Dec)"], maintain_order=True).agg(
        pl.col("Inches (Frac)").drop_nulls().first(),
        pl.col("Unified Thread Standard").drop_nulls().first(),
        pl.col("Drill Bit Letter").drop_nulls().first(),
        pl.col("Source"),
    )
    df = df.with_columns(pl.col("Source").list.join(", "))
    df = df.fill_null("")

    df_md = polars_to_markdown(df)

    with open(out_file, "w") as f:
        f.write(df_md)

    print(f"{len(df)} rows.")


if __name__ == "__main__":
    main()
