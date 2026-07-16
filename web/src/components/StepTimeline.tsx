import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wand2, ScrollText, Sparkles, Clipboard } from 'lucide-react';

interface Step { number: number; icon: React.ReactNode; title: string; code: string; desc: string; }

const STEPS: Step[] = [
  { number: 1, icon: <Wand2 size={12} />, title: '安装依赖', code: 'pip install -r requirements.txt', desc: '安装所有 Python 依赖包，包括 FastAPI、pydantic、anthropic、openai 等。' },
  { number: 2, icon: <ScrollText size={12} />, title: '配置 API 密钥', code: '# 在 Settings 面板中输入你的 API Key\n# 或设置环境变量:\nexport ANTHROPIC_API_KEY=sk-ant-...', desc: '支持 Anthropic 和 OpenAI 两种 Provider。密钥安全存储在 OS Keyring 或 AES-GCM 加密文件中。' },
  { number: 3, icon: <Sparkles size={12} />, title: '启动服务', code: 'make run\n# 或直接:\nuvicorn server.main:app --host 127.0.0.1 --port 8000 --reload', desc: '启动 FastAPI 开发服务器，WebSocket 和 REST API 自动就绪。' },
  { number: 4, icon: <Wand2 size={12} />, title: '开始施法', code: '# 打开浏览器访问 http://localhost:8000\n# 在 Agent 页面输入你的任务，开始施法！', desc: '在聊天界面输入任务描述，Agent 将自动规划、执行、观察并自我修正。' },
];

const StepItem: React.FC<{ step: Step; isLast: boolean }> = ({ step, isLast }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="step-item">
      {!isLast && <div className="step-item__connector" />}
      <motion.button className={`step-item__bubble ${expanded ? 'step-item__bubble--active' : ''}`} onClick={() => setExpanded(!expanded)} whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}>
        <span className="step-item__icon">{step.icon}</span>
        <span className="step-item__number">{step.number}</span>
      </motion.button>
      <div className="step-item__content">
        <h3 className="step-item__title" onClick={() => setExpanded(!expanded)} style={{ cursor: 'pointer' }}>{step.title}</h3>
        <AnimatePresence>
          {expanded && (
            <motion.div className="step-item__body" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
              <p className="step-item__desc">{step.desc}</p>
              <pre className="step-item__code"><code>{step.code}</code></pre>
              <button className="step-item__copy" onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(step.code); }} type="button"><Clipboard size={14} /> Copy</button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

const StepTimeline: React.FC = () => (
  <div className="step-timeline">
    {STEPS.map((step, idx) => (<StepItem key={step.number} step={step} isLast={idx === STEPS.length - 1} />))}
  </div>
);

export default StepTimeline;
