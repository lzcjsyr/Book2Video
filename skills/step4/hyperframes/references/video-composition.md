# Video Composition

Standalone compositions place the root `data-composition-id` element directly in
`body`; do not wrap the standalone page in `template`.

Required root pattern:

```html
<div data-composition-id="segment" data-width="1280" data-height="720" data-duration="5" data-track-index="1">
  ...
</div>
```

Use CSS to create a full-frame layout:

```css
[data-composition-id="segment"] {
  width: 100%;
  height: 100%;
  overflow: hidden;
  box-sizing: border-box;
}
```

Register a paused GSAP timeline:

```js
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
window.__timelines.segment = tl;
```
