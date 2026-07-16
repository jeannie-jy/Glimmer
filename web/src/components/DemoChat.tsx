import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: number;
  type: 'user' | 'thinking' | 'bot' | 'done';
  text?: string;
  codeLines?: string[];
}

const DEMOS = [
  {
    question: '帮我用 Python 写一个快速排序',
    code: `def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

print(quicksort([3, 6, 8, 10, 1, 2, 1]))`,
  },
  {
    question: '帮我生成一个 React Hook 管理倒计时',
    code: `import { useState, useEffect, useCallback } from 'react';

function useCountdown(initial: number) {
  const [time, setTime] = useState(initial);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running || time <= 0) return;
    const id = setInterval(() => setTime(t => t - 1), 1000);
    return () => clearInterval(id);
  }, [running, time]);

  const start = useCallback(() => setRunning(true), []);
  const reset = useCallback(() => {
    setRunning(false); setTime(initial);
  }, [initial]);

  return { time, running, start, reset };
}`,
  },
];

const DemoChat: React.FC = () => {
  const [round, setRound] = useState(0);
  const [messages, setMessages] = useState<Message[]>([]);
  const [step, setStep] = useState<'idle' | 'typing' | 'thinking' | 'code' | 'done'>('idle');
  const scrollRef = useRef<HTMLDivElement>(null);
  const msgId = useRef(0);

  const demo = DEMOS[round % DEMOS.length];

  const nextId = () => ++msgId.current;

  // ---- Animation loop ----
  useEffect(() => {
    const userText = demo.question;
    const codeLines = demo.code.split('\n');
    let cancelled = false;

    const run = async () => {
      // Reset
      setMessages([]);
      setStep('idle');
      await delay(600);

      if (cancelled) return;

      // Step 1: user typing
      setStep('typing');
      const userMsg: Message = { id: nextId(), type: 'user', text: '' };
      setMessages([userMsg]);
      for (let i = 0; i <= userText.length; i++) {
        if (cancelled) return;
        setMessages([{ ...userMsg, text: userText.slice(0, i) }]);
        await delay(i === userText.length ? 400 : 30 + Math.random() * 40);
      }

      if (cancelled) return;

      // Step 2: thinking
      setStep('thinking');
      setMessages((prev) => [...prev, { id: nextId(), type: 'thinking' }]);
      await delay(1200 + Math.random() * 600);

      if (cancelled) return;

      // Step 3: code typing
      setStep('code');
      const botMsg: Message = { id: nextId(), type: 'bot', codeLines: [] };
      setMessages((prev) => [...prev.slice(0, -1), botMsg]);
      for (let i = 0; i <= codeLines.length; i++) {
        if (cancelled) return;
        setMessages((prev) => {
          const msgs = [...prev];
          const last = msgs[msgs.length - 1];
          if (last.type === 'bot') {
            msgs[msgs.length - 1] = { ...last, codeLines: codeLines.slice(0, i) };
          }
          return msgs;
        });
        await delay(i === codeLines.length ? 300 : 80 + Math.random() * 120);
      }

      if (cancelled) return;

      // Step 4: done
      setStep('done');
      setMessages((prev) => [...prev, { id: nextId(), type: 'done', text: '代码生成完毕' }]);
      await delay(3000);

      if (cancelled) return;

      // Next round
      setRound((r) => r + 1);
    };

    run();
    return () => { cancelled = true; };
  }, [round]);

  // ---- Auto-scroll ----
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="demo-chat">
      {/* Window chrome */}
      <div className="demo-chat__chrome">
        <span className="demo-chat__dot demo-chat__dot--red" />
        <span className="demo-chat__dot demo-chat__dot--yellow" />
        <span className="demo-chat__dot demo-chat__dot--green" />
        <span className="demo-chat__chrome-title">Glimmer Agent</span>
      </div>

      {/* Messages */}
      <div className="demo-chat__body" ref={scrollRef}>
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {msg.type === 'user' && (
                <div className="demo-chat__msg demo-chat__msg--user">
                  <span className="demo-chat__msg-label">You</span>
                  <p className="demo-chat__msg-text">
                    {msg.text}
                    {step === 'typing' && messages[messages.length - 1].id === msg.id && (
                      <span className="demo-chat__cursor" />
                    )}
                  </p>
                </div>
              )}

              {msg.type === 'thinking' && (
                <div className="demo-chat__msg demo-chat__msg--thinking">
                  <span className="demo-chat__msg-label">Agent</span>
                  <span className="demo-chat__pulse" />
                  <span className="demo-chat__thinking-text">thinking...</span>
                </div>
              )}

              {msg.type === 'bot' && (
                <div className="demo-chat__msg demo-chat__msg--bot">
                  <span className="demo-chat__msg-label">Agent</span>
                  <pre className="demo-chat__code">
                    <code>
                      {msg.codeLines?.join('\n')}
                      {step === 'code' && messages[messages.length - 1].id === msg.id && (
                        <span className="demo-chat__cursor" />
                      )}
                    </code>
                  </pre>
                </div>
              )}

              {msg.type === 'done' && (
                <div className="demo-chat__done">{msg.text}</div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default DemoChat;
