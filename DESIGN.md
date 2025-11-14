# BaseballBinder Design System
Vision UI Dashboard React Theme Reference

## Color Palette

### Primary Colors
```
Brand Blue:     #0075ff
Primary Purple: #4318ff (focus: #9f7aea)
Secondary Dark: #0f1535 (focus: #131538)
```

### Background & Surface
```
Dark Body:      #030c1d
Card/Surface:   Gradient (rgba(6,11,40,0.94) to rgba(10,14,35,0.49))
Sidenav Button: #1a1f37
```

### Text Colors
```
Primary Text:   #a0aec0 (grey-400)
Focus/White:    #ffffff
Dark Headings:  #344767
```

### Semantic Colors
```
Success:  #01b574 (focus: #35d28a)
Warning:  #ffb547 (focus: #ffcd75)
Error:    #e31a1a (focus: #ee5d50)
Info:     #0075ff (focus: #3993fe)
```

### Accent Colors
```
Light Blue: #4299e1
Orange:     #f6ad55
```

### Grey Scale
```
100: #edf2f7  (lightest)
200: #e2e8f0
300: #cbd5e0
400: #a0aec0  (main text)
500: #718096
600: #4a5568
700: #2d3748  (borders)
800: #1a202a
900: #171923  (darkest)
```

### Borders
```
Main:   #56577a
Red:    #e31a1a
Navbar: rgba(226,232,240,0.3)
```

---

## Typography

### Font Family
```
"Plus Jakarta Display", "Helvetica", "Arial", sans-serif
```

### Font Weights
```
Light:   300
Regular: 400
Medium:  500
Bold:    700
```

### Headings
```
h1: 48px, line-height: 1.25
h2: 36px, line-height: 1.3
h3: 30px, line-height: 1.375
h4: 24px, line-height: 1.375
h5: 20px, line-height: 1.375
h6: 16px, line-height: 1.625
```

### Body Text
```
XL:      20px
Regular: 16px
SM:      14px
XS:      12px
XXS:     10px
```

### Display Sizes (for big numbers/stats)
```
d1: 80px
d2: 72px
d3: 64px
d4: 56px
d5: 48px
d6: 40px
```

---

## Component Styling

### Cards
```css
Background: linear-gradient(127.09deg,
  rgba(6,11,40,0.94) 19.41%,
  rgba(10,14,35,0.49) 76.65%)
Border-radius: 15px
Padding: 20-24px
Box-shadow: rgba(0,0,0,0.1) 0px 2px 5px
```

### Buttons

**Primary**
```css
Background: #0075ff
Color: #ffffff
Padding: 10px 24px
Border-radius: 12px
Font: 14px bold uppercase
Hover: brightness(1.1)
```

**Secondary**
```css
Background: transparent
Border: 1px solid #56577a
Color: #a0aec0
Hover: background #1a1f37
```

**Success**
```css
Background: #01b574
Color: #ffffff
```

**Danger/Error**
```css
Background: #e31a1a
Color: #ffffff
```

### Tables
```css
Header Background: rgba(255,255,255,0.05)
Row Border: 1px solid #2d3748 (grey-700)
Row Hover: rgba(255,255,255,0.03)
Text: #a0aec0
Padding: 12px
```
- Dark Data Grids (Checklist & Admin tables):
  * Use CSS grid for header + rows to keep column widths aligned (define `gridTemplateColumns` once and reuse).
  * Table wrapper: `linear-gradient(135deg, rgba(6,11,40,0.95), rgba(10,14,35,0.6))`, `border-radius: 15px`, `border: 1px solid rgba(255,255,255,0.1)`.
  * Header strip: `background-color: rgba(6,11,40,0.96)` with uppercase captions, `letter-spacing: 0.8px`.
  * Row background by status:
    - Pending: `rgba(255, 181, 71, 0.15)`
    - Approved/Completed: `rgba(1, 181, 116, 0.15)`
    - Rejected: `rgba(227, 26, 26, 0.15)`
    - Default: `rgba(255,255,255,0.04)`
  * Status badges remain in-column but rows carry subtle tint for quick scanning.
  * Action buttons live inside their own grid cell to avoid shifting headers.

### Forms & Inputs
```css
Background: #0f1535
Border: 1px solid rgba(226,232,240,0.3)
Focus Border: rgba(226,232,240,0.6)
Color: #ffffff
Padding: 12px 16px
Border-radius: 12px
Box-shadow (focus): #628fc2
```

### Sidebar/Navigation
```css
Background: linear-gradient(127.09deg,
  rgba(6,11,40,0.94) 19.41%,
  rgba(10,14,35,0.49) 76.65%)
Width: 250px
Item Hover: #1a1f37
Active Item: #0075ff with gradient
Icon Size: 15px
```

---

## Spacing Scale
```
xs:  4px
sm:  8px
md:  16px
lg:  24px
xl:  32px
xxl: 48px
```

---

## Shadows
```
Card:   0 2px 5px rgba(0,0,0,0.1)
Button: 0 3px 12px rgba(0,117,255,0.3)
Hover:  0 5px 15px rgba(0,0,0,0.2)
```

---

## Icon Guidelines
- Use react-icons library
- Icon size: 15px for navigation, 20px for actions
- Color: inherit from parent or #a0aec0
- Active/hover: #0075ff

---

## Gradients

### Card Gradient
```css
background: linear-gradient(127.09deg,
  rgba(6,11,40,0.94) 19.41%,
  rgba(10,14,35,0.49) 76.65%)
```

### Primary Button Gradient (optional)
```css
background: linear-gradient(97.89deg,
  #4318ff,
  #9f7aea)
```

---

## Best Practices
1. Always use VuiBox, VuiTypography components (Vision UI)
2. Maintain dark theme consistency
3. Use semantic color variables (success, error, warning)
4. Keep contrast ratio WCAG AA compliant
5. Test with white text on dark backgrounds
6. Use gradients for depth and visual interest
