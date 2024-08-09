from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

def generate_pdf(user, projects):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # フォントの登録
    # フォントファイルのパスは、実際のフォントファイルのパスに変更してください
    pdfmetrics.registerFont(TTFont('NotoSans', 'NotoSansJP-VariableFont_wght.ttf'))

    # タイトル
    c.setFont("NotoSans", 16)
    c.drawString(72, height - 72, "スキルシート")

    # プロフィール
    c.setFont("NotoSans", 12)
    c.drawString(72, height - 120, "Profile")
    c.setFont("NotoSans", 12)
    y = height - 150
    profile_lines = [
        f"名前: {user.display_name}",
        f"年齢: {user.age}",
        f"性別: {user.gender}",
        f"最寄駅: {user.nearest_station}",
        f"経験年数: {user.experience_years}",
        f"学歴: {user.education}"
    ]
    for line in profile_lines:
        c.drawString(72, y, line)
        y -= 20

    # プロジェクト
    c.setFont("NotoSans", 12)
    y -= 40
    c.drawString(72, y, "Projects")
    y -= 20

    for item in projects:
        c.setFont("NotoSans", 12)
        c.drawString(72, y, item['project'].project_name)
        y -= 20
        c.setFont("NotoSans", 12)
        c.drawString(72, y, f"業界: {item['project'].industry}")
        y -= 20
        c.drawString(72, y, f"プロジェクト期間: {item['project'].start_month} から {item['project'].end_month}")
        y -= 20
        c.drawString(72, y, f"プロジェクト概要: {item['project'].project_summary}")
        y -= 20
        c.drawString(72, y, f"担当業務: {item['project'].responsibilities}")
        y -= 20

        c.setFont("NotoSans", 12)
        c.drawString(72, y, "使用技術")
        y -= 20
        c.setFont("NotoSans", 12)
        for tech in item['technologies']:
            c.drawString(72, y, f"{tech.type}: {tech.name} ({tech.duration_months} ヶ月)")
            y -= 20

        c.setFont("NotoSans", 12)
        c.drawString(72, y, "担当工程")
        y -= 20
        c.setFont("NotoSans", 12)
        for process in item['processes']:
            c.drawString(72, y, f"{process.name}")
            y -= 20

        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
