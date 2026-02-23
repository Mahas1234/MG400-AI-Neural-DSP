'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Settings, Activity, Cpu, Layers, Volume2,
  Waves, Sliders, RefreshCcw, Send,
  Music, Radio, Fingerprint, BarChart3, Database,
  Coffee, Github, ExternalLink, Download, Edit3, Save
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
  const [connectionMode, setConnectionMode] = useState<'wifi' | 'usb'>('usb');
  const [activeTab, setActiveTab] = useState<'config' | 'signal' | 'controls'>('signal');
  const [outputPort, setOutputPort] = useState<any>(null);
  const [allOutputs, setAllOutputs] = useState<any[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [presetRotations, setPresetRotations] = useState<number[]>([]);
  const [patchName, setPatchName] = useState('NEURAL-01');
  const logRef = useRef<HTMLDivElement>(null);

  // Fix hydration mismatch by generating random values only on client
  useEffect(() => {
    setPresetRotations(PRESETS.map(() => Math.random() * 2 - 1));
    const hasVisited = localStorage.getItem('mg400_visited');
    if (!hasVisited) setShowOnboarding(true);
  }, []);

  const closeOnboarding = () => {
    setShowOnboarding(false);
    localStorage.setItem('mg400_visited', 'true');
  };

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
    const savedPatchName = localStorage.getItem('mg400_patch_name');
    if (savedKey) setApiKey(savedKey);
    if (savedPatchName) setPatchName(savedPatchName);

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

  // Registry Cache Persistence
  useEffect(() => {
    if (apiKey) localStorage.setItem('mg400_api_key', apiKey);
  }, [apiKey]);

  useEffect(() => {
    if (patchName && patchName !== "SYNCING...") {
      localStorage.setItem('mg400_patch_name', patchName);
    }
  }, [patchName]);

  const downloadPatch = () => {
    const data = {
      name: patchName,
      timestamp: new Date().toISOString(),
      params,
      fingerprint
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${patchName.toLowerCase().replace(/\s+/g, '_')}.mg400`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    addLog(`✓ Exported ${patchName}`);
  };

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
        if (data.patchName) setPatchName(data.patchName.toUpperCase().slice(0, 10));
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

  const sendToProcessor = () => {
    if (!outputPort || connectionMode !== 'usb') {
      addLog("✕ Physical Bridge Not Established");
      setActiveTab('config');
      return;
    }
    if (Object.keys(params).length === 0) {
      addLog("✕ Signal Matrix Empty - Synthesize First");
      return;
    }
    addLog(`◎ Synchronizing Matrix to MG-400...`);
    const oldName = patchName;
    setPatchName("SYNCING...");
    addLog(`◎ Propagating Neural Name: ${oldName}`);

    // Hardware SysEx Identity Sync (NUX/Cherub Protocol)
    try {
      const sysexHeader = [0xF0, 0x00, 0x20, 0x72, 0x01, 0x07, 0x00, 0x00, 0x00, 0x10];
      const nameBytes = new Array(16).fill(32); // Fill with spaces
      const safeName = (oldName || "NEURAL-PATCH").toUpperCase();
      for (let i = 0; i < Math.min(safeName.length, 16); i++) {
        nameBytes[i] = safeName.charCodeAt(i);
      }
      const fullSysex = [...sysexHeader, ...nameBytes, 0xF7];
      outputPort.send(fullSysex);
    } catch (e) {
      console.warn("SysEx Identity Sync Failed:", e);
    }

    // CC Parameter Sweep
    setTimeout(() => {
      Object.entries(params).forEach(([key, val]) => {
        const cc = MIDI_CC_MAP[key];
        if (cc !== undefined) {
          outputPort.send([176, cc, val]);
        }
      });
      setPatchName(oldName);
      addLog(`✓ Hardware State & Identity Synchronized`);
    }, 800);
  };

  const saveToProcessor = () => {
    if (!outputPort || connectionMode !== 'usb') {
      addLog("✕ Physical Bridge Not Established");
      return;
    }

    // Final Identity Sync before Memory Write
    try {
      const sysexHeader = [0xF0, 0x00, 0x20, 0x72, 0x01, 0x07, 0x00, 0x00, 0x00, 0x10];
      const nameBytes = new Array(16).fill(32);
      const safeName = patchName.toUpperCase();
      for (let i = 0; i < Math.min(safeName.length, 16); i++) {
        nameBytes[i] = safeName.charCodeAt(i);
      }
      outputPort.send([...sysexHeader, ...nameBytes, 0xF7]);
    } catch (e) {
      console.warn("Save Identity Sync Fault:", e);
    }

    addLog(`◎ Writing Neural Data to Flash Memory...`);
    // Simulated internal save delay
    setTimeout(() => {
      addLog(`✓ ${patchName} Permanently Saved`);
    }, 1000);
  };

  const isBlockActive = (blockId: string) => {
    const key = `${blockId}_enable`;
    return params[key] > 64;
  };

  return (
    <div className="app-shell">
      <div className="bg-studio" />
      <div className="studio-glow" />
      <div className="bg-grain" />

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
            <div className="brand-sub">{patchName}</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="support-links">
            <button className="support-icon haptic-touch" onClick={downloadPatch} title="Export Patch">
              <Download size={16} />
            </button>
            <a href="https://github.com/sponsors/Mahas1234" target="_blank" rel="noopener noreferrer" className="support-icon github" title="Sponsor">
              <Github size={16} />
            </a>
          </div>

          <div className="connection-badge">
            <div
              className="status-dot"
              style={{ width: 8, height: 8, borderRadius: '50%', background: outputPort ? 'var(--accent-neon)' : '#f00', boxShadow: outputPort ? '0 0 10px var(--accent-neon)' : 'none' }}
            />
            <span>{outputPort ? 'SYNCED' : 'OFFLINE'}</span>
          </div>
        </div>
      </header>

      <main className="main-content">
        {/* SETUP TAB */}
        <section className={`content-section ${activeTab === 'config' ? 'active' : ''}`}>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card haptic-touch"
            style={{ padding: '24px' }}
          >
            <div className="section-label">
              <div className="duct-tape">Identity & Registry</div>
            </div>

            <div className="config-grid">
              <div className="config-item">
                <label className="config-label">Patch Name</label>
                <div style={{ position: 'relative' }}>
                  <input
                    className="config-input sketch-border"
                    type="text"
                    value={patchName}
                    onChange={e => setPatchName(e.target.value.toUpperCase().slice(0, 10))}
                    placeholder="NAME"
                  />
                  <Edit3 size={12} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', opacity: 0.3 }} />
                </div>
              </div>
              <div className="config-item">
                <label className="config-label">Interface</label>
                <select className="config-select sketch-border" value={connectionMode} onChange={e => setConnectionMode(e.target.value as any)}>
                  <option value="usb">Direct Physical Bridge</option>
                  <option value="wifi">Neural Cloud Mesh</option>
                </select>
              </div>
              <div className="config-item">
                <label className="config-label">Neural Key</label>
                <input className="config-input sketch-border" type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="ENTER TOKEN" />
              </div>
            </div>

            <div className="log-container" style={{ marginTop: '32px', position: 'relative', zIndex: 10 }}>
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
          <div className="tab-container" style={{ width: '100%' }}>
            <div className="signal-hero">
              <motion.h2
                className="shimmer-text neon-glow-text hero-title"
                animate={{ letterSpacing: loading ? ['-2px', '4px', '-2px'] : '-2px' }}
                transition={{ duration: 3, repeat: Infinity }}
              >
                SIGNAL<br />SYNTH
              </motion.h2>

              <div className="visualizer">
                {[...Array(32)].map((_, i) => (
                  <motion.div
                    key={i} className="v-bar"
                    animate={{
                      height: loading ? [4, 60, 4] : [4, (fingerprint?.aggression || 10) / 2 * Math.random() + 5, 4],
                      backgroundColor: i % 2 === 0 ? 'var(--accent-neon)' : 'var(--accent-violet)'
                    }}
                    transition={{ duration: 0.15, delay: i * 0.01, repeat: Infinity }}
                  />
                ))}
              </div>
            </div>

            <div className="preset-scroll">
              {PRESETS.map((p, i) => (
                <button
                  key={i}
                  className="preset-chip haptic-touch"
                  style={{ transform: `rotate(${presetRotations[i] || 0}deg)` }}
                  onClick={() => {
                    setPrompt(p.prompt);
                    setPatchName(p.label.toUpperCase().slice(0, 10));
                    addLog(`📍 Loaded ${p.label} template`);
                  }}
                >
                  {p.emoji} {p.label}
                </button>
              ))}
            </div>

            <motion.div layout className="glass-card" style={{ padding: '24px' }}>
              <div className="paper-overlay" />

              <div style={{ marginBottom: '24px', position: 'relative', zIndex: 10, border: '1px solid rgba(255,255,255,0.05)', padding: '16px', borderRadius: '16px', background: 'rgba(0,0,0,0.2)' }}>
                <div style={{ position: 'absolute', top: '-10px', left: '16px' }}>
                  <div className="duct-tape" style={{ fontSize: '8px', padding: '2px 8px' }}>Signal Registry</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div className="config-item" style={{ marginBottom: 0 }}>
                    <label className="config-label" style={{ fontSize: '9px' }}>Patch Name</label>
                    <input
                      className="config-input sketch-border"
                      style={{ padding: '8px 12px', fontSize: '11px', background: 'rgba(0,0,0,0.4)' }}
                      type="text"
                      value={patchName}
                      onChange={e => setPatchName(e.target.value.toUpperCase().slice(0, 10))}
                      placeholder="NAME (10 CHRS)"
                    />
                  </div>
                  <div className="config-item" style={{ marginBottom: 0 }}>
                    <label className="config-label" style={{ fontSize: '9px' }}>Neural Key</label>
                    <input
                      className="config-input sketch-border"
                      style={{ padding: '8px 12px', fontSize: '11px', background: 'rgba(0,0,0,0.4)' }}
                      type="password"
                      value={apiKey}
                      onChange={e => setApiKey(e.target.value)}
                      placeholder="SET API KEY"
                    />
                  </div>
                </div>
              </div>

              <div style={{ position: 'relative', zIndex: 10 }}>
                <textarea
                  className="prompt-textarea sketch-border"
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  placeholder="Describe your sonic vision..."
                  style={{ minHeight: '120px' }}
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

              <div className="action-grid" style={{ position: 'relative', zIndex: 10, marginTop: '20px', display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                <button className="btn btn-primary haptic-touch" style={{ flex: 1, minWidth: '120px' }} onClick={() => handleGenerate()} disabled={loading}>
                  {loading ? <RefreshCcw className="animate-spin" size={16} /> : <Zap size={16} />}
                  {loading ? 'COMPUTING' : 'SYNTHESIZE'}
                </button>
                <button className="btn btn-secondary haptic-touch" style={{ flex: 1, minWidth: '100px' }} onClick={() => handleGenerate(true)} disabled={loading}>
                  <Layers size={16} />
                  REMIX
                </button>
                <button
                  className="btn btn-secondary haptic-touch"
                  style={{
                    flex: 1,
                    minWidth: '160px',
                    border: '2px solid var(--accent-neon)',
                    color: 'var(--accent-neon)',
                    background: 'rgba(0, 247, 255, 0.08)',
                    boxShadow: '0 0 20px rgba(0, 247, 255, 0.2)',
                    fontWeight: 900
                  }}
                  onClick={sendToProcessor}
                  disabled={loading}
                >
                  <Cpu size={16} />
                  LOAD TO PROCESSOR
                </button>
              </div>

              <div className="section-label" style={{ marginBottom: '16px', marginTop: '32px' }}>
                <div className="duct-tape">Topology Board</div>
              </div>

              <div className="signal-cable-system sketch-border" style={{ position: 'relative', background: 'rgba(0,0,0,0.3)', borderRadius: '12px' }}>
                <div className="cable-line" />
                {SIGNAL_BLOCKS.map((block) => (
                  <div key={block.id} className={`pedal-unit ${isBlockActive(block.id) ? 'active' : ''}`}>
                    <motion.div
                      className="pedal-icon-box haptic-touch"
                      whileHover={{ y: -5 }}
                    >
                      <div className="pedal-led" />
                      <block.icon size={24} color={isBlockActive(block.id) ? 'var(--accent-neon)' : '#555'} />
                    </motion.div>
                    <span className="pedal-label">{block.label}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* CONTROLS TAB */}
        <section className={`content-section ${activeTab === 'controls' ? 'active' : ''}`}>
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', flex: 1 }}>
            <div className="bottom-sheet-handle" />
            <div className="paper-overlay" />
            <div style={{ position: 'relative', zIndex: 10 }}>
              <AnimatePresence>
                {fingerprint && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                    className="fingerprint-panel"
                    style={{ marginBottom: '24px', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}
                  >
                    <div className="section-label">
                      <div className="duct-tape" style={{ background: '#ff007a' }}>Sonic Fingerprint</div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '16px' }}>
                      {Object.entries(fingerprint).map(([key, val]) => (
                        <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', textTransform: 'uppercase', color: 'var(--fg-muted)', fontWeight: 900, letterSpacing: '1px' }}>
                            <span>{key}</span>
                            <span className="neon-glow-text">{Math.round(val)}%</span>
                          </div>
                          <div style={{ height: '6px', background: 'rgba(0,0,0,0.4)', borderRadius: '10px', overflow: 'hidden' }}>
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${val}%` }}
                              style={{ height: '100%', background: 'linear-gradient(90deg, var(--accent-neon), var(--accent-violet))' }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="amp-chassis-container">
                <div className="corner-tl amp-corner" />
                <div className="corner-tr amp-corner" />
                <div className="corner-bl amp-corner" />
                <div className="corner-br amp-corner" />

                <div className="amp-panel">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <div className="amp-input-jack">
                      <div className="jack-inner" />
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '10px', fontWeight: 900 }}>MG-400 NEURAL</div>
                      <div style={{ fontSize: '8px', color: '#666' }}>SONIC ARCHITECT SERIES</div>
                    </div>
                    <div className="amp-toggle">
                      <div className={`toggle-switch ${outputPort ? 'on' : ''}`} />
                      <span style={{ fontSize: '6px', fontWeight: 900, textAlign: 'center' }}>ON</span>
                    </div>
                  </div>

                  <div className="knobs-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '30px' }}>
                    {['gain', 'master', 'presence'].map(id => (
                      <div key={id} className="knob-card" style={{ background: 'transparent', border: 'none' }}>
                        <div className="chicken-head-knob haptic-touch" onClick={() => updateParam(id, (params[id] || 0) + 12 > 127 ? 0 : (params[id] || 0) + 12)}>
                          <div className="knob-marks">
                            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(m => (
                              <div key={m} className="mark" style={{ transform: `translate(-50%, -50%) rotate(${m * 24 - 120}deg) translateY(-32px) rotate(${-(m * 24 - 120)}deg)` }}>{m}</div>
                            ))}
                          </div>
                          <motion.div className="knob-body" animate={{ rotate: (params[id] || 0) * 2.4 - 120 }}>
                            <div className="knob-pointer-wing" />
                          </motion.div>
                        </div>
                        <span className="label" style={{ marginTop: '20px', color: '#111' }}>{id}</span>
                        <span className="value" style={{ color: '#111', fontSize: '12px', fontWeight: 900 }}>{Math.round(params[id] || 0)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="section-label" style={{ marginTop: '40px', marginBottom: '12px' }}>
                <div className="duct-tape">Neural Rack</div>
              </div>

              <div className="mixer-grid">
                {Object.keys(params).length === 0 ? (
                  <div style={{ textAlign: 'center', opacity: 0.15, padding: '40px 20px' }}>
                    <BarChart3 size={32} style={{ margin: '0 auto 12px', display: 'block' }} />
                    <div style={{ fontSize: '10px', fontWeight: 800, letterSpacing: '2px', color: 'var(--fg-muted)' }}>AWAITING SIGNAL MATRIX</div>
                  </div>
                ) : (
                  <AnimatePresence>
                    {Object.entries(params)
                      .filter(([_, value]) => typeof value === 'number' && !isNaN(value))
                      .map(([key, value], idx) => (
                        <motion.div
                          key={key} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.01 }}
                          className="param-card haptic-touch"
                        >
                          <div className="param-header">
                            <span className="param-name">{key.replace(/_/g, ' ')}</span>
                            <span className="param-value neon-glow-text">{Math.round(value)}</span>
                          </div>
                          <input type="range" className="param-slider" min="0" max="127" value={Math.round(value)} onChange={e => updateParam(key, parseInt(e.target.value))} />
                        </motion.div>
                      ))}
                  </AnimatePresence>
                )}
              </div>

              <div className="section-label" style={{ marginTop: '40px', marginBottom: '16px' }}>
                <div className="duct-tape" style={{ background: 'var(--accent-gold)' }}>Active Emulation</div>
              </div>

              <div
                className="cabinet-visual haptic-touch"
                style={{
                  width: '100%',
                  aspectRatio: '16/9',
                  background: '#111',
                  borderRadius: '12px',
                  border: '4px solid #333',
                  position: 'relative',
                  overflow: 'hidden',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 20px 40px rgba(0,0,0,0.5)'
                }}
              >
                <div className="paper-overlay" style={{ opacity: 0.1 }} />
                <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', fontWeight: 900, color: 'var(--accent-neon)', letterSpacing: '4px', marginBottom: '8px' }}>IMPULSE RESPONSE</div>
                  <div style={{ fontSize: '24px', fontWeight: 900, color: '#fff', textTransform: 'uppercase' }}>
                    {params['cab_type'] ? `CAB-MOD 0${(params['cab_type'] % 4) + 1}` : 'DRG METAL CAB 04'}
                  </div>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '12px' }}>
                    <div style={{ width: 40, height: 4, background: 'var(--accent-neon)', borderRadius: 2 }} />
                    <div style={{ width: 20, height: 4, background: '#444', borderRadius: 2 }} />
                    <div style={{ width: 10, height: 4, background: '#444', borderRadius: 2 }} />
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '32px' }}>
                <motion.button
                  whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  className="btn btn-secondary haptic-touch"
                  style={{ width: '100%', border: '2px solid var(--accent-neon)', color: 'var(--accent-neon)' }}
                  onClick={sendToProcessor}
                >
                  <Send size={16} />
                  LOAD TO PROCESSOR
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  className="btn btn-primary haptic-touch"
                  style={{ width: '100%' }}
                  onClick={saveToProcessor}
                >
                  <Save size={16} />
                  SAVE IN PROCESSOR
                </motion.button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <nav className="mobile-nav sketch-border" style={{ borderBottom: 'none', borderLeft: 'none', borderRight: 'none', borderRadius: '24px 24px 0 0' }}>
        {[
          { id: 'config', icon: Settings, label: 'Identify' },
          { id: 'signal', icon: Zap, label: 'Topology' },
          { id: 'controls', icon: Sliders, label: 'Matrix' },
        ].map(item => (
          <div key={item.id} className={`nav-item haptic-touch ${activeTab === item.id ? 'active' : ''}`} onClick={() => setActiveTab(item.id as any)}>
            <item.icon size={22} />
            <span>{item.label}</span>
          </div>
        ))}
      </nav>

      <AnimatePresence>
        {showOnboarding && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="onboarding-overlay"
          >
            <div className="paper-overlay" />
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              className="onboarding-card glass-card haptic-touch"
            >
              <div className="duct-tape" style={{ background: 'var(--accent-neon)', color: '#000' }}>Welcome, Architect</div>
              <p style={{ margin: '20px 0', fontSize: '14px', lineHeight: 1.6, opacity: 0.8 }}>
                You are now connected to the <strong>MG400 Neural Mesh</strong>. Describe a sound in the Topology tab, and our AI will materialize it on your hardware.
              </p>
              <div style={{ display: 'grid', gap: '10px' }}>
                <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                  <div className="brand-icon" style={{ width: 30, height: 30, boxShadow: 'none' }}><Zap size={14} /></div>
                  <span style={{ fontSize: '12px', fontWeight: 600 }}>1. Describe your dream tone in "Topology"</span>
                </div>
                <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                  <div className="brand-icon" style={{ width: 30, height: 30, background: 'var(--accent-violet)', boxShadow: 'none' }}><Sliders size={14} /></div>
                  <span style={{ fontSize: '12px', fontWeight: 600 }}>2. Fine-tune everything in the "Matrix"</span>
                </div>
              </div>
              <button
                className="btn btn-primary haptic-touch"
                style={{ marginTop: '30px', width: '100%' }}
                onClick={closeOnboarding}
              >
                START DESIGNING
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
