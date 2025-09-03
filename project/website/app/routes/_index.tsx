import type { Route } from "./+types/home";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Textarea } from "~/components/ui/textarea";
import { Button } from "~/components/ui/button";
import { useState, useEffect } from "react";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Contact Us" },
    { name: "description", content: "Get in touch with us!" },
  ];
}

export default function Home() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'success' | 'error' | null>(null);
  const [storedForms, setStoredForms] = useState<any[]>([]);
  const [showStoredForms, setShowStoredForms] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3030';
      const response = await fetch(`${apiBaseUrl}/api/contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setSubmitStatus('success');
        setFormData({ name: '', email: '', message: '' });
        // Refresh the stored forms list
        loadStoredForms();
      } else {
        setSubmitStatus('error');
      }
    } catch (error) {
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const loadStoredForms = async () => {
    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3030';
      const response = await fetch(`${apiBaseUrl}/api/contacts`);
      
      if (response.ok) {
        const data = await response.json();
        setStoredForms(data.forms);
      }
    } catch (error) {
      console.error('Failed to load stored forms:', error);
    }
  };

  useEffect(() => {
    loadStoredForms();
  }, []);

  const refreshForms = () => {
    loadStoredForms();
    setShowStoredForms(true);
  };

  return (
    <div className="min-h-screen p-4 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Contact Form */}
          <Card className="w-full">
        <CardHeader>
          <CardTitle>Contact Us</CardTitle>
          <CardDescription>
            Send us a message and we'll get back to you as soon as possible.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <Input
                id="name"
                name="name"
                type="text"
                required
                value={formData.name}
                onChange={handleChange}
                placeholder="Your full name"
              />
            </div>
            
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="your.email@example.com"
              />
            </div>
            
            <div>
              <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                Message
              </label>
              <Textarea
                id="message"
                name="message"
                required
                rows={4}
                value={formData.message}
                onChange={handleChange}
                placeholder="Tell us how we can help you..."
              />
            </div>

            {submitStatus === 'success' && (
              <div className="p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                Thank you! Your message has been sent successfully.
              </div>
            )}

            {submitStatus === 'error' && (
              <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                Sorry, there was an error sending your message. Please try again.
              </div>
            )}

            <Button 
              type="submit" 
              disabled={isSubmitting}
              className="w-full"
            >
              {isSubmitting ? 'Sending...' : 'Send Message'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Stored Forms Display */}
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Stored Contact Forms</CardTitle>
          <CardDescription>
            Proof that data is being stored in Couchbase ({storedForms.length} forms stored)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Button onClick={refreshForms} variant="outline" className="w-full">
              🔄 Refresh Forms ({storedForms.length} stored)
            </Button>
            
            {storedForms.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No forms submitted yet</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {storedForms.map((form) => (
                  <div key={form.id} className="border rounded p-3 bg-white">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium">{form.name}</h4>
                      <span className="text-xs text-gray-500">
                        {new Date(form.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">{form.email}</p>
                    <p className="text-sm">{form.message}</p>
                    <p className="text-xs text-gray-400 mt-2">ID: {form.id}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

    </div>
  </div>
</div>
  );
}
