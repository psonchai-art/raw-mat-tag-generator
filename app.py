import streamlit as st
import pandas as pd
from io import BytesIO
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Raw Mat Tag PDF Generator", layout="centered")

st.title("🏷️ ระบบสร้าง Raw Mat Tag (ส่งออกเป็น PDF)")
st.markdown("ระบบจะดึงข้อมูลจาก Master List มาสร้าง Tag 4 ใบ/หน้า ตามดีไซน์มาตรฐาน")

def get_bg_color(material_type):
    # กำหนดสีพื้นหลังของ Tag ตามชนิด Material
    mat = str(material_type).upper()
    if 'STEEL' in mat or 'EAX' in mat: return colors.HexColor('#CCCCCC') # สีเทา
    if 'INCO' in mat or 'HCX' in mat or 'QMP' in mat: return colors.HexColor('#F4B183') # สีส้ม
    if 'TITANIUM' in mat or 'TAF' in mat or 'TBB' in mat or 'TDY' in mat: return colors.HexColor('#9DC3E6') # สีฟ้า
    if 'A286' in mat: return colors.HexColor('#FFE699') # สีเหลือง
    return colors.HexColor('#E7E6E6') # สีเทาอ่อน (Default)

def draw_tag(c, x, y, width, height, data, bg_color):
    # ฟังก์ชันวาด Tag 1 ใบ
    
    # 1. วาดเส้นประรอบนอก
    c.setDash(6, 4) # เส้นประ
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.roundRect(x, y, width, height, 5) # วาดสี่เหลี่ยมมุมโค้ง
    
    # วาดกรอบสีทึบด้านใน (เว้นขอบจากเส้นประนิดหน่อย)
    inner_margin = 3 * mm
    in_x, in_y = x + inner_margin, y + inner_margin
    in_w, in_h = width - (2 * inner_margin), height - (2 * inner_margin)
    
    c.setDash() # ยกเลิกเส้นประ
    c.setFillColor(bg_color)
    c.roundRect(in_x, in_y, in_w, in_h, 5, fill=1)
    
    c.setFillColor(colors.black)
    c.setLineWidth(1.5)
    
    # 2. ตีเส้นตารางภายใน
    # เส้นขอบตารางใหญ่
    c.rect(in_x + 2*mm, in_y + 8*mm, in_w - 4*mm, in_h - 10*mm) 
    
    # เส้นแนวนอน
    y_row1 = in_y + in_h - 32*mm # ใต้ Symbol
    y_row2 = y_row1 - 12*mm      # ใต้ Mat type/Heat/Supplier
    y_row3 = y_row2 - 12*mm      # ใต้ Dia/Weight/Position
    
    c.line(in_x + 2*mm, y_row1, in_x + in_w - 2*mm, y_row1)
    c.line(in_x + 2*mm, y_row2, in_x + in_w - 2*mm, y_row2)
    c.line(in_x + 2*mm, y_row3, in_x + in_w - 2*mm, y_row3)
    
    # เส้นแนวตั้ง (แบ่ง 3 ช่อง)
    col1_x = in_x + 2*mm + (in_w - 4*mm) / 3.5
    col2_x = col1_x + (in_w - 4*mm) / 2.5
    
    c.line(col1_x, y_row1, col1_x, y_row3)
    c.line(col2_x, y_row1, col2_x, y_row3)

    # 3. ใส่ตัวหนังสือ
    # ใช้ฟอนต์มาตรฐานของ PDF ไปก่อน (ถ้าต้องการฟอนต์เฉพาะ ต้องโหลดไฟล์ .ttf มาฝัง)
    
    # Header: Material Symbol
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(in_x + in_w/2, in_y + in_h - 10*mm, "Material Symbol")
    
    # Symbol Value (ตัวใหญ่)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(in_x + in_w/2, in_y + in_h - 26*mm, data['symbol'])
    c.setFillColor(colors.black)
    
    # Row 1 Labels
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(in_x + 2*mm + (col1_x - (in_x + 2*mm))/2, y_row1 - 4*mm, "Mat type")
    c.drawCentredString(col1_x + (col2_x - col1_x)/2, y_row1 - 4*mm, "Heat")
    c.drawCentredString(col2_x + (in_x + in_w - 2*mm - col2_x)/2, y_row1 - 4*mm, "Supplier")
    
    # Row 1 Values (ตัวหนังสือสีขาว)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(in_x + 2*mm + (col1_x - (in_x + 2*mm))/2, y_row1 - 8*mm, data['mat_type'][:12]) # ตัดคำยาว
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(col1_x + (col2_x - col1_x)/2, y_row1 - 10*mm, data['heat'])
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(col2_x + (in_x + in_w - 2*mm - col2_x)/2, y_row1 - 9*mm, data['mfg'][:10])
    
    # Row 2 Labels
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(in_x + 2*mm + (col1_x - (in_x + 2*mm))/2, y_row2 - 4*mm, "Diameter")
    c.drawCentredString(col1_x + (col2_x - col1_x)/2, y_row2 - 4*mm, "Weigh")
    c.drawCentredString(col2_x + (in_x + in_w - 2*mm - col2_x)/2, y_row2 - 4*mm, "Position")
    
    # Row 2 Values (ตัวหนังสือสีขาว)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(in_x + 2*mm + (col1_x - (in_x + 2*mm))/2, y_row2 - 9*mm, data['dia'])
    c.drawCentredString(col1_x + (col2_x - col1_x)/2, y_row2 - 9*mm, "") # Weight ไม่มีใน DB
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(col2_x + (in_x + in_w - 2*mm - col2_x)/2, y_row2 - 9*mm, "WOOD BOX")
    
    # Comment & Cer ID
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(in_x + 5*mm, y_row3 - 6*mm, "Comment :")
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(in_x + in_w/2, y_row3 - 18*mm, f"Cer ID: {data['cert']}")
    
    # รหัสเอกสารมุมขวาล่าง
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    c.drawRightString(in_x + in_w - 5*mm, in_y + 3*mm, "05.078_6_LTL")


