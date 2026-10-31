import React, { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs`;

interface BoundingBox {
  x0: float;
  y0: float;
  x1: float;
  y1: float;
  coordinate_system?: string;
}

type float = number;

interface HighlightBox {
  bbox: BoundingBox;
  id: string;
  label?: string;
  pageIndex: number;
}

interface PdfViewerProps {
  pdfUrl: string | null;
  targetPageIndex: number;
  activeHighlight: HighlightBox | null;
  onPageChange?: (pageIndex: number) => void;
}

export const PdfViewer: React.FC<PdfViewerProps> = ({
  pdfUrl,
  targetPageIndex,
  activeHighlight,
  onPageChange,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const highlightRef = useRef<HTMLDivElement | null>(null);
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState<number>(targetPageIndex + 1);
  const [numPages, setNumPages] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.15);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Sync when targetPageIndex changes from citation clicks
  useEffect(() => {
    if (pdfDoc && targetPageIndex >= 0 && targetPageIndex < pdfDoc.numPages) {
      setCurrentPage(targetPageIndex + 1);
    }
  }, [targetPageIndex, pdfDoc]);

  // Auto-scroll highlight into view when page renders
  useEffect(() => {
    if (activeHighlight && activeHighlight.pageIndex === currentPage - 1 && highlightRef.current && containerRef.current) {
      setTimeout(() => {
        highlightRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 100);
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
        setError("Failed to load PDF preview. Use PDF download if needed.");
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

      const viewport = page.getViewport({ scale });
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
  }, [pdfDoc, currentPage, scale]);

  const handlePrevPage = () => {
    if (currentPage > 1) {
      const p = currentPage - 1;
      setCurrentPage(p);
      onPageChange?.(p - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < numPages) {
      const p = currentPage + 1;
      setCurrentPage(p);
      onPageChange?.(p - 1);
    }
  };

  // Check if highlight applies strictly to current page
  const showHighlight = activeHighlight && activeHighlight.pageIndex === currentPage - 1;

  return (
    <div className="pdf-viewer-container" ref={containerRef}>
      <div className="pdf-toolbar">
        <div className="pdf-nav">
          <button
            type="button"
            className="tool-btn"
            disabled={currentPage <= 1}
            onClick={handlePrevPage}
            title="Previous Page"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="page-indicator">
            Page {currentPage} of {numPages}
          </span>
          <button
            type="button"
            className="tool-btn"
            disabled={currentPage >= numPages}
            onClick={handleNextPage}
            title="Next Page"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        <div className="pdf-zoom">
          <button
            type="button"
            className="tool-btn"
            onClick={() => setScale((s) => Math.max(0.7, s - 0.15))}
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <span className="zoom-indicator">{Math.round(scale * 100)}%</span>
          <button
            type="button"
            className="tool-btn"
            onClick={() => setScale((s) => Math.min(2.0, s + 0.15))}
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
        </div>
      </div>

      <div className="pdf-canvas-wrapper">
        {loading && <div className="pdf-loading">Loading PDF page...</div>}
        {error && <div className="pdf-error">{error}</div>}

        <div className="canvas-overlay-container" style={{ position: "relative", display: "inline-block" }}>
          <canvas ref={canvasRef} className="pdf-canvas" />

          {/* Interactive Bounding Box Highlight Overlay */}
          {showHighlight && activeHighlight && (
            <div
              ref={highlightRef}
              className="bounding-box-highlight"
              style={{
                position: "absolute",
                left: `${activeHighlight.bbox.x0 * 100}%`,
                top: `${activeHighlight.bbox.y0 * 100}%`,
                width: `${Math.max(0.04, activeHighlight.bbox.x1 - activeHighlight.bbox.x0) * 100}%`,
                height: `${Math.max(0.02, activeHighlight.bbox.y1 - activeHighlight.bbox.y0) * 100}%`,
              }}
            >
              <div className="highlight-tag">
                {activeHighlight.label || "Cited Evidence"}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

