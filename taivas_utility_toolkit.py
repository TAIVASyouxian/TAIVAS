from __future__ import annotations

from datetime import datetime
from io import BytesIO, StringIO
import re
import zipfile

import pandas as pd
import streamlit as st

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency fallback
    Image = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:  # pragma: no cover - optional dependency fallback
    colors = None
    A4 = None
    getSampleStyleSheet = None
    cm = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None


TAIVAS_TARGET_FIELDS = [
    "timestamp",
    "country",
    "city",
    "lat",
    "lon",
    "temperature",
    "wind_speed",
    "solar_radiation",
    "precipitation",
    "humidity",
    "population",
    "solar_capacity",
    "wind_capacity",
    "geothermal_capacity",
    "hydro_capacity",
    "battery_capacity",
]

TAIVAS_RECOMMENDED_FIELDS = [
    "timestamp",
    "country",
    "city",
    "temperature",
    "wind_speed",
    "solar_radiation",
    "precipitation",
    "humidity",
    "population",
    "solar_capacity",
    "wind_capacity",
    "geothermal_capacity",
    "hydro_capacity",
    "battery_capacity",
]

TAIVAS_NUMERIC_FIELDS = [
    "lat",
    "lon",
    "temperature",
    "wind_speed",
    "solar_radiation",
    "precipitation",
    "humidity",
    "population",
    "solar_capacity",
    "wind_capacity",
    "geothermal_capacity",
    "hydro_capacity",
    "battery_capacity",
]

NON_NEGATIVE_FIELDS = [
    "wind_speed",
    "solar_radiation",
    "precipitation",
    "humidity",
    "population",
    "solar_capacity",
    "wind_capacity",
    "geothermal_capacity",
    "hydro_capacity",
    "battery_capacity",
]

COLUMN_ALIASES = {
    "time": "timestamp",
    "date": "timestamp",
    "datetime": "timestamp",
    "timestamp_utc": "timestamp",
    "country_name": "country",
    "nation": "country",
    "city_name": "city",
    "location": "city",
    "latitude": "lat",
    "longitude": "lon",
    "long": "lon",
    "temp": "temperature",
    "temp_c": "temperature",
    "temperature_c": "temperature",
    "wind": "wind_speed",
    "wind_m_s": "wind_speed",
    "wind_speed_m_s": "wind_speed",
    "solar": "solar_radiation",
    "irradiance": "solar_radiation",
    "solar_irradiance": "solar_radiation",
    "rain": "precipitation",
    "rainfall": "precipitation",
    "precip": "precipitation",
    "humid": "humidity",
    "pop": "population",
    "solar_mw": "solar_capacity",
    "wind_mw": "wind_capacity",
    "geo_capacity": "geothermal_capacity",
    "geothermal_mw": "geothermal_capacity",
    "hydro_mw": "hydro_capacity",
    "battery_mwh": "battery_capacity",
    "storage_capacity": "battery_capacity",
}

PDF_DISCLAIMER = (
    "TAIVAS is a decision-support simulation tool. It does not provide guaranteed "
    "predictions, emergency commands, or final operational decisions. Results should "
    "be reviewed together with real-time data, professional judgment, and institutional protocols."
)


def normalize_column_name(name: object) -> str:
    normalized = str(name).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return COLUMN_ALIASES.get(normalized, normalized)


