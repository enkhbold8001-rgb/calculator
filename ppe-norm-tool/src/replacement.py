"""Ажилтан тус бүрийн ХХХ солих хугацааны хяналт (2-р үе шат).

issuance.xlsx (олголтын бүртгэл) дэх ажилтан тус бүрийн сүүлийн олголтоос
norm.xlsx-ийн хугацаа_сар-ыг ашиглан дуусах огноог тооцож, хугацаа хэтэрсэн
болон удахгүй (--days) дуусах жагсаалтыг output/replacement_due.xlsx-д бичнэ.
`элэгдлээр` төрлийн зүйлд due-date тооцохгүй, тусдаа "Үзлэгээр солино" хуудсанд
гаргана.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ТҮЛХҮҮР = ["талбай", "албан_тушаал", "нэр_төрөл"]


def _сүүлийн_олголт(issuance_df: pd.DataFrame) -> pd.DataFrame:
    """Ажилтан + нэр_төрөл тус бүрийн хамгийн сүүлийн олголтын мөрийг сонгоно."""
    issuance_df = issuance_df.sort_values("олгосон_огноо")
    return (
        issuance_df.groupby(["ажилтны_код", "нэр_төрөл"], as_index=False)
        .last()
    )


def _дуусах_огноо(мөр: pd.Series) -> pd.Timestamp | None:
    if pd.isna(мөр["хугацаа_сар"]):
        return None
    return мөр["олгосон_огноо"] + pd.DateOffset(months=int(мөр["хугацаа_сар"]))


def хяналт_хийх(
    data_dir: Path,
    output_dir: Path,
    asof: str | None = None,
    days: int = 30,
) -> None:
    """replacement_due.xlsx үүсгэнэ."""
    output_dir.mkdir(parents=True, exist_ok=True)

    issuance_df = pd.read_excel(data_dir / "issuance.xlsx")
    norm_df = pd.read_excel(data_dir / "norm.xlsx")

    issuance_df["олгосон_огноо"] = pd.to_datetime(issuance_df["олгосон_огноо"])
    as_of_огноо = pd.Timestamp(asof) if asof else pd.Timestamp.today().normalize()

    сүүлийн = _сүүлийн_олголт(issuance_df)
    нэгтгэл = сүүлийн.merge(
        norm_df[ТҮЛХҮҮР + ["хугацаа_төрөл", "хугацаа_сар"]], on=ТҮЛХҮҮР, how="left"
    )

    норм_олдсонгүй = нэгтгэл[нэгтгэл["хугацаа_төрөл"].isna()].copy()
    нэгтгэл = нэгтгэл[нэгтгэл["хугацаа_төрөл"].notna()].copy()

    элэгдлээр = нэгтгэл[нэгтгэл["хугацаа_төрөл"] == "элэгдлээр"].copy()
    тогтмол = нэгтгэл[нэгтгэл["хугацаа_төрөл"] == "тогтмол"].copy()

    тогтмол["дуусах_огноо"] = тогтмол.apply(_дуусах_огноо, axis=1)
    тогтмол["үлдсэн_хоног"] = (тогтмол["дуусах_огноо"] - as_of_огноо).dt.days

    хэтэрсэн = тогтмол[тогтмол["үлдсэн_хоног"] < 0].copy()
    хэтэрсэн["хэтэрсэн_хоног"] = -хэтэрсэн["үлдсэн_хоног"]

    удахгүй = тогтмол[(тогтмол["үлдсэн_хоног"] >= 0) & (тогтмол["үлдсэн_хоног"] <= days)].copy()

    БАГАНУУД = [
        "ажилтны_код", "овог_нэр", "талбай", "албан_тушаал", "нэр_төрөл",
        "олгосон_огноо", "дуусах_огноо",
    ]

    def _эрэмбэлэх(df: pd.DataFrame, нэмэлт_багана: str | None = None) -> pd.DataFrame:
        баганууд = БАГАНУУД + ([нэмэлт_багана] if нэмэлт_багана else [])
        return df[баганууд].sort_values(["талбай", "дуусах_огноо"]).reset_index(drop=True)

    хэтэрсэн_тайлан = _эрэмбэлэх(хэтэрсэн, "хэтэрсэн_хоног")
    удахгүй_тайлан = _эрэмбэлэх(удахгүй, "үлдсэн_хоног")
    элэгдлээр_тайлан = элэгдлээр[
        ["ажилтны_код", "овог_нэр", "талбай", "албан_тушаал", "нэр_төрөл", "олгосон_огноо"]
    ].sort_values(["талбай", "нэр_төрөл"]).reset_index(drop=True)
    элэгдлээр_тайлан["тэмдэглэл"] = "үзлэгээр солино"

    report_path = output_dir / "replacement_due.xlsx"
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        if not норм_олдсонгүй.empty:
            анхааруулга = pd.DataFrame(
                [{
                    "АНХААРУУЛГА": (
                        f"{len(норм_олдсонгүй)} мөрийн талбай/албан_тушаал/нэр_төрөл "
                        "norm.xlsx-с олдсонгүй тул хугацаа тооцоогүй."
                    )
                }]
            )
            анхааруулга.to_excel(writer, sheet_name="Анхааруулга", index=False)
        хэтэрсэн_тайлан.to_excel(writer, sheet_name="Хугацаа хэтэрсэн", index=False)
        удахгүй_тайлан.to_excel(writer, sheet_name=f"{days} хоногт дуусах", index=False)
        элэгдлээр_тайлан.to_excel(writer, sheet_name="Үзлэгээр солино", index=False)

    print(
        f"Тайлан бэлэн: {report_path} "
        f"(хэтэрсэн: {len(хэтэрсэн_тайлан)}, удахгүй дуусах: {len(удахгүй_тайлан)}, "
        f"үзлэгээр: {len(элэгдлээр_тайлан)})"
    )
