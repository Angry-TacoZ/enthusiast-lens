import { useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleDot,
  Clock3,
  Code2,
  Database,
  FileSearch,
  Gauge,
  Info,
  Menu,
  PanelRightClose,
  Play,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import { vehicleOptions } from './data/recordedRun'
import { recordedRunClient } from './lib/analysisClient'
import {
  categoryFromFieldId,
  formatDuration,
  formatFactValue,
  formatFieldLabel,
} from './lib/formatters'
import type { AnalysisRecord, FactResult, RunMode } from './types'

const categories = [
  ['all', 'All facts'],
  ['engine_and_measured_performance', 'Performance'],
  ['transmission', 'Transmission'],
  ['drivetrain_and_differentials', 'Drivetrain'],
  ['suspension_axles_and_chassis', 'Chassis'],
  ['brakes_wheels_and_tires', 'Brakes & tires'],
  ['audio', 'Audio'],
  ['driver_assistance_and_highway_automation', 'Driver assist'],
  ['configuration_dependencies', 'Dependencies'],
] as const

const categoryLabels = Object.fromEntries(categories)

function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </div>
  )
}

function AnimatedCarLogo() {
  return (
    <div className="animated-car-logo" role="img" aria-label="Enthusiast Lens animated sports car mark">
      <div className="logo-meta" aria-hidden="true">
        <span>EL / 01</span>
        <span>CONFIGURATION SIGNAL</span>
      </div>
      <svg className="car-logo-svg" viewBox="0 0 420 150" aria-hidden="true">
        <defs>
          <linearGradient id="car-glow" x1="0" x2="1">
            <stop offset="0" stopColor="#d8ff3e" stopOpacity="0" />
            <stop offset="0.5" stopColor="#d8ff3e" stopOpacity="0.8" />
            <stop offset="1" stopColor="#d8ff3e" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path className="speed-line speed-line-a" d="M19 93H91" />
        <path className="speed-line speed-line-b" d="M39 105H119" />
        <path className="speed-line speed-line-c" d="M324 83h73" />
        <path className="car-trace" d="M87 91c12-5 22-23 38-27l42-8 30-26h65l35 30 49 11c13 3 26 10 35 20v12H87z" />
        <path className="car-trace car-trace-animated" d="M87 91c12-5 22-23 38-27l42-8 30-26h65l35 30 49 11c13 3 26 10 35 20v12H87z" />
        <path className="car-window" d="M181 57l21-20h55l24 22" />
        <path className="car-highlight" d="M102 82h249" />
        <path className="car-glow" d="M91 94h292" />
        <circle className="car-wheel" cx="143" cy="95" r="20" />
        <circle className="car-wheel" cx="323" cy="95" r="20" />
        <circle className="car-wheel-core" cx="143" cy="95" r="7" />
        <circle className="car-wheel-core" cx="323" cy="95" r="7" />
        <path className="car-lamp" d="M371 78l16 4" />
        <path className="car-lamp car-lamp-front" d="M94 80l-13 5" />
        <rect className="logo-scan" x="95" y="32" width="3" height="77" rx="1.5" />
      </svg>
      <div className="logo-caption" aria-hidden="true">
        <span>OBJECTIVE / VERIFIED / IN MOTION</span>
        <span>ENTHUSIAST LENS</span>
      </div>
    </div>
  )
}

function FactStatus({ fact }: { fact: FactResult }) {
  const status = fact.state === 'known' ? fact.origin ?? 'known' : fact.state
  const labels: Record<string, string> = {
    structured: 'Structured',
    researched: 'Web verified',
    derived: 'Derived',
    known: 'Known',
    unknown: 'Unknown',
    conflicted: 'Conflict',
    not_available: 'Not available',
    not_applicable: 'N/A',
  }
  return <span className={`status-chip status-${status}`}>{labels[status]}</span>
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  )
}

