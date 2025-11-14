# 🎨 NormScout Style Blueprint - Quick Reference

## 📐 DESIGN TOKENS (Copy These Exact Values)

```css
/* COLORS - Use These Exact Hex Values */
--brand-blue: #3869FA;      /* Primary brand, logos, highlights */
--royal-blue: #2048D5;      /* Headings, CTAs, important text */
--accent-blue: #448CF7;     /* Buttons, hover states, links */
--text-dark: #1a1a1a;       /* Body text, headings */
--text-light: #666666;      /* Descriptions, secondary text */
--text-muted: #94a3b8;      /* Hints, disabled states */
--white: #FFFFFF;           /* Backgrounds, button text */
--medium-gray: #EEF0F3;     /* Borders, dividers */

/* GRADIENTS - Copy Exact Values */
linear-gradient(135deg, #2048D5 0%, #1a3eb3 100%)    /* Hero sections */
linear-gradient(135deg, #667eea 0%, #764ba2 100%)    /* Chat bubbles (user) */
linear-gradient(135deg, #3869FA 0%, #448CF7 100%)    /* Buttons, CTAs */
linear-gradient(135deg, #10b981 0%, #059669 100%)    /* Success, progress */

/* SPACING - Use These Variables */
var(--spacing-xs): 8px      /* Tight spacing, badges */
var(--spacing-sm): 16px     /* Default gaps, padding */
var(--spacing-md): 24px     /* Section spacing */
var(--spacing-lg): 32px     /* Large sections */
var(--spacing-xl): 48px     /* Major sections */
var(--spacing-2xl): 64px    /* Page sections */
var(--spacing-3xl): 96px    /* Hero sections */

/* TYPOGRAPHY */
font-family: 'Inter', sans-serif;
font-size-base: 16px        /* Body text */
font-size-large: 18px       /* Large text, buttons */
font-size-xl: 24px          /* Section titles */
font-size-2xl: 32px         /* Page titles */
font-size-3xl: 48px         /* Hero titles */

/* RADIUS */
var(--radius-md): 8px       /* Buttons, inputs */
var(--radius-lg): 12px      /* Cards */
var(--radius-xl): 16px      /* Modals, large cards */

/* SHADOWS */
var(--shadow-sm): 0 1px 2px rgba(0, 0, 0, 0.05)      /* Subtle elevation */
var(--shadow-md): 0 4px 6px rgba(0, 0, 0, 0.1)       /* Cards, hover */
var(--shadow-lg): 0 10px 15px rgba(0, 0, 0, 0.1)     /* Lifted cards */
var(--shadow-xl): 0 20px 25px rgba(0, 0, 0, 0.08)    /* Modals */
```

---

## 🏗️ PAGE TEMPLATES (Choose One)

### **Template A: Main App Page** (Dashboard, Workspace, etc.)
```html
{% extends "base.html" %}

{% block title %}Your Page - NormScout{% endblock %}

{% block nav_links %}
    <a href="/dashboard" class="nav-link">Dashboard</a>
    <a href="/contact" class="nav-link">Contact</a>
{% endblock %}

{% block content %}
    <div class="[BACKGROUND-CLASS]">
        <div class="container">
            <!-- Your content here -->
        </div>
    </div>
{% endblock %}

{% block extra_scripts %}
    <script src="/your-script.js"></script>
{% endblock %}
```

**Backgrounds:**
- Dashboard/workspace style: `class="dashboard-container"` → gradient background
- Clean white: `class="section"` → white background
- Homepage style: No wrapper → white default

---

### **Template B: Static Page** (Contact, Legal, etc.)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title - NormScout</title>
    <link rel="icon" type="image/svg+xml" href="/img/logo_icon.svg">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Copy design tokens from style.css :root section */
        /* Add page-specific styles */
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">
                <img src="/img/full_logo.svg" alt="NormScout" class="logo-svg">
            </a>
            <a href="/" class="btn btn-outline">← Back to Home</a>
        </div>
    </header>

    <main class="main-content">
        <!-- Content here -->
    </main>

    <footer class="footer">
        <p>© 2025 NormScout. All rights reserved.</p>
    </footer>
