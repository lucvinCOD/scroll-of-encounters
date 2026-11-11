import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  return (
    <main className="min-h-screen bg-stone-950 px-6 py-16 text-stone-100 sm:py-24">
      <div className="mx-auto max-w-3xl">{children}</div>
    </main>
  );
}