function Sidebar({
  open,
  onClose,
  selectedVehicle,
  onVehicleChange,
  mode,
  onModeChange,
  onRun,
  loading,
}: {
  open: boolean
  onClose: () => void
  selectedVehicle: string
  onVehicleChange: (id: string) => void
  mode: RunMode
  onModeChange: (mode: RunMode) => void
  onRun: () => void
  loading: boolean
}) {
  return (
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <div className="brand-row">
        <BrandMark />
        <div>
          <strong>Enthusiast Lens</strong>
          <span>Objective vehicle intelligence</span>
        </div>
        <button className="icon-button sidebar-close" onClick={onClose} aria-label="Close navigation">
          <X size={18} />
        </button>
      </div>

      <nav aria-label="Primary">
        <a href="#report" className="nav-item nav-item-active">
          <FileSearch size={18} /> Analysis
        </a>
        <a href="#comparison" className="nav-item">
          <Gauge size={18} /> Comparison <span>Soon</span>
        </a>
        <a href="#run-details" className="nav-item">
          <Activity size={18} /> Run details
        </a>
      </nav>

      <div className="sidebar-workspace">
        <p className="eyebrow">Analysis setup</p>
        <label className="field-label" htmlFor="vehicle-select">
          Vehicle context
        </label>
        <div className="select-wrap">
          <select
            id="vehicle-select"
            value={selectedVehicle}
            onChange={(event) => onVehicleChange(event.target.value)}
          >
            {vehicleOptions.map((vehicle) => (
              <option key={vehicle.id} value={vehicle.id}>
                {vehicle.label}
              </option>
            ))}
          </select>
          <ChevronDown size={16} aria-hidden="true" />
        </div>
        <p className="vehicle-detail">
          {vehicleOptions.find((vehicle) => vehicle.id === selectedVehicle)?.detail}
        </p>

        <span className="field-label">Pipeline</span>
        <div className="mode-switch" role="group" aria-label="Analysis pipeline">
          <button
            className={mode === 'full_web' ? 'active' : ''}
            onClick={() => onModeChange('full_web')}
            aria-pressed={mode === 'full_web'}
          >
            Full-Web
          </button>
          <button
            className={mode === 'hybrid' ? 'active' : ''}
            onClick={() => onModeChange('hybrid')}
            aria-pressed={mode === 'hybrid'}
          >
            Hybrid
          </button>
        </div>
        <p className="mode-help">
          {mode === 'full_web'
            ? 'Researches the complete schema from public evidence.'
            : 'Starts with vPIC, then researches only unresolved facts.'}
        </p>

        <button className="run-button" onClick={onRun} disabled={loading}>
          {loading ? <RotateCcw className="spin" size={17} /> : <Play size={17} fill="currentColor" />}
          {loading ? 'Loading run…' : 'Load recorded run'}
        </button>
        <p className="demo-note">
          <Info size={14} /> Recorded evidence only. Live API connection follows the backend contract.
        </p>
      </div>

      <div className="principle">
        <ShieldCheck size={18} />
        <div>
          <strong>Rules first</strong>
          <span>Evidence second. Human decision always.</span>
        </div>
      </div>
    </aside>
  )
}

function EvidenceInspector({ fact, onClose }: { fact: FactResult; onClose: () => void }) {
  return (
    <aside className="inspector" aria-label="Fact evidence">
      <div className="inspector-header">
        <div>
          <span className="eyebrow">Evidence inspector</span>
          <h2>{formatFieldLabel(fact.field_id)}</h2>
        </div>
        <button className="icon-button" onClick={onClose} aria-label="Close evidence inspector">
          <PanelRightClose size={19} />
        </button>
      </div>

      <div className="inspector-value">
        <FactStatus fact={fact} />
        <strong>{formatFactValue(fact)}</strong>
        <code>{fact.field_id}</code>
      </div>

      {fact.configuration_dependency_notes && (
        <div className="inspector-note">
          <AlertTriangle size={17} />
          <div>
            <strong>Configuration dependency</strong>
            <p>{fact.configuration_dependency_notes}</p>
          </div>
        </div>
      )}

      <div className="inspector-section">
        <div className="section-title-row">
          <h3>Supporting evidence</h3>
          <span>{fact.provenance.length}</span>
        </div>
        {fact.provenance.length === 0 ? (
          <p className="empty-copy">No external source is needed for this deterministic value.</p>
        ) : (
          fact.provenance.map((item, index) => (
            <article className="source-item" key={`${item.publisher}-${index}`}>
              <div className="source-rank">{String(index + 1).padStart(2, '0')}</div>
              <div>
                <div className="source-topline">
                  <strong>{item.publisher ?? 'Unlabeled source'}</strong>
                  <span>{item.configuration_match?.replace('_', ' ') ?? 'match unknown'}</span>
                </div>
                <p>{item.notes ?? 'Source retained with the canonical fact.'}</p>
                {item.source_url && (
                  <a href={item.source_url} target="_blank" rel="noreferrer">
                    Open source <ArrowUpRight size={14} />
                  </a>
                )}
              </div>
            </article>
          ))
        )}
      </div>

      <div className="inspector-section compact">
        <h3>Verification</h3>
        <dl className="definition-list">
          <div>
            <dt>Origin</dt>
            <dd>{fact.origin ?? 'Unspecified'}</dd>
          </div>
          <div>
            <dt>Confidence</dt>
            <dd>{fact.confidence ?? 'Deterministic'}</dd>
          </div>
          <div>
            <dt>State</dt>
            <dd>{fact.state.replace('_', ' ')}</dd>
          </div>
        </dl>
      </div>
    </aside>
  )
}