</body>
</html>
```

---

## 🧩 COMPONENT LIBRARY (Copy & Paste)

### **1. BUTTONS**

```html
<!-- Primary CTA -->
<button class="btn btn-accent">
    Try Now
</button>

<!-- Large CTA -->
<button class="btn btn-accent btn-large">
    Get Started Free
</button>

<!-- Secondary -->
<button class="btn btn-primary">
    Save Changes
</button>

<!-- Destructive -->
<button class="btn btn-danger">
    Delete
</button>

<!-- Outline -->
<button class="btn btn-outline">
    Cancel
</button>

<!-- With Icon -->
<button class="btn btn-accent">
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 2v12M2 8h12"/>
    </svg>
    Create New
</button>
```

---

### **2. CARDS**

```html
<!-- Standard Card -->
<div class="dashboard-section">
    <h2 class="section-title">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4 4h12v12H4V4z"/>
        </svg>
        Section Title
    </h2>
    <div class="section-content">
        <!-- Content here -->
    </div>
</div>

<!-- Hoverable Card (Grid Item) -->
<div class="workspace-card">
    <div class="workspace-card-header">
        <h3 class="workspace-name">Card Title</h3>
        <span class="count-badge">5</span>
    </div>
    <p class="workspace-description">Card description text</p>
    <div class="workspace-meta">
        <span>Created 2 days ago</span>
    </div>
</div>

<!-- Step Card (How It Works style) -->
<div class="step-card">
    <div class="step-icon">
        <svg width="48" height="48"><!-- Icon --></svg>
    </div>
    <h3 class="step-title">Step Title</h3>
    <p class="step-description">Description text</p>
</div>
```

---

### **3. GRIDS**

```html
<!-- Auto-fit Grid (Cards) -->
<div class="workspaces-grid">
    <!-- Grid items auto-fit at 320px minimum -->
</div>

<!-- Steps Grid (2-4 columns) -->
<div class="steps-grid">
    <!-- 1 col mobile → 2 tablet → 4 desktop -->
</div>

<!-- Stats Grid -->
<div class="stats-grid">
    <!-- Auto-fit, minimum 250px -->
</div>
```

**When to use:**
- `workspaces-grid`: Workspace cards, project cards
- `steps-grid`: Features, how-it-works sections
- `stats-grid`: Metrics, dashboard statistics

---

### **4. FORMS**

```html
<!-- Input Field -->
<input type="text" class="input-field" placeholder="Enter text">

<!-- Textarea -->
<textarea class="input-field" rows="3" placeholder="Enter description"></textarea>

<!-- Form Group -->
<div class="account-info-item">
    <label>Field Label</label>
    <span>Field Value</span>
</div>

<!-- Input with Button -->
<div class="input-group">
    <input type="text" placeholder="Type here">
    <button class="btn btn-accent">Send</button>
</div>
```

---

### **5. MODALS**

```html
<!-- Standard Modal -->
<div id="myModal" class="modal" style="display: none;">
    <div class="modal-content modal-small">
        <button class="modal-close" onclick="hideModal()">&times;</button>
        <div class="modal-header">
            <h2>Modal Title</h2>
            <p>Optional description</p>
        </div>
        <div class="modal-body">
            <!-- Content here -->
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="hideModal()">Cancel</button>
            <button class="btn btn-accent" onclick="save()">Confirm</button>
        </div>
    </div>
</div>

<script>
function showModal() {
    document.getElementById('myModal').style.display = 'flex';
}
function hideModal() {
    document.getElementById('myModal').style.display = 'none';
}
</script>
```

---

### **6. STATES (Loading, Empty, Error)**

```html
<!-- Loading State -->
<div class="loading-state">
    <div class="loading-spinner"></div>
    <p>Loading...</p>
</div>

<!-- Empty State -->
<div class="empty-state">
    <svg width="64" height="64" class="empty-icon">
        <!-- Icon -->
    </svg>
    <h3>No Items Yet</h3>
    <p>Description of empty state</p>
    <button class="btn btn-accent">Create First Item</button>
</div>

<!-- Error State -->
<div class="error-state">
    <svg width="64" height="64" class="error-icon">
        <!-- Error icon -->
    </svg>
    <h2>Something Went Wrong</h2>
    <p>Error description</p>
    <button class="btn btn-primary">Try Again</button>
