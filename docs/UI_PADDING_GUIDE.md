# UI Padding Modification Guide

This guide explains where and how to modify padding in the Unguard application's user interface.

## Overview

The Unguard frontend is built with **Next.js** and uses **TailwindCSS** for styling along with **HeroUI** components. Padding can be modified at different levels depending on your needs.

## Key Files for Padding Changes

### 1. Global Layout Padding (`/src/frontend-nextjs/app/layout.tsx`)

**Main container padding:**
```tsx
// Line 42 - Navigation container
<div className='container mx-auto max-w-7xl pt-8 px-6'>

// Line 45 - Main content area  
<main className='container mx-auto max-w-7xl pt-12 px-6 flex-grow p-6 pl-20 pr-20 '>
```

**Padding classes explained:**
- `pt-8` = padding-top: 2rem (32px)
- `px-6` = padding-left and padding-right: 1.5rem (24px) 
- `pt-12` = padding-top: 3rem (48px)
- `pl-20` = padding-left: 5rem (80px)
- `pr-20` = padding-right: 5rem (80px)
- `p-6` = padding: 1.5rem (24px) on all sides

### 2. Component-Level Padding

**CreatePost Component (`/src/frontend-nextjs/components/CreatePost.tsx`):**
```tsx
// Line 64 - Card container
<Card className='w-full border-primary border-1 p-2'>

// Line 66, 71, 127 - Card sections
<CardHeader className='justify-between px-3'>
<CardBody className='px-3 text-small text-default-600'>
<CardFooter className='gap-3 justify-start px-3'>
```

**Navigation Bar (`/src/frontend-nextjs/components/Navbar/NavigationBar.tsx`):**
```tsx
// Line 34 - Logo text spacing
<p className='font-bold text-inherit px-2 text-large text-secondary'>
```

### 3. Global CSS Styles (`/src/frontend-nextjs/styles/globals.css`)

For custom padding that applies globally:
```css
/* Add custom padding classes here */
.custom-padding {
    padding: 1rem;
}
```

### 4. Tailwind Configuration (`/src/frontend-nextjs/tailwind.config.js`)

To add custom padding values:
```javascript
theme: {
    extend: {
        spacing: {
            '18': '4.5rem',
            '88': '22rem',
        },
        padding: {
            '15': '3.75rem',
        }
    },
},
```

## Common Padding Modifications

### Increase Main Content Side Padding
Change horizontal padding in layout.tsx:
```tsx
// Before: pl-20 pr-20 (80px each side)
<main className='container mx-auto max-w-7xl pt-12 px-6 flex-grow p-6 pl-20 pr-20 '>

// After: pl-32 pr-32 (128px each side)  
<main className='container mx-auto max-w-7xl pt-12 px-6 flex-grow p-6 pl-32 pr-32 '>
```

### Adjust Card Component Padding
Modify component padding:
```tsx
// Before: p-2 (8px all sides)
<Card className='w-full border-primary border-1 p-2'>

// After: p-4 (16px all sides)
<Card className='w-full border-primary border-1 p-4'>
```

### Change Navigation Bar Spacing
Adjust navbar container:
```tsx
// Before: pt-8 px-6 
<div className='container mx-auto max-w-7xl pt-8 px-6'>

// After: pt-4 px-8 (less top, more horizontal)
<div className='container mx-auto max-w-7xl pt-4 px-8'>
```

## Tailwind Padding Reference

| Class | CSS | Pixels (default) |
|-------|-----|------------------|
| `p-0` | `padding: 0` | 0px |
| `p-1` | `padding: 0.25rem` | 4px |
| `p-2` | `padding: 0.5rem` | 8px |
| `p-3` | `padding: 0.75rem` | 12px |
| `p-4` | `padding: 1rem` | 16px |
| `p-6` | `padding: 1.5rem` | 24px |
| `p-8` | `padding: 2rem` | 32px |
| `p-12` | `padding: 3rem` | 48px |
| `p-20` | `padding: 5rem` | 80px |
| `p-32` | `padding: 8rem` | 128px |

### Directional Padding
- `pt-*` - padding-top
- `pr-*` - padding-right  
- `pb-*` - padding-bottom
- `pl-*` - padding-left
- `px-*` - padding-left and padding-right
- `py-*` - padding-top and padding-bottom

## Testing Changes

1. **Start development server:**
   ```bash
   cd /src/frontend-nextjs
   npm run dev
   ```

2. **Access the app:**
   ```
   http://localhost:3000/ui
   ```

3. **Hot reload:** Changes to Tailwind classes are reflected immediately

## Best Practices

1. **Use Tailwind classes** instead of custom CSS when possible
2. **Be consistent** with spacing throughout the application
3. **Test on different screen sizes** to ensure responsive behavior
4. **Follow existing patterns** in the codebase
5. **Document significant changes** for team awareness

## Component Examples

### Post Card (`/src/frontend-nextjs/components/Timeline/Post.tsx`)
```tsx
// Line 37 - Card container
<Card className='p-2'>

// Line 38 - Card header
<CardHeader className='justify-between'>

// Line 48 - Content container  
<div className='flex flex-col gap-1 items-start justify-center'>
```

### User Profile Components
Cards typically use:
- `p-2` for small cards (8px padding)
- `p-4` for medium cards (16px padding) 
- `px-3` for header/footer sections (12px horizontal)

## Component Hierarchy for Padding

```
Root Layout (layout.tsx)
├── Navigation Container (pt-8 px-6)
├── Main Content Area (pt-12 px-6 p-6 pl-20 pr-20)
│   ├── Timeline/Posts (p-2)
│   │   ├── Card Headers (justify-between)
│   │   ├── Card Bodies (px-3)
│   │   └── Card Footers (gap-3 justify-start px-3)
│   ├── CreatePost Form (p-2, px-3)
│   └── Page Components (varies)
└── Footer (py-3)
```

## Quick Reference for Common Changes

| To Change | File Location | Current Class | Example New Class |
|-----------|---------------|---------------|-------------------|
| Main content width | `/app/layout.tsx` | `pl-20 pr-20` | `pl-32 pr-32` |
| Card spacing | `/components/CreatePost.tsx` | `p-2` | `p-4` |
| Header sections | `/components/CreatePost.tsx` | `px-3` | `px-4` |
| Navigation spacing | `/app/layout.tsx` | `pt-8 px-6` | `pt-4 px-8` |