function EmptyRun({ mode }: { mode: RunMode }) {
  return (
    <div className="empty-run">
      <div className="empty-run-mark">
        <Database size={24} />
      </div>
      <span className="eyebrow">No compatible recorded result</span>
      <h2>{mode === 'hybrid' ? 'Hybrid result pending' : 'Choose a recorded vehicle'}</h2>
      <p>
        This UI never invents comparison metrics. A result appears only after a validated backend or
        tracked artifact supplies the canonical record.
      </p>
    </div>
  )
}

function Report({
  record,
  selectedFact,
  onFactSelect,
}: {
  record: AnalysisRecord
  selectedFact: FactResult | null
  onFactSelect: (fact: FactResult) => void
}) {
  const [category, setCategory] = useState('all')
  const [query, setQuery] = useState('')

  const visibleFacts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return record.facts.filter((item) => {
      const inCategory = category === 'all' || categoryFromFieldId(item.field_id) === category
      const inSearch =
        !normalizedQuery ||
        item.field_id.toLowerCase().includes(normalizedQuery) ||
        formatFactValue(item).toLowerCase().includes(normalizedQuery)
      return inCategory && inSearch
    })
  }, [category, query, record.facts])

  const knownCount = record.facts.filter((item) => item.state === 'known').length
  const unknownCount = record.facts.filter((item) => item.state === 'unknown').length

  return (
    <>
      <section className="report-hero" id="report">
        <div className="report-kicker">
          <span className="recorded-dot" /> Recorded evaluation run
          <span>•</span>
          <span>{new Date(record.completed_at ?? record.started_at).toLocaleDateString()}</span>
        </div>
        <div className="vehicle-title-row">
          <div>
            <h1>
              {record.vehicle.year} {record.vehicle.make} <span>{record.vehicle.model}</span>
            </h1>
            <p>
              {record.vehicle.trim} · {record.vehicle.body_style} · {record.vehicle.market} market
            </p>
          </div>
          <div className="run-status"><Check size={15} /> Run complete</div>
        </div>
        <div className="configuration-line" aria-label="Selected configuration">
          <span>{record.vehicle.transmission}</span>
          <span>{record.vehicle.drivetrain}</span>
          <span>VIN •••{record.vehicle.vin?.slice(-6)}</span>
          <span>{record.run_mode === 'full_web' ? 'Full-Web' : 'Hybrid'}</span>
        </div>
      </section>

      {record.configuration_notes[0] && (
        <section className="configuration-alert">
          <div className="alert-icon"><AlertTriangle size={18} /></div>
          <div>
            <span>Configuration changes the answer</span>
            <p>{record.configuration_notes[0]}</p>
          </div>
          <button
            onClick={() => {
              const dependency = record.facts.find((item) => item.field_id.startsWith('configuration_dependencies'))
              if (dependency) onFactSelect(dependency)
            }}
          >
            Inspect evidence <ArrowUpRight size={15} />
          </button>
        </section>
      )}

      <section className="metrics-strip" aria-label="Run metrics">
        <Metric label="Resolved" value={`${knownCount}/${record.facts.length}`} detail="facts in this report view" />
        <Metric label="Unknown" value={String(unknownCount)} detail="left explicit, not inferred" />
        <Metric label="Sources" value={String(record.grounded_source_count ?? '—')} detail="grounded references" />
        <Metric label="Run time" value={formatDuration(record.latency_ms)} detail={`${record.model_call_count ?? '—'} model calls`} />
        <Metric label="Est. cost" value={record.estimated_cost_usd === null ? '—' : `$${record.estimated_cost_usd.toFixed(3)}`} detail="recorded provider estimate" />
      </section>

      <section className="facts-workspace">
        <div className="facts-toolbar">
          <div>
            <span className="eyebrow">Objective report</span>
            <h2>Configuration-matched facts</h2>
          </div>
          <label className="search-box">
            <Search size={16} />
            <span className="sr-only">Search facts</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search facts"
            />
          </label>
        </div>

        <div className="category-tabs" role="tablist" aria-label="Fact category">
          {categories.map(([id, label]) => (
            <button
              key={id}
              role="tab"
              aria-selected={category === id}
              className={category === id ? 'active' : ''}
              onClick={() => setCategory(id)}
            >
              {label}
              <span>
                {id === 'all'
                  ? record.facts.length
                  : record.facts.filter((item) => categoryFromFieldId(item.field_id) === id).length}
              </span>
            </button>
          ))}
        </div>

        <div className="fact-list">
          <div className="fact-list-head" aria-hidden="true">
            <span>Fact</span><span>Result</span><span>Evidence</span>
          </div>
          {visibleFacts.map((item) => (
            <button
              key={item.field_id}
              className={`fact-row ${selectedFact?.field_id === item.field_id ? 'selected' : ''}`}
              onClick={() => onFactSelect(item)}
              aria-label={`Inspect ${formatFieldLabel(item.field_id)} evidence`}
            >
              <span className="fact-name">
                <strong>{formatFieldLabel(item.field_id)}</strong>
                <small>{categoryLabels[categoryFromFieldId(item.field_id)] ?? 'Other'}</small>
              </span>
              <span className="fact-value">
                <strong>{formatFactValue(item)}</strong>
                {item.configuration_dependency_notes && <small>Configuration-specific</small>}
              </span>
              <span className="fact-evidence">
                <FactStatus fact={item} />
                <small>{item.provenance.length} source{item.provenance.length === 1 ? '' : 's'}</small>
              </span>
              <ArrowUpRight className="fact-arrow" size={16} />
            </button>
          ))}
          {visibleFacts.length === 0 && <p className="no-results">No facts match this filter.</p>}
        </div>
      </section>

      <section className="run-details" id="run-details">
        <div>
          <span className="eyebrow">Inspectable execution</span>
          <h2>Run details</h2>
          <p>Enough operational context to reproduce or challenge the result—without exposing hidden reasoning.</p>
        </div>
        <dl>
          <div><dt><Sparkles size={16} /> Model</dt><dd>{record.model}</dd></div>
          <div><dt><Search size={16} /> Searches</dt><dd>{record.search_query_count ?? '—'}</dd></div>
          <div><dt><Clock3 size={16} /> Duration</dt><dd>{formatDuration(record.latency_ms)}</dd></div>
          <div><dt><Code2 size={16} /> System</dt><dd>{record.system_version}</dd></div>
        </dl>
      </section>
    </>
  )
}

