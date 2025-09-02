import type { Route } from "./+types/home";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "~/components/ui/card";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "{{ project-name }}" },
    { name: "description", content: "Welcome to {{ project-name }}!" },
  ];
}

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="pt-6 pb-6">
          <div className="text-center">
            <span className="mx-2">hello world!</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