# 1. ส่วนรับไฟล์
master_file = st.file_uploader("1. อัปโหลดไฟล์ Master List", type=["xlsx"])
cert_id = st.text_input("2. กรอก Certificate ID (เช่น 001391022):")

if st.button("สร้าง Tag (PDF)", type="primary"):
    if not master_file:
        st.warning("⚠️ กรุณาอัปโหลดไฟล์ Master List")
    elif not cert_id:
        st.warning("⚠️ กรุณากรอก Certificate ID")
    else:
        try:
            with st.spinner('กำลังสร้างไฟล์ PDF...'):
                df = pd.read_excel(master_file, sheet_name='05.075_8_LTL', header=6)
                col_cert = df.columns[9]
                df_match = df[df[col_cert].astype(str).str.strip() == cert_id.strip()]
                
                if df_match.empty:
                    st.error(f"❌ ไม่พบ Certificate ID: {cert_id}")
                else:
                    row = df_match.iloc[0]
                    # ดึงข้อมูล
                    data = {
                        'symbol': str(row.iloc[0]) if pd.notna(row.iloc[0]) else "-",
                        'mfg': str(row.iloc[2]) if pd.notna(row.iloc[2]) else "-",
                        'mat_type': str(row.iloc[6]) if pd.notna(row.iloc[6]) else "-",
                        'spec': str(row.iloc[7]) if pd.notna(row.iloc[7]) else "-",
                        'heat': str(row.iloc[8]) if pd.notna(row.iloc[8]) else "-",
                        'cert': str(row.iloc[9]) if pd.notna(row.iloc[9]) else "-",
                        'dia': str(row.iloc[10]) if pd.notna(row.iloc[10]) else "-",
                    }
                    
                    try: qty = int(row.iloc[19])
                    except: qty = 1
                    
                    if qty <= 0:
                        st.error("จำนวน Tag ที่ต้องสร้าง (Qty) เป็น 0")
                        st.stop()
                        
                    bg_color = get_bg_color(data['mat_type'])
                    
                    # เริ่มสร้าง PDF
                    pdf_buffer = BytesIO()
                    c = canvas.Canvas(pdf_buffer, pagesize=A4)
                    page_w, page_h = A4
                    
                    # กำหนดขนาด Tag และระยะห่าง (ปรับจูนให้พอดี A4)
                    tag_w = 90 * mm
                    tag_h = 120 * mm
                    margin_x = (page_w - (2 * tag_w)) / 3
                    margin_y = (page_h - (2 * tag_h)) / 3
                    
                    pos_coords = [
                        (margin_x, page_h - margin_y - tag_h),                     # บนซ้าย
                        (margin_x * 2 + tag_w, page_h - margin_y - tag_h),         # บนขวา
                        (margin_x, page_h - (margin_y * 2) - (tag_h * 2)),         # ล่างซ้าย
                        (margin_x * 2 + tag_w, page_h - (margin_y * 2) - (tag_h * 2)) # ล่างขวา
                    ]
                    
                    tag_count = 0
                    for _ in range(qty):
                        pos_in_page = tag_count % 4
                        if tag_count > 0 and pos_in_page == 0:
                            c.showPage() # ขึ้นหน้าใหม่เมื่อครบ 4 ชิ้น
                            
                        x, y = pos_coords[pos_in_page]
                        draw_tag(c, x, y, tag_w, tag_h, data, bg_color)
                        tag_count += 1
                        
                    c.save()
                    pdf_buffer.seek(0)
                    
                    st.success(f"✅ สำเร็จ! สร้าง Tag จำนวน {qty} ใบ")
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์ Tag (.pdf)",
                        data=pdf_buffer,
                        file_name=f"Tag_{cert_id}.pdf",
                        mime="application/pdf"
                    )
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
