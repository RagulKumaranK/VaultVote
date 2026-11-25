import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import config
from database import get_db_connection, log_enrollment

# Dimensions for PDF canvas (PVC card standard ~100mm x 66mm aspect)
CARD_WIDTH = 100 * mm
CARD_HEIGHT = 66 * mm

LABELS_DIR = os.path.join(config.STATIC_DIR, 'img', 'card_labels')

def _get_font(font_name: str, size: int, fallback_names: list = None, font_index: int = 0):
    fonts_dir = r"C:\Windows\Fonts"
    candidates = [font_name] + (fallback_names or [])
    for cand in candidates:
        full_path = os.path.join(fonts_dir, cand)
        if os.path.exists(full_path):
            try:
                if cand.lower().endswith('.ttc'):
                    return ImageFont.truetype(full_path, size, index=font_index)
                return ImageFont.truetype(full_path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def _get_label_image(filename: str):
    path = os.path.join(LABELS_DIR, filename)
    if os.path.exists(path):
        try:
            return Image.open(path).convert('RGBA')
        except Exception:
            pass
    return None

def generate_voter_card_image(voter: dict) -> str:
    """
    Renders a high-resolution PVC-style Voter ID Card PNG (1024 x 682)
    using the official Election Commission of India card template with pixel-perfect alignment.
    Saves to static/uploads/cards/{voter_id}_card.png and returns the absolute path.
    """
    voter_id = voter['voter_id']
    template_path = os.path.join(config.STATIC_DIR, 'img', 'voter_card_template.png')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Voter card base template not found at {template_path}")
        
    card = Image.open(template_path).convert('RGBA')
    draw = ImageDraw.Draw(card)

    # Standard high-fidelity fonts (Pure Pillow)
    font_epic_lbl = _get_font("segoeuib.ttf", 25, ["arialbd.ttf"])
    font_epic_val = _get_font("segoeuib.ttf", 27, ["arialbd.ttf"])
    font_val = _get_font("segoeuib.ttf", 19, ["arialbd.ttf"])
    font_fallback_lbl = _get_font("segoeuib.ttf", 17, ["arialbd.ttf"])
    font_badge = _get_font("segoeuib.ttf", 13, ["arialbd.ttf"])
    font_sig = _get_font("LHANDW.TTF", 34, ["BRUSHSCI.TTF", "segoeui.ttf"])
    font_sig_lbl = _get_font("segoeui.ttf", 13, ["arial.ttf"])
    font_qr_lbl = _get_font("segoeuib.ttf", 14, ["arialbd.ttf"])
    font_date = _get_font("segoeuib.ttf", 17, ["arialbd.ttf"])
    font_footer = _get_font("segoeui.ttf", 14, ["arial.ttf"])

    # 1. Ashoka Watermark in Center Background
    wm_path = os.path.join(config.STATIC_DIR, 'img', 'ashoka_watermark.png')
    if os.path.exists(wm_path):
        try:
            wm = Image.open(wm_path).convert('RGBA')
            card.paste(wm, (610, 275), wm)
        except Exception as e:
            print(f"Notice: Ashoka watermark overlay skipped: {e}")

    # 2. EPIC Number inside Blue Pill (Centered between Photo and QR)
    # Exact coordinates matching the official card layout: x=286, y=180, w=377, h=46
    px0, py0, pw, ph = 286, 180, 377, 46
    draw.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=12, fill='#EFF6FF', outline='#2563EB', width=2)
    draw.text((px0 + 26, py0 + 7), "EPIC No. : ", fill='#0F2B48', font=font_epic_lbl)
    draw.text((px0 + 160, py0 + 6), voter_id, fill='#0F2B48', font=font_epic_val)

    # 3. Voter Photograph (Left Column: x=51, y=214, w=203, h=220)
    photo_w, photo_h = 203, 220
    photo_x, photo_y = 51, 214
    photo_drawn = False

    if voter.get('photo_path'):
        photo_full = os.path.join(config.STATIC_DIR, voter['photo_path'])
        if os.path.exists(photo_full):
            try:
                src_photo = Image.open(photo_full).convert('RGBA')
                fitted_photo = ImageOps.fit(src_photo, (photo_w, photo_h), Image.Resampling.LANCZOS)
                
                # Apply rounded corner mask
                mask = Image.new('L', (photo_w, photo_h), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([0, 0, photo_w, photo_h], radius=8, fill=255)
                
                card.paste(fitted_photo, (photo_x, photo_y), mask)
                photo_drawn = True
            except Exception as e:
                print(f"Error processing voter photo for card: {e}")

    if not photo_drawn:
        placeholder = Image.new('RGB', (photo_w, photo_h), color=(241, 245, 249))
        p_draw = ImageDraw.Draw(placeholder)
        p_draw.rounded_rectangle([0, 0, photo_w, photo_h], radius=8, fill=(241, 245, 249))
        p_draw.text((photo_w // 2 - 32, photo_h // 2 - 12), "PHOTO", fill=(100, 116, 139), font=font_val)
        card.paste(placeholder, (photo_x, photo_y))

    # Photo Outer Border
    draw.rounded_rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], radius=8, outline='#002147', width=2)

    # 4. Biometric Enrolled Badge (Directly below photo)
    bx, by, bw, bh = photo_x, 444, photo_w, 38
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=6, fill='#F0FDF4', outline='#16A34A', width=2)
    cx, cy, cr = bx + 18, by + 19, 10
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill='#16A34A')
    draw.line([(cx - 4, cy), (cx - 1, cy + 4), (cx + 5, cy - 4)], fill='#FFFFFF', width=2)
    draw.text((bx + 38, by + 10), "BIOMETRIC ENROLLED", fill='#15803D', font=font_badge)

    # 5. Holder's Signature Area
    name = voter.get('full_name', 'Voter').strip()
    name_parts = name.split()
    if len(name_parts) >= 2:
        sig_text = f"{name_parts[0]} {name_parts[-1][0]}."
    elif name_parts:
        sig_text = name_parts[0]
    else:
        sig_text = "Signature"

    draw.text((85, 512), sig_text, fill='#1E3A8A', font=font_sig)
    draw.line([(photo_x + 10, 558), (photo_x + photo_w - 10, 558)], fill='#0F2B48', width=1)
    draw.text((75, 564), "Holder's Signature", fill='#475569', font=font_sig_lbl)

    # 6. Dynamic QR Code (Top-Right: x=788, y=232, w=170, h=170)
    qr_w, qr_h = 170, 170
    qr_x, qr_y = 788, 232
    qr_drawn = False

    if voter.get('qr_image_path'):
        qr_full = os.path.join(config.STATIC_DIR, voter['qr_image_path'])
        if os.path.exists(qr_full):
            try:
                src_qr = Image.open(qr_full).convert('RGBA')
                resized_qr = src_qr.resize((qr_w, qr_h), Image.Resampling.LANCZOS)
                card.paste(resized_qr, (qr_x, qr_y))
                qr_drawn = True
            except Exception as e:
                print(f"Error processing QR code for card: {e}")

    if qr_drawn:
        draw.rectangle([qr_x, qr_y, qr_x + qr_w, qr_y + qr_h], outline='#CBD5E1', width=1)
    draw.text((qr_x + 36, qr_y + qr_h + 8), "Scan to verify", fill='#334155', font=font_qr_lbl)

    # 7. Security Hologram Sticker (Bottom-Right, directly under QR)
    holo_path = os.path.join(config.STATIC_DIR, 'img', 'eci_hologram_clean.png')
    if os.path.exists(holo_path):
        try:
            holo = Image.open(holo_path).convert('RGBA')
            card.paste(holo, (815, 475), holo)
        except Exception as e:
            print(f"Notice: Hologram overlay skipped: {e}")

    # 8. Bilingual Details Table with strictly aligned columns
    x_lbl = 280
    x_colon = 430
    x_val = 448

    # Helper to paste label or fallback to text
    def paste_or_text(lbl_filename, fallback_text, x, y, font=font_fallback_lbl):
        img = _get_label_image(lbl_filename)
        if img:
            card.paste(img, (x, y), img)
        else:
            draw.text((x, y), fallback_text, fill='#0F172A', font=font)

    # Row 1: Full Name
    paste_or_text('lbl_name.png', "Name", x_lbl, 246)
    draw.text((x_colon, 246), ":", fill='#0F172A', font=font_val)
    draw.text((x_val, 246), voter.get('full_name', ''), fill='#0F172A', font=font_val)

    # Row 2: Father's Name (Two lines: Hindi on top, English below)
    paste_or_text('lbl_father_hi.png', "Father's Name", x_lbl, 282)
    paste_or_text('lbl_father_en.png', "", x_lbl, 304)
    draw.text((x_colon, 292), ":", fill='#0F172A', font=font_val)
    draw.text((x_val, 292), voter.get('father_name', ''), fill='#0F172A', font=font_val)

    # Row 3: Gender
    paste_or_text('lbl_gender.png', "Gender", x_lbl, 338)
    draw.text((x_colon, 338), ":", fill='#0F172A', font=font_val)
    gender_raw = voter.get('gender', 'Male')
    if gender_raw == 'Male':
        val_img = _get_label_image('val_gender_male.png')
        if val_img:
            card.paste(val_img, (x_val, 338), val_img)
        else:
            draw.text((x_val, 338), "Male", fill='#0F172A', font=font_val)
    elif gender_raw == 'Female':
        val_img = _get_label_image('val_gender_female.png')
        if val_img:
            card.paste(val_img, (x_val, 338), val_img)
        else:
            draw.text((x_val, 338), "Female", fill='#0F172A', font=font_val)
    else:
        val_img = _get_label_image('val_gender_other.png')
        if val_img:
            card.paste(val_img, (x_val, 338), val_img)
        else:
            draw.text((x_val, 338), gender_raw, fill='#0F172A', font=font_val)

    # Row 4: Age & DOB
    paste_or_text('lbl_age.png', "Age", x_lbl, 378)
    draw.text((x_colon, 378), ":", fill='#0F172A', font=font_val)
    age_str = f"{voter.get('age', '')} Years (DOB: {voter.get('dob', '')})"
    draw.text((x_val, 378), age_str, fill='#0F172A', font=font_val)

    # Row 5: Identity No. / Protected Aadhaar (Two lines: Hindi on top, English below)
    paste_or_text('lbl_id_hi.png', "Identity No.", x_lbl, 414)
    paste_or_text('lbl_id_en.png', "", x_lbl, 436)
    draw.text((x_colon, 424), ":", fill='#0F172A', font=font_val)
    aadhaar_str = f"{voter.get('aadhaar_masked', 'XXXX-XXXX-XXXX')} (Protected)"
    draw.text((x_val, 424), aadhaar_str, fill='#0F172A', font=font_val)

    # Row 6: Address (Street on line 1, District + State + PIN on line 2)
    paste_or_text('lbl_address.png', "Address", x_lbl, 464)
    draw.text((x_colon, 464), ":", fill='#0F172A', font=font_val)
    
    street = voter.get('address', '').strip()
    area_parts = [voter.get('district', ''), voter.get('state', '')]
    if voter.get('pincode'):
        area_parts.append(str(voter.get('pincode')))
    area_str = ", ".join([p.strip() for p in area_parts if p and str(p).strip()])
    
    # Format line 1 & line 2 cleanly
    if street and area_str:
        if len(street) > 34:
            wrapped = textwrap.wrap(street, width=34)
            line1 = wrapped[0] + ("," if not wrapped[0].endswith(",") else "")
            line2 = area_str
        else:
            line1 = street + ("," if not street.endswith(",") else "")
            line2 = area_str
    elif street:
        wrapped = textwrap.wrap(street, width=34)
        line1 = wrapped[0]
        line2 = wrapped[1] if len(wrapped) > 1 else ""
    else:
        line1 = area_str
        line2 = ""

    draw.text((x_val, 464), line1, fill='#0F172A', font=font_val)
    if line2:
        draw.text((x_val, 488), line2, fill='#0F172A', font=font_val)

    # 9. ECI Circular Stamp (Positioned at x=422, y=517 below details so it never overlaps colons or address)
    stamp_path = os.path.join(config.STATIC_DIR, 'img', 'eci_stamp_clean.png')
    if os.path.exists(stamp_path):
        try:
            stamp = Image.open(stamp_path).convert('RGBA').resize((122, 122), Image.Resampling.LANCZOS)
            card.paste(stamp, (422, 517), stamp)
        except Exception as e:
            print(f"Notice: ECI stamp overlay skipped: {e}")

    # 10. Issued Details (Positioned between Stamp and Hologram)
    issue_date = datetime.now().strftime("%d/%m/%Y")
    draw.text((585, 552), "Issued On :", fill='#0F172A', font=font_date)
    draw.text((685, 552), issue_date, fill='#0F172A', font=font_date)
    draw.text((585, 580), "Issued At  :", fill='#0F172A', font=font_date)
    state_display = voter.get('state', 'India')
    if state_display == 'TamilNadu':
        state_display = 'Tamil Nadu'
    draw.text((685, 580), state_display, fill='#0F172A', font=font_date)

    # 11. Security Footer Bar (Deep Navy with bilingual statutory notice)
    footer_img = Image.new("RGB", (1024, 48), (0, 32, 74))
    card.paste(footer_img, (0, 634))
    f_draw = ImageDraw.Draw(card)
    f_draw.text((60, 648), "Not Transferable  •  Valid Only for Electoral Purposes", fill='#FFFFFF', font=font_footer)
    
    footer_hi = _get_label_image('footer_hindi.png')
    if footer_hi:
        card.paste(footer_hi, (575, 646), footer_hi)
    else:
        f_draw.text((575, 648), "Valid Only for Electoral Purposes", fill='#FFFFFF', font=font_footer)

    # Save rendered PNG image
    os.makedirs(config.CARDS_DIR, exist_ok=True)
    out_png_path = os.path.join(config.CARDS_DIR, f"{voter_id}_card.png")
    card.convert('RGB').save(out_png_path, "PNG", quality=95)

    return out_png_path

