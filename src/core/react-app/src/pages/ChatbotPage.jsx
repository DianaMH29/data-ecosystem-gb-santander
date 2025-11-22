import { useState, useEffect, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { chatbotService } from "@/services/endpoints";
import {
  MessageCircle,
  Send,
  Bot,
  User,
  Sparkles,
  HelpCircle,
} from "lucide-react";

// Custom Markdown components for styling
const markdownComponents = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="text-sm">{children}</li>,
  h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
  h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
  code: ({ inline, children }) =>
    inline ? (
      <code className="bg-black/10 dark:bg-white/10 px-1 py-0.5 rounded text-xs font-mono">
        {children}
      </code>
    ) : (
      <pre className="bg-black/10 dark:bg-white/10 p-2 rounded text-xs font-mono overflow-x-auto mb-2">
        <code>{children}</code>
      </pre>
    ),
  table: ({ children }) => (
    <div className="overflow-x-auto mb-2">
      <table className="min-w-full text-xs border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-black/5 dark:bg-white/5">{children}</thead>,
  th: ({ children }) => <th className="border border-border px-2 py-1 text-left font-semibold">{children}</th>,
  td: ({ children }) => <td className="border border-border px-2 py-1">{children}</td>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-primary pl-3 italic mb-2">{children}</blockquote>
  ),
  a: ({ href, children }) => (
    <a href={href} className="text-primary underline hover:no-underline" target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
};

// Hook for typewriter effect
function useTypewriter(text, speed = 15, enabled = true, onUpdate) {
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!enabled) {
      setDisplayedText(text);
      setIsComplete(true);
      return;
    }

    setDisplayedText("");
    setIsComplete(false);

    if (!text) return;

    let currentIndex = 0;
    const intervalId = setInterval(() => {
      if (currentIndex < text.length) {
        // Add characters in chunks for faster rendering
        const chunkSize = Math.min(3, text.length - currentIndex);
        const newText = text.slice(0, currentIndex + chunkSize);
        setDisplayedText(newText);
        currentIndex += chunkSize;
        // Notify parent for scroll updates
        if (onUpdate) onUpdate();
      } else {
        setIsComplete(true);
        clearInterval(intervalId);
      }
    }, speed);

    return () => clearInterval(intervalId);
  }, [text, speed, enabled]);

  return { displayedText, isComplete };
}

function Message({ message, isBot, isTyping = false, onTypingUpdate }) {
  const { displayedText, isComplete } = useTypewriter(
    message.text,
    10,
    isBot && isTyping,
    onTypingUpdate
  );

  const textToShow = isBot && isTyping ? displayedText : message.text;

  return (
    <div className={`flex gap-3 ${isBot ? "" : "flex-row-reverse"}`}>
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isBot ? "bg-primary text-primary-foreground" : "bg-muted"
        }`}
      >
        {isBot ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
      </div>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isBot
            ? "bg-muted text-foreground"
            : "bg-primary text-primary-foreground"
        }`}
      >
        {isBot ? (
          <div className="text-sm prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {textToShow}
            </ReactMarkdown>
            {isTyping && !isComplete && (
              <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-0.5" />
            )}
          </div>
        ) : (
          <p className="text-sm whitespace-pre-wrap">{message.text}</p>
        )}
        {message.tipo_consulta && isComplete && (
          <Badge variant="outline" className="mt-2 text-xs">
            {message.tipo_consulta}
          </Badge>
        )}
      </div>
    </div>
  );
}

