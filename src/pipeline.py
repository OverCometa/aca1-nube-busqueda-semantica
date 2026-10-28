"""Ingesta y recuperación documental en Qdrant Cloud. No genera respuestas clínicas o normativas."""
from pathlib import Path
import hashlib, json, os, re, sqlite3, time, uuid
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
COLLECTION = 'aca1_permanencia_documental_v1'
SIZE, OVERLAP = 60, 12  # palabras; limitado además por el tokenizer del modelo

def prepare_dataset():
    """Datos UCI de Portugal. Las vinculaciones al corpus son temáticas, nunca individuales."""
    if not (ROOT/'data/data.csv').exists():
        import urllib.request, zipfile, io
        url='https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip'
        blob=urllib.request.urlopen(url,timeout=60).read()
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            name=next(n for n in z.namelist() if n.endswith('data.csv'))
            (ROOT/'data/data.csv').write_bytes(z.read(name))
    df = pd.read_csv(ROOT/'data/data.csv', sep=';')
    audit = {'filas':len(df),'columnas':len(df.columns),
             'faltantes':int(df.isna().sum().sum()), 'duplicados':int(df.duplicated().sum()),
             'pais':'Portugal', 'target':df.Target.value_counts().to_dict()}
    with sqlite3.connect(ROOT/'data/catalogo.sqlite') as db:
        df.to_sql('estudiantes',db,if_exists='replace',index=False)
        pd.DataFrame([
            {'tema':'academico','variable':'Curricular units 1st sem (approved)','descripcion':'Asignaturas aprobadas al cierre del primer semestre'},
            {'tema':'financiero','variable':'Tuition fees up to date','descripcion':'Situación de pago de matrícula'},
            {'tema':'financiero','variable':'Scholarship holder','descripcion':'Condición de becario'},
            {'tema':'bienestar','variable':'Educational special needs','descripcion':'Necesidades educativas especiales'}
        ]).to_sql('mapa_tematico',db,if_exists='replace',index=False)
    (ROOT/'results/dataset_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    return audit

def chunks():
    manifest=json.loads((ROOT/'corpus/manifest.json').read_text())
    result=[]
    for doc in manifest:
        path=ROOT/'corpus'/doc['file']
        if path.suffix=='.pdf':
            import fitz
            pages=[(i+1,p.get_text()) for i,p in enumerate(fitz.open(path))]
        else: pages=[(1,path.read_text())]
        for page,text in pages:
            words=re.sub(r'\s+',' ',text).split()
            for start in range(0,len(words),SIZE-OVERLAP):
                fragment=' '.join(words[start:start+SIZE])
                if len(fragment)<100: continue
                ident=str(uuid.uuid5(uuid.NAMESPACE_URL,f"{doc['file']}:{page}:{start}:{hashlib.sha256(fragment.encode()).hexdigest()}"))
                result.append({'id':ident,'text':fragment,'document':doc['title'],'file':doc['file'],
                    'page':page,'word_start':start,'tema':doc['tema'],'source':doc['url'],
                    'dataset':'UCI 697','dataset_country':'Portugal','dataset_fields':doc['dataset_fields'],
                    'relation':'Vinculación temática; no relación individual ni validación causal',
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (ROOT/'results/chunks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result

def connect():
    load_dotenv(ROOT/'.env',override=False)
    url=os.environ.get('QDRANT_URL','');key=os.environ.get('QDRANT_API_KEY','')
    if not url.startswith('https://') or not key:
        raise RuntimeError('Configura QDRANT_URL y QDRANT_API_KEY en variables de entorno o .env privado.')
    return QdrantClient(url=url,api_key=key,timeout=60)

def index(client,encoder,docs):
    vectors=np.asarray(list(encoder.embed([d['text'] for d in docs])),dtype='float32')
    vectors/=np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
    if not client.collection_exists(COLLECTION):
        client.create_collection(COLLECTION,vectors_config=models.VectorParams(size=vectors.shape[1],distance=models.Distance.COSINE))
    info=client.get_collection(COLLECTION)
    assert info.config.params.vectors.size==vectors.shape[1], 'Dimensión incompatible'
    if 'tema' not in info.payload_schema:
        client.create_payload_index(COLLECTION,field_name='tema',field_schema=models.PayloadSchemaType.KEYWORD,wait=True)
    for start in range(0,len(docs),32):
        client.upsert(COLLECTION,points=[models.PointStruct(id=d['id'],vector=v.tolist(),payload=d)
            for d,v in zip(docs[start:start+32],vectors[start:start+32])],wait=True)
    # No se borra la colección ni se sustituyen datos ajenos. IDs deterministas evitan duplicados.
    return {'indexed':len(docs),'dimension':vectors.shape[1],'remote_count':client.count(COLLECTION,exact=True).count}

def search(client,encoder,question,k=3,tema=None):
    if not question.strip(): raise ValueError('La consulta no puede estar vacía.')
    if not 1<=k<=10: raise ValueError('Top-k debe estar entre 1 y 10.')
    t=time.perf_counter()
    v=list(encoder.embed([question]))[0]
    filt=None if tema is None else models.Filter(must=[models.FieldCondition(key='tema',match=models.MatchValue(value=tema))])
    t_remote=time.perf_counter()
    hits=client.query_points(COLLECTION,query=v.tolist(),limit=k,with_payload=True,query_filter=filt).points
    remote_ms=(time.perf_counter()-t_remote)*1000
    return {'question':question,'total_ms':round((time.perf_counter()-t)*1000,2),'remote_ms':round(remote_ms,2),
        'hits':[{'rank':i+1,'score':float(h.score),**h.payload} for i,h in enumerate(hits)]}

def validate(client,encoder):
    tests=json.loads((ROOT/'data/queries.json').read_text())
    reports=[]
    for t in tests:
        r=search(client,encoder,t['question']);r['expected_theme']=t['expected_theme']
        r['theme_precision_at_3']=sum(h['tema']==t['expected_theme'] for h in r['hits'])/3
        r['theme_hit_at_3']=int(any(h['tema']==t['expected_theme'] for h in r['hits']))
        reports.append(r)
    out={'model':MODEL,'collection':COLLECTION,'tests':reports,
         'mean_theme_precision_at_3':float(np.mean([r['theme_precision_at_3'] for r in reports])),
         'theme_hit_rate_at_3':float(np.mean([r['theme_hit_at_3'] for r in reports])),
         'median_total_ms':float(np.median([r['total_ms'] for r in reports])),
         'median_remote_ms':float(np.median([r['remote_ms'] for r in reports])),
         'limitations':'Prueba exploratoria por tema preasignado; no mide relevancia humana de cada fragmento, ni precisión general. Similitud no equivale a probabilidad de verdad.'}
    (ROOT/'results/validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    return out