def generate_voter_id_card_pdf(voter_id: str) -> str:
    """
    Generates an official high-resolution PVC-style Voter ID Card (PNG + PDF)
    matching the Election Commission of India digital card specifications.
    Saves to static/uploads/cards/{voter_id}_card.pdf and returns the relative path.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT v.*, fb.photo_path, qr.qr_token, qr.qr_image_path
        FROM voters v
        LEFT JOIN face_biometrics fb ON v.voter_id = fb.voter_id
        LEFT JOIN voter_qr_tokens qr ON v.voter_id = qr.voter_id
        WHERE v.voter_id = ?
    ''', (voter_id,))
    voter = cursor.fetchone()
    conn.close()

    if not voter:
        raise ValueError(f"Voter with ID '{voter_id}' not found.")

    voter_dict = dict(voter)
    
    # 1. Generate the pixel-perfect card PNG image
    card_png_abs = generate_voter_card_image(voter_dict)

    # 2. Generate PDF embedding this card image at precise card dimensions
    pdf_filename = f"{voter_id}_card.pdf"
    pdf_abs_path = os.path.join(config.CARDS_DIR, pdf_filename)
    pdf_rel_path = f"uploads/cards/{pdf_filename}"

    c = canvas.Canvas(pdf_abs_path, pagesize=(CARD_WIDTH, CARD_HEIGHT))
    c.drawImage(card_png_abs, 0, 0, width=CARD_WIDTH, height=CARD_HEIGHT, preserveAspectRatio=False)
    c.showPage()
    c.save()

    log_enrollment(
        voter_id=voter_id,
        action="CARD_GENERATED",
        details=f"Official Voter ID Card created at {pdf_rel_path}"
    )

    return pdf_rel_path
