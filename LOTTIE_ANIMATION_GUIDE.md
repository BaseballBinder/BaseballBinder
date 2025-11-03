# Lottie Animation Integration Guide

## Overview

BaseballBinder now supports Lottie animations for the hero banner! Lottie animations are lightweight, scalable, and provide professional motion graphics.

## What You Have Now

✅ **Lottie Player Library** - Loaded from CDN
✅ **Dual Animation System** - Lottie (primary) + CSS fallback (backup)
✅ **Automatic Fallback** - Falls back to CSS animation if Lottie fails
✅ **Responsive Design** - Adapts to mobile, tablet, and desktop
✅ **Accessibility** - Respects `prefers-reduced-motion` setting
✅ **Click to Replay** - Click the animation to replay it

## How to Add Your Own Lottie Animation

### Option 1: Use LottieFiles (Recommended)

1. **Find an animation:**
   - Visit https://lottiefiles.com/
   - Search for "baseball", "cards", "binder", "sports", etc.
   - Preview animations and find one you like

2. **Download the JSON:**
   - Click on the animation
   - Click "Download" → "Lottie JSON"
   - Save the file

3. **Replace the animation:**
   - Rename your downloaded file to `hero-animation.json`
   - Replace the existing `hero-animation.json` in the project folder

### Option 2: Create Your Own Animation

1. **Design in After Effects:**
   - Create your animation in Adobe After Effects
   - Use the Bodymovin plugin to export as JSON

2. **Use Online Editors:**
   - https://editor.lottiefiles.com/
   - https://www.lottielab.com/

### Option 3: Use a Different JSON Path

If you want to keep multiple animations, you can change the file path:

```html
<!-- In index.html, find this line: -->
<lottie-player
    id="lottiePlayer"
    src="hero-animation.json"  <!-- Change this path -->
    background="transparent"
    speed="1"
    style="width: 100%; height: 400px;"
    autoplay>
</lottie-player>
```

## Customization Options

### Change Animation Speed

```html
<lottie-player
    speed="1.5"  <!-- 1.5x speed -->
    ...
</lottie-player>
```

### Enable Looping

```html
<lottie-player
    loop  <!-- Add this attribute -->
    ...
</lottie-player>
```

### Add Controls

```html
<lottie-player
    controls  <!-- Add playback controls -->
    ...
</lottie-player>
```

### Change Background Color

```html
<lottie-player
    background="#667eea"  <!-- Purple background -->
    ...
</lottie-player>
```

## Animation Specifications

**Recommended Settings:**
- **Width:** 800-1200px
- **Height:** 400-600px
- **Frame Rate:** 30-60 fps
- **Duration:** 2-4 seconds (60-240 frames)
- **File Size:** Keep under 200KB for fast loading

## Fallback Behavior

The system automatically falls back to the CSS animation if:
- The JSON file is not found
- The JSON file is corrupted
- The Lottie library fails to load
- The animation takes more than 5 seconds to load
- User has `prefers-reduced-motion` enabled

## Testing Your Animation

1. **Load the page normally:**
   - Should see your Lottie animation
   - Check browser console for any errors

2. **Test fallback:**
   - Temporarily rename `hero-animation.json`
   - Page should show CSS animation instead

3. **Test reduced motion:**
   - Enable "Reduce Motion" in your OS settings
   - Page should show static content

## Recommended Animations from LottieFiles

Here are some great animations you could use:

1. **Baseball Theme:**
   - Search: "baseball"
   - Look for: ball bouncing, bat swinging, diamond animations

2. **Card Theme:**
   - Search: "cards shuffle", "deck cards", "card flip"
   - Modern card animations work great

3. **Binder/Book Theme:**
   - Search: "book open", "folder", "document"
   - Page turning animations

4. **Abstract/Modern:**
   - Search: "data visualization", "modern loader"
   - Clean, professional motion graphics

## Advanced: Custom Text Integration

If your Lottie animation doesn't include text, the title and subtitle will appear below the animation (current setup). If your animation includes text, you can hide the text overlay:

```css
/* In the CSS section */
.lottie-text {
    display: none; /* Hide text if animation includes it */
}
```

## Troubleshooting

**Animation not showing?**
- Check browser console for errors
- Verify `hero-animation.json` exists in the correct folder
- Check file permissions

**Animation too large/small?**
- Adjust height in the HTML: `style="height: 400px;"`
- Modify responsive CSS in the `@media` queries

**Animation plays too fast/slow?**
- Change `speed="1"` attribute (0.5 = half speed, 2 = double speed)

**Want to prevent autoplay?**
- Remove the `autoplay` attribute
- Add `controls` attribute for manual playback

## Resources

- **LottieFiles:** https://lottiefiles.com/
- **Lottie Documentation:** https://airbnb.io/lottie/
- **Lottie Player Docs:** https://github.com/LottieFiles/lottie-player
- **After Effects + Bodymovin:** https://exchange.adobe.com/creativecloud.details.12557.html

## Current Sample Animation

The included `hero-animation.json` is a simple placeholder with a bouncing baseball. Replace it with a professional animation from LottieFiles or create your own custom animation that matches your brand!
