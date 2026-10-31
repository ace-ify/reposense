import React, { useState, useMemo } from "react";
import { TableItem } from "../types";
import { Table, ArrowUpDown, ArrowUp, ArrowDown, ExternalLink, Info, FileSpreadsheet } from "lucide-react";

interface SelectedValueInfo {
  table: TableItem;
  rowIdx: number;
  colIdx: number;
  value: any;
  header: string;
  rowLabel: string;
  unit?: string;
  footnotes: string[];
}

interface TableExplorerProps {
  tables: TableItem[];
  isLoading?: boolean;
  onHighlightTable?: (table: TableItem, label?: string) => void;
}

export const TableExplorer: React.FC<TableExplorerProps> = ({
  tables,
  isLoading = false,
  onHighlightTable,
}) => {
  const [selectedTableIdx, setSelectedTableIdx] = useState<number>(0);
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [selectedValue, setSelectedValue] = useState<SelectedValueInfo | null>(null);

  const activeTable = tables[selectedTableIdx] || null;

  // Flatten headers if multi-level
  const displayHeaders = useMemo(() => {
    if (!activeTable || !activeTable.headers || activeTable.headers.length === 0) return [];
    if (activeTable.headers.length === 1) return activeTable.headers[0];
    // If multi-level, join non-empty segments
    const rowCount = activeTable.headers.length;
    const colCount = Math.max(...activeTable.headers.map((h) => h.length));
    const flat: string[] = [];
    for (let c = 0; c < colCount; c++) {
      const parts: string[] = [];
      for (let r = 0; r < rowCount; r++) {
        const val = activeTable.headers[r]?.[c];
        if (val && !parts.includes(val)) parts.push(val);
      }
      flat.push(parts.join(" - ") || `Column ${c + 1}`);
    }
    return flat;
  }, [activeTable]);

  // Sortable rows
  const sortedRows = useMemo(() => {
    if (!activeTable || !activeTable.rows) return [];
    const rows = [...activeTable.rows];
    if (sortCol === null) return rows;

    return rows.sort((a, b) => {
      const valA = a[sortCol];
      const valB = b[sortCol];

      // Clean numeric conversion
      const numA = typeof valA === "number" ? valA : parseFloat(String(valA).replace(/[^0-9.-]/g, ""));
      const numB = typeof valB === "number" ? valB : parseFloat(String(valB).replace(/[^0-9.-]/g, ""));

      if (!isNaN(numA) && !isNaN(numB)) {
        return sortDir === "asc" ? numA - numB : numB - numA;
      }
      const strA = String(valA || "").toLowerCase();
      const strB = String(valB || "").toLowerCase();
      return sortDir === "asc" ? strA.localeCompare(strB) : strB.localeCompare(strA);
    });
  }, [activeTable, sortCol, sortDir]);

  const handleHeaderClick = (colIdx: number) => {
    if (sortCol === colIdx) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortCol(colIdx);
      setSortDir("asc");
    }
  };

  const handleCellClick = (row: any[], rowIdx: number, colIdx: number) => {
    if (!activeTable) return;
    const header = displayHeaders[colIdx] || `Col ${colIdx + 1}`;
    const rowLabel = String(row[0] || `Row ${rowIdx + 1}`);
    const cellVal = row[colIdx];

    // Find unit if defined
    let unit: string | undefined;
    if (activeTable.units) {
      for (const [k, v] of Object.entries(activeTable.units)) {
        if (header.toLowerCase().includes(k.toLowerCase())) {
          unit = v;
          break;
        }
      }
    }

    const info: SelectedValueInfo = {
      table: activeTable,
      rowIdx,
      colIdx,
      value: cellVal,
      header,
      rowLabel,
      unit,
      footnotes: activeTable.footnotes || [],
    };

    setSelectedValue(info);

    // Call highlight callback using table's actual bounding box (honest bounding box provenance)
    if (onHighlightTable) {
      onHighlightTable(
        activeTable,
        `Table Provenance · Page ${activeTable.printed_page_number || activeTable.pdf_page_index + 1}`
      );
    }
  };

  if (isLoading) {
    return (
      <div className="table-explorer-state loading">
        <div className="spinner" />
        <span>Loading structured table data from document...</span>
      </div>
    );
  }

  if (!tables || tables.length === 0) {
    return (
      <div className="table-explorer-state empty">
        <FileSpreadsheet size={32} className="state-icon" />
        <div className="state-title">No Structured Tables Detected</div>
        <div className="state-desc">
          This document either contains only narrative text or table extraction did not detect formal grid boundaries.
        </div>
      </div>
    );
  }

  return (
    <div className="table-explorer">
      {/* Table Selector Header */}
      <div className="table-explorer-toolbar">
        <div className="table-selector-group">
          <Table size={15} className="toolbar-icon" />
          <select
            className="table-select-input"
            value={selectedTableIdx}
            onChange={(e) => {
              setSelectedTableIdx(Number(e.target.value));
              setSortCol(null);
              setSelectedValue(null);
            }}
          >
            {tables.map((tbl, idx) => (
              <option key={tbl.table_id || idx} value={idx}>
                {tbl.title ? tbl.title.slice(0, 50) : `Table on Page ${tbl.printed_page_number || tbl.pdf_page_index + 1}`}
                {" "}({tbl.rows.length} rows)
              </option>
            ))}
          </select>
        </div>

        {activeTable && onHighlightTable && (
          <button
            type="button"
            className="btn-text-action"
            onClick={() =>
              onHighlightTable(
                activeTable,
                `Table ${activeTable.printed_page_number ? `p.${activeTable.printed_page_number}` : ""}`
              )
            }
            title="Navigate to table page on PDF"
          >
            <ExternalLink size={13} />
            <span>Jump to Page {activeTable.printed_page_number || activeTable.pdf_page_index + 1}</span>
          </button>
        )}
      </div>

      {activeTable && (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                {displayHeaders.map((head, idx) => {
                  const isSorted = sortCol === idx;
                  return (
                    <th
                      key={idx}
                      className={`sortable-th ${isSorted ? "sorted" : ""}`}
                      onClick={() => handleHeaderClick(idx)}
                      title="Click to sort column"
                    >
                      <div className="th-content">
                        <span>{head}</span>
                        <span className="sort-icon">
                          {isSorted ? (
                            sortDir === "asc" ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                          ) : (
                            <ArrowUpDown size={12} className="sort-idle" />
                          )}
                        </span>
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, rIdx) => {
                const isRowSelected = selectedValue?.rowIdx === rIdx;
                return (
                  <tr key={rIdx} className={isRowSelected ? "row-selected" : ""}>
                    {row.map((cell: any, cIdx: number) => {
                      const isCellSelected = selectedValue?.rowIdx === rIdx && selectedValue?.colIdx === cIdx;
                      return (
                        <td
                          key={cIdx}
                          className={`table-cell ${isCellSelected ? "cell-selected" : ""}`}
                          onClick={() => handleCellClick(row, rIdx, cIdx)}
                        >
                          {cell !== null && cell !== undefined ? String(cell) : "—"}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Selected Cell Provenance Inspector */}
      {selectedValue && (
        <div className="selected-cell-inspector">
          <div className="inspector-header">
            <div className="inspector-title">
              <Info size={14} className="inspector-icon" />
              <span>SELECTED VALUE PROVENANCE</span>
            </div>
            {onHighlightTable && (
              <button
                type="button"
                className="btn-tiny-cobalt"
                onClick={() =>
                  onHighlightTable(
                    selectedValue.table,
                    `Table Row: ${selectedValue.rowLabel}`
                  )
                }
              >
                Highlight on PDF
              </button>
            )}
          </div>

          <div className="inspector-grid">
            <div className="inspector-field">
              <span className="field-label">Source Document</span>
              <span className="field-value">{selectedValue.table.document_id}</span>
            </div>
            <div className="inspector-field">
              <span className="field-label">Page</span>
              <span className="field-value">
                Page {selectedValue.table.printed_page_number || selectedValue.table.pdf_page_index + 1} (PDF index: {selectedValue.table.pdf_page_index})
              </span>
            </div>
            <div className="inspector-field">
              <span className="field-label">Row</span>
              <span className="field-value bold">{selectedValue.rowLabel}</span>
            </div>
            <div className="inspector-field">
              <span className="field-label">Column</span>
              <span className="field-value">{selectedValue.header}</span>
            </div>
            <div className="inspector-field">
              <span className="field-label">Value</span>
              <span className="field-value bold highlight">{String(selectedValue.value)}</span>
            </div>
            {selectedValue.unit && (
              <div className="inspector-field">
                <span className="field-label">Unit</span>
                <span className="field-value">{selectedValue.unit}</span>
              </div>
            )}
          </div>

          {selectedValue.footnotes.length > 0 && (
            <div className="inspector-footnotes">
              <span className="field-label">Footnotes:</span>
              <ul>
                {selectedValue.footnotes.map((fn, i) => (
                  <li key={i}>{fn}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="inspector-provenance-note">
            Bounding Box provenance: <code>[x0: {selectedValue.table.bbox?.x0.toFixed(3) || "0"}, y0: {selectedValue.table.bbox?.y0.toFixed(3) || "0"}, x1: {selectedValue.table.bbox?.x1.toFixed(3) || "1"}, y1: {selectedValue.table.bbox?.y1.toFixed(3) || "1"}]</code>
          </div>
        </div>
      )}
    </div>
  );
};

