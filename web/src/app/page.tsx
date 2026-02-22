'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Settings, Activity, Cpu, Layers, Volume2,
  Waves, Sliders, RefreshCcw, Send,
  Music, Radio, Fingerprint, BarChart3, Database,
  Coffee, Github, ExternalLink
} from 'lucide-react';
import { MIDI_CC_MAP } from '@/utils/midiMapping';
import Pusher from 'pusher-js';

// Quick Preset Prompts
const PRESETS = [
  { emoji: '🔥', label: 'Death Metal', prompt: 'Aggressive modern death metal with scooped mids, high gain amp, tight noise gate, and heavy cab simulation. Enhance low-end punch and high-end sizzle.' },
  { emoji: '🌊', label: 'Ethereal', prompt: 'Ethereal ambient soundscape with extreme reverb decay, shimmering chorus, analog delay taps, and transparent compression.' },
  { emoji: '🎸', label: 'TX Blues', prompt: 'SRV-style Texas blues with warm tube overdrive, moderate compression, spring reverb, and bridge-position cab sim.' },
  { emoji: '🎹', label: 'Funk Pop', prompt: 'Crisp funk clean with fast compression, bright EQ, subtle modulation, and high dynamic range.' },
];

const SIGNAL_BLOCKS = [
  { id: 'cmp', label: 'CMP', icon: Activity },
  { id: 'efx', label: 'EFX', icon: Zap },
  { id: 'amp', label: 'AMP', icon: Cpu },
  { id: 'eq', label: 'EQ', icon: Sliders },
  { id: 'nr', label: 'NR', icon: Radio },
  { id: 'mod', label: 'MOD', icon: Waves },
  { id: 'dly', label: 'DLY', icon: Music },
  { id: 'rvb', label: 'RVB', icon: Volume2 },
];

