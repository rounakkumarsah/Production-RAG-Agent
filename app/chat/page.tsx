import { AppShell } from "@/components/layout/app-shell";
import { ChatInterface } from "@/components/chat/chat-interface";

export default function ChatPage() {
  return (
    <AppShell activePath="/chat">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Chat</h1>
        <p className="mt-1 text-muted-foreground">
          Query your knowledge base with AI-powered answers
        </p>
      </div>

      <ChatInterface />
    </AppShell>
  );
}
