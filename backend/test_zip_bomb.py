import zipfile
import io
import time

def create_valid_zip_bomb():
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Create minimal valid docx structure
        zf.writestr('[Content_Types].xml', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        zf.writestr('_rels/.rels', b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        # The bomb: 100MB of 'A' (should expand to ~100MB string)
        # For a real bomb, we'd do 1GB. But 1GB might actually OOM the docker container (2GB limit usually). Let's try 500MB.
        xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + b'A' * (500 * 1024 * 1024) + b'</w:t></w:r></w:p></w:body></w:document>'
        zf.writestr('word/document.xml', xml)
    return out.getvalue()

if __name__ == "__main__":
    start = time.time()
    zb = create_valid_zip_bomb()
    print('Zip bomb compressed size (MB):', len(zb) / (1024*1024))
    
    from app.services.parsers.docx_parser import DocxParser
    parser = DocxParser()
    try:
        res = parser.parse(zb, 'bomb.docx')
        print('Parsed full text length:', len(res.full_text))
    except Exception as e:
        print('Caught exception:', type(e).__name__, str(e)[:100])
    print('Time taken:', time.time() - start)