</div>
```

---

### **7. CHAT INTERFACE**

```html
<div class="teaser-chat-container">
    <div class="teaser-chat-messages" id="chatMessages">
        <!-- Assistant Message -->
        <div class="teaser-message teaser-assistant">
            <strong>NormScout AI</strong>
            <p>Message text here</p>
        </div>

        <!-- User Message -->
        <div class="teaser-message teaser-user">
            <strong>You</strong>
            <p>User message text</p>
        </div>
    </div>

    <!-- Input -->
    <div class="teaser-input-container">
        <textarea class="teaser-input" rows="3" placeholder="Type here..."></textarea>
        <button class="btn btn-accent btn-large">Send</button>
    </div>
</div>
```

---

### **8. BADGES & LABELS**

```html
<!-- Count Badge -->
<span class="count-badge">5</span>

<!-- Confidence Badge (Colored) -->
<span class="confidence-badge confidence-high">High</span>
<span class="confidence-badge confidence-medium">Medium</span>
<span class="confidence-badge confidence-low">Low</span>

<!-- Small Badge -->
<span class="workspace-number">#123</span>
```

---

### **9. NAVIGATION**

```html
<!-- Breadcrumb -->
<div class="workspace-breadcrumb">
    <a href="/dashboard">Dashboard</a>
    <span>/</span>
    <span>Current Page</span>
</div>

<!-- User Dropdown (Already in base.html) -->
<!-- Just reference: #userDropdown, #userMenu -->
```

---

## 🎯 DECISION TREE: "Which Pattern Should I Use?"

### **CHOOSING A PAGE TEMPLATE:**
```
├─ Is it part of the main app? (needs auth, nav, footer)
│  └─ YES → Use Template A (extends base.html)
│
└─ Is it standalone? (legal, contact, marketing)
   └─ YES → Use Template B (standalone HTML)
```

### **CHOOSING A BACKGROUND:**
```
├─ User workspace/dashboard?
│  └─ Use: class="dashboard-container" (gradient background)
│
├─ Marketing/homepage section?
│  └─ Use: class="section" with custom bg-color
│
└─ Clean app interface?
   └─ Use: white default (no special class)
```

### **CHOOSING A GRID:**
```
├─ Cards that should auto-fit based on width?
│  └─ Use: class="workspaces-grid"
│
├─ Equal-width columns (2-4)?
│  └─ Use: class="steps-grid"
│
└─ Statistics/metrics?
   └─ Use: class="stats-grid"
```

### **CHOOSING A BUTTON:**
```
├─ Primary action (most important)?
│  └─ Use: btn btn-accent (blue gradient)
│
├─ Secondary action?
│  └─ Use: btn btn-primary (solid blue)
│
├─ Destructive action?
│  └─ Use: btn btn-danger (red)
│
└─ Cancel/go back?
   └─ Use: btn btn-outline (border only)
```

### **CHOOSING A CARD STYLE:**
```
├─ Section with title & content?
│  └─ Use: dashboard-section
│
├─ Grid item (workspace, project)?
│  └─ Use: workspace-card
│
└─ Feature/step showcase?
   └─ Use: step-card
```

---

## 📱 RESPONSIVE CHECKLIST

**For Every New Page:**
```css
/* Mobile First - Start Here */
.your-element {
    /* Base mobile styles */
}

/* Tablet (768px+) */
@media (min-width: 768px) {
    .your-element {
        /* Tablet adjustments */
    }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
    .your-element {
        /* Desktop features */
    }
}
```

**Key Responsive Patterns:**
- Grids: `1fr` → `2fr` → `4fr`
- Padding: `16px` → `24px` → `32px`
- Font: `32px` → `42px` → `56px` (hero)
- Buttons: `full-width` → `inline-flex`

---

## 🎨 COMMON PATTERNS & THEIR EXACT CODE

### **Hero Section**
```html
<section class="hero">
    <div class="container">
        <div class="hero-content">
            <div class="hero-text">
                <h1 class="hero-title">Your Title</h1>
                <p class="hero-subtitle">Subtitle text</p>
                <a href="#demo" class="btn btn-accent btn-large">CTA Text</a>
            </div>
        </div>
    </div>
