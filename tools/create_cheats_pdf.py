"""Build the cheat reference directly from the game's player-facing descriptions."""
from pathlib import Path
import json
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'game/src/core/cheats.gd').read_text(encoding='utf-8')
descriptions = json.loads(re.search(r'const DESCRIPTIONS := (\{.*?\n\})', SOURCE, re.S).group(1))
codes = json.loads(re.search(r'const CODES := (\{.*?\})', SOURCE, re.S).group(1))
assert descriptions.keys() == codes.keys(), 'Code/reference mismatch'
assert len(codes) == 26
OUT = ROOT / 'output/pdf/Beyond-Heroes-Cheat-Codes.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
for name, file in [('Body', 'segoeui.ttf'), ('Bold', 'segoeuib.ttf'), ('Code', 'consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts') / file)))
ink = colors.HexColor('#22353E')
muted = colors.HexColor('#52636C')
teal = colors.HexColor('#176171')
styles = {
    'title': ParagraphStyle('Title', fontName='Bold', fontSize=27, leading=33, textColor=ink, spaceAfter=8),
    'heading': ParagraphStyle('Heading', fontName='Bold', fontSize=16, leading=21, textColor=teal, spaceAfter=10),
    'body': ParagraphStyle('Body', fontName='Body', fontSize=10.5, leading=15, textColor=ink, spaceAfter=8),
    'small': ParagraphStyle('Small', fontName='Body', fontSize=9, leading=13, textColor=muted, spaceAfter=8),
    'code': ParagraphStyle('Code', fontName='Code', fontSize=11, leading=15, textColor=teal),
    'cell': ParagraphStyle('Cell', fontName='Body', fontSize=10, leading=14, textColor=ink),
}

def p(text, style='body'):
    return Paragraph(escape(text), styles[style])

def table(keys):
    rows = [[p('Code', 'code'), p('Effect', 'cell')]]
    rows += [[p(key, 'code'), p(descriptions[key], 'cell')] for key in keys]
    t = Table(rows, colWidths=[115, A4[0] - 96 - 115], repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E1EEF0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F6F7')]),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, colors.HexColor('#D3DEE1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return t

def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#D3DEE1'))
    canvas.line(48, 42, A4[0] - 48, 42)
    canvas.setFont('Body', 8)
    canvas.setFillColor(muted)
    canvas.drawString(48, 28, 'Beyond Heroes | Cheat reference | 1 October 2026')
    canvas.drawRightString(A4[0] - 48, 28, str(doc.page))

instructions = ('On desktop, press Enter to open chat, type one code and press Enter again. '
                'On touch controls, open Chat, enter the code and tap Send. '
                'Codes ignore capitalization and spaces at the beginning or end; enter the full code as one message. '
                'In Multiplayer, only the host can use cheats. Codes and cheat results are private and never appear in hero speech bubbles.')
notes = ('Codes can be repeated. Rewards and point changes are kept by the normal save system. '
         'Item gifts add nothing if the entire gift will not fit. Skill, stat and talent points are separate pools.')
requested = ['lel', 'qwe', 'asd', 'qqq', 'www', 'zzz', 'orb']
progression = ['asdf', 'lemonq', 'taicho', 'greg', 'deep pockets', 'jjwp', 'azrin', 'oneup', 'talenttime', 'freshstart']
extra = [key for key in descriptions if key not in requested + progression]
assert len(requested + progression + extra) == len(codes)
chat_notes = ('Press Enter or tap Chat to write a message. Multiplayer keeps a scrollable party chat log at the side; '
              'messages also appear above heroes for 3 seconds. Type @ and a player name, then press Right, Space or Enter '
              'to complete the suggested name (or tap a suggestion). Press Enter again to send. Names containing spaces '
              'are completed as @"Player Name". Use @everyone to ping the whole party. Mentioned players hear an alert '
              'and see the sender\'s message flash. Use the Emoji button to insert an emoji. Both devices need this game version.')
story = [p('Beyond Heroes', 'small'), p('Cheat codes', 'title'), p(instructions), Spacer(1, 9),
         p('New and changed codes', 'heading'), table(requested), Spacer(1, 12), p(notes, 'small'),
         PageBreak(), p('Gold and progression', 'title'), table(progression), Spacer(1, 15),
         p('Distribute stat points', 'heading'),
         p('Open Character. Each attribute has an All button to assign every remaining point to that attribute. '
           'Hold + to keep adding points; release or move away to stop. Existing choices for other attributes are preserved. '
           'Select Apply Points to spend the points, or Clear to discard the pending choices.'),
         Spacer(1, 12), p('Party chat', 'heading'), p(chat_notes),
         PageBreak(), p('Equipment and recovery', 'title'), table(extra)]
SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=42, bottomMargin=57,
                  title='Beyond Heroes - All Cheat Codes', author='Beyond Heroes').build(story, onFirstPage=footer, onLaterPages=footer)
md = '# Beyond Heroes cheat codes\n\n' + instructions + '\n\n' + notes + '\n\n'
md += '| Code | Effect |\n| --- | --- |\n'
md += ''.join(f'| `{key}` | {description} |\n' for key, description in descriptions.items())
md += '\n## Stats\n\nHold + to add points repeatedly. All assigns every remaining point to that attribute. Apply Points commits your choices; Clear discards them.\n\n## Party chat\n\n' + chat_notes + '\n'
(ROOT / 'docs/CHEATS.md').write_text(md, encoding='utf-8')
print(OUT)
