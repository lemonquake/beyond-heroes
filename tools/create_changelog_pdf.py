"""Render the checked-in version history as a readable, reproducible PDF."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/Beyond-Heroes-Changelog-BH016-BH020.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
fontdir = Path('C:/Windows/Fonts')
for name, filename in [('Body', 'segoeui.ttf'), ('Bold', 'segoeuib.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(fontdir / filename)))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('Text', fontName='Body', fontSize=10.3, leading=14.1, spaceAfter=8, textColor=colors.HexColor('#263240')))
styles.add(ParagraphStyle('BulletText', parent=styles['Text'], leftIndent=12, firstLineIndent=-10, spaceAfter=7))
styles.add(ParagraphStyle('Version', fontName='Bold', fontSize=23, leading=29, spaceAfter=16, textColor=colors.HexColor('#183E4B')))
styles.add(ParagraphStyle('SourceNote', parent=styles['Text'], fontSize=8.7, leading=11.5, textColor=colors.HexColor('#586675'), spaceBefore=6))
styles.add(ParagraphStyle('CoverTitle', fontName='Bold', fontSize=35, leading=42, textColor=colors.HexColor('#183E4B'), spaceAfter=20))

def markup(s):
    s = escape(s)
    return re.sub(r'`([^`]+)`', r'<b>\1</b>', s)

def footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(colors.HexColor('#CDD8DB'))
    canvas.line(48, 41, w-48, 41)
    canvas.setFont('Body', 8)
    canvas.setFillColor(colors.HexColor('#586675'))
    canvas.drawString(48, 27, 'Beyond Heroes | Version history | 29 September 2026')
    canvas.drawRightString(w-48, 27, str(doc.page))
    canvas.restoreState()

story = [Spacer(1, 55), Paragraph('Beyond Heroes', styles['CoverTitle']),
         Paragraph('Version-by-version changelog', styles['Version']),
         Paragraph('BH-016 through BH-020', styles['Text']), Spacer(1, 18),
         Paragraph('The two latest earlier Git updates, followed by the socketing and town work continued from Claude Code and the completion fixes.', styles['Text']),
         Paragraph('The BH numbers are development update identifiers found in this repository. They are not semantic release tags. Earlier Git history is outside this report.', styles['Text']), Spacer(1, 22)]
rows = [['Update', 'Contents', 'Git reference'],
        ['BH-016', 'Skills, Guild House, player trading', '4f0b64b'],
        ['BH-017', 'Merchant Rows, effects, companions', '05d8219'],
        ['BH-018', 'Sockets, crystals, town redesign', 'Current completion'],
        ['BH-019', 'Lape, practice dummies, shared vault', 'Current completion'],
        ['BH-020', 'Shop access, labels, release checks', 'Current completion']]
rows = [[Paragraph(escape(c), styles['SourceNote']) for c in row] for row in rows]
t=Table(rows, colWidths=[68, 265, 166-2*0], hAlign='LEFT')
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7EFF0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor('#CDD8DB')),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
story += [t, Spacer(1, 24), Paragraph('Source: the Git commit diffs, checked-in handoff records, game data, implementation and tests. Each update identifies its supporting files.', styles['Text']),
          Paragraph('Repository: <link href="https://github.com/lemonquake/beyond-heroes" color="#183E4B">github.com/lemonquake/beyond-heroes</link>', styles['Text'])]

text=(ROOT/'docs/CHANGELOG.md').read_text(encoding='utf8')
sections=re.split(r'^## ',text,flags=re.M)[1:]
for section in sections:
    title, content=section.split('\n',1)
    story += [PageBreak(), Paragraph(markup(title),styles['Version'])]
    for block in content.strip().split('\n\n'):
        if block.startswith('- '):
            for bullet in block.split('\n- '):
                story.append(Paragraph('&#8226; '+markup(bullet.removeprefix('- ')),styles['BulletText']))
        elif block.startswith('Sources:') or block.startswith('Validation and build'):
            story.append(Paragraph(markup(block),styles['SourceNote']))
        else:
            for sha in re.findall(r'\b[0-9a-f]{40}\b',block):
                block=block.replace(sha,sha[:7])
            story.append(Paragraph(markup(block),styles['Text']))

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=48,bottomMargin=57,title='Beyond Heroes - BH-016 to BH-020 changelog',author='Beyond Heroes',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
