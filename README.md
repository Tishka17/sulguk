Sulguk - HTML to telegram entities converter
================================================

Need to deliver formatted content to your bot clients?
Having a hangover after trying to fit HTML into telegram? 
Beautifulsoup is too complicated and not helping with messages?

Try `sulguk` (술국, a hangover soup) - [delivered since 1800s](https://en.wikipedia.org/wiki/Food_delivery).

### Example

1. Add `SulgukMiddleware` to your bot
```python
from sulguk.aiogram_middleware import SulgukMiddleware
bot.session.middleware(SulgukMiddleware())
```

2. Create your nice HTML:
```html
<ol start="10">
    <li>some item</li>
    <li>other item</li>
</ol>
<p>Some <b>text</b> in a paragraph</p>
```

3. Send it using `sulguk` as a `parse_mode`:
```python
await bot.send_message(
    chat_id=CHAT_ID,
    text=raw_html,
    parse_mode="sulguk"
)
```


### Usage without middleware

Instead of usage of custom parse mode you can import `transform_html` and transform HTML to entities manually.
