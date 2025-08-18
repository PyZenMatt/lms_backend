import { PropsWithChildren, useEffect } from 'react';
import { Sidebar, SidebarContent } from '@/components/ui';
import { Toaster } from '@/components/ui';

export function AppShell({ children }: PropsWithChildren) {
  useEffect(() => {
    const html = document.documentElement;
    html.setAttribute('data-theme', 'v2');
    return () => html.removeAttribute('data-theme');
  }, []);

  return (
    <div className="bg-background text-foreground min-h-dvh">
      <div className="flex">
        <Sidebar className="border-r border-border">
          <SidebarContent />
        </Sidebar>
        <main className="flex-1 p-4 lg:p-6">
          {children}
        </main>
      </div>
      <Toaster />
    </div>
  );
}
