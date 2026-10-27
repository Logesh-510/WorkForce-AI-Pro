import { Search } from "lucide-react";

export default function WorkforceTable({
  title,
  description,
  columns,
  rows,
  loading,
  error,
  search,
  onSearchChange,
  emptyMessage,
}) {
  const normalizedSearch = search.trim().toLowerCase();

  const filteredRows = rows.filter((row) =>
    columns.some((column) =>
      String(column.value(row) ?? "")
        .toLowerCase()
        .includes(normalizedSearch)
    )
  );

  return (
    <section className="panel workforce-panel">
      <div className="panel-header workforce-table-header">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
        <span className="model-tag">
          {loading ? "LOADING" : `${filteredRows.length} RECORDS`}
        </span>
      </div>

      <label className="search-box workforce-search">
        <Search size={17} />
        <input
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder={`Search ${title.toLowerCase()}...`}
          aria-label={`Search ${title}`}
        />
      </label>

      {error && (
        <div className="workforce-message workforce-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="workforce-message">
          Loading {title.toLowerCase()}...
        </div>
      ) : !error && filteredRows.length === 0 ? (
        <div className="workforce-message">
          {normalizedSearch ? "No matching records found." : emptyMessage}
        </div>
      ) : !error ? (
        <div className="workforce-table-wrap">
          <table className="workforce-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((row) => (
                <tr key={row.id}>
                  {columns.map((column) => (
                    <td key={column.key}>
                      {column.render
                        ? column.render(row)
                        : column.value(row) ?? "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
