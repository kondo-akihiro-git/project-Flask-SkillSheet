from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak
from reportlab.lib import colors

def generate_pdf(user, projects):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72, title="スキルシート")
    story = []

    # フォントの登録
    pdfmetrics.registerFont(TTFont('NotoSans', 'NotoSansJP-VariableFont_wght.ttf'))
    pdfmetrics.registerFont(TTFont('NotoSansBold', 'NotoSansJP-Bold.ttf'))

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    heading1_style = styles['Heading1']
    heading2_style = styles['Heading2']
    heading3_style = styles['Heading3']
    title_style = styles['Title']

    # フォント設定
    normal_style.fontName = 'NotoSans'
    heading1_style.fontName = 'NotoSans'
    heading2_style.fontName = 'NotoSans'
    title_style.fontName = 'NotoSans'


    # タイトル
    title = Paragraph("スキルシート", title_style)
    story.append(title)
    story.append(Paragraph("<br/>", normal_style))

    # 氏名の追加
    name_section = Paragraph(f"氏名: {user.display_name or '記載なし'}", heading2_style)
    story.append(name_section)
    story.append(Paragraph("<br/>", normal_style))

    # プロフィール
    profile_title = Paragraph("プロフィール", heading2_style)
    story.append(profile_title)

    profile_data = [
        ["内容","詳細"],
        ["年齢:", user.age or "記載なし"],
        ["性別:", user.gender or "記載なし"],
        ["最寄駅:", user.nearest_station or "記載なし"],
        ["経験年数:", f"{user.experience_years // 12} 年 {user.experience_years % 12} ヶ月" if user.experience_years else "記載なし"],
        ["学歴:", user.education or "記載なし"]
    ]

    profile_table = Table(profile_data, colWidths=[150, doc.pagesize[0] - 2 * 72 - 150])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'NotoSans'),
        ('FONTNAME', (0, 0), (-1, 0), 'NotoSansBold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(profile_table)
    story.append(Paragraph("<br/>", normal_style))

    # スキル歴項目
    skill_history_title = Paragraph("スキル歴", heading2_style)
    story.append(skill_history_title)

    # スキル歴のデータを集計
    skill_categories = {}

    tech_labels = {
        'os': 'OS',
        'language': '言語',
        'framework': 'フレームワーク',
        'database': 'データベース',
        'containertech': 'コンテナ技術',
        'cicd': 'CI/CD',
        'logging': 'ログ',
        'tools': 'その他ツール'
    }    

    for project in projects:
        for tech in project['technologies']:
            tech_type = tech_labels.get(tech.type, tech.type)
            if tech_type not in skill_categories:
                skill_categories[tech_type] = {}
            
            if tech.name not in skill_categories[tech_type]:
                skill_categories[tech_type][tech.name] = tech.duration_months
            else:
                skill_categories[tech_type][tech.name] += tech.duration_months

    # カテゴリーごとにスキル歴テーブルを作成
    for category, skills in skill_categories.items():
        skill_history_data = []
        skill_history_data.append([category, "期間"])
        for name, duration in skills.items():
            skill_history_data.append([name, f"{duration // 12} 年 {duration % 12} ヶ月" if duration >= 12 else f"{duration} ヶ月"])
        
        skill_history_table = Table(skill_history_data, colWidths=[doc.pagesize[0] - 2 * 72 - 100, 100])
        skill_history_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'NotoSans'),
            ('FONTNAME', (0, 0), (-1, 0), 'NotoSansBold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(skill_history_table)
        story.append(Paragraph("<br/>", normal_style))

    # プロジェクト
    for idx, item in enumerate(projects, 1):
        story.append(PageBreak())

        project_title = Paragraph(f"プロジェクトNo.{idx}  {item['project'].project_name}", heading1_style)
        story.append(project_title)

        project_data = [
            ["内容","詳細"],
            ["業界", Paragraph(item['project'].industry, normal_style)],
            ["プロジェクト期間", f"{item['project'].start_month} から {item['project'].end_month}"],
            ["プロジェクト概要", Paragraph(item['project'].project_summary, normal_style)],
            ["担当業務", Paragraph(item['project'].responsibilities, normal_style)]
        ]

        project_width = doc.pagesize[0] - 2 * 72

        project_table = Table(project_data, colWidths=[150, project_width - 150])
        project_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'NotoSans'),
            ('FONTNAME', (0, 0), (-1, 0), 'NotoSansBold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(project_table)
        story.append(Paragraph("<br/>", normal_style))

        tech_data = [["技術タイプ", "技術名", "使用期間"]]
        for tech in item['technologies']:
            tech_data.append([tech_labels.get(tech.type, tech.type), tech.name, f"{tech.duration_months // 12} 年 {tech.duration_months % 12} ヶ月" if tech.duration_months >= 12 else f"{tech.duration_months} ヶ月"])

        tech_table = Table(tech_data, colWidths=[150, project_width - 300, 150])  # 統一されたカラム幅
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'NotoSans'),
            ('FONTNAME', (0, 0), (-1, 0), 'NotoSansBold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(tech_table)

        # 担当工程テーブルの追加
        role_data = [["担当工程"]]
        rolename = ""
        for i, role in enumerate(item['processes']):
            if i==0:
                rolename += role.name
            else:
                rolename += '・'+role.name
        role_data.append([rolename])

        role_table = Table(role_data, colWidths=[project_width])
        role_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'NotoSans'),
            ('FONTNAME', (0, 0), (-1, 0), 'NotoSansBold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(role_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
