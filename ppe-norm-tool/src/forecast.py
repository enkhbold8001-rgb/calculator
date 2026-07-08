"""ХХХ-ийн жилийн норм хэрэглээ ба төсвийн тооцоо (forecast).

norm.xlsx (норм) болон headcount.xlsx (ажилтны тоо) өгөгдлийг нэгтгэж,
2027 оны төсвийн саналд зориулсан жилийн хэрэгцээ, төсвийг тооцоолж
output/forecast_report.xlsx болон (шаардлагатай бол) output/mismatch.xlsx
файлд бичнэ.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

НОРМ_БАГАНУУД = [
    "талбай", "албан_тушаал", "нэр_төрөл", "норм_тоо", "хугацаа_төрөл",
    "хугацаа_сар", "элэгдэл_дундаж_сар", "нэгж_үнэ",
]
ТҮЛХҮҮР = ["талбай", "албан_тушаал"]


def _унших(norm_path: Path, headcount_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    norm_df = pd.read_excel(norm_path)
    headcount_df = pd.read_excel(headcount_path)
    return norm_df, headcount_df


def _mismatch_олох(norm_df: pd.DataFrame, headcount_df: pd.DataFrame) -> pd.DataFrame:
    """norm ба headcount хооронд талбай+албан_тушаал таарахгүй мөрүүдийг олно."""
    norm_keys = norm_df[ТҮЛХҮҮР].drop_duplicates()
    headcount_keys = headcount_df[ТҮЛХҮҮР].drop_duplicates()

    норм_гэхдээ_headcount_үгүй = norm_keys.merge(
        headcount_keys, on=ТҮЛХҮҮР, how="left", indicator=True
    )
    норм_гэхдээ_headcount_үгүй = норм_гэхдээ_headcount_үгүй[
        норм_гэхдээ_headcount_үгүй["_merge"] == "left_only"
    ][ТҮЛХҮҮР].copy()
    норм_гэхдээ_headcount_үгүй["төрөл"] = "norm.xlsx-д байгаа ч headcount.xlsx-д алба тушаал олдсонгүй"

    headcount_гэхдээ_норм_үгүй = headcount_keys.merge(
        norm_keys, on=ТҮЛХҮҮР, how="left", indicator=True
    )
    headcount_гэхдээ_норм_үгүй = headcount_гэхдээ_норм_үгүй[
        headcount_гэхдээ_норм_үгүй["_merge"] == "left_only"
    ][ТҮЛХҮҮР].copy()
    headcount_гэхдээ_норм_үгүй["төрөл"] = "headcount.xlsx-д байгаа ч norm.xlsx-д алба тушаал олдсонгүй"

    return pd.concat([норм_гэхдээ_headcount_үгүй, headcount_гэхдээ_норм_үгүй], ignore_index=True)


def _хэрэгцээ_тооцох(мөр: pd.Series) -> tuple[float | None, str | None]:
    """Нэг мөрийн жилийн хэрэгцээ (ширхэг)-ийг тооцно. Тооцох боломжгүй бол (None, флаг)."""
    ажилтан = мөр["ажилтны_тоо"] + мөр.get("төлөвлөсөн_нэмэгдэл", 0)

    if мөр["хугацаа_төрөл"] == "тогтмол":
        хугацаа_сар = мөр["хугацаа_сар"]
        if pd.isna(хугацаа_сар) or хугацаа_сар == 0:
            return None, "хугацаа_сар дутуу"
    elif мөр["хугацаа_төрөл"] == "элэгдлээр":
        хугацаа_сар = мөр["элэгдэл_дундаж_сар"]
        if pd.isna(хугацаа_сар) or хугацаа_сар == 0:
            return None, "тоогоор тооцох боломжгүй (элэгдэл_дундаж_сар дутуу)"
    else:
        return None, f"үл мэдэгдэх хугацаа_төрөл: {мөр['хугацаа_төрөл']}"

    хэрэгцээ = ажилтан * мөр["норм_тоо"] * (12 / хугацаа_сар)
    return хэрэгцээ, None


def _нэгтгэл_тооцох(norm_df: pd.DataFrame, headcount_df: pd.DataFrame) -> pd.DataFrame:
    нэгтгэл = norm_df.merge(headcount_df, on=ТҮЛХҮҮР, how="inner")
    нэгтгэл["төлөвлөсөн_нэмэгдэл"] = нэгтгэл["төлөвлөсөн_нэмэгдэл"].fillna(0)

    хэрэгцээ_флаг = нэгтгэл.apply(_хэрэгцээ_тооцох, axis=1, result_type="expand")
    нэгтгэл["жилийн_хэрэгцээ_ш"] = хэрэгцээ_флаг[0]
    нэгтгэл["анхаарах_тэмдэглэл"] = хэрэгцээ_флаг[1].astype(object)

    үнэ_дутуу = нэгтгэл["нэгж_үнэ"].isna()
    нэгтгэл.loc[үнэ_дутуу, "анхаарах_тэмдэглэл"] = "үнэ дутуу"

    нэгтгэл["жилийн_төсөв_₮"] = нэгтгэл["жилийн_хэрэгцээ_ш"] * нэгтгэл["нэгж_үнэ"]
    нэгтгэл.loc[үнэ_дутуу, "жилийн_төсөв_₮"] = None

    return нэгтгэл


def _дэлгэрэнгүй_тайлан(нэгтгэл: pd.DataFrame) -> pd.DataFrame:
    баганууд = [
        "талбай", "албан_тушаал", "нэр_төрөл", "ажилтны_тоо", "төлөвлөсөн_нэмэгдэл",
        "норм_тоо", "хугацаа_төрөл", "хугацаа_сар", "элэгдэл_дундаж_сар",
        "нэгж_үнэ", "жилийн_хэрэгцээ_ш", "жилийн_төсөв_₮", "анхаарах_тэмдэглэл",
    ]
    return нэгтгэл[баганууд].sort_values(["талбай", "албан_тушаал", "нэр_төрөл"]).reset_index(drop=True)


def _талбайн_нэгтгэл(нэгтгэл: pd.DataFrame) -> pd.DataFrame:
    тооцох = нэгтгэл[нэгтгэл["жилийн_төсөв_₮"].notna()]
    нэгтгэсэн = (
        тооцох.groupby("талбай", as_index=False)[["жилийн_хэрэгцээ_ш", "жилийн_төсөв_₮"]]
        .sum()
        .sort_values("талбай")
        .reset_index(drop=True)
    )
    return нэгтгэсэн


def _компанийн_нийт(талбайн_нэгтгэл: pd.DataFrame, нөөцийн_хувь: float) -> pd.DataFrame:
    нийт_төсөв = талбайн_нэгтгэл["жилийн_төсөв_₮"].sum()
    нөөц = нийт_төсөв * нөөцийн_хувь
    мөрүүд = [
        {"үзүүлэлт": "Нийт төсөв (нөөцгүй)", "дүн_₮": нийт_төсөв},
        {"үзүүлэлт": f"Нөөцийн мөр ({нөөцийн_хувь * 100:.0f}%)", "дүн_₮": нөөц},
        {"үзүүлэлт": "Нийт төсөв (нөөцтэй)", "дүн_₮": нийт_төсөв + нөөц},
    ]
    return pd.DataFrame(мөрүүд)


def тооцоолол_хийх(
    data_dir: Path,
    output_dir: Path,
    reserve: float = 0.1,
    site: str | None = None,
) -> None:
    """forecast_report.xlsx (болон шаардлагатай бол mismatch.xlsx) үүсгэнэ."""
    output_dir.mkdir(parents=True, exist_ok=True)

    norm_df, headcount_df = _унших(data_dir / "norm.xlsx", data_dir / "headcount.xlsx")

    if site:
        norm_df = norm_df[norm_df["талбай"] == site].copy()
        headcount_df = headcount_df[headcount_df["талбай"] == site].copy()

    mismatch_df = _mismatch_олох(norm_df, headcount_df)
    if not mismatch_df.empty:
        mismatch_path = output_dir / "mismatch.xlsx"
        mismatch_df.to_excel(mismatch_path, index=False)
        print(f"Анхаар: {len(mismatch_df)} мөр таарсангүй -> {mismatch_path}")

    нэгтгэл = _нэгтгэл_тооцох(norm_df, headcount_df)
    дэлгэрэнгүй = _дэлгэрэнгүй_тайлан(нэгтгэл)
    талбайн_нэгтгэл = _талбайн_нэгтгэл(нэгтгэл)
    компанийн_нийт = _компанийн_нийт(талбайн_нэгтгэл, reserve)

    report_path = output_dir / "forecast_report.xlsx"
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        if not mismatch_df.empty:
            анхааруулга = pd.DataFrame(
                [{"АНХААРУУЛГА": f"{len(mismatch_df)} мөрийн талбай/албан_тушаал norm.xlsx ба headcount.xlsx хооронд таарсангүй. Дэлгэрэнгүйг output/mismatch.xlsx-с харна уу."}]
            )
            анхааруулга.to_excel(writer, sheet_name="Анхааруулга", index=False)
        дэлгэрэнгүй.to_excel(writer, sheet_name="Дэлгэрэнгүй", index=False)
        талбайн_нэгтгэл.to_excel(writer, sheet_name="Талбайгаар нэгтгэл", index=False)
        компанийн_нийт.to_excel(writer, sheet_name="Компанийн нийт", index=False)

    print(f"Тайлан бэлэн: {report_path}")
