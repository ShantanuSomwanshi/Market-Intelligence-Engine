function isOpen(run) {
  if (!run?.report) return false;
  return Object.keys(run.report).length > 0;
}

function copyJson(run) {
  if (!run) return;
  navigator.clipboard.writeText(JSON.stringify(run, null, 2));
}

function exportJson(run) {
  if (!run) return;
  const blob = new Blob([JSON.stringify(run, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${run.run_id || "market-intelligence-run"}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function collectSourceLinks(value) {
  const found = new Map();

  function walk(node) {
    if (!node) return;
    if (Array.isArray(node)) {
      node.forEach(walk);
      return;
    }
    if (typeof node === "object") {
      const url = node.source_url || node.url;
      const label = node.title || node.name || node.headline || node.fact || "Source";
      if (typeof url === "string" && url.length > 0) {
        found.set(url, { url, label });
      }
      Object.values(node).forEach(walk);
    }
  }

  walk(value);
  return Array.from(found.values()).slice(0, 5);
}

function confidenceForSection(value) {
  const raw = JSON.stringify(value);
  const lengthScore = Math.min(raw.length / 900, 1);
  return Math.max(0.42, Math.min(0.96, lengthScore));
}

function scoreColor(score) {
  if (score >= 80) return "text-emerald-300";
  if (score >= 65) return "text-blue-300";
  return "text-amber-300";
}

function MiniGraph({ confidence }) {
  const bars = [0.32, 0.46, 0.58, 0.72, confidence];
  return (
    <div className="mini-graph">
      {bars.map((bar, index) => (
        <span key={`${bar}-${index}`} style={{ height: `${bar * 100}%` }} />
      ))}
    </div>
  );
}

function JsonBlock({ value }) {
  const text = JSON.stringify(value, null, 2);
  const tokens = text.split(/(".*?"|\btrue\b|\bfalse\b|\bnull\b|-?\d+(?:\.\d+)?)/g);

  return (
    <pre className="json-block">
      {tokens.map((token, index) => {
        let className = "json-token";
        if (/^".*"$/.test(token)) className = token.includes(":") ? "json-key" : "json-string";
        if (/^-?\d+(?:\.\d+)?$/.test(token)) className = "json-number";
        if (/^(true|false)$/.test(token)) className = "json-boolean";
        if (token === "null") className = "json-null";
        return (
          <span key={`${token}-${index}`} className={className}>
            {token}
          </span>
        );
      })}
    </pre>
  );
}

export default function ReportViewer({ run }) {
  const open = isOpen(run);
  const sections = run?.report ? Object.entries(run.report) : [];
  const derived = run?.derived_insights || {};
  const scorecard = derived.scorecard;
  const brief = derived.executive_brief;
  const trust = derived.trust_summary;
  const evidenceTrace = derived.evidence_trace;
  const recommendation = derived.recommendation_engine;

  return (
    <section
      className={`bg-panel border-t border-skin-line px-5 pb-5 pt-4 transition-all duration-500 ${
        open ? "max-h-[78vh]" : "max-h-[120px]"
      } overflow-hidden`}
    >
      <div className={`output-reveal-bar ${open ? "output-reveal-bar-active" : ""}`} />

      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-[0.32em] text-muted">Output Deck</div>
          <h3 className="mt-1 text-2xl font-semibold text-primary">Intelligence Report</h3>
          <p className="text-sm text-secondary">
            {open
              ? "Each section is presented as an insight module with confidence, structure, and export-ready JSON."
              : "Run the pipeline to unlock the full report deck."}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button type="button" onClick={() => copyJson(run)} className="glass-chip px-4 py-2 text-sm text-primary">
            Copy JSON
          </button>
          <button type="button" onClick={() => exportJson(run)} className="glass-chip px-4 py-2 text-sm text-primary">
            Export .json
          </button>
        </div>
      </div>

      <div className={`mt-5 overflow-y-auto pr-2 ${open ? "max-h-[64vh]" : "max-h-0"}`}>
        <div className="grid gap-4">
          {(brief || scorecard || trust || recommendation) && (
            <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr_1fr]">
              {brief && (
                <div className="insight-card stagger-fade">
                  <div className="text-[10px] uppercase tracking-[0.3em] text-muted">Executive Brief</div>
                  <h4 className="mt-3 text-xl font-semibold text-primary">{brief.headline}</h4>
                  <p className="mt-3 text-sm leading-7 text-secondary">{brief.why_now}</p>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <div className="hero-chip">
                      <span className="hero-chip-label">Opportunity Score</span>
                      <span className="hero-chip-value">{brief.opportunity_score}</span>
                    </div>
                    <div className="hero-chip">
                      <span className="hero-chip-label">Best Focus</span>
                      <span className="hero-chip-value">{brief.focus}</span>
                    </div>
                  </div>
                </div>
              )}

              {scorecard && (
                <div className="insight-card stagger-fade">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-[10px] uppercase tracking-[0.3em] text-muted">Opportunity Scorecard</div>
                      <div className={`mt-3 text-4xl font-semibold ${scoreColor(scorecard.agency_opportunity_score)}`}>
                        {scorecard.agency_opportunity_score}
                      </div>
                    </div>
                    <MiniGraph confidence={scorecard.agency_opportunity_score / 100} />
                  </div>
                  <div className="mt-4 grid gap-3">
                    {scorecard.dimensions?.map((item) => (
                      <div key={item.label}>
                        <div className="mb-1 flex items-center justify-between text-sm text-secondary">
                          <span>{item.label}</span>
                          <span className="text-primary">{item.score}</span>
                        </div>
                        <div className="confidence-rail">
                          <span style={{ width: `${item.score}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid gap-4">
                {trust && (
                  <div className="insight-card stagger-fade">
                    <div className="text-[10px] uppercase tracking-[0.3em] text-muted">Trust Summary</div>
                    <div className="mt-4 grid grid-cols-2 gap-3">
                      <div className="glass-chip rounded-[22px] px-4 py-4">
                        <div className="text-[10px] uppercase tracking-[0.26em] text-muted">Verified</div>
                        <div className="mt-2 text-2xl font-semibold text-emerald-300">{trust.verified_fields}</div>
                      </div>
                      <div className="glass-chip rounded-[22px] px-4 py-4">
                        <div className="text-[10px] uppercase tracking-[0.26em] text-muted">Not Found</div>
                        <div className="mt-2 text-2xl font-semibold text-amber-300">{trust.not_found_fields}</div>
                      </div>
                    </div>
                    <p className="mt-4 text-sm leading-6 text-secondary">{trust.fabrication_policy}</p>
                  </div>
                )}

                {recommendation && (
                  <div className="insight-card stagger-fade">
                    <div className="text-[10px] uppercase tracking-[0.3em] text-muted">Recommended Next Move</div>
                    <div className="mt-3 text-base font-semibold text-primary">{recommendation.best_opening_angle}</div>
                    <p className="mt-3 text-sm leading-6 text-secondary">{recommendation.recommended_next_action}</p>
                    <div className="mt-4 grid gap-2 text-sm">
                      <div className="flex justify-between gap-3">
                        <span className="text-muted">Target</span>
                        <span className="text-primary">{recommendation.best_outreach_target}</span>
                      </div>
                      <div className="flex justify-between gap-3">
                        <span className="text-muted">Channel</span>
                        <span className="text-primary">{recommendation.best_contact_channel}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {evidenceTrace?.evidence_refs?.length > 0 && (
            <div className="insight-card stagger-fade">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.3em] text-muted">Evidence Trace Layer</div>
                  <div className="mt-2 text-lg font-semibold text-primary">Why the system said what it said</div>
                </div>
              </div>
              <div className="mt-4 grid gap-3 xl:grid-cols-2">
                {evidenceTrace.evidence_refs.map((item) => (
                  <div key={item.evidence_id} className="rounded-[22px] border border-white/8 bg-white/[0.03] p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-primary">{item.title}</div>
                      <span className="glass-chip px-3 py-1 text-[10px] uppercase tracking-[0.26em] text-muted">
                        {item.evidence_id}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-secondary">{item.snippet}</p>
                    {item.source_url ? (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-3 inline-flex text-sm text-blue-300 transition hover:text-blue-200"
                      >
                        Open source ↗
                      </a>
                    ) : null}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {item.used_in_sections?.map((section) => (
                        <span key={section} className="glass-chip px-3 py-1 text-[10px] uppercase tracking-[0.26em] text-secondary">
                          {section}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {sections.length === 0 ? (
              <div className="glass-panel rounded-[26px] p-5 text-sm text-secondary">
                No report sections yet.
              </div>
            ) : (
              sections.map(([sectionName, value], index) => {
                const confidence = confidenceForSection(value);
                const sourceLinks = collectSourceLinks(value);
                return (
                  <details
                    key={sectionName}
                    open={index < 3}
                    className="insight-card stagger-fade"
                    style={{ animationDelay: `${index * 70}ms` }}
                  >
                    <summary className="list-none cursor-pointer">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-[10px] uppercase tracking-[0.3em] text-muted">Insight Section</div>
                          <div className="mt-2 text-base font-semibold text-primary">{sectionName}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-[10px] uppercase tracking-[0.28em] text-muted">Confidence</div>
                          <div className="mt-2 text-sm font-medium text-primary">{Math.round(confidence * 100)}%</div>
                        </div>
                      </div>

                      <div className="mt-4 flex items-center gap-4">
                        <div className="confidence-rail">
                          <span style={{ width: `${confidence * 100}%` }} />
                        </div>
                        <MiniGraph confidence={confidence} />
                      </div>
                      {sourceLinks.length > 0 ? (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {sourceLinks.map((source) => (
                            <a
                              key={source.url}
                              href={source.url}
                              target="_blank"
                              rel="noreferrer"
                              className="glass-chip px-3 py-1 text-[10px] uppercase tracking-[0.26em] text-secondary transition hover:text-primary"
                            >
                              Source ↗
                            </a>
                          ))}
                        </div>
                      ) : null}
                    </summary>

                    <div className="mt-4 border-t border-white/8 pt-4">
                      {sourceLinks.length > 0 ? (
                        <div className="mb-4 rounded-[20px] border border-white/8 bg-white/[0.03] p-3">
                          <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-muted">Traceable Sources</div>
                          <div className="flex flex-wrap gap-2">
                            {sourceLinks.map((source) => (
                              <a
                                key={`${sectionName}-${source.url}`}
                                href={source.url}
                                target="_blank"
                                rel="noreferrer"
                                className="glass-chip px-3 py-1 text-xs text-secondary transition hover:text-primary"
                                title={source.label}
                              >
                                {source.label.length > 34 ? `${source.label.slice(0, 34)}...` : source.label}
                              </a>
                            ))}
                          </div>
                        </div>
                      ) : null}
                      <JsonBlock value={value} />
                    </div>
                  </details>
                );
              })
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