def normalize_taivas_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    cleaned = df.copy()
    cleaned.columns = [normalize_column_name(col) for col in cleaned.columns]
    duplicate_columns = cleaned.columns[cleaned.columns.duplicated()].tolist()
    if duplicate_columns:
        cleaned = cleaned.loc[:, ~cleaned.columns.duplicated()]
    ordered_columns = [col for col in TAIVAS_TARGET_FIELDS if col in cleaned.columns]
    extra_columns = [col for col in cleaned.columns if col not in ordered_columns]
    cleaned = cleaned[ordered_columns + extra_columns]
    missing = [col for col in TAIVAS_TARGET_FIELDS if col not in cleaned.columns]
    warnings = []
    if duplicate_columns:
        warnings.append(f"Duplicate normalized columns were removed: {', '.join(sorted(set(duplicate_columns)))}")
    if missing:
        warnings.append(f"Missing TAIVAS fields: {', '.join(missing)}")
    return cleaned, warnings


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def validate_taivas_csv_dataframe(df: pd.DataFrame) -> tuple[str, str, pd.DataFrame, pd.DataFrame]:
    cleaned, normalize_warnings = normalize_taivas_dataframe(df)
    issues = []
    for warning in normalize_warnings:
        issues.append({"Severity": "Warning", "Field": "columns", "Issue": warning})

    if cleaned.empty:
        issues.append({"Severity": "Error", "Field": "file", "Issue": "The uploaded CSV has no rows."})

    for field in TAIVAS_RECOMMENDED_FIELDS:
        if field not in cleaned.columns:
            issues.append({"Severity": "Warning", "Field": field, "Issue": "Recommended field is missing."})

    for field in cleaned.columns:
        empty_count = int(cleaned[field].isna().sum() + (cleaned[field].astype(str).str.strip() == "").sum())
        if empty_count > 0:
            severity = "Warning" if field not in ("country", "city") else "Error"
            issues.append({"Severity": severity, "Field": field, "Issue": f"{empty_count} empty value(s) detected."})

    if "timestamp" in cleaned.columns:
        parsed = pd.to_datetime(cleaned["timestamp"], errors="coerce")
        invalid_count = int(parsed.isna().sum())
        if invalid_count > 0:
            issues.append({"Severity": "Warning", "Field": "timestamp", "Issue": f"{invalid_count} timestamp value(s) could not be parsed."})
        duplicate_count = int(cleaned["timestamp"].duplicated().sum())
        if duplicate_count > 0:
            issues.append({"Severity": "Warning", "Field": "timestamp", "Issue": f"{duplicate_count} duplicate timestamp row(s) detected."})

    for field in TAIVAS_NUMERIC_FIELDS:
        if field not in cleaned.columns:
            continue
        numeric_values = pd.to_numeric(cleaned[field], errors="coerce")
        invalid_count = int(numeric_values.isna().sum() - cleaned[field].isna().sum())
        if invalid_count > 0:
            issues.append({"Severity": "Warning", "Field": field, "Issue": f"{invalid_count} non-numeric value(s) detected."})
        if field in NON_NEGATIVE_FIELDS:
            negative_count = int((numeric_values < 0).sum())
            if negative_count > 0:
                issues.append({"Severity": "Warning", "Field": field, "Issue": f"{negative_count} negative value(s) detected."})

    ranges = {
        "temperature": (-60, 70),
        "wind_speed": (0, 80),
        "solar_radiation": (0, 1400),
        "precipitation": (0, 1000),
        "humidity": (0, 100),
        "population": (1, 100000000),
        "solar_capacity": (0, 100000),
        "wind_capacity": (0, 100000),
        "geothermal_capacity": (0, 100000),
        "hydro_capacity": (0, 100000),
        "battery_capacity": (0, 1000000),
    }
    for field, (low, high) in ranges.items():
        if field not in cleaned.columns:
            continue
        numeric_values = pd.to_numeric(cleaned[field], errors="coerce")
        suspicious_count = int(((numeric_values < low) | (numeric_values > high)).sum())
        if suspicious_count > 0:
            issues.append({"Severity": "Warning", "Field": field, "Issue": f"{suspicious_count} suspicious value(s) outside expected range {low} to {high}."})

    for field in ("country", "city"):
        if field in cleaned.columns and cleaned[field].dropna().astype(str).str.strip().nunique() > 1:
            issues.append({"Severity": "Warning", "Field": field, "Issue": f"Multiple {field} values detected. Verify the file is intended for mixed locations."})

    issues_df = pd.DataFrame(issues, columns=["Severity", "Field", "Issue"])
    has_error = not issues_df.empty and (issues_df["Severity"] == "Error").any()
    has_warning = not issues_df.empty and (issues_df["Severity"] == "Warning").any()
    if has_error:
        status = "Error"
        message = "This file is not ready. Please fix the listed issues."
    elif has_warning:
        status = "Warning"
        message = "This file can be used, but some fields need review."
    else:
        status = "Pass"
        message = "This file appears ready for TAIVAS."
    return status, message, issues_df, cleaned


