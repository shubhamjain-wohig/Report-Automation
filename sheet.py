# paste this anywhere and run it once
from slides_agent import _build_services
drive, slides = _build_services()
prs = slides.presentations().get(
    presentationId="12qOnUGaiG6Ft_VJcQfb_C9i--a6-zd6eMrAzBAj7M4M"
).execute()
slide2 = prs["slides"][1]
for elem in slide2.get("pageElements", []):
    obj_id = elem.get("objectId")
    title  = elem.get("title", "")
    shape  = elem.get("shape", {})
    texts  = [te.get("textRun", {}).get("content", "") 
              for te in shape.get("text", {}).get("textElements", [])]
    text = "".join(texts).strip()
    if text or title:
        print(f"ID={obj_id} | title='{title}' | text='{text[:80]}'")