export default function Home() {
  const [apiKey, setApiKey] = useState('');
  const [prompt, setPrompt] = useState('');
  const [params, setParams] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [connectionMode, setConnectionMode] = useState<'wifi' | 'usb'>('wifi');
  const [activeTab, setActiveTab] = useState<'config' | 'signal' | 'controls'>('signal');
  const [outputPort, setOutputPort] = useState<any>(null);
  const [allOutputs, setAllOutputs] = useState<any[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const logRef = useRef<HTMLDivElement>(null);

  // Sonic Fingerprint Analysis
  const fingerprint = useMemo(() => {
    if (Object.keys(params).length === 0) return null;

    const getVal = (ks: string[]) => {
      for (const k of ks) {
        const v = params[k];
        if (typeof v === 'number' && !isNaN(v)) return v;
      }
      return 0;
    };

    const aggression = (getVal(['gain', 'amp_gain']) + getVal(['nr_enable']) / 1.27) / 2;
    const space = (getVal(['reverb_mix', 'rvb_knob_2']) + getVal(['delay_mix', 'dly_knob_3'])) / 2;
    const warmth = (getVal(['bass', 'amp_bass']) + getVal(['eq_low'])) / 2;
    const clarity = (getVal(['treble', 'amp_treble']) + getVal(['eq_high']) + getVal(['presence'])) / 3;
    const depth = (getVal(['mod_knob_1']) + getVal(['cab_level'])) / 2;

    return { aggression, space, warmth, clarity, depth };
  }, [params]);

  const addLog = (msg: string) => {
    const time = new Date().toLocaleTimeString();
    setLog(prev => [...prev.slice(-10), `[${time}] ${msg}`]);
  };

  useEffect(() => {
    const savedKey = localStorage.getItem('mg400_api_key');
    if (savedKey) setApiKey(savedKey);

    if (navigator.requestMIDIAccess) {
      navigator.requestMIDIAccess().then((access: any) => {
        const scan = () => {
          const outputs = Array.from(access.outputs.values()) as any[];
          setAllOutputs(outputs);
          const mg400 = outputs.find(o => o.name?.includes("NUX") || o.name?.includes("MG-400"));
          if (mg400) setOutputPort(mg400);
        };
        scan();
        access.onstatechange = scan;
        addLog("✓ MIDI Engine Core Synchronized");
      });
    }

    const pusher = new Pusher('854cb7b69b1f213de54a', {
      cluster: 'ap2'
    });

    const channel = pusher.subscribe('mg400-updates');
    channel.bind('patch-update', (data: any) => {
      if (data.source !== 'mobile_web' && data.params) {
        setParams(prev => {
          const next = { ...prev };
          for (const [k, v] of Object.entries(data.params)) {
            if (typeof v === 'number') next[k] = v;
          }
          return next;
        });
      }
    });

    return () => {
      channel.unbind_all();
      channel.unsubscribe();
      pusher.disconnect();
    };
  }, []);

  const handleGenerate = async (isRemix = false) => {
    if (!apiKey) {
      addLog("✕ Logic Key Missing");
      setActiveTab('config');
      return;
    }
    setLoading(true);
    addLog(`◎ Synthesizing Neural Topology...`);
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, apiKey, isRemix }),
      });
      const data = await res.json();
      if (res.ok) {
        // AI sanity check - handle potential "wrapped" JSON from LLM
        let rawParams = data;
        if (data.params && typeof data.params === 'object') rawParams = data.params;
        else if (data.parameters && typeof data.parameters === 'object') rawParams = data.parameters;

        const cleanParams: Record<string, number> = {};
        Object.entries(rawParams).forEach(([k, v]) => {
          if (typeof v === 'number' && !isNaN(v)) cleanParams[k] = v;
        });

        setParams(cleanParams);
        addLog(`✓ Pattern Matrix Generated`);

        // Broadcast new state globally
        fetch('/api/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: 'generator', params: data })
        });

        if (window.innerWidth < 1024) setActiveTab('controls');
      } else {
        addLog(`✕ Kernel Fault: ${data.error || 'System failed'}`);
      }
    } catch (e) { addLog("✕ Transmission Interrupted"); }
    setLoading(false);
  };

  const updateParam = (key: string, val: number) => {
    setParams(prev => ({ ...prev, [key]: val }));

    // Always broadcast to cloud for global UI synchronization
    fetch('/api/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: 'mobile_web', params: { [key]: val } })
    });

    // Handle local hardware sync
    const cc = MIDI_CC_MAP[key];
    if (cc !== undefined && outputPort && connectionMode === 'usb') {
      outputPort.send([176, cc, val]);
    }
  };

  const isBlockActive = (blockId: string) => {
    const key = `${blockId}_enable`;
    return params[key] > 64;
  };

  return (
    <div className="app-shell">
      <div className="bg-grain" />
      <div className="bg-blobs">
        <div className="blob blob-1" />
        <div className="blob blob-2" />
        <div className="blob blob-3" />
      </div>

      <header className="app-header">
        <div className="brand">
          <motion.div
            className="brand-icon"
            animate={{
              rotate: loading ? [0, 90, 180, 270, 360] : 0,
              scale: loading ? [1, 1.2, 1] : 1
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Database size={18} color="white" />
          </motion.div>
          <div>
            <div className="brand-text">LAB-400</div>
            <div className="brand-sub">SONIC ARCHITECT</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="support-links">
            <a href="https://buymeacoffee.com/mahas" target="_blank" rel="noopener noreferrer" className="support-icon coffee" title="Buy Me a Coffee">
              <Coffee size={16} />
            </a>
            <a href="https://github.com/sponsors/Mahas1234" target="_blank" rel="noopener noreferrer" className="support-icon github" title="Sponsor on GitHub">
              <Github size={16} />
            </a>
          </div>

          <div className="connection-badge">
            <motion.div
              className={`connection-dot ${outputPort ? '' : 'offline'}`}
              animate={outputPort ? { opacity: [1, 0.4, 1], scale: [1, 1.2, 1] } : {}}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <span>{outputPort ? 'SYNCED' : 'OFFLINE'}</span>
          </div>
        </div>
      </header>

      <main className="main-content">

        {/* SETUP TAB */}
        <section className={`content-section ${activeTab === 'config' ? 'active' : ''}`}>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card" style={{ padding: '24px' }}>
            <div className="section-label">
              <div className="duct-tape">Identity & Protocol</div>
            </div>

            <div className="config-grid">
              <div className="config-item">
                <label className="config-label">Interface</label>
                <select className="config-select" value={connectionMode} onChange={e => setConnectionMode(e.target.value as any)}>
                  <option value="wifi">Neural Cloud Mesh</option>
                  <option value="usb">Direct Physical Bridge</option>
                </select>
              </div>
              <div className="config-item">
                <label className="config-label">Gemini Key</label>
                <input className="config-input" type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="ENTER TOKEN" />
              </div>
            </div>

            <div className="log-container" style={{ marginTop: '32px' }}>
              <div className="log-header">
                <Activity size={10} style={{ marginRight: '6px' }} />
                <span>Stream Input</span>
              </div>
              <div className="log-body" ref={logRef}>
                {log.map((l, i) => <div key={i} className="log-entry">{l}</div>)}
              </div>
            </div>
          </motion.div>
        </section>

        {/* SIGNAL TAB */}
        <section className={`content-section ${activeTab === 'signal' ? 'active' : ''}`}>
          <div className="signal-hero">
            <motion.h2
              className="shimmer-text"
              animate={{ letterSpacing: loading ? ['-2px', '4px', '-2px'] : '-2px' }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              SIGNAL<br />SYNTH
            </motion.h2>

            <div className="visualizer">
              {[...Array(24)].map((_, i) => (
                <motion.div
                  key={i} className="v-bar"
                  animate={{
                    height: loading ? [4, 40, 4] : [4, (fingerprint?.aggression || 10) / 3 * Math.random() + 2, 4],
                    backgroundColor: i % 2 === 0 ? 'var(--accent-neon)' : 'var(--accent-violet)'
                  }}
                  transition={{ duration: 0.15, delay: i * 0.02, repeat: Infinity }}
                />
              ))}
            </div>
          </div>

          <div className="preset-scroll">
            {PRESETS.map((p, i) => (
              <button key={i} className="preset-chip" onClick={() => setPrompt(p.prompt)}>{p.label}</button>
            ))}
          </div>

          <motion.div layout className="glass-card" style={{ padding: '24px' }}>
            <div style={{ position: 'relative' }}>
              <textarea
                className="prompt-textarea"
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                placeholder="Describe your sonic vision..."
              />
              <AnimatePresence>
                {loading && (
                  <motion.div
                    initial={{ top: '0%' }}
                    animate={{ top: '100%' }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="scan-line"
                  />
                )}
              </AnimatePresence>
            </div>

            <div className="action-grid">
              <button className="btn btn-primary" onClick={() => handleGenerate()} disabled={loading}>
                {loading ? <RefreshCcw className="animate-spin" size={16} /> : <Zap size={16} />}
                {loading ? 'COMPUTING' : 'SYNTHESIZE'}
              </button>
              <button className="btn btn-secondary" onClick={() => handleGenerate(true)} disabled={loading}>
                <Layers size={16} />
                REMIX
              </button>
            </div>

            <div className="section-label" style={{ marginBottom: '12px' }}>
              <div className="duct-tape">Topology Blocks</div>
            </div>
            <div className="signal-path">
              {SIGNAL_BLOCKS.map((block, i) => (
                <div key={block.id} style={{ display: 'flex', alignItems: 'center' }}>
                  <motion.div
                    className={`path-block ${isBlockActive(block.id) ? 'active' : ''}`}
                    whileHover={{ scale: 1.05 }}
                    animate={isBlockActive(block.id) ? { boxShadow: ['0 0 0px var(--accent-neon)', '0 0 20px var(--accent-neon)', '0 0 0px var(--accent-neon)'] } : {}}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <block.icon className="block-icon" />
                    <span className="block-label">{block.label}</span>
                  </motion.div>
                  {i < SIGNAL_BLOCKS.length - 1 && <div className="path-connector" />}
                </div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* CONTROLS TAB */}
        <section className={`content-section ${activeTab === 'controls' ? 'active' : ''}`}>
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', flex: 1 }}>

            {/* Sonic Fingerprint Radar-style breakdown */}
            <AnimatePresence>
              {fingerprint && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                  className="fingerprint-panel"
                  style={{ marginBottom: '24px', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}
                >
                  <div className="section-label">
                    <div className="duct-tape">Sonic Fingerprint</div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '12px' }}>
                    {Object.entries(fingerprint).map(([key, val]) => (
                      <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '8px', textTransform: 'uppercase', color: 'var(--fg-muted)', fontWeight: 800 }}>
                          <span>{key}</span>
                          <span style={{ color: 'var(--accent-neon)' }}>{Math.round(val)}%</span>
                        </div>
                        <div style={{ height: '4px', background: 'rgba(0,0,0,0.3)', borderRadius: '2px', overflow: 'hidden' }}>
                          <motion.div initial={{ width: 0 }} animate={{ width: `${val}%` }} style={{ height: '100%', background: 'var(--accent-neon)' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="knobs-grid">
              {['gain', 'master', 'presence'].map(id => (
                <div key={id} className="knob-card" onClick={() => updateParam(id, (params[id] || 0) + 5 > 127 ? 0 : (params[id] || 0) + 5)}>
                  <div className="knob-outer">
                    <motion.div className="knob-cap" animate={{ rotate: (params[id] || 0) * 2.4 - 120 }}>
                      <div className="knob-pointer" />
                    </motion.div>
                  </div>
                  <span className="value">{Math.round(params[id] || 0)}</span>
                  <span className="label">{id}</span>
                </div>
              ))}
            </div>

            <div className="mixer-grid">
              {Object.keys(params).length === 0 ? (
                <div style={{ textAlign: 'center', opacity: 0.2, padding: '60px' }}>
                  <BarChart3 size={48} style={{ margin: '0 auto 16px', display: 'block' }} />
                  <div style={{ fontSize: '12px', fontWeight: 800, letterSpacing: '2px' }}>AWAITING SIGNAL MATRIX</div>
                </div>
              ) : (
                <AnimatePresence>
                  {Object.entries(params)
                    .filter(([_, value]) => typeof value === 'number' && !isNaN(value))
                    .map(([key, value], idx) => (
                      <motion.div
                        key={key} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.02 }}
                        className="param-card"
                      >
                        <div className="param-header">
                          <span className="param-name">{key.replace(/_/g, ' ')}</span>
                          <span className="param-value">{Math.round(value)}</span>
                        </div>
                        <input type="range" className="param-slider" min="0" max="127" value={Math.round(value)} onChange={e => updateParam(key, parseInt(e.target.value))} />
                      </motion.div>
                    ))}
                </AnimatePresence>
              )}
            </div>

            {Object.keys(params).length > 0 && (
              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="btn btn-primary" style={{ marginTop: '24px' }} onClick={() => addLog("System Synchronized")}>
                <Send size={16} />
                OVERWRITE CORE
              </motion.button>
            )}
          </div>
        </section>
      </main>

      <nav className="mobile-nav">
        {[
          { id: 'config', icon: Settings, label: 'Identify' },
          { id: 'signal', icon: Zap, label: 'Topology' },
          { id: 'controls', icon: Sliders, label: 'Matrix' },
        ].map(item => (
          <div key={item.id} className={`nav-item ${activeTab === item.id ? 'active' : ''}`} onClick={() => setActiveTab(item.id as any)}>
            <item.icon size={22} />
            <span>{item.label}</span>
          </div>
        ))}
      </nav>
    </div>
  );
}
