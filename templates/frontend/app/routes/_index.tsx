import type { Route } from "./+types/home";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "~/components/ui/card";
import { Button } from "~/components/ui/button";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "{{ project-name }}" },
    { name: "description", content: "Welcome to {{ project-name }}!" },
  ];
}

export default function Home() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{{ project-name }}</CardTitle>
          <CardDescription>
            Your application starting point
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-muted-foreground">
              This template provides a solid foundation with React Router v7, shadcn/ui components,
              and automatic light/dark mode support.
            </p>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-2">Ready to expand:</p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Ask an AI agent to build features for you</li>
                <li>• Edit files in <code className="text-foreground">app/routes/</code></li>
                <li>• Add components to <code className="text-foreground">app/components/</code></li>
              </ul>
            </div>
            {/* Example buttons - uncomment to see theming examples
            <div className="flex gap-2">
              <Button>Primary Action</Button>
              <Button variant="outline">Secondary</Button>
              <Button variant="destructive">Delete</Button>
            </div>
            */}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
