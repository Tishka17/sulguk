from html2tg import transform_html

raw_html = """
<a href="123">hello</a>
test
<b>bold</b><i>italic</i>
<ol>
<li>item1</li>
<li>item2</li>
</ol>
--
<ul>
<li>item1</li>
<li>item2</li>
</ul>
"""

result = transform_html(raw_html)
print("Text:")
print(result.text)
print(result.entities)
