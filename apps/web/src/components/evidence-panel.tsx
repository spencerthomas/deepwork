import type { EvidenceRecord } from "../lib/task-types";

export function EvidencePanel({ evidence }: { evidence: readonly EvidenceRecord[] }) {
  return (
    <section className="evidence-panel" aria-labelledby="evidence-heading">
      <header className="evidence-heading">
        <div>
          <p className="eyebrow">Provenance</p>
          <h2 id="evidence-heading">Evidence inspected</h2>
        </div>
        <span>{evidence.length} records</span>
      </header>

      {evidence.length === 0 ? (
        <div className="evidence-empty" role="status">
          No evidence has been recorded for this task yet. A result is not considered verified
          without explicit evidence.
        </div>
      ) : (
        <ul className="evidence-list">
          {evidence.map((record) => (
            <li key={record.evidenceId}>
              <div className="evidence-card-heading">
                <strong>{record.kind}</strong>
                <span className={record.verified ? "evidence-verified" : "evidence-unverified"}>
                  {record.verified ? "Verified" : "Not independently verified"}
                </span>
              </div>
              <p>{record.summary}</p>
              <dl>
                <div>
                  <dt>Source</dt>
                  <dd>{record.source}</dd>
                </div>
                <div>
                  <dt>Evidence ID</dt>
                  <dd>{record.evidenceId}</dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
