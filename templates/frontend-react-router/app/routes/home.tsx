import type { Route } from "./+types/home";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "React Router + Bun Template" },
    { name: "description", content: "A modern React app template with React Router, Bun, and shadcn/ui" },
  ];
}

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <Card className="max-w-2xl w-full">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold mb-2">
            React Router + Bun Template
          </CardTitle>
          <CardDescription className="text-lg">
            A modern, production-ready template for building React applications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center space-y-4">
            <p className="text-gray-600 dark:text-gray-400">
              This template includes everything you need to start building:
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <Badge variant="secondary">React 19</Badge>
              <Badge variant="secondary">React Router 7</Badge>
              <Badge variant="secondary">Bun Runtime</Badge>
              <Badge variant="secondary">shadcn/ui Components</Badge>
              <Badge variant="secondary">Tailwind CSS</Badge>
              <Badge variant="secondary">TypeScript</Badge>
              <Badge variant="secondary">Polytope Containerization</Badge>
            </div>
          </div>
          
          <div className="border rounded-lg p-4 bg-gray-50 dark:bg-gray-800">
            <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">
              Adding Dependencies
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              Use the polytope module to add new packages:
            </p>
            <code className="text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-800 dark:text-gray-200">
              polytope run {`{{ project-name }}`}-add --packages "package-name"
            </code>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Start building your application by editing the routes in the <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">app/</code> directory.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
