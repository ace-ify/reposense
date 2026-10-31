import React, { useEffect, useRef, useState, useCallback } from "react";
import * as pdfjsLib from "pdfjs-dist";
import {
  ChevronLeft,
  ChevronRight,
  Minus,
  Plus,
  Maximize2,
  Search,
  FileText,
  AlertCircle,
  Loader2,
  Minimize2,
} from "lucide-react";
import { HighlightBox } from "../types";

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs`;

interface PdfViewerProps {
  pdfUrl: string | null;
  targetPageIndex: number;
  activeHighlight: HighlightBox | null;
  onPageChange?: (pageIndex: number) => void;
  documentTitle?: string;
}

export const PdfViewer: React.FC<PdfViewerProps> = ({
  pdfUrl,
  targetPageIndex,
  activeHighlight,
  onPageChange,
  documentTitle,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const highlightRef = useRef<HTMLDivElement | null>(null);

  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState<number>(targetPageIndex + 1);
  const [numPages, setNumPages] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.25);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isFitWidth, setIsFitWidth] = useState<boolean>(false);

  // Sync when targetPageIndex changes from citation clicks
  useEffect(() => {
    if (pdfDoc && targetPageIndex >= 0 && targetPageIndex < pdfDoc.numPages) {
      setCurrentPage(targetPageIndex + 1);
    }
  }, [targetPageIndex, pdfDoc]);

  // Auto-scroll highlight into view when page renders
  useEffect(() => {
    if (activeHighlight && activeHighlight.pageIndex === currentPage - 1 && highlightRef.current) {
      const timer = setTimeout(() => {
        highlightRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [currentPage, activeHighlight]);

  // Load PDF document
  useEffect(() => {
    if (!pdfUrl) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    const loadingTask = pdfjsLib.getDocument(pdfUrl);
    loadingTask.promise
      .then((doc) => {
        if (!isMounted) return;
        setPdfDoc(doc);
        setNumPages(doc.numPages);
        setCurrentPage(Math.min(targetPageIndex + 1, doc.numPages));
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error("PDF load error:", err);
        setError("Unable to load document preview. You can still download the file.");
        setLoading(false);
      });

    return () => {
      isMounted = false;
      try {
        loadingTask.destroy();
      } catch (e) {
        // ignore
      }
    };
  }, [pdfUrl]);

  // Render current page to canvas
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    let renderTask: any = null;

    pdfDoc.getPage(currentPage).then((page: any) => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      let effectiveScale = scale;
      if (isFitWidth && containerRef.current) {
        const containerWidth = containerRef.current.clientWidth - 48; // padding
        const unscaledViewport = page.getViewport({ scale: 1.0 });
        if (unscaledViewport.width > 0) {
          effectiveScale = containerWidth / unscaledViewport.width;
        }
      }

      const viewport = page.getViewport({ scale: effectiveScale });
      const context = canvas.getContext("2d");
      if (!context) return;

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      renderTask = page.render(renderContext);
      renderTask.promise.catch((err: any) => {
        if (err?.name !== "RenderingCancelledException") {
          console.warn("Render error:", err);
        }
      });
    });

    return () => {
      if (renderTask) {
        renderTask.cancel();
      }
    };
  }, [pdfDoc, currentPage, scale, isFitWidth]);

  const handlePrevPage = useCallback(() => {
    if (currentPage > 1) {
      const p = currentPage - 1;
      setCurrentPage(p);
      onPageChange?.(p - 1);
    }
  }, [currentPage, onPageChange]);

  const handleNextPage = useCallback(() => {
    if (currentPage < numPages) {
      const p = currentPage + 1;
      setCurrentPage(p);
      onPageChange?.(p - 1);
    }
  }, [currentPage, numPages, onPageChange]);

  const handlePageSelect = (pageNo: number) => {
    const valid = Math.max(1, Math.min(pageNo, numPages));
    setCurrentPage(valid);
    onPageChange?.(valid - 1);
  };

  // Check if highlight applies strictly to current page
  const showHighlight = activeHighlight && activeHighlight.pageIndex === currentPage - 1;

  if (!pdfUrl) {
    return (
      <div className="pdf-viewer-empty-state">
        <FileText size={48} className="empty-icon" />
        <div className="empty-title">No Document Selected</div>
        <p className="empty-subtitle">Select a report from your research desk to inspect evidence.</p>
      </div>
    );
  }

  return (
    <div className="pdf-workspace-viewer" ref={containerRef}>
      {/* Top Document Toolbar */}
      <div className="pdf-viewer-toolbar">
        {/* Left: Page Jumper */}
        <div className="pdf-toolbar-group page-controls">
          <button
            type="button"
            className="pdf-tool-btn"
            disabled={currentPage <= 1}
            onClick={handlePrevPage}
            title="Previous Page"
          >
            <ChevronLeft size={16} />
          </button>

          <div className="page-select-wrapper">
            <select
              className="page-select-input"
              value={currentPage}
              onChange={(e) => handlePageSelect(Number(e.target.value))}
            >
              {Array.from({ length: numPages }, (_, i) => i + 1).map((pg) => (
                <option key={pg} value={pg}>
                  {pg}
                </option>
              ))}
            </select>
            <span className="page-total">/ {numPages}</span>
          </div>

          <button
            type="button"
            className="pdf-tool-btn"
            disabled={currentPage >= numPages}
            onClick={handleNextPage}
            title="Next Page"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        {/* Center: Zoom Controls */}
        <div className="pdf-toolbar-group zoom-controls">
          <button
            type="button"
            className="pdf-tool-btn"
            onClick={() => setScale((s) => Math.max(0.6, s - 0.15))}
            title="Zoom Out"
          >
            <Minus size={15} />
          </button>

          <select
            className="zoom-select-input"
            value={Math.round(scale * 100)}
            onChange={(e) => {
              setIsFitWidth(false);
              setScale(Number(e.target.value) / 100);
            }}
          >
            <option value="75">75%</option>
            <option value="100">100%</option>
            <option value="125">125%</option>
            <option value="150">150%</option>
            <option value="175">175%</option>
            <option value="200">200%</option>
          </select>

          <button
            type="button"
            className="pdf-tool-btn"
            onClick={() => setScale((s) => Math.min(2.5, s + 0.15))}
            title="Zoom In"
          >
            <Plus size={15} />
          </button>

          <button
            type="button"
            className={`pdf-tool-btn ${isFitWidth ? "active" : ""}`}
            onClick={() => setIsFitWidth(!isFitWidth)}
            title={isFitWidth ? "Original Scale" : "Fit to Width"}
          >
            {isFitWidth ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>
        </div>

        {/* Right: Document Search Input */}
        <div className="pdf-toolbar-group search-box">
          <Search size={14} className="search-icon" />
          <input
            type="text"
            className="document-search-input"
            placeholder="Search in document..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Main Canvas Scroll Area */}
      <div className="pdf-canvas-viewport">
        {loading && (
          <div className="pdf-overlay-status loading">
            <Loader2 size={24} className="spinner-icon" />
            <span>Rendering page {currentPage}...</span>
          </div>
        )}

        {error && (
          <div className="pdf-overlay-status error">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        <div className="pdf-canvas-container">
          <canvas ref={canvasRef} className="pdf-canvas" />

          {/* Glowing Bounding Box Highlight Overlay */}
          {showHighlight && activeHighlight && (
            <div
              ref={highlightRef}
              className="bounding-box-highlight active-citation"
              style={{
                position: "absolute",
                left: `${activeHighlight.bbox.x0 * 100}%`,
                top: `${activeHighlight.bbox.y0 * 100}%`,
                width: `${Math.max(0.04, activeHighlight.bbox.x1 - activeHighlight.bbox.x0) * 100}%`,
                height: `${Math.max(0.02, activeHighlight.bbox.y1 - activeHighlight.bbox.y0) * 100}%`,
              }}
            >
              <div className="highlight-tag-badge">
                {activeHighlight.label || "Cited Evidence"}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
