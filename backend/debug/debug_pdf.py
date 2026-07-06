import fitz

doc = fitz.open("/tmp/test_resume.pdf")
page = doc[0]
md = page.get_text("markdown")
print("MARKDOWN:")
print(repr(md))
doc.close()
