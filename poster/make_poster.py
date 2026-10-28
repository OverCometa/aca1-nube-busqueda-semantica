from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
for n,f in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf')]: pdfmetrics.registerFont(TTFont(n,'/usr/share/fonts/truetype/dejavu/'+f))
pdfmetrics.registerFontFamily('D',normal='D',bold='DB',italic='D',boldItalic='DB')
W,H=1190,842; navy=HexColor('#142d46');teal=HexColor('#007c83');gray=HexColor('#42596a')
c=canvas.Canvas(str(ROOT/'poster/Poster_ACA1_Computacion_Nube.pdf'),pagesize=(W,H));c.setTitle('Búsqueda semántica cloud para la permanencia estudiantil');c.setAuthor('Over Santiago Cometa Hernández')
def text(s,x,y,w,size=12,leading=17,color=navy):
 p=Paragraph(s,ParagraphStyle('p',fontName='D',fontSize=size,leading=leading,textColor=color));_,h=p.wrap(w,1200);p.drawOn(c,x,y-h);return y-h
def title(s,x,y,w):return text(s,x,y,w,17,22,teal)-10
c.setFillColor(navy);c.rect(0,H-145,W,145,fill=1,stroke=0)
text('CUN · ESPECIALIZACIÓN EN INTELIGENCIA ARTIFICIAL · COMPUTACIÓN EN LA NUBE · ACA 1',34,H-20,1120,10,14,white)
text('<b>Búsqueda semántica cloud<br/>para la permanencia estudiantil</b>',34,H-43,1120,30,35,white)
text('Over Santiago Cometa Hernández · Trabajo individual · Docente Hamilton Rivera Flor · Octubre de 2026',34,H-121,1120,10,14,white)
xs=[34,419,804];w=350;top=H-169
x=xs[0];y=title('1. Problema y objetivo',x,top,w)
y=text('<b>Problema.</b> La información de orientación estudiantil está distribuida en documentos y requiere recuperación con trazabilidad.<br/><br/><b>Objetivo.</b> Implementar ingesta, fragmentación, embeddings e indexación cloud para recuperar fragmentos relevantes ante preguntas en español.',x,y,w)-18
y=title('2. Corpus y metadatos',x,y,w)
y=text('<b>Pilar: educación.</b> Tres guías didácticas propias en Markdown: acompañamiento académico, orientación financiera y bienestar e inclusión. Son propuestas académicas, no reglamentos oficiales de CUN.<br/><br/><b>Dataset UCI 697:</b> 4.424 estudiantes de Portugal; 37 columnas, sin faltantes ni duplicados. Catálogo SQLite local y vínculo temático mediante campos de avance académico, matrícula, becas y necesidades educativas (Realinho et al., 2021).',x,y,w,11.5,16)-15
y=text('No existe enlace individual entre estudiantes portugueses y orientaciones colombianas; no se infiere causalidad.',x,y,w,10.5,14,gray)
x=xs[1];y=title('3. Arquitectura y herramientas',x,top,w)
boxes=[('INGESTA','Markdown + dataset UCI'),('PREPARACIÓN','60 palabras · solapamiento 12'),('EMBEDDINGS','MiniLM multilingüe · 384 dimensiones'),('CLOUD Y CONSULTA','Qdrant · coseno · Top-3')]
for a,b in boxes:
 c.setFillColor(HexColor('#eaf4f4'));c.roundRect(x,y-60,w,60,7,fill=1,stroke=0)
 text('<b>'+a+'</b>',x+12,y-9,w-24,11,15,teal);text(b,x+12,y-30,w-24,10.5,15)
 y-=76
 if a!='CLOUD Y CONSULTA':
  c.setStrokeColor(teal);c.line(x+w/2,y+14,x+w/2,y+3)
y=text('<b>Diseño.</b> Embeddings abiertos mediante FastEmbed/ONNX en CPU. Clúster gratuito Qdrant Cloud, AWS São Paulo: un nodo, 1 GiB RAM y 4 GiB disco. Lotes de 32, IDs deterministas e índice de metadatos por tema.<br/><br/>Credenciales desde variables de entorno o .env privado. SQL local; vectores remotos. No se atribuye alta disponibilidad ni escalado serverless ilimitado.',x,y,w,11,15)
x=xs[2];y=title('4. Validación remota',x,top,w)
r=json.loads((ROOT/'results/validation.json').read_text())
y=text('<b>26 fragmentos indexados · 6 consultas · Top-3</b><br/><br/>'+f"Coincidencia temática media: <b>{r['mean_theme_precision_at_3']:.1%}</b><br/>Consultas con acierto temático en Top-3: <b>{r['theme_hit_rate_at_3']:.0%}</b><br/>Mediana de búsqueda remota: <b>{r['median_remote_ms']:.0f} ms</b>",x,y,w,12,18)-16
hit=r['tests'][2]['hits'][0]
y=text('<b>Ejemplo real</b><br/>«¿Qué debo consultar si no puedo pagar la matrícula?»<br/>'+f"Primer fragmento: {hit['document']}. Similitud coseno: <b>{hit['score']:.3f}</b>.",x,y,w,11.5,16)-16
y=text('<b>Límites.</b> Evaluación exploratoria por tema predefinido, sin jueces independientes de relevancia. Los tiempos varían entre ejecuciones. La similitud no certifica veracidad ni vigencia. No genera respuestas ni toma decisiones sobre estudiantes.',x,y,w,11,15)-16
y=title('5. Acceso y sustentación',x,y,w)
y=text('<link href="https://github.com/OverCometa/aca1-nube-busqueda-semantica" color="#007c83"><b>Abrir repositorio y notebook</b></link><br/><br/><b>Video:</b> pendiente de grabación y publicación. Añadir el enlace antes de la entrega definitiva.',x,y,w,11.5,16)
c.setStrokeColor(HexColor('#bdced5'));c.line(34,156,W-34,156)
y=text('<b>Referencias</b>',34,144,W-68,11,14)
refs=[
'Ministerio de Educación Nacional. (2016). <i>Lineamientos de política de bienestar para instituciones de educación superior.</i> https://www.mineducacion.gov.co/1759/articles-360314_recurso.pdf',
'Ministerio de Educación Nacional. (2023, 29 de mayo). <i>Gestión de la permanencia.</i> https://www.mineducacion.gov.co/sistemasinfo/spadies/secciones/Gestion-de-la-permanencia/',
'Realinho, V., Vieira Martins, M., Machado, J., &amp; Baptista, L. (2021). <i>Predict students’ dropout and academic success</i> [Conjunto de datos]. UCI. https://doi.org/10.24432/C5MC89',
'Reimers, N., &amp; Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. <i>EMNLP-IJCNLP</i>, 3982-3992. https://doi.org/10.18653/v1/D19-1410']
for ref in refs:y=text(ref,34,y-5,W-68,8.5,12,gray)
text('Figuras y guías: elaboración propia. Referencias técnicas completas, decisiones metodológicas y resultados en el notebook.',34,y-7,W-68,8.5,12,gray)
c.showPage();c.save()
