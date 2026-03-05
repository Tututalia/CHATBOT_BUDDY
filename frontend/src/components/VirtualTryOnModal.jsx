import React, { useState, useRef, useCallback } from "react";
import "./VirtualTryOnModal.css";

// Resize image on canvas to reduce upload size and speed up Vertex AI processing
function resizeImageFile(file, maxDim = 1024, quality = 0.85) {
  return new Promise((resolve) => {
    const img = new window.Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      let { width, height } = img;
      if (
        width <= maxDim &&
        height <= maxDim &&
        file.size <= 1.5 * 1024 * 1024
      ) {
        resolve(file); // Already small enough
        return;
      }
      const scale = Math.min(maxDim / width, maxDim / height, 1);
      width = Math.round(width * scale);
      height = Math.round(height * scale);
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, width, height);
      canvas.toBlob(
        (blob) => {
          if (blob) {
            const resized = new File([blob], file.name, { type: "image/jpeg" });
            resolve(resized);
          } else {
            resolve(file);
          }
        },
        "image/jpeg",
        quality,
      );
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(file);
    };
    img.src = url;
  });
}

export default function VirtualTryOnModal({ product, onClose }) {
  const [personImage, setPersonImage] = useState(null);
  const [personPreview, setPersonPreview] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [zoomImage, setZoomImage] = useState(null);
  const [zoomScale, setZoomScale] = useState(1);
  const fileInputRef = useRef(null);

  // Zoom lightbox handlers
  const openZoom = useCallback((src) => {
    if (src) {
      setZoomImage(src);
      setZoomScale(1);
    }
  }, []);

  const closeZoom = useCallback(() => {
    setZoomImage(null);
    setZoomScale(1);
  }, []);

  const handleZoomIn = useCallback((e) => {
    e.stopPropagation();
    setZoomScale((s) => Math.min(s + 0.3, 5));
  }, []);

  const handleZoomOut = useCallback((e) => {
    e.stopPropagation();
    setZoomScale((s) => Math.max(s - 0.3, 0.5));
  }, []);

  const handleZoomWheel = useCallback((e) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      setZoomScale((s) => Math.min(s + 0.15, 5));
    } else {
      setZoomScale((s) => Math.max(s - 0.15, 0.5));
    }
  }, []);

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Please upload a valid image file (JPG, PNG, etc.)");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Image size must be less than 10MB");
      return;
    }
    setError("");
    setPersonImage(file);
    setResultImage(null);
    const reader = new FileReader();
    reader.onloadend = () => setPersonPreview(reader.result);
    reader.readAsDataURL(file);
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleTryOn = async () => {
    if (!personImage) {
      setError("Please upload your photo first");
      return;
    }
    setIsLoading(true);
    setError("");
    setResultImage(null);

    try {
      // Resize person image for faster upload & Vertex AI processing
      const optimizedPerson = await resizeImageFile(personImage, 1024, 0.85);
      const formData = new FormData();
      formData.append("person_image", optimizedPerson);

      // Fetch the product image and send it as a file for maximum reliability
      const productImgUrl = product.image_reference || "";
      if (productImgUrl) {
        try {
          const imgResp = await fetch(productImgUrl);
          if (imgResp.ok) {
            const blob = await imgResp.blob();
            const ext = productImgUrl.split(".").pop() || "jpg";
            formData.append("product_image", blob, `product.${ext}`);
          } else {
            // Fallback: send the URL string instead
            formData.append("product_image_url", productImgUrl);
          }
        } catch {
          // Fallback: send the URL string instead
          formData.append("product_image_url", productImgUrl);
        }
      }

      const response = await fetch("http://localhost:8000/api/virtual-tryon", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setResultImage(data.image);
      } else {
        setError(
          data.error ||
            "Virtual try-on failed. Please try with a clearer full-body photo.",
        );
      }
    } catch (err) {
      console.error("Virtual try-on error:", err);
      setError(
        "Failed to connect to the virtual try-on service. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setPersonImage(null);
    setPersonPreview(null);
    setResultImage(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="vto-overlay" onClick={onClose}>
      <div className="vto-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="vto-header">
          <div className="vto-header-title">
            <span className="vto-header-icon">👗</span>
            <div>
              <h3>Virtual Trial Room</h3>
              <p className="vto-subtitle">Try on {product.product_name}</p>
            </div>
          </div>
          <button
            className="vto-close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="vto-body">
          {/* Product preview (left side) */}
          <div className="vto-product-section">
            <div className="vto-section-label">Product</div>
            <div
              className="vto-product-preview vto-zoomable"
              onClick={() =>
                openZoom(product.image_reference || "/images/placeholder.png")
              }
              title="Click to zoom"
            >
              <img
                src={product.image_reference || "/images/placeholder.png"}
                alt={product.product_name}
                onError={(e) => {
                  e.target.src = "/images/placeholder.png";
                }}
              />
              <div className="vto-zoom-hint">🔍</div>
            </div>
            <div className="vto-product-name">{product.product_name}</div>
          </div>

          {/* Arrow / Plus indicator */}
          <div className="vto-plus-indicator">
            <span>+</span>
          </div>

          {/* Upload section (middle) */}
          <div className="vto-upload-section">
            <div className="vto-section-label">Your Photo</div>
            {!personPreview ? (
              <div
                className={`vto-dropzone ${dragActive ? "drag-active" : ""}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="vto-dropzone-icon">📸</div>
                <p className="vto-dropzone-text">
                  Drag & drop your full-body photo here
                </p>
                <p className="vto-dropzone-hint">or click to browse</p>
                <span className="vto-dropzone-formats">
                  JPG, PNG • Max 10MB
                </span>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleInputChange}
                  className="vto-file-input"
                />
              </div>
            ) : (
              <div className="vto-person-preview">
                <img
                  src={personPreview}
                  alt="Your photo"
                  className="vto-zoomable"
                  onClick={() => openZoom(personPreview)}
                  title="Click to zoom"
                />
                <div
                  className="vto-zoom-hint"
                  onClick={() => openZoom(personPreview)}
                >
                  🔍
                </div>
                <button
                  className="vto-change-photo-btn"
                  onClick={handleReset}
                  title="Change photo"
                >
                  🔄 Change
                </button>
              </div>
            )}
          </div>

          {/* Arrow indicator */}
          <div className="vto-arrow-indicator">
            <span>→</span>
          </div>

          {/* Result section (right) */}
          <div className="vto-result-section">
            <div className="vto-section-label">Try-On Result</div>
            <div className="vto-result-preview">
              {isLoading ? (
                <div className="vto-loading">
                  <div className="vto-spinner"></div>
                  <p>Generating your virtual try-on...</p>
                  <p className="vto-loading-hint">
                    This may take a few seconds
                  </p>
                </div>
              ) : resultImage ? (
                <img
                  src={resultImage}
                  alt="Virtual try-on result"
                  className="vto-zoomable"
                  onClick={() => openZoom(resultImage)}
                  title="Click to zoom"
                />
              ) : (
                <div className="vto-result-placeholder">
                  <span className="vto-result-placeholder-icon">🪞</span>
                  <p>Your try-on result will appear here</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="vto-error">
            <span>⚠️</span> {error}
          </div>
        )}

        {/* Footer / Action */}
        <div className="vto-footer">
          <div className="vto-tips">
            <strong>💡 Tips:</strong> Use a clear, full-body photo with good
            lighting for best results.
          </div>
          <button
            className="vto-try-btn"
            onClick={handleTryOn}
            disabled={!personImage || isLoading}
          >
            {isLoading ? (
              <>
                <span className="vto-btn-spinner"></span> Generating...
              </>
            ) : resultImage ? (
              "🔄 Try Again"
            ) : (
              "✨ Try It On!"
            )}
          </button>
        </div>
      </div>

      {/* Zoom Lightbox Overlay — click anywhere outside the image to close */}
      {zoomImage && (
        <div
          className="vto-zoom-overlay"
          onClick={(e) => {
            e.stopPropagation();
            closeZoom();
          }}
          onWheel={handleZoomWheel}
        >
          <div
            className="vto-zoom-controls"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="vto-zoom-ctrl-btn"
              onClick={handleZoomIn}
              title="Zoom In"
            >
              ＋
            </button>
            <span className="vto-zoom-level">
              {Math.round(zoomScale * 100)}%
            </span>
            <button
              className="vto-zoom-ctrl-btn"
              onClick={handleZoomOut}
              title="Zoom Out"
            >
              －
            </button>
            <button
              className="vto-zoom-ctrl-btn vto-zoom-close"
              onClick={(e) => {
                e.stopPropagation();
                closeZoom();
              }}
              title="Close"
            >
              ✕
            </button>
          </div>
          <img
            src={zoomImage}
            alt="Zoomed view"
            className="vto-zoom-img"
            style={{ transform: `scale(${zoomScale})` }}
            draggable={false}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}