function SuggestionChip({ text, onClick }) {
  return (
    <button
      onClick={() => onClick(text)}
      className="px-3 py-1.5 text-xs rounded-full border border-primary/20 bg-primary/5 hover:bg-primary/10 text-primary transition-colors"
    >
      {text}
    </button>
  );
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [capacidades, setCapacidades] = useState(null);
  const [typingMessageId, setTypingMessageId] = useState(null);
  const scrollRef = useRef(null);
  const messageIdRef = useRef(0);

  // Load suggestions on mount
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const [suggestionsRes, capacidadesRes] = await Promise.all([
          chatbotService.getSugerencias(),
          chatbotService.getCapacidades(),
        ]);
        setSuggestions(suggestionsRes?.sugerencias || []);
        setCapacidades(capacidadesRes?.categorias || null);
      } catch (error) {
        console.error("Error loading suggestions:", error);
        setSuggestions([
          "¿Cuántos delitos hay en Bucaramanga?",
          "¿Qué municipio tiene más hurtos?",
          "¿Cómo han evolucionado los delitos por año?",
          "¿Qué género sufre más violencia intrafamiliar?",
        ]);
      }
    };
    loadSuggestions();
  }, []);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    const userMessage = { id: ++messageIdRef.current, text, isBot: false };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await chatbotService.consultar(text);
      const botMessageId = ++messageIdRef.current;
      const botMessage = {
        id: botMessageId,
        text: response?.respuesta || "Lo siento, no pude procesar tu consulta.",
        isBot: true,
        tipo_consulta: response?.tipo_consulta,
      };
      setMessages((prev) => [...prev, botMessage]);
      setTypingMessageId(botMessageId);
      
      // Clear typing state after animation completes (estimate based on text length)
      const typingDuration = Math.min(botMessage.text.length * 10 + 500, 10000);
      setTimeout(() => setTypingMessageId(null), typingDuration);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessageId = ++messageIdRef.current;
      const errorMessage = {
        id: errorMessageId,
        text: "Lo siento, ocurrió un error al procesar tu consulta. Por favor intenta de nuevo.",
        isBot: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setTypingMessageId(errorMessageId);
      setTimeout(() => setTypingMessageId(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="h-[calc(100vh-120px)] flex gap-6">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              Asistente de Consultas
            </CardTitle>
            <CardDescription>
              Haz preguntas en lenguaje natural sobre los datos de seguridad
            </CardDescription>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0">
            {/* Messages */}
            <ScrollArea
              ref={scrollRef}
              className="flex-1 px-6"
            >
              <div className="space-y-4 py-4">
                {messages.length === 0 ? (
                  <div className="text-center py-12">
                    <Sparkles className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
                    <h3 className="text-lg font-medium mb-2">
                      ¡Bienvenido al Asistente!
                    </h3>
                    <p className="text-sm text-muted-foreground mb-6">
                      Puedo ayudarte a analizar datos de seguridad de Santander.
                      <br />
                      Prueba con alguna de las sugerencias abajo.
                    </p>
                    <div className="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
                      {suggestions.slice(0, 4).map((sug, i) => (
                        <SuggestionChip
                          key={i}
                          text={sug}
                          onClick={sendMessage}
                        />
                      ))}
                    </div>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <Message 
                      key={msg.id} 
                      message={msg} 
                      isBot={msg.isBot} 
                      isTyping={msg.id === typingMessageId}
                      onTypingUpdate={scrollToBottom}
                    />
                  ))
                )}
                {loading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="bg-muted rounded-lg px-4 py-3">
                      <Spinner size="sm" />
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="p-4 border-t">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Escribe tu pregunta..."
                  disabled={loading}
                  className="flex-1"
                />
                <Button type="submit" disabled={loading || !input.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sidebar */}
      <div className="w-80 hidden lg:block space-y-4">
        {/* Suggestions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              Sugerencias
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {suggestions.map((sug, i) => (
              <button
                key={i}
                onClick={() => sendMessage(sug)}
                className="w-full text-left text-xs p-2 rounded hover:bg-muted transition-colors"
              >
                {sug}
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Capabilities */}
        {capacidades && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <HelpCircle className="h-4 w-4" />
                Capacidades
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="space-y-3">
                  {Object.entries(capacidades).map(([key, value]) => (
                    <div key={key}>
                      <h4 className="font-medium text-xs uppercase text-muted-foreground mb-1">
                        {key}
                      </h4>
                      <p className="text-xs text-foreground mb-1">
                        {value.descripcion}
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {value.ejemplos?.slice(0, 3).map((ej, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {ej}
                          </Badge>
                        ))}
                      </div>
                      <Separator className="mt-3" />
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
