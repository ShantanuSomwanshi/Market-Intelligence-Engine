function FieldIcon({ children }) {
  return <span className="field-icon">{children}</span>;
}

export default function InputForm({ values, onChange, onSubmit, isSubmitting, currentRun, onOpenCommand }) {
  return (
    <form
      onSubmit={onSubmit}
      className="glass-panel stagger-fade grid gap-4 rounded-[30px] p-5 md:grid-cols-[1.1fr_1.8fr_auto_auto] md:items-end"
    >
      <label className="grid gap-2 text-xs uppercase tracking-[0.28em] text-muted">
        Company Name
        <div className="input-shell">
          <FieldIcon>◉</FieldIcon>
          <input
            className="lux-input"
            name="company_name"
            placeholder="Apple, Stripe, Notion..."
            value={values.company_name}
            onChange={onChange}
          />
        </div>
      </label>

      <label className="grid gap-2 text-xs uppercase tracking-[0.28em] text-muted">
        Category
        <div className="input-shell">
          <FieldIcon>△</FieldIcon>
          <input
            className="lux-input"
            name="category_description"
            placeholder="AI infrastructure, luxury retail, biotech therapeutics..."
            value={values.category_description}
            onChange={onChange}
          />
        </div>
      </label>

      <button type="submit" disabled={isSubmitting} className="launch-button">
        <span className="launch-button-sheen" />
        <span className="launch-button-label">{isSubmitting ? "Initializing..." : "Launch Pipeline"}</span>
      </button>

      <div className="signal-card">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.26em] text-muted">Latest Run</div>
            <div className="mt-1 truncate text-sm font-medium text-primary">
              {currentRun?.input?.company_name || "No run yet"}
            </div>
          </div>
          <button type="button" onClick={onOpenCommand} className="glass-chip px-3 py-2 text-[11px] text-secondary">
            Ctrl+K
          </button>
        </div>
      </div>
    </form>
  );
}
