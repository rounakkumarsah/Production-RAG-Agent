import fitz
doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 50), "Hello World", fontsize=11)
try:
    md = page.get_text("markdown")
    print("Supports markdown")
except Exception as e:
    print("Does not support markdown:", e)
doc.close()