</section>
```

### **Section with Title**
```html
<section class="value-proposition">
    <div class="container">
        <h2 class="section-title">Section Title</h2>
        <!-- Content -->
    </div>
</section>
```

### **Dashboard Layout**
```html
<div class="dashboard-container">
    <div class="container">
        <div class="dashboard-welcome">
            <h1 class="dashboard-title">Welcome!</h1>
        </div>

        <div class="dashboard-section">
            <!-- Section content -->
        </div>
    </div>
</div>
```

### **Two-Column Grid**
```html
<div class="workspace-grid">
    <div class="workspace-main">
        <!-- Main content -->
    </div>
    <div class="workspace-sidebar">
        <!-- Sidebar -->
    </div>
</div>
```

---

## ⚡ QUICK COPY-PASTE SNIPPETS

### **Add Icon to Text**
```html
<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style="margin-right: 8px;">
    <path d="YOUR_PATH_HERE"/>
</svg>
```

### **Hover Effect (Any Element)**
```css
.your-element {
    transition: all 0.2s ease;
}
.your-element:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
```

### **Standard Page Padding**
```css
padding: var(--spacing-2xl) 0; /* Top/bottom sections */
margin-top: 80px; /* Account for fixed header */
```

### **Center Content Card**
```css
max-width: 800px;
margin: 0 auto;
padding: var(--spacing-xl);
background: white;
border-radius: var(--radius-xl);
box-shadow: var(--shadow-sm);
```

---

## 🚀 NEW PAGE CHECKLIST

**Before You Start:**
- [ ] Decide: Template A (app) or B (standalone)?
- [ ] Choose background style
- [ ] List components needed

**While Building:**
- [ ] Use exact design token values
- [ ] Add loading/empty/error states
- [ ] Include responsive breakpoints
- [ ] Add hover effects to interactive elements
- [ ] Use semantic HTML

**Before Committing:**
- [ ] Test on mobile (< 768px)
- [ ] Test on tablet (768-1024px)
- [ ] Test on desktop (> 1024px)
- [ ] Verify colors match design tokens
- [ ] Check spacing consistency
- [ ] Ensure buttons have proper states

---

## 💡 PRO TIPS

1. **Color Usage:**
   - `--brand-blue`: Logos, highlights, icons
   - `--royal-blue`: Headings, primary text, section titles
   - `--accent-blue`: Buttons, links, hover states

2. **Spacing Rule:**
   - Same-type elements: `--spacing-sm` (16px)
   - Different sections: `--spacing-xl` (48px)
   - Major divisions: `--spacing-2xl` (64px)

3. **Shadow Hierarchy:**
   - Flat elements: `--shadow-sm`
   - Cards: `--shadow-md`
   - Lifted/hover: `--shadow-lg`
   - Modals: `--shadow-xl`

4. **Animation Standard:**
   ```css
   transition: all 0.2s ease; /* Fast interactions */
   transition: all 0.3s ease; /* Medium animations */
   ```

5. **Z-Index Layers:**
   - Content: 1
   - Header: 1000
   - Dropdowns: 100
   - Modals: 10000

---

## 📄 FULL PAGE EXAMPLE

**Copy this entire structure for a new app page:**

```html
{% extends "base.html" %}

{% block title %}My New Page - NormScout{% endblock %}

{% block nav_links %}
    <a href="/dashboard" class="nav-link">Dashboard</a>
    <a href="/contact" class="nav-link">Contact</a>
{% endblock %}

{% block content %}
    <div class="dashboard-container">
        <div class="container">
            <!-- Welcome Section -->
            <div class="dashboard-welcome">
                <h1 class="dashboard-title">My New Page</h1>
                <p class="dashboard-subtitle">Page description</p>
            </div>

            <!-- Main Section -->
            <div class="dashboard-section">
                <h2 class="section-title">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M4 4h12v12H4V4z"/>
                    </svg>
                    Section Title
                </h2>
                <div class="section-content">
                    <!-- Your content here -->
                </div>
            </div>
        </div>
    </div>
{% endblock %}

{% block extra_scripts %}
    <script src="/my-script.js"></script>
{% endblock %}
```

---

**That's it! You now have everything you need to create consistent pages. Just copy-paste and customize! 🎉**
