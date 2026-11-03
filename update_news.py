#!/usr/bin/env python3
"""GÜNDEM: yayıncı RSS özetlerinden her gün kaynak gösteren kısa Türkçe bülten derler.

Haricî API anahtarı gerektirmez. Gazetecilik araştırması veya tam makale yayını değildir.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
ISTANBUL = ZoneInfo('Europe/Istanbul')
FEEDS = [
    ('Anadolu Ajansı', 'https://www.aa.com.tr/tr/rss/default?cat=guncel', 'Türkiye'),
    ('TRT Haber', 'https://www.trthaber.com/sondakika_articles.rss', 'Türkiye'),
    ('BBC Türkçe', 'https://feeds.bbci.co.uk/turkce/rss.xml', 'Dünya'),
    ('DW Türkçe', 'https://rss.dw.com/rdf/rss-tur-all', 'Dünya'),
    ('Euronews Türkçe', 'https://tr.euronews.com/rss', 'Dünya'),
    ('Bloomberg HT', 'https://www.bloomberght.com/rss', 'Ekonomi'),
    ('Webtekno', 'https://www.webtekno.com/rss.xml', 'Teknoloji'),
    ('ShiftDelete.Net', 'https://shiftdelete.net/feed', 'Teknoloji'),
]
KEYWORDS = {
    'Ekonomi': ['enflasyon','faiz','merkez bankası','borsa','dolar','euro','ekonomi','piyasa','petrol','altın','kira','asgari ücret','ticaret','vergi','bütçe','istihdam','işsizlik','şirket','enerji fiyat'],
    'Teknoloji': ['yapay zek','teknoloji','yazılım','çip','akıllı telefon','siber','robot','uzay','uydu','bilgisayar','openai','internet','elektronik'],
    'Türkiye': ['türkiye','istanbul','ankara','izmir','tbmm','meclis','bakanlık','cumhurbaşkan','tüik','türk','deprem','belediye','yargı'],
    'Dünya': ['abd','trump','avrupa','ukrayna','rusya','iran','gazze','israil','filistin','çin','almanya','fransa','ingiltere','savaş','bm','nato','ab '],
}
ART = {'Türkiye':'turkey','Dünya':'world','Ekonomi':'economy','Teknoloji':'tech'}
MAX_BY_CAT = {'Türkiye':12,'Dünya':12,'Ekonomi':8,'Teknoloji':8}
MIN_ITEMS = 6

def clean(value: str) -> str:
    value = re.sub(r'<[^>]*>', ' ', str(value or ''))
    value = html.unescape(value)
    return re.sub(r'\s+', ' ', value).strip()

def shorten(text: str, words: int = 18) -> str:
    bits = clean(text).split()
    return ' '.join(bits[:words]) + ('…' if len(bits) > words else '')

def child_text(node, *names):
    for name in names:
        for el in node:
            if el.tag.rsplit('}',1)[-1] == name and el.text:
                return clean(el.text)
    return ''

def parse_date(raw):
    if not raw:
        return None
    try:
        out = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        try:
            out = datetime.fromisoformat(raw.replace('Z','+00:00'))
        except ValueError:
            return None
    return out.replace(tzinfo=timezone.utc) if out.tzinfo is None else out.astimezone(timezone.utc)

def read_feed(name, url, default_cat, *, xml_data=None):
    if xml_data is None:
        req = urllib.request.Request(url,headers={'User-Agent':'GundemDailyReader/1.0 (+RSS aggregator; contact repository owner)','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'})
        with urllib.request.urlopen(req,timeout=18) as response:
            xml_data = response.read(3_000_000)
    root=ET.fromstring(xml_data)
    entries=[]
    for item in root.iter():
        if item.tag.rsplit('}',1)[-1] not in ('item','entry'):
            continue
        title=child_text(item,'title')
        desc=child_text(item,'description','summary','content')
        url=child_text(item,'link')
        if not url:
            for c in item:
                if c.tag.rsplit('}',1)[-1]=='link' and c.attrib.get('href'):
                    url=c.attrib['href'];break
        published=parse_date(child_text(item,'pubDate','date','published','updated'))
        if not title or not url.startswith(('https://','http://')) or not desc or len(desc)<25:
            continue
        entries.append({'title':title,'description':desc,'url':url,'published':published,'source':name,'default_cat':default_cat})
    return entries

def classify(item):
    text=(item['title']+' '+item['description'][:160]).casefold()
    # Kaynağın odaklandığı alanı koru; belirgin konu varsa sınıflandırmayı düzelt.
    scores={cat:sum(1 for word in words if word in text) for cat,words in KEYWORDS.items()}
    if item['default_cat']=='Teknoloji' or scores['Teknoloji']>=2:return 'Teknoloji'
    if item['default_cat']=='Ekonomi' or scores['Ekonomi']>=2:return 'Ekonomi'
    if item['default_cat']=='Türkiye': return 'Türkiye'
    if scores['Türkiye']>=2 and scores['Dünya']==0:return 'Türkiye'
    return 'Dünya'

def convert(item):
    date=item['published'].astimezone(ISTANBUL) if item['published'] else datetime.now(ISTANBUL)
    day=date.strftime('%d.%m.%Y %H:%M')
    source=item['source'];cat=classify(item)
    desc=shorten(item['description'],18)
    # Birebir RSS alıntısı kısa tutuluyor; tam telifli makaleler kopyalanmıyor.
    return {
        'id':'rss-'+hashlib.sha256(item['url'].encode()).hexdigest()[:16],
        'cat':cat,'eyebrow':cat.upper()+' · '+source.upper(),
        'title':item['title'],
        'dek':desc,
        'minutes':1,'time':day,'art':ART[cat],
        'body':[
            f'{source}, {day} tarihinde bu gelişmeyi haberleştirdi.',
            f'Yayımlanan RSS bültenindeki kısa bilgi: “{desc}”',
            'Bu sayfa, kaynağın herkese açık haber akışındaki özetinden otomatik oluşturulmuştur. Kaynakta yer almayan ayrıntılar eklenmemiştir. Daha kapsamlı açıklamalar ve sonraki gelişmeler için haberin tarihini ve kaynak bilgisini dikkate alın.'
        ],
        'why':'Haberin konusu ve etkileri hakkında kesin değerlendirme yapmak için doğrulanmış ayrıntılar ve güncellemeler önemlidir.',
        'sources':[source, f'RSS yayını · {day}'],
        'url':item['url'],
        'short_brief':True,
        'published':item['published'].isoformat() if item['published'] else None,
    }

def make_edition(feeds, *, now=None):
    now=now or datetime.now(timezone.utc)
    unique=set();candidates=[];errors=[]
    for name,url,default_cat in feeds:
        try:
            items=read_feed(name,url,default_cat)
            print(f'{name}: {len(items)} RSS kaydı')
        except Exception as err:
            errors.append(name+': '+str(err)[:120]); print('UYARI:',errors[-1],file=sys.stderr);continue
        for item in items:
            when=item['published']
            if not when or (now-when)>timedelta(hours=56) or when>now+timedelta(hours=2):continue
            key=re.sub(r'\W+','',item['title'].casefold())[:76]
            if key in unique:continue
            unique.add(key)
            candidates.append(item)
    candidates.sort(key=lambda x:x['published'],reverse=True)
    count_by_cat={cat:0 for cat in MAX_BY_CAT};count_by_source={}
    selected=[]
    for entry in candidates:
        cat=classify(entry)
        if count_by_cat[cat]>=MAX_BY_CAT[cat] or count_by_source.get(entry['source'],0)>=4:continue
        selected.append(convert(entry));count_by_cat[cat]+=1
        count_by_source[entry['source']]=count_by_source.get(entry['source'],0)+1
    # Başlık ve editoryal sıralama; son dakika ile magazin karıştırmamak için kategoriler dengelenir.
    if len(selected)<MIN_ITEMS:
        raise RuntimeError(f'Yeterli yeni haber yok: {len(selected)}. Eski yayın korunmalı. Hatalar: {errors}')
    order={'Türkiye':0,'Dünya':1,'Ekonomi':2,'Teknoloji':3}
    selected.sort(key=lambda a:(order[a['cat']], -(datetime.fromisoformat(a['published']).timestamp())))
    selected[0]['lead']=True
    timestamp=now.astimezone(ISTANBUL)
    return {'edition_date':timestamp.strftime('%d.%m.%Y'),'updated_at':timestamp.isoformat(timespec='minutes'),
            'notice':'RSS kaynaklarından otomatik derlenen kısa haber özetleri. Tam makale veya editör onaylı analiz değildir.',
            'articles':selected,'source_count':len(count_by_source)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--demo',action='store_true',help='Ağ kullanmadan örnek RSS ile sistem testi');args=parser.parse_args()
    if args.demo:
        now=datetime.now(timezone.utc)
        rows=[]
        for i in range(20):
            rows.append(f'<item><title>Türkiye ekonomi teknoloji dünya gündeminde haber {i+1}</title><link>https://example.org/haber-{i}</link><description>Güncel gelişmelere dair bültende yer alan haber özeti ve önemli açıklamalar bulundu.</description><pubDate>{(now-timedelta(minutes=i*20)).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate></item>')
        mock=('<rss><channel>'+''.join(rows)+'</channel></rss>').encode()
        global read_feed
        real=read_feed
        def fake(name,url,cat):
            raw=mock.replace(b'example.org/haber-',('example.org/'+hashlib.sha256(name.encode()).hexdigest()[:6]+'-haber-').encode()).replace(b'Turkiye ekonomi teknoloji',b'Turkiye ekonomi teknoloji')
            raw=raw.replace('Türkiye ekonomi teknoloji dünya'.encode(),('Haber '+name+' yeni dünya').encode())
            return real(name,url,cat,xml_data=raw)
        read_feed=fake
    edition=make_edition(FEEDS)
    # Tam atomik yazma: hata olursa mevcut haberler korunur.
    out=ROOT/('edition.demo.json' if args.demo else 'edition.json');tmp=ROOT/'edition.tmp'
    tmp.write_text(json.dumps(edition,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(out)
    print(f'Hazır: {len(edition["articles"])} haber, {edition["edition_date"]}, {edition["source_count"]} kaynak')

if __name__=='__main__':
    main()
