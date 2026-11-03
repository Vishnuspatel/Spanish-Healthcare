import os
import pandas as pd
import pdfminer.high_level
import pdfminer.layout

# Input PDF files
pdf_files = [
    ("2022", "Datos_ccaa_dic2022.pdf"),
    ("2023", "Datos_ccaa_dic2023.pdf"),
    ("2024", "Datos_ccaa_dic2024.pdf"),
]

ccaa_list = [
    "ANDALUCÍA",
    "ANDALUCIA",
    "ARAGON",
    "PDO DE ASTURIAS",
    "BALEARES",
    "CANARIAS",
    "CANTABRIA",
    "CASTILLA Y LEON",
    "CASTILLA-LA MANCHA",
    "CATALUÑA",
    "CATALUNA",
    "COMUNIDAD VALENCIANA",
    "EXTREMADURA",
    "GALICIA",
    "MADRID",
    "MURCIA",
    "C. FORAL DE NAVARRA",
    "PAÍS VASCO",
    "PAIS VASCO",
    "RIOJA",
    "CEUTA",
    "MELILLA",
]

# Column definitions
cols_table1 = [
    "Comunidad Autónoma",
    "Cirugía General y de Digestivo",
    "Ginecología",
    "Oftalmología",
    "ORL",
    "Traumatología",
    "Urología",
    "Cirugía Cardíaca",
    "Angiología/Cir. Vascular",
    "Cirugía Maxilofacial",
    "Cirugía Pediátrica",
    "Cirugía Plástica",
    "Cirugía Torácica",
    "Neurocirugía",
    "Dermatología",
]

cols_table2 = cols_table1

cols_table3 = [
    "Comunidad Autónoma",
    "Catarata",
    "Hernia Inguinal/Crural",
    "Prótesis Cadera",
    "Artroscopia",
    "Várices MM.II.",
    "Colecistectomía",
    "Hallux Valgus",
    "Adenoamigdalectomía",
    "Hipertrofia Benigna de Próstata",
    "Quiste Pilonidal",
    "Túnel Carpiano",
    "Total Procesos Seleccionados",
    "Prótesis Rodilla",
    "Cirugía Cardíaca Valvular",
    "By-pass Coronario",
    "Histerectomía",
]

cols_table4 = [
    "Comunidad Autónoma",
    "TOTAL",
    "Ginecología",
    "Oftalmología",
    "Traumatología",
    "Dermatología",
    "ORL",
    "Neurología",
    "C.Gral y A.Digestivo",
    "Urología",
    "Digestivo",
    "Cardiología",
]

# X-bins for Tables 1 & 2 (14 specialty columns)
x_bins_14 = [
    (175, 220),
    (220, 275),
    (275, 315),
    (315, 345),
    (345, 400),
    (400, 445),
    (445, 480),
    (480, 520),
    (520, 560),
    (560, 600),
    (600, 635),
    (635, 670),
    (670, 720),
    (720, 780),
]

# X-bins for Table 3 Selected Procedures (16 specialty columns)
x_bins_17 = [
    (170, 215),
    (215, 260),
    (260, 305),
    (305, 345),
    (345, 385),
    (385, 425),
    (425, 465),
    (465, 505),
    (505, 545),
    (545, 585),
    (585, 625),
    (625, 670),
    (670, 710),
    (710, 740),
    (740, 770),
    (770, 805),
]

# X-bins for Table 4 Consultations (11 specialty columns)
x_bins_11 = [
    (170, 230),
    (230, 280),
    (280, 330),
    (330, 380),
    (380, 430),
    (430, 480),
    (480, 530),
    (530, 580),
    (580, 630),
    (630, 680),
    (680, 780),
]


def extract_table_by_bins(pdf_path, page_num, x_bins, col_names):
  rows_data = []
  for page_layout in pdfminer.high_level.extract_pages(
      pdf_path, page_numbers=[page_num - 1]
  ):
    line_elements = []
    for element in page_layout:
      if isinstance(element, pdfminer.layout.LTTextContainer):
        for text_line in element:
          txt = text_line.get_text().strip()
          if txt:
            bbox = text_line.bbox
            line_elements.append((bbox[0], bbox[1], bbox[2], bbox[3], txt))

    line_elements.sort(key=lambda k: -k[1])

    rows = []
    current_y = None
    current_row = []
    for el in line_elements:
      y = el[1]
      if current_y is None or abs(y - current_y) > 6:
        if current_row:
          rows.append(current_row)
        current_row = [el]
        current_y = y
      else:
        current_row.append(el)
    if current_row:
      rows.append(current_row)

    for row in rows:
      row_text = " ".join([e[4] for e in row])
      matched_ccaa = None
      for ccaa in ccaa_list:
        if row_text.startswith(ccaa) or any(
            e[4].startswith(ccaa) for e in row if e[0] < 140
        ):
          matched_ccaa = ccaa
          break

      if matched_ccaa:
        bin_values = [pd.NA] * len(x_bins)
        for el in row:
          x0 = el[0]
          txt = el[4]
          if x0 < 140:
            continue
          for b_idx, (b_min, b_max) in enumerate(x_bins):
            if b_min <= x0 < b_max:
              clean_val = (
                  txt.replace(".", "").replace(",", ".")
                  if isinstance(txt, str)
                  else txt
              )
              bin_values[b_idx] = clean_val
              break
        rows_data.append([matched_ccaa] + bin_values)

  return pd.DataFrame(rows_data, columns=col_names)


# Execution loop across all years
t1_all, t2_all, t3_all, t4_all = [], [], [], []

for year, pdf_path in pdf_files:
  if not os.path.exists(pdf_path):
    continue

  # Page 3: Table 1 (Lower half - Rates per 1000)
  df_p3 = extract_table_by_bins(pdf_path, 3, x_bins_14, cols_table1)
  if not df_p3.empty:
    df_p3.insert(0, "Year", year)
    t1_all.append(df_p3.iloc[len(df_p3) // 2 :])

  # Page 4: Table 2 (Upper half - Surgical Avg Days)
  df_p4 = extract_table_by_bins(pdf_path, 4, x_bins_14, cols_table2)
  if not df_p4.empty:
    df_p4.insert(0, "Year", year)
    t2_all.append(df_p4.iloc[: len(df_p4) // 2])

  # Page 6: Table 3 (Lower half - Selected Procedures % > 6 Months)
  df_p6 = extract_table_by_bins(pdf_path, 6, x_bins_17, cols_table3)
  if not df_p6.empty:
    df_p6.insert(0, "Year", year)
    t3_all.append(df_p6.iloc[len(df_p6) // 2 :])

  # Page 8: Table 4 (Upper half - Consultations Avg Days)
  df_p8 = extract_table_by_bins(pdf_path, 8, x_bins_11, cols_table4)
  if not df_p8.empty:
    df_p8.insert(0, "Year", year)
    t4_all.append(df_p8.iloc[: len(df_p8) // 2])

# Save final aligned CSVs (including Table 3)
if t1_all:
  pd.concat(t1_all, ignore_index=True).to_csv(
      "Table_1_Surgical_Rates_Aligned.csv", index=False
  )
if t2_all:
  pd.concat(t2_all, ignore_index=True).to_csv(
      "Table_2_Surgical_Avg_Days_Aligned.csv", index=False
  )
if t3_all:
  pd.concat(t3_all, ignore_index=True).to_csv(
      "Table_3_Procedures_Pct_Aligned.csv", index=False
  )
if t4_all:
  pd.concat(t4_all, ignore_index=True).to_csv(
      "Table_4_Consultations_Aligned.csv", index=False
  )