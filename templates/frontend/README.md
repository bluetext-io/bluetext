# React Frontend Template

React Router v7 application with Bun, TypeScript, Tailwind CSS, and shadcn/ui components.

## Stack
- **Runtime**: Bun
- **Framework**: React Router v7
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui + Radix UI
- **Auth**: Curity Token Handler support
- **TypeScript**: Full type safety

## Scripts
```bash
bun dev       # Development server
bun build     # Production build  
bun start     # Start built app
bun typecheck # Type checking
```

## Dependencies
To add packages, use the polytope-mcp run tool:
```json
{"module": "add-{{ project-name }}", "arguments": {"packages": "axios react-query"}}
```

## Structure
- `app/` - Application source code
- `app/components/ui/` - Reusable UI components (shadcn/ui)
- `app/routes/` - Route components
- `app/root.tsx` - Root layout component