def build_pdf_report(context: dict, results: dict, inputs: dict, notes: str = "") -> bytes:
    if SimpleDocTemplate is None:
        raise RuntimeError("PDF support requires reportlab. Install reportlab or update requirements.txt.")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.6 * cm, leftMargin=1.6 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("TAIVAS Energy Resilience Simulation Report", styles["Title"]),
        Spacer(1, 0.25 * cm),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Spacer(1, 0.35 * cm),
    ]

    summary_rows = [
        ["Country", context.get("country", "-")],
        ["City", context.get("city", "-")],
        ["Scenario", str(context.get("scenario", "-")).replace("_", " ").title()],
        ["Risk Level", context.get("risk_level", results.get("risk_tier", "-"))],
    ]
    capacity_rows = [
        ["Solar Capacity", f"{inputs.get('solar_capacity', '-')} MW"],
        ["Wind Capacity", f"{inputs.get('wind_capacity', '-')} MW"],
        ["Geothermal Capacity", f"{inputs.get('geothermal_capacity', '-')} MW"],
        ["Hydro Capacity", f"{inputs.get('hydro_capacity', '-')} MW"],
        ["Battery Capacity", f"{inputs.get('battery_capacity', '-')} MWh"],
    ]
    output_rows = [
        ["Demand", f"{results.get('demand', '-')} MW"],
        ["Renewable Supply", f"{results.get('renewable_supply', '-')} MW"],
        ["Final Supply", f"{results.get('final_supply', '-')} MW"],
        ["Possible Energy Gap", f"{results.get('shortfall', '-')} MW"],
        ["Renewable Ratio", f"{results.get('renewable_ratio', '-')}%"],
        ["Battery Level", f"{results.get('battery_levels', '-')} MWh"],
        ["System Efficiency", f"{results.get('system_efficiency', '-')}%"],
        ["Grid Dependency", f"{results.get('grid_dependency', '-')}%"],
    ]

    for title, rows in (("Scenario Summary", summary_rows), ("Input Capacity Summary", capacity_rows), ("Key Output Summary", output_rows)):
        story.append(Paragraph(title, styles["Heading2"]))
        table = Table(rows, colWidths=[5.2 * cm, 10.5 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8EEF7")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.35 * cm))

    if notes.strip():
        story.append(Paragraph("Notes", styles["Heading2"]))
        story.append(Paragraph(notes.strip(), styles["Normal"]))
        story.append(Spacer(1, 0.25 * cm))

    story.append(Paragraph("Decision-Support Disclaimer", styles["Heading2"]))
    story.append(Paragraph(PDF_DISCLAIMER, styles["Normal"]))
    doc.build(story)
    return buffer.getvalue()


def safe_filename(value: object) -> str:
    text = str(value or "TAIVAS").strip()
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    return text or "TAIVAS"


def convert_image_file(uploaded_file, output_format: str, quality: int, resize_width: int | None) -> tuple[str, bytes, int, int]:
    if Image is None:
        raise RuntimeError("Image conversion requires Pillow. Install pillow or update requirements.txt.")
    source_bytes = uploaded_file.getvalue()
    with Image.open(BytesIO(source_bytes)) as image:
        image = image.convert("RGB") if output_format.upper() in ("JPEG", "JPG", "WEBP") else image.convert("RGBA")
        if resize_width and resize_width > 0 and image.width > resize_width:
            new_height = max(1, int(image.height * (resize_width / image.width)))
            image = image.resize((resize_width, new_height))
        output = BytesIO()
        save_format = "JPEG" if output_format.upper() == "JPG" else output_format.upper()
        save_kwargs = {}
        if save_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = int(quality)
            save_kwargs["optimize"] = True
        image.save(output, format=save_format, **save_kwargs)
    extension = "jpg" if output_format.upper() in ("JPG", "JPEG") else output_format.lower()
    base_name = safe_filename(".".join(uploaded_file.name.split(".")[:-1]) or uploaded_file.name)
    return f"{base_name}.{extension}", output.getvalue(), len(source_bytes), len(output.getvalue())


def zip_bytes(file_items: list[tuple[str, bytes]]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in file_items:
            archive.writestr(filename, content)
    return buffer.getvalue()


def render_excel_to_csv_tool():
    st.markdown("Convert an Excel sheet into a TAIVAS-compatible CSV. Missing fields are reported as warnings, not hard failures.")
    uploaded_excel = st.file_uploader("Upload Excel file", type=["xlsx", "xls"], key="toolkit_excel_upload")
    if not uploaded_excel:
        return
    try:
        excel_file = pd.ExcelFile(uploaded_excel)
    except Exception as exc:
        st.error(f"Unable to read Excel file: {exc}")
        return
    sheet_name = st.selectbox("Select sheet", excel_file.sheet_names, key="toolkit_excel_sheet")
    try:
        raw_df = pd.read_excel(uploaded_excel, sheet_name=sheet_name)
    except Exception as exc:
        st.error(f"Unable to load selected sheet: {exc}")
        return
    cleaned_df, warnings = normalize_taivas_dataframe(raw_df)
    if warnings:
        for warning in warnings:
            st.warning(warning)
    st.subheader("Preview")
    st.dataframe(cleaned_df.head(20), use_container_width=True)
    st.download_button(
        "Download TAIVAS CSV",
        dataframe_to_csv_bytes(cleaned_df),
        file_name=f"taivas_converted_{safe_filename(sheet_name)}.csv",
        mime="text/csv",
    )


def render_csv_validator_tool():
    st.markdown("Check whether a CSV file is ready for TAIVAS. The validator favors clear warnings over aggressive rejection.")
    uploaded_csv = st.file_uploader("Upload TAIVAS CSV", type=["csv"], key="toolkit_csv_validator")
    if not uploaded_csv:
        return
    try:
        df = pd.read_csv(uploaded_csv)
    except Exception as exc:
        st.error(f"Unable to read CSV file: {exc}")
        return
    status, message, issues_df, cleaned_df = validate_taivas_csv_dataframe(df)
    status_method = st.success if status == "Pass" else st.warning if status == "Warning" else st.error
    status_method(message)
    summary_cols = st.columns(3)
    summary_cols[0].metric("Status", status)
    summary_cols[1].metric("Rows", len(cleaned_df))
    summary_cols[2].metric("Issues", len(issues_df))
    if not issues_df.empty:
        st.subheader("Detected Issues")
        st.dataframe(issues_df, use_container_width=True, hide_index=True)
    st.subheader("Cleaned Preview")
    st.dataframe(cleaned_df.head(20), use_container_width=True)
    st.download_button(
        "Download Cleaned CSV",
        dataframe_to_csv_bytes(cleaned_df),
        file_name="taivas_cleaned.csv",
        mime="text/csv",
    )


def render_pdf_report_tool(current_context: dict, current_results: dict, current_inputs: dict):
    st.markdown("Generate a simple decision-support PDF report from the current TAIVAS simulation result.")
    notes = st.text_area("Optional notes", "", key="toolkit_pdf_notes")
    if st.button("Generate PDF Report", key="toolkit_pdf_generate"):
        try:
            pdf_bytes = build_pdf_report(current_context, current_results, current_inputs, notes)
        except Exception as exc:
            st.error(f"Unable to generate PDF report: {exc}")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = (
            f"TAIVAS_Report_{safe_filename(current_context.get('country'))}_"
            f"{safe_filename(current_context.get('city'))}_{safe_filename(current_context.get('scenario'))}_{timestamp}.pdf"
        )
        st.download_button("Download PDF Report", pdf_bytes, file_name=filename, mime="application/pdf")
        st.success("PDF report generated.")
    st.caption(PDF_DISCLAIMER)


def render_image_converter_tool():
    st.markdown("Convert or compress screenshots and presentation images. HEIC may not be supported unless Pillow can read it in the deployment environment.")
    uploaded_images = st.file_uploader("Upload images", type=["png", "jpg", "jpeg", "webp", "heic"], accept_multiple_files=True, key="toolkit_image_upload")
    output_format = st.selectbox("Output format", ["PNG", "JPG", "WEBP"], key="toolkit_image_format")
    quality = st.slider("Quality for JPG/WEBP", 30, 100, 82, key="toolkit_image_quality")
    resize_enabled = st.checkbox("Resize width", value=False, key="toolkit_image_resize_enabled")
    resize_width = st.number_input("Maximum width in pixels", min_value=100, max_value=6000, value=1600, step=100, disabled=not resize_enabled, key="toolkit_image_width")
    if not uploaded_images:
        return
    converted_items = []
    for uploaded_image in uploaded_images:
        try:
            filename, content, original_size, output_size = convert_image_file(
                uploaded_image,
                output_format,
                quality,
                int(resize_width) if resize_enabled else None,
            )
        except Exception as exc:
            st.error(f"{uploaded_image.name}: {exc}")
            continue
        converted_items.append((filename, content))
        st.write(f"{uploaded_image.name} -> {filename} | {original_size / 1024:.1f} KB -> {output_size / 1024:.1f} KB")
        st.download_button(f"Download {filename}", content, file_name=filename, mime=f"image/{'jpeg' if filename.endswith('.jpg') else output_format.lower()}")
    if len(converted_items) > 1:
        st.download_button("Download All as ZIP", zip_bytes(converted_items), file_name="taivas_converted_images.zip", mime="application/zip")


def render_batch_renamer_tool():
    st.markdown("Create renamed copies of uploaded files and download them as a ZIP. Original files are not renamed on the server.")
    uploaded_files = st.file_uploader("Upload files to rename", accept_multiple_files=True, key="toolkit_rename_upload")
    prefix = st.text_input("Filename prefix", "TAIVAS_Dashboard", key="toolkit_rename_prefix")
    numbering = st.selectbox("Numbering style", ["001, 002, 003...", "01, 02, 03..."], key="toolkit_rename_numbering")
    digits = 3 if numbering.startswith("001") else 2
    if not uploaded_files:
        return
    preview = []
    renamed_items = []
    for index, uploaded_file in enumerate(uploaded_files, start=1):
        extension = uploaded_file.name.split(".")[-1] if "." in uploaded_file.name else "bin"
        new_name = f"{safe_filename(prefix)}_{index:0{digits}d}.{extension}"
        preview.append({"Original Filename": uploaded_file.name, "New Filename": new_name})
        renamed_items.append((new_name, uploaded_file.getvalue()))
    st.subheader("Preview")
    st.dataframe(pd.DataFrame(preview), use_container_width=True, hide_index=True)
    st.download_button("Download Renamed Files ZIP", zip_bytes(renamed_items), file_name=f"{safe_filename(prefix)}_renamed.zip", mime="application/zip")


def render_taivas_utility_toolkit(current_context: dict, current_results: dict, current_inputs: dict):
    st.subheader("TAIVAS Utility Toolkit")
    st.caption("Practical file utilities for TAIVAS workflows. These tools do not change simulation formulas or scenario logic.")
    tabs = st.tabs([
        "Excel to TAIVAS CSV",
        "CSV Validator",
        "PDF Report Exporter",
        "Image Converter",
        "Batch Renamer",
    ])
    with tabs[0]:
        render_excel_to_csv_tool()
    with tabs[1]:
        render_csv_validator_tool()
    with tabs[2]:
        render_pdf_report_tool(current_context, current_results, current_inputs)
    with tabs[3]:
        render_image_converter_tool()
    with tabs[4]:
        render_batch_renamer_tool()
