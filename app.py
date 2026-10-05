import streamlit as st
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, PatternFill, Font, Border, Side
from io import BytesIO

# ตั้งค่าหน้าเว็บให้กว้างขึ้น
st.set_page_config(page_title="Raw Mat Tag Generator", layout="centered")

def get_color(material_type):
    # กำหนดสีตาม Material
    mat = str(material_type).upper()
    if 'STEEL' in mat or 'EAX' in mat: return 'D9D9D9' # สีเทา
    if 'INCO' in mat or 'HCX' in mat or 'QMP' in mat: return 'FCE4D6' # สีส้มอ่อน
    if 'TITANIUM' in mat or 'TAF' in mat or 'TBB' in mat or 'TDY' in mat: return 'D9E1F2' # สีฟ้าอ่อน
    if 'A286' in mat: return 'FFF2CC' # สีเหลืองอ่อน
    return 'FFFFFF' # สีขาว (Default)

st.title("🏷️ ระบบสร้าง Raw Mat Tag อัตโนมัติ")
st.markdown("โปรแกรมสำหรับดึงข้อมูลจาก Master List มาสร้าง Tag พร้อมปริ้นท์ (4 ชิ้น/หน้า A4)")

# 1. ส่วนอัปโหลดไฟล์
uploaded_file = st.file_uploader("1. อัปโหลดไฟล์ Master List (Excel .xlsx)", type=["xlsx"])

# 2. ส่วนกรอกข้อมูล
cert_id = st.text_input("2. กรอก Certificate ID (เช่น KUB8620C, 000788492):")

# 3. ปุ่มกดดำเนินการ
if st.button("สร้าง Tag", type="primary"):
    if uploaded_file is None:
        st.warning("⚠️ กรุณาอัปโหลดไฟล์ Master List ก่อนครับ")
    elif not cert_id:
        st.warning("⚠️ กรุณากรอก Certificate ID")
    else:
        try:
            with st.spinner('กำลังค้นหาข้อมูลและสร้าง Tag...'):
                # อ่านไฟล์ Excel (เริ่มที่บรรทัดที่ 7)
                df = pd.read_excel(uploaded_file, sheet_name='05.075_8_LTL', header=6)
                col_cert = df.columns[9]
                
                # ค้นหา Cert ID
                df_match = df[df[col_cert].astype(str).str.strip() == cert_id.strip()]

                if df_match.empty:
                    st.error(f"❌ ไม่พบ Certificate ID: {cert_id} ในไฟล์ที่อัปโหลด")
                else:
                    # สร้าง Excel สำหรับปริ้นท์
                    wb = Workbook()
                    ws = wb.active
                    ws.title = "Print_Tags"
                    ws.page_setup.paperSize = ws.PAPERSIZE_A4

                    tag_count = 0
                    for idx, row in df_match.iterrows():
                        # ดึงข้อมูลจากคอลัมน์
                        symbol = str(row.iloc[0]) if pd.notna(row.iloc[0]) else "-"
                        mfg = str(row.iloc[2]) if pd.notna(row.iloc[2]) else "-"
                        mat_type = str(row.iloc[6]) if pd.notna(row.iloc[6]) else "-"
                        spec = str(row.iloc[7]) if pd.notna(row.iloc[7]) else "-"
                        heat = str(row.iloc[8]) if pd.notna(row.iloc[8]) else "-"
                        cert = str(row.iloc[9]) if pd.notna(row.iloc[9]) else "-"
                        dia = str(row.iloc[10]) if pd.notna(row.iloc[10]) else "-"
                        
                        # จำนวนที่ต้องสร้าง
                        qty_val = row.iloc[19]
                        try:
                            qty = int(qty_val)
                        except:
                            qty = 1

                        color = get_color(mat_type)

                        # วนลูปสร้างตามจำนวน Qty
                        for _ in range(qty):
                            tag_count += 1
                            page_index = (tag_count - 1) // 4
                            pos_in_page = (tag_count - 1) % 4
                            base_row = (page_index * 42) + 2 

                            # กำหนดตำแหน่งในหน้ากระดาษ (ซ้าย-ขวา, บน-ล่าง)
                            if pos_in_page == 0:   start_row, start_col = base_row, 2
                            elif pos_in_page == 1: start_row, start_col = base_row, 8
                            elif pos_in_page == 2: start_row, start_col = base_row + 20, 2
                            else:                  start_row, start_col = base_row + 20, 8

                            # วาด Tag
                            ws.merge_cells(start_row=start_row, start_column=start_col, end_row=start_row+15, end_column=start_col+4)
                            cell = ws.cell(row=start_row, column=start_col)
                            
                            text = f"{symbol}\n{heat}\n{mfg}\n{dia}\n\n\nCert ID : {cert}\n{mat_type}\n{spec}"
                            cell.value = text
                            cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
                            cell.font = Font(name="Arial", size=16, bold=True)
                            cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
                            
                            thin = Side(border_style="medium", color="000000")
                            cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

                            # จัดความกว้างคอลัมน์
                            for col_letter in ['B','C','D','E','F','H','I','J','K','L']:
                                ws.column_dimensions[col_letter].width = 8
                            ws.column_dimensions['G'].width = 4

                    if tag_count > 0:
                        # บันทึกไฟล์ไว้ในหน่วยความจำชั่วคราว (ไม่เซฟลงเครื่องเซิร์ฟเวอร์)
                        output = BytesIO()
                        wb.save(output)
                        output.seek(0)
                        
                        st.success(f"✅ สร้าง Tag เสร็จสมบูรณ์ จำนวน {tag_count} ใบ!")
                        
                        # ปุ่มให้ User ดาวน์โหลด
                        st.download_button(
                            label="📥 ดาวน์โหลดไฟล์ Tag (.xlsx)",
                            data=output,
                            file_name=f"Tags_Output_{cert_id}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผล: {e}")