export function App() {
  const [selectedVehicle, setSelectedVehicle] = useState('miata-gt-auto')
  const [mode, setMode] = useState<RunMode>('full_web')
  const [record, setRecord] = useState<AnalysisRecord | null>(null)
  const [selectedFact, setSelectedFact] = useState<FactResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  async function loadRun() {
    setLoading(true)
    setSelectedFact(null)
    const nextRecord = await recordedRunClient.loadRecordedRun(selectedVehicle, mode)
    setRecord(nextRecord)
    setLoading(false)
    setSidebarOpen(false)
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to report</a>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        selectedVehicle={selectedVehicle}
        onVehicleChange={(id) => {
          setSelectedVehicle(id)
          setRecord(null)
          setSelectedFact(null)
        }}
        mode={mode}
        onModeChange={(nextMode) => {
          setMode(nextMode)
          setRecord(null)
          setSelectedFact(null)
        }}
        onRun={loadRun}
        loading={loading}
      />
      {sidebarOpen && <button className="scrim" onClick={() => setSidebarOpen(false)} aria-label="Close navigation" />}

      <div className="main-column">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <div className="topbar-context">
            <CircleDot size={14} /> Local judge preview
          </div>
          <div className="topbar-boundary"><Database size={14} /> Recorded artifact</div>
        </header>
        <main id="main-content" className={selectedFact ? 'with-inspector' : ''}>
          {record ? (
            <Report record={record} selectedFact={selectedFact} onFactSelect={setSelectedFact} />
          ) : loading ? (
            <div className="loading-state"><RotateCcw className="spin" size={24} /><span>Loading validated record…</span></div>
          ) : mode === 'hybrid' ? (
            <EmptyRun mode={mode} />
          ) : (
            <div className="welcome-state">
              <div className="welcome-grid" aria-hidden="true" />
              <AnimatedCarLogo />
              <div className="welcome-copy">
                <span className="eyebrow"><ShieldCheck size={14} /> Evidence-first analysis</span>
                <h1>See what the listing leaves out.</h1>
                <p>Resolve the exact configuration, inspect objective enthusiast facts, and challenge every answer at its source.</p>
                <button onClick={loadRun}><Play size={17} fill="currentColor" /> Open recorded analysis</button>
                <span>2026 MX-5 Miata · Full-Web · tracked evaluation artifact</span>
              </div>
              <div className="welcome-principles" aria-label="Product principles">
                <div><span>01</span><strong>Exact configuration</strong><p>Trim, transmission, drivetrain, package, and build date stay attached.</p></div>
                <div><span>02</span><strong>Unknown is honest</strong><p>Missing evidence remains visible instead of becoming an invented answer.</p></div>
                <div><span>03</span><strong>Sources stay open</strong><p>Every researched value keeps provenance and confidence.</p></div>
              </div>
            </div>
          )}
        </main>
      </div>

      {selectedFact && <EvidenceInspector fact={selectedFact} onClose={() => setSelectedFact(null)} />}
    </div>
  )
}
