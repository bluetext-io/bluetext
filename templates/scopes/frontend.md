# Frontend Development Guidelines

React Router v7 application with Bun, TypeScript, Tailwind CSS, and shadcn/ui + Radix UI components.

## Import Path Guidelines

**CRITICAL**: Follow these import aliases exactly.

### Use `~` for App Code (app/ directory)
```tsx
// CORRECT - For files in app/ directory
import { Button } from "~/components/ui/button";      // app/components/ui/button.tsx
import { HomePage } from "~/routes/home";             // app/routes/home.tsx
```

### Use `@` for Root-Level Files
```tsx
// CORRECT - For files in project root
import { apiClient } from "@/lib/apiClient";          // lib/apiClient.ts
import { utils } from "@/lib/utils";                  // lib/utils.ts
```

### Path Mappings (from tsconfig.json)
- `~/*` → `./app/*` (app directory only)
- `@/*` → `./*` (project root)

### Common Mistakes to Avoid
```tsx
// WRONG - Using ~ for root-level files
import { apiClient } from "~/lib/apiClient";          // lib/ is not in app/

// WRONG - Relative imports from routes
import { Button } from "../../components/ui/button";  // Use ~ instead
```

**Rule**: If it's in `app/`, use `~`. If it's in project root, use `@`.

## Adding Dependencies

```mcp
run(tool: <frontend-name>-add, args: {packages: "axios react-query"})
```

## Theming & Styling

This template uses **shadcn/ui's theme system** which auto-adapts to light/dark mode.

### DO: Use Theme-Aware Classes
```tsx
// CORRECT - Works in both light and dark modes
<div className="bg-background text-foreground">
<div className="bg-card text-card-foreground">
<Button className="bg-primary text-primary-foreground">
<div className="border border-border">
```

### DON'T: Use Fixed Tailwind Colors
```tsx
// WRONG - Breaks theme consistency
<div className="bg-white text-black">        // Breaks in dark mode
<div className="bg-gray-50 text-gray-900">   // No theme adaptation
```

### Available Theme Classes
All auto-adapt to light/dark:
- **Main**: `background`, `foreground` (page background and default text)
- **Components**: `card`, `popover`, `muted` (with matching `-foreground` variants)
- **Interactive**: `primary`, `secondary`, `accent`, `destructive` (with `-foreground`)
- **Form/UI**: `border`, `input`, `ring`

### Opacity Modifiers
Use Tailwind's opacity modifiers for variations:
```tsx
<div className="bg-primary/10">            // 10% opacity of primary color
<div className="text-muted-foreground/50"> // 50% opacity text
<div className="bg-gradient-to-r from-primary/20 to-secondary/20">
```

## Always Use shadcn/ui Components First

Never create custom HTML elements when shadcn components exist:

```tsx
// CORRECT - Use shadcn components
import { Button } from "~/components/ui/button";
<Button variant="destructive" onClick={handleClick}>Click me</Button>
<Button variant="outline">Cancel</Button>

// WRONG - Manual button styling
<button className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90">
```

### Available Components
`Button`, `Card`, `Input`, `Textarea`, `Badge`, `Avatar`, `Dialog`, `Popover`, `Sheet`, `Switch`, `Separator`, `ScrollArea`, `DropdownMenu`, `Sonner`

## Key Rules

1. **Use shadcn components first** - Don't reinvent buttons, cards, inputs, etc.
2. **If you find yourself typing a color name (red, blue, gray, slate, etc.), STOP!** Use semantic classes instead.
3. **Exception**: Pure black/white for logos or truly neutral elements that must stay constant